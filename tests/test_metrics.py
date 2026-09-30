from app.metrics import percentile


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_failed_requests_count_as_traffic(monkeypatch):
    from collections import Counter
    from app import metrics
    monkeypatch.setattr(metrics, "TRAFFIC", 0)
    monkeypatch.setattr(metrics, "ERRORS", Counter())
    metrics.record_request(100, 50, .001, 20, 80, .8)
    metrics.record_error("RuntimeError")
    assert metrics.snapshot()["traffic"] == 2
    assert metrics.snapshot()["error_rate_pct"] == 50
