"""Capture a browser-rendered view of real saved output (not a terminal screenshot)."""
import argparse
import html
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


def capture(source: Path, output: Path, title: str = "Lab evidence") -> None:
    if source.suffix == ".html":
        page_url = source.resolve().as_uri()
    else:
        raw = source.read_bytes()
        text = raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
        page = source.with_suffix(".html")
        page.write_text(
            '<!doctype html><meta charset="utf-8"><style>body{background:#101827;color:#e7edf6;'
            'font:16px Consolas,monospace;padding:30px}h1{font:26px Arial}pre{white-space:pre-wrap;'
            'overflow-wrap:anywhere;line-height:1.5}small{color:#a1b6cd}</style>'
            f'<h1>{html.escape(title)}</h1><small>Saved runtime output: {html.escape(str(source))}'
            f' | Captured {datetime.now(timezone.utc).isoformat()}</small><pre>{html.escape(text)}</pre>',
            encoding="utf-8",
        )
        page_url = page.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
        page.goto(page_url)
        page.screenshot(path=str(output), full_page=True)
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", default="Lab evidence — runtime output")
    args = parser.parse_args()
    capture(args.source, args.output, args.title)
