#!/usr/bin/env python3
"""Render one emotion-diagnosis JSON payload as a standalone offline HTML file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


TOKEN = "__REPORT_DATA__"


def encode_for_script(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return (
        encoded.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def render(input_path: Path, output_path: Path) -> None:
    with input_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")

    template_path = Path(__file__).resolve().parent.parent / "assets" / "emotion-report-template.html"
    template = template_path.read_text(encoding="utf-8")
    if template.count(TOKEN) != 1:
        raise ValueError("HTML template must contain exactly one report-data token")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template.replace(TOKEN, encode_for_script(payload)), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an offline emotion diagnosis HTML report")
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_html", type=Path)
    args = parser.parse_args()
    try:
        render(args.input_json, args.output_html)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
