#!/usr/bin/env python3
"""Scan adjacent series units for repeated tags without declaring quality."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


FIELDS = (
    "hook_source",
    "pressure_source",
    "defense_strategy",
    "choice_type",
    "reveal_function",
    "relationship_shift",
    "ending_load",
    "motif_function",
)
INCREMENT_FIELDS = ("knowledge", "leverage", "cost", "tactic", "relationship", "motif_meaning", "state_delta")


def _units(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("units", "episodes", "entries", "ledger", "episode_distinction_matrix"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _value(unit: dict[str, Any], key: str) -> str:
    value = unit.get(key, "")
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def scan(payload: Any) -> list[dict[str, Any]]:
    units = _units(payload)
    results: list[dict[str, Any]] = []
    for previous, current in zip(units, units[1:]):
        repeated = [field for field in FIELDS if _value(previous, field) and _value(previous, field) == _value(current, field)]
        increment = [field for field in INCREMENT_FIELDS if _value(current, field) and _value(current, field) != _value(previous, field)]
        if not repeated:
            classification = "NO_REPEATED_TAGS"
        elif increment:
            classification = "UPGRADED_REPETITION"
        else:
            classification = "REPETITION_RISK"
        results.append({
            "previous": previous.get("id") or previous.get("episode") or previous.get("unit") or previous.get("scope"),
            "current": current.get("id") or current.get("episode") or current.get("unit") or current.get("scope"),
            "repeated_tags": repeated,
            "state_delta_fields": increment,
            "classification": classification,
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan adjacent series units for repeated tags")
    parser.add_argument("input_json", type=Path)
    args = parser.parse_args()
    try:
        with args.input_json.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"variation scan failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"units": scan(payload)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
