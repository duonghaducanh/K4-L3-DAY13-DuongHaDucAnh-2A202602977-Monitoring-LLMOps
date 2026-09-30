"""Six-panel dashboard calculated only from the structured JSONL log."""
from __future__ import annotations

import html
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml


def percentile(values, percent):
    ordered = sorted(values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * percent / 100
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def summarize(path=Path("data/logs.jsonl"), *, end=None, minutes=60):
    end = end or datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)
    rows, malformed = [], 0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                when = datetime.fromisoformat(row["ts"].replace("Z", "+00:00"))
                if start <= when <= end:
                    rows.append(row)
            except (ValueError, KeyError, TypeError):
                malformed += 1
    requests = [r for r in rows if r.get("event") == "request_received"]
    responses = [r for r in rows if r.get("event") == "response_sent"]
    failures = [r for r in rows if r.get("event") == "request_failed"]
    # Retrieval outcomes exist on both successful and failed terminal events.
    tools = [r for r in responses + failures if r.get("tool_name") == "retrieval" and isinstance(r.get("tool_success"), bool)]
    first_minute = start.replace(second=0, microsecond=0)
    buckets = {(first_minute + timedelta(minutes=i)).isoformat(): {"requests": 0, "cost": 0.0, "latency": []} for i in range(minutes + 1)}
    for row in requests + responses:
        key = datetime.fromisoformat(row["ts"].replace("Z", "+00:00")).replace(second=0, microsecond=0).isoformat()
        bucket = buckets[key]
        if row["event"] == "request_received":
            bucket["requests"] += 1
        else:
            bucket["cost"] += row.get("cost_usd", 0)
            bucket["latency"].append(row["latency_ms"])
    good = sum(r["latency_ms"] <= 3000 for r in responses)
    return {
        "start": start.isoformat(), "end": end.isoformat(), "source": str(path),
        "malformed_lines": malformed, "requests": len(requests), "responses": len(responses),
        "failures": len(failures), "latency": {f"P{p}": percentile([r["latency_ms"] for r in responses], p) for p in [50, 95, 99]},
        "ttft_p95": percentile([r["ttft_ms"] for r in responses], 95),
        "error_rate_pct": 100 * len(failures) / len(requests) if requests else None,
        "retrieval_success_pct": 100 * sum(r["tool_success"] for r in tools) / len(tools) if tools else None,
        "error_types": dict(Counter(r.get("error_type", "unknown") for r in failures)),
        "cost_usd": sum(r.get("cost_usd", 0) for r in responses),
        "tokens_in": sum(r.get("tokens_in", 0) for r in responses),
        "tokens_out": sum(r.get("tokens_out", 0) for r in responses),
        "quality_mean": sum(r["quality_score"] for r in responses) / len(responses) if responses else None,
        "slo_good": good, "slo_bad_or_pending": len(requests) - good,
        "buckets": buckets,
    }


def chart(series, threshold, labels=None, show_threshold=True):
    width, height, base = 620, 135, 110
    scale = max([v for v in series if v is not None] + [threshold, 0.001]) * 1.1
    step = width / max(len(series), 1)
    bars = "".join(f'<rect x="{i*step:.1f}" y="{base-(v or 0)/scale*95:.1f}" width="{max(1,step-2):.1f}" height="{(v or 0)/scale*95:.1f}" fill="#58b8fa"/>' for i, v in enumerate(series))
    y = base - threshold / scale * 95
    texts = "".join(f'<text x="{(i+.5)*step:.1f}" y="130" text-anchor="middle">{html.escape(label)}</text>' for i, label in enumerate(labels or []))
    line = f'<path d="M0,{y:.1f} H620" stroke="#ffc66d" stroke-dasharray="5 4"/><text x="2" y="{max(12,y-5):.1f}">threshold {threshold:g}</text>' if show_threshold else ""
    return f'<svg viewBox="0 0 {width} {height}">{bars}{line}{texts}</svg>'


