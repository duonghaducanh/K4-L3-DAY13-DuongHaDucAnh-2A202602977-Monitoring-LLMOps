"""Check submitted text for configured credentials, raw sample PII and broken report links."""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEST = ROOT / "submission/evidence/cp4"
values = dotenv_values(ROOT / ".env")
secrets = [values.get(k) for k in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY") if values.get(k)]
failures = []
paths = [p for folder in ("app", "scripts", "tests", "config", "docs", "submission") for p in (ROOT / folder).rglob("*") if p.is_file() and p.suffix in (".py", ".yaml", ".md", ".txt", ".json", ".html") and p.name != "challenge.json"]
for path in paths:
    raw = path.read_bytes()
    text = raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
    if any(secret in text for secret in secrets):
        failures.append(f"Configured credential in {path.relative_to(ROOT)}")
    if re.search(r"(?:sk|pk)-lf-[a-zA-Z0-9-]{20,}", text):
        failures.append(f"Credential-shaped value in {path.relative_to(ROOT)}")

report = ROOT / "submission/REPORT.md"
for target in re.findall(r"\]\(([^)]+)\)", report.read_text(encoding="utf-8")):
    # This script creates its own manifest immediately after validation.
    if (report.parent / target).resolve() == (DEST / "security-and-source-manifest.json").resolve():
        continue
    if not target.startswith(("http://", "https://", "#")) and not (report.parent / target.split("#")[0]).exists():
        failures.append(f"Broken report link: {target}")

# Inputs are synthetic test fixtures; check that they never reached logs or traces.
samples = [json.loads(line) for line in (ROOT / "data/sample_queries.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
from app.pii import PII_PATTERNS
pii = {match.group() for q in samples for pattern in PII_PATTERNS.values() for match in re.finditer(pattern, q["message"])}
pii.update(["demo@example.org", "0901234567", "012345678901", "4111 1111 1111 1111"])
runtime_paths = [ROOT / "data/logs.jsonl", ROOT / "submission/evidence/cp2/observations.json"]
for path in runtime_paths:
    text = path.read_text(encoding="utf-8")
    if any(value in text for value in pii):
        failures.append(f"Raw test PII in {path.relative_to(ROOT)}")

manifest = {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_text(encoding="utf-8-sig").replace("\r\n", "\n").encode("utf-8")).hexdigest() for p in paths if "submission" not in p.parts}
result = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "text_files_checked": len(paths), "sample_pii_values_checked": len(pii), "failures": failures, "source_hash_format": "UTF-8, BOM removed, LF newlines", "source_sha256": manifest}
DEST.mkdir(parents=True, exist_ok=True)
(DEST / "security-and-source-manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"Checked {len(paths)} text files, {len(pii)} synthetic PII values, report links; failures={len(failures)}")
for failure in failures:
    print(failure)
raise SystemExit(bool(failures))
