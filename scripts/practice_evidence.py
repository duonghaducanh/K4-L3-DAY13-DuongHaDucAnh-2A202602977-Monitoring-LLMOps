"""Practice only: record metrics first, then select a correlated error log."""
import concurrent.futures
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.dashboard import summarize, render
from capture_evidence import capture

DEST = Path("submission/evidence/cp3-practice")
DEST.mkdir(parents=True, exist_ok=True)


def snapshot(label):
    data = summarize()
    (DEST / f"{label}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    path = DEST / f"{label}.html"
    path.write_text(render(data), encoding="utf-8")
    capture(path, path.with_suffix(".png"))
    return data


with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30) as client:
    payloads = [json.loads(line) for line in Path("data/sample_queries.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    snapshot("before")
    began = datetime.now(timezone.utc).isoformat()
    client.post("/incidents/tool_fail/enable").raise_for_status()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            responses = list(pool.map(lambda body: client.post("/chat", json=body), payloads))
        metric = snapshot("12-incident-metric")
        # Selection occurs AFTER measuring symptoms, before looking up traces.
        rows = [json.loads(line) for line in Path("data/logs.jsonl").read_text(encoding="utf-8").splitlines()]
        failures = [r for r in rows if r.get("event") == "request_failed" and r["ts"] >= began]
        chosen = failures[0]
        evidence = {"mode": "practice, not official challenge", "scenario": "tool_fail", "start_utc": began,
                    "end_utc": datetime.now(timezone.utc).isoformat(), "http_statuses": [r.status_code for r in responses],
                    "error_rate_pct_60min": metric["error_rate_pct"], "retrieval_success_pct_60min": metric["retrieval_success_pct"],
                    "selected_log": chosen}
        path = DEST / "13-incident-log.json"
        path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        capture(path, path.with_suffix(".png"), "CP3 practice - log selected after metrics")
    finally:
        client.post("/incidents/tool_fail/disable").raise_for_status()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        recovered = list(pool.map(lambda body: client.post("/chat", json=body), payloads))
    (DEST / "recovery.json").write_text(json.dumps({"at": datetime.now(timezone.utc).isoformat(), "http_statuses": [r.status_code for r in recovered], "health": client.get("/health").json()}, indent=2), encoding="utf-8")
    snapshot("after-recovery")
    print(f"Practice: {len(failures)} failures; selected {chosen['correlation_id']}; recovery statuses {[r.status_code for r in recovered]}")
