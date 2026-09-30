import json
from datetime import datetime, timezone

from app.dashboard import summarize, render


def test_dashboard_time_window_denominators_and_quantiles(tmp_path):
    path = tmp_path / "logs.jsonl"
    stamp = "2026-09-30T03:00:00+00:00"
    rows = [
        {"ts": stamp, "event": "request_received"},
        {"ts": stamp, "event": "request_received"},
        {"ts": stamp, "event": "response_sent", "latency_ms": 100, "ttft_ms": 50, "tokens_in": 20, "tokens_out": 80, "cost_usd": .01, "quality_score": .8, "tool_name": "retrieval", "tool_success": True},
        {"ts": stamp, "event": "request_failed", "error_type": "RuntimeError", "tool_name": "retrieval", "tool_success": False},
        {"ts": "2026-09-29T03:00:00+00:00", "event": "request_received"},
    ]
    path.write_text("\n".join(map(json.dumps, rows)), encoding="utf-8")
    result = summarize(path, end=datetime(2026, 9, 30, 3, 1, tzinfo=timezone.utc))
    assert result["requests"] == 2
    assert result["error_rate_pct"] == result["retrieval_success_pct"] == 50
    assert result["latency"]["P95"] == 100
    assert result["cost_usd"] == .01 and result["tokens_in"] == 20
    assert len(result["buckets"]) == 61
    assert render(result).count("<section>") == 6


def test_dashboard_no_data_is_not_false_health(tmp_path):
    data = summarize(tmp_path / "absent.jsonl")
    assert data["error_rate_pct"] is None
    assert data["retrieval_success_pct"] is None
    assert data["quality_mean"] is None
