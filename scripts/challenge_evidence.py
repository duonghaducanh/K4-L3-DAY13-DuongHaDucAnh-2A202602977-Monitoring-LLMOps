"""Execute the supplied official challenge and capture metrics before selecting a log."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.challenge import load_challenge
from app.dashboard import percentile, render, summarize
from capture_evidence import capture

DEST = Path("submission/evidence/cp3-official")
DEST.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now(timezone.utc)


def save(name, value):
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    for name_env in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
        if os.getenv(name_env):
            text = text.replace(os.environ[name_env], "[REDACTED_API_KEY]")
    path = DEST / name
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def command(script, *args):
    result = subprocess.run([sys.executable, script, *args], capture_output=True, text=True,
                            encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if result.returncode:
        raise RuntimeError(f"{script} failed: {result.stdout}\n{result.stderr}")
    return result.stdout + result.stderr


def phase(name):
    start = now()
    output = command("scripts/load_test.py", "--challenge", "--concurrency", "5")
    end = now()
    (DEST / f"{name}-workload.txt").write_text(output, encoding="utf-8")
    rows = [json.loads(line) for line in Path("data/logs.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if start <= datetime.fromisoformat(r["ts"].replace("Z", "+00:00")) <= end]
    sent = [r for r in rows if r["event"] == "response_sent"]
    failed = [r for r in rows if r["event"] == "request_failed"]
    received = [r for r in rows if r["event"] == "request_received"]
    tools = [r for r in sent + failed if isinstance(r.get("tool_success"), bool)]
    metrics = {
        "phase": name, "start_utc": start.isoformat(), "end_utc": end.isoformat(),
        "received": len(received), "succeeded": len(sent), "failed": len(failed),
        "latency_p50_ms": percentile([r["latency_ms"] for r in sent], 50),
        "latency_p95_ms": percentile([r["latency_ms"] for r in sent], 95),
        "latency_p99_ms": percentile([r["latency_ms"] for r in sent], 99),
        "ttft_p95_ms": percentile([r["ttft_ms"] for r in sent], 95),
        "cost_total_usd": sum(r["cost_usd"] for r in sent),
        "error_rate_pct": 100 * len(failed) / len(received) if received else None,
        "retrieval_success_pct": 100 * sum(r["tool_success"] for r in tools) / len(tools) if tools else None,
        "quality_mean": sum(r["quality_score"] for r in sent) / len(sent) if sent else None,
    }
    save(f"{name}-metrics.json", metrics)
    snapshot = summarize(end=end)
    save(f"{name}-dashboard.json", snapshot)
    html = render(snapshot).replace("<main>", f'<h2>Official challenge phase: {name}</h2><p>Phase UTC: {start.isoformat()} → {end.isoformat()}<br>Phase requests: {len(received)}; P95: {metrics["latency_p95_ms"]} ms; error: {metrics["error_rate_pct"]}%</p><main>')
    page = DEST / f"{name}-dashboard.html"
    page.write_text(html, encoding="utf-8")
    capture(page, page.with_suffix(".png"))
    return metrics, sent + failed


def workload():
    if (DEST / "run.json").exists():
        raise RuntimeError("Official evidence already exists; preserve it before rerunning.")
    raw = Path("config/challenge.json").read_bytes()
    challenge = load_challenge()
    assert challenge.cohort == "K4", "Wrong cohort"
    health = httpx.get("http://127.0.0.1:8000/health").json()
    assert health["ok"] and not any(health["incidents"].values()), "Start with all incidents disabled"
    baseline, baseline_logs = phase("baseline")
    try:
        output = command("scripts/inject_incident.py")
        (DEST / "enable.txt").write_text(output, encoding="utf-8")
        incident, logs = phase("incident")
        # Metrics have been captured above; only now select a representative request.
        errors = [r for r in logs if r["event"] == "request_failed"]
        if errors:
            selected = errors[0]
            symptom = "request errors"
        elif incident["latency_p95_ms"] > challenge.latency_threshold_ms or incident["latency_p95_ms"] > baseline["latency_p95_ms"] * 1.5:
            selected = max(logs, key=lambda r: r.get("latency_ms", 0))
            symptom = "latency regression"
        else:
            selected = max(logs, key=lambda r: r.get("cost_usd", 0))
            symptom = "cost/quality comparison; inspect measured deltas"
        safe_log = {k:v for k,v in selected.items() if k != "payload"}
        path = save("13-incident-log.json", {"challenge_id": challenge.challenge_id, "selection_after_metric": now().isoformat(), "symptom": symptom, "log": safe_log})
        capture(path, path.with_suffix(".png"), "CP3 official - log selected after metrics")
    finally:
        output = command("scripts/inject_incident.py", "--disable")
        (DEST / "disable.txt").write_text(output, encoding="utf-8")
    recovery, recovery_logs = phase("recovery")
    assert len(logs) == len(baseline_logs) == len(recovery_logs) == len(challenge.queries)
    assert raw == Path("config/challenge.json").read_bytes() == Path("K4-L3B-challenge.json").read_bytes()
    # Preserve hashes instead of publishing the private query set/seed.
    save("run.json", {"challenge_id": challenge.challenge_id, "cohort": challenge.cohort,
                      "challenge_sha256": hashlib.sha256(raw).hexdigest(), "challenge_unmodified": True,
                      "query_count": len(challenge.queries), "concurrency": 5,
                      "query_set_sha256": hashlib.sha256(json.dumps(challenge.queries, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                      "baseline": baseline, "incident": incident, "recovery": recovery,
                      "correlation_id": selected["correlation_id"], "symptom": symptom,
                      "health_after": httpx.get("http://127.0.0.1:8000/health").json()})
    print(json.dumps({"baseline": baseline, "incident": incident, "recovery": recovery, "selected_correlation_id": selected["correlation_id"]}, indent=2))


def trace():
    from dotenv import load_dotenv
    load_dotenv()
    from langfuse import get_client
    from render_trace_evidence import page, waterfall
    run = json.loads((DEST / "run.json").read_text(encoding="utf-8"))
    client = get_client()
    try:
        start = datetime.fromisoformat(run["incident"]["start_utc"]) - timedelta(seconds=1)
        end = datetime.fromisoformat(run["incident"]["end_utc"]) + timedelta(seconds=1)
        rows, cursor = [], None
        while True:
            batch = client.api.observations.get_many(from_start_time=start, to_start_time=end,
                fields="core,basic,metadata,usage,model,prompt", limit=100, cursor=cursor).model_dump(mode="json", by_alias=True)
            rows.extend(batch["data"])
            cursor = batch.get("meta", {}).get("cursor")
            if not cursor:
                break
        chosen = [r for r in rows if r.get("metadata", {}).get("correlation_id") == run["correlation_id"]]
        if not chosen:
            raise RuntimeError("Selected trace not ingested yet; retry trace action later, not the workload")
        for row in chosen:
            # Query text is private coach material; timings/IDs/usage remain exact.
            row["metadata"] = {k:v for k,v in row.get("metadata", {}).items() if k != "query_preview" and not k.startswith(("scope.", "resourceAttributes."))}
            row["input"] = None
            row["output"] = None
        path = save("14-incident-trace.json", chosen)
        path.with_suffix(".html").write_text(page("CP3 official - actual Langfuse API waterfall", waterfall(chosen)), encoding="utf-8")
        capture(path.with_suffix(".html"), path.with_suffix(".png"))
        assert len({r["traceId"] for r in chosen}) == 1
        print(json.dumps([{k:r.get(k) for k in ["traceId", "name", "level", "startTime", "endTime", "statusMessage"]} for r in chosen], indent=2))
    finally:
        client.shutdown()


def compare():
    """Explain a potentially slow baseline using the same input in all three phases."""
    from dotenv import load_dotenv
    load_dotenv()
    from langfuse import get_client
    run = json.loads((DEST / "run.json").read_text(encoding="utf-8"))
    logs = [json.loads(line) for line in Path("data/logs.jsonl").read_text(encoding="utf-8").splitlines()]
    selected = next(r for r in logs if r.get("correlation_id") == run["correlation_id"] and r["event"] == "response_sent")
    correlations = {}
    for label in ("baseline", "incident", "recovery"):
        start, end = [datetime.fromisoformat(run[label][key]) for key in ("start_utc", "end_utc")]
        matches = [r for r in logs if r["event"] == "request_received" and
                   start <= datetime.fromisoformat(r["ts"].replace("Z", "+00:00")) <= end and
                   r.get("session_id") == selected.get("session_id") and r.get("user_id_hash") == selected.get("user_id_hash")]
        assert len(matches) == 1, "Cannot unambiguously match the same challenge input"
        correlations[label] = matches[0]["correlation_id"]
    client = get_client()
    try:
        data = client.api.observations.get_many(
            from_start_time=datetime.fromisoformat(run["baseline"]["start_utc"]),
            to_start_time=datetime.fromisoformat(run["recovery"]["end_utc"]),
            fields="core,basic,metadata,prompt", limit=100,
        ).model_dump(mode="json", by_alias=True)["data"]
        comparisons = []
        for label, correlation in correlations.items():
            rows = [r for r in data if r.get("metadata", {}).get("correlation_id") == correlation]
            assert {r["name"] for r in rows} >= {"lab-agent-run", "retrieval", "generation"}
            spans = {r["name"]: round((datetime.fromisoformat(r["endTime"].replace("Z", "+00:00")) - datetime.fromisoformat(r["startTime"].replace("Z", "+00:00"))).total_seconds()*1000, 3) for r in rows}
            root = next(r for r in rows if r["name"] == "lab-agent-run")
            comparisons.append({"phase": label, "correlation_id": correlation, "trace_id": root["traceId"],
                "duration_ms": spans, "root_time_outside_children_ms": round(spans["lab-agent-run"] - spans["retrieval"] - spans["generation"], 3),
                "prompt_source": root["metadata"].get("prompt_source"), "prompt_fetch_error": root["metadata"].get("prompt_fetch_error"),
                "prompt_version": root["metadata"].get("prompt_version")})
        path = save("15-span-comparison.json", {"challenge_id": run["challenge_id"], "challenge_threshold_ms": load_challenge().latency_threshold_ms,
            "same_input_matched_by_session_and_user_hash": True, "comparison": comparisons,
            "selection_note": "Initial baseline was also slow; compare span durations and recovery, not just incident/baseline ratio. Original run and initial heuristic retained."})
        capture(path, path.with_suffix(".png"), "CP3 official - same input, baseline vs incident vs recovery")
        print(json.dumps(comparisons, indent=2))
    finally:
        client.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["workload", "trace", "compare"])
    args = parser.parse_args()
    {"workload": workload, "trace": trace, "compare": compare}[args.action]()
