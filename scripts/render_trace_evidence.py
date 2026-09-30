"""Render actual exported Langfuse observations; clearly distinct from Langfuse UI."""
import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from capture_evidence import capture

ROOT = Path("submission/evidence")
CP = ROOT / "cp2"


def page(title, body):
    project = json.loads((CP / "project.json").read_text(encoding="utf-8"))["data"][0]
    return ('<!doctype html><meta charset="utf-8"><style>body{background:#0b1220;color:#e4edf7;font:16px Segoe UI,Arial;margin:30px}h1{font-size:26px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #354860;padding:10px;text-align:left}pre{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.45;background:#142238;padding:20px}a{color:#83caff}svg text{fill:white;font:16px monospace}</style>'
            f'<h1>{html.escape(title)}</h1><p>Project: {html.escape(project["name"])} · {project["id"]}</p>'
            '<p>Source: Langfuse Observations API v2 export. Local evidence viewer, not a Langfuse UI screenshot. API keys redacted.</p>' + body)


def write(name, title, body):
    path = ROOT / f"{name}.html"
    path.write_text(page(title, body), encoding="utf-8")
    capture(path, path.with_suffix(".png"))


def waterfall(rows):
    rows = sorted(rows, key=lambda r: (r["parentObservationId"] is not None, r["startTime"]))
    start = min(datetime.fromisoformat(r["startTime"].replace("Z", "+00:00")) for r in rows)
    def ms(value):
        return (datetime.fromisoformat(value.replace("Z", "+00:00")) - start).total_seconds() * 1000
    total = max(ms(r["endTime"]) for r in rows)
    shapes, details = [], []
    for i, row in enumerate(rows):
        offset, duration = ms(row["startTime"]), ms(row["endTime"]) - ms(row["startTime"])
        x = 260 + offset / max(total, 1) * 850
        color = "#ff7f7f" if row["level"] == "ERROR" else "#55b5f4"
        name = ("  └ " if row["parentObservationId"] else "") + row["name"]
        shapes.append(f'<text x="5" y="{i*60+30}">{name}</text><rect x="{x:.2f}" y="{i*60+8}" width="{max(2,duration/max(total,1)*850):.2f}" height="30" fill="{color}"/><text x="1130" y="{i*60+30}">{duration:.1f} ms</text>')
        details.append({k: row.get(k) for k in ["name", "id", "parentObservationId", "traceId", "startTime", "endTime", "level", "statusMessage", "model", "promptName", "promptVersion", "usageDetails", "costDetails", "input", "output"]})
    root = rows[0]
    safe_metadata = {k: v for k, v in root.get("metadata", {}).items() if not k.startswith(("scope.", "resourceAttributes."))}
    return (f'<h2>Trace {root["traceId"]}</h2><p>UTC start: {start.isoformat()} · total {total:.1f} ms · correlation: {safe_metadata.get("correlation_id")}</p>'
            f'<svg viewBox="0 0 1300 {len(rows)*60}">{"".join(shapes)}</svg>'
            f'<pre>{html.escape(json.dumps({"root_metadata":safe_metadata,"observations":details},ensure_ascii=False,indent=2))}</pre>')


def main():
    observations = json.loads((CP / "observations.json").read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    for row in observations:
        grouped[row["traceId"]].append(row)
    valid = {k:v for k,v in grouped.items() if {r["name"] for r in v} >= {"lab-agent-run", "retrieval", "generation"}}
    roots = [next(r for r in v if r["name"] == "lab-agent-run") for v in valid.values()]
    body = f'<h2>{len(valid)} traces with agent → retrieval + generation</h2><table><tr><th>Trace ID</th><th>Correlation ID</th><th>UTC start</th><th>Prompt</th></tr>'
    for r in roots:
        m = r["metadata"]
        body += f'<tr><td>{r["traceId"]}</td><td>{m["correlation_id"]}</td><td>{r["startTime"]}</td><td>{m.get("prompt_label")} / {m.get("prompt_version")}</td></tr>'
    write("06-trace-list-api", "CP2 · Actual traces with full span tree", body + "</table>")
    chosen = next(v for v in valid.values() if any(r.get("sessionId") == "cp2-prompt-demo" for r in v))
    write("07-trace-waterfall-api", "CP2 · Actual observation waterfall and metadata", waterfall(chosen))
    history = json.loads((CP / "prompt-history.json").read_text(encoding="utf-8"))
    for event in history:
        root = next(r for r in roots if r["metadata"].get("correlation_id") == event["correlation_id"])
        event["trace_id"] = root["traceId"]
        event["observed_prompt_version"] = root["metadata"]["prompt_version"]
        assert str(event["observed_prompt_version"]) == str(event["version_from_langfuse"])
    (CP / "prompt-trace-links.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    versions = json.loads((CP / "prompt-versions.json").read_text(encoding="utf-8"))
    write("09-10-prompt-rollback-api", "CP2 · Prompt versions, promote and rollback verified by traces", '<pre>' + html.escape(json.dumps({"versions_at_creation":versions,"lifecycle":history}, indent=2)) + '</pre>')
    print(f"Captured {len(valid)} complete trace trees; prompt versions verified against actual observations.")


if __name__ == "__main__":
    main()
