import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.dashboard import render, summarize
from capture_evidence import capture

parser = argparse.ArgumentParser()
parser.add_argument("--output", default="submission/evidence/11-dashboard-overview")
args = parser.parse_args()
path = Path(args.output)
path.parent.mkdir(parents=True, exist_ok=True)
data = summarize()
path.with_suffix(".json").write_text(json.dumps(data, indent=2), encoding="utf-8")
path.with_suffix(".html").write_text(render(data), encoding="utf-8")
capture(path.with_suffix(".html"), path.with_suffix(".png"))
print(f"Dashboard snapshot: {path}; requests={data['requests']}")
