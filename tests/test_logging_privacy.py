import asyncio
import json
import re

import httpx

from app import logging_config
from app.main import app
from app.pii import scrub_text


def test_identifier_redaction_preserves_observability_ids():
    for value, marker in [
        ("012345678901", "CCCD"),
        ("4111 1111 1111 1111", "CREDIT_CARD"),
        ("4111111111111111", "CREDIT_CARD"),
        ("+84 90 123 4567", "PHONE_VN"),
    ]:
        assert scrub_text(value) == f"[REDACTED_{marker}]"
    assert scrub_text("req-12345678 abc012345678901def") == "req-12345678 abc012345678901def"


def test_scrubs_nested_values_and_exception_before_file(monkeypatch, tmp_path):
    path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", path)
    logging_config.get_logger().error(
        "privacy_test", payload={"nested": [{"email": "test@example.org"}]},
        session_id="test@example.org", exception="Contact 0901234567",
    )
    raw = path.read_text(encoding="utf-8")
    assert "test@example.org" not in raw and "0901234567" not in raw
    assert "REDACTED_EMAIL" in raw and "REDACTED_PHONE_VN" in raw


def test_concurrent_request_context_and_invalid_header(monkeypatch, tmp_path):
    path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", path)

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
            async def send(index):
                return await client.post("/chat", headers={"x-request-id": f"req-{index:08x}"}, json={
                    "user_id": f"user-{index}", "session_id": f"session-{index}",
                    "feature": "qa", "message": "Explain monitoring",
                })
            responses = await asyncio.gather(*(send(i) for i in range(4)))
            bad = await client.get("/health", headers={"x-request-id": "test@example.org"})
            return responses, bad

    responses, bad = asyncio.run(run())
    for i, response in enumerate(responses):
        assert response.headers["x-request-id"] == response.json()["correlation_id"] == f"req-{i:08x}"
        assert float(response.headers["x-response-time-ms"]) > 0
    assert re.fullmatch(r"req-[0-9a-f]{8}", bad.headers["x-request-id"])
    for event in map(json.loads, path.read_text(encoding="utf-8").splitlines()):
        index = int(event["correlation_id"][4:], 16)
        assert event["session_id"] == f"session-{index}"
