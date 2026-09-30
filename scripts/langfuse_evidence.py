"""Run actual prompt lifecycle and export Langfuse v2 observations. Never fabricates IDs."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv()
from langfuse import get_client

DEST = Path("submission/evidence/cp2")
DEST.mkdir(parents=True, exist_ok=True)


def save(name, data):
    path = DEST / name
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    for key in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
        if os.getenv(key):
            text = text.replace(os.environ[key], "[REDACTED_API_KEY]")
    path.write_text(text, encoding="utf-8")
    return path


def prompt_demo(client):
    from fastapi.testclient import TestClient
    from app.main import app
    from capture_evidence import capture

    name = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    existing = client.api.prompts.list(name=name)
    if existing.data:
        # Reuse baseline/candidate, never blindly append more prompt versions.
        v1 = client.get_prompt(name, label="baseline", cache_ttl_seconds=0)
        v2 = client.get_prompt(name, label="candidate", cache_ttl_seconds=0)
    else:
        v1 = client.create_prompt(name=name, type="text", prompt="Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}", labels=["baseline", "production"], commit_message="CP2 baseline")
        v2 = client.create_prompt(name=name, type="text", prompt="Answer concisely using the supplied context.\nFeature={{feature}}\nDocs={{docs}}\nQuestion={{message}}", labels=["candidate"], commit_message="CP2 candidate: concise answer instruction")
    save("prompt-versions.json", [{"name": name, "version": v.version, "labels": v.labels, "prompt": v.prompt} for v in (v1, v2)])
    history = []
    original_label = os.environ.get("LANGFUSE_PROMPT_LABEL", "production")
    payload = {"user_id": "student-2A202602977", "session_id": "cp2-prompt-demo", "feature": "qa", "message": "Explain monitoring metrics logs traces"}
    try:
        with TestClient(app) as http:
            for label, stage in [("baseline", "baseline"), ("candidate", "candidate"), ("production", "promoted"), ("production", "rollback")]:
                if stage in ("promoted", "rollback"):
                    client.update_prompt(name=name, version=v2.version if stage == "promoted" else v1.version, new_labels=["production"])
                os.environ["LANGFUSE_PROMPT_LABEL"] = label
                client.clear_prompt_cache()
                actual = client.get_prompt(name, label=label, cache_ttl_seconds=0)
                response = http.post("/chat", json=payload)
                response.raise_for_status()
                history.append({"stage": stage, "at": datetime.now(timezone.utc).isoformat(), "label": label, "version_from_langfuse": actual.version, "correlation_id": response.json()["correlation_id"], "response": response.json()})
                path = save(f"prompt-{stage}.json", history[-1])
                capture(path, path.with_suffix(".png"), f"CP2 - {stage} - actual Langfuse label + ASGI request")
            for index in range(10):
                response = http.post("/chat", json={**payload, "session_id": "cp2-workload"})
                response.raise_for_status()
    finally:
        os.environ["LANGFUSE_PROMPT_LABEL"] = original_label
        client.update_prompt(name=name, version=v1.version, new_labels=["production"])
        client.clear_prompt_cache()
        client.flush()
    save("prompt-history.json", history)
    print("Prompt versions and rollback completed:", [(x["stage"], x["version_from_langfuse"]) for x in history])


def export(client):
    project = client.api.projects.get().model_dump(mode="json")
    save("project.json", project)
    end = datetime.now(timezone.utc)
    observations, cursor = [], None
    for _ in range(20):
        page = client.api.observations.get_many(
            from_start_time=end - timedelta(hours=3), to_start_time=end,
            limit=100, cursor=cursor, fields="core,basic,metadata,usage,model,prompt,io",
        ).model_dump(mode="json", by_alias=True)
        observations.extend(page["data"])
        cursor = page.get("meta", {}).get("cursor")
        if not cursor:
            break
    # Export only observations linked to requests in this workspace's current log.
    logs = [json.loads(line) for line in Path("data/logs.jsonl").read_text(encoding="utf-8").splitlines()]
    ids = {r.get("correlation_id") for r in logs}
    matched = [o for o in observations if o.get("metadata", {}).get("correlation_id") in ids]
    save("observations.json", matched)
    print("Exported actual observations:", len(matched), "unique traces:", len({o['traceId'] for o in matched}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prompts", "export"])
    args = parser.parse_args()
    client = get_client()
    try:
        assert client.auth_check(), "Langfuse authentication failed"
        prompt_demo(client) if args.action == "prompts" else export(client)
    finally:
        client.shutdown()