def render(data):
    config = yaml.safe_load(Path("config/dashboard.yaml").read_text(encoding="utf-8"))["dashboard"]
    def n(value, digits=2):
        return "N/A" if value is None else f"{value:,.{digits}f}"
    panels = []
    for panel in config["panels"]:
        key, threshold = panel["id"], panel["threshold"]["value"]
        if key == "latency":
            values = list(data["latency"].values()) + [data["ttft_p95"]]
            labels = ["P50", "P95", "P99", "TTFT P95"]
            body = " | ".join(f"{k}: {n(v)} ms" for k, v in zip(labels, values))
            graph = chart(values, threshold, labels)
        elif key == "traffic":
            body = f'{data["requests"]} requests / 60 min; zero-traffic minutes included'
            graph = chart([b["requests"] for b in data["buckets"].values()], threshold)
            graph += f'<small>{data["start"][11:16]} → {data["end"][11:16]} UTC · one bar per minute</small>'
        elif key == "errors":
            body = f'Errors: {n(data["error_rate_pct"])}%; retrieval success: {n(data["retrieval_success_pct"])}% (target ≥90%)'
            body += f'<br>Failed/received: {data["failures"]}/{data["requests"]}; breakdown: {html.escape(str(data["error_types"]))}'
            graph = chart([data["error_rate_pct"], data["retrieval_success_pct"]], threshold, ["Error %", "Retrieval success %"])
        elif key == "cost":
            costs = [b["cost"] for b in data["buckets"].values()]
            body = f'Total: ${n(data["cost_usd"],6)} ≤ ${threshold}; bars = USD/min; peak minute ${max(costs):.6f}'
            graph = chart(costs, 0, show_threshold=False) + f'<div>{data["start"][11:16]} → {data["end"][11:16]} UTC · Window budget used: {data["cost_usd"]/threshold*100:.2f}%</div>'
            graph += chart([data["cost_usd"]], threshold, ["Window total USD"])
        elif key == "tokens":
            body = f'Input: {data["tokens_in"]:,}; output: {data["tokens_out"]:,} tokens'
            graph = chart([data["tokens_in"], data["tokens_out"]], threshold, ["Input", "Output"])
        else:
            body = f'Mean quality proxy: {n(data["quality_mean"])} / 1.00; target ≥{threshold}'
            graph = chart([data["quality_mean"]], threshold, ["Mean quality"])
        panels.append(f'<section><h2>{html.escape(panel["title"])}</h2><p>{body}</p>{graph}<footer>Unit: {panel["unit"]} · {panel["threshold"]["aggregation"]} {panel["threshold"]["operator"]} {threshold}</footer></section>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="{config["refresh_seconds"]}">'
            '<title>Day 13 Monitoring dashboard</title><style>body{font:16px Segoe UI,Arial;background:#0b1220;color:#e4edf7;margin:26px}h1{margin-bottom:8px}h2{font-size:20px}main{display:grid;grid-template-columns:1fr 1fr;gap:16px}section{background:#142238;border:1px solid #31445b;border-radius:10px;padding:16px}p{min-height:44px;line-height:1.5}footer,small{color:#acbed2}svg{width:100%;height:150px}svg text{fill:#e4edf7;font:12px Arial}</style>'
            f'<h1>K4-L3B · Monitoring & LLMOps · 2A202602977</h1><p>Source: {html.escape(data["source"])} · Last 60 minutes · Refresh 30s<br>UTC: {data["start"]} → {data["end"]}</p><main>{"".join(panels)}</main>'
            f'<p>SLI: {data["slo_good"]}/{data["requests"]} successful requests ≤3000 ms. 28-day target 99.5%; budget 0.5%. This view covers 60 minutes only.<br>Fake LLM token/cost estimates; quality is a heuristic. Malformed lines: {data["malformed_lines"]}.</p></html>')
