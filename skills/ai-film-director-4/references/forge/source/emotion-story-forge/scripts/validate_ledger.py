#!/usr/bin/env python3
"""Validate series continuation ledger entries without third-party packages.

The validator checks structural handoff integrity. It does not claim that a
listed change is dramatically earned; that remains an audit judgment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


LEDGER_KEYS = (
    "episodes",
    "entries",
    "ledger",
    "series_bible_ledger",
    "continuation_ledger",
)


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return bool(value)


def _first(entry: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in entry and _present(entry[key]):
            return entry[key]
    return None


def _entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in LEDGER_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [value]
    for parent in ("long_form", "series"):
        value = payload.get(parent)
        if isinstance(value, dict):
            nested = _entries(value)
            if nested:
                return nested
    if any(key in payload for key in ("episode", "scope", "last_irreversible_change", "irreversible_change")):
        return [payload]
    return []


def validate_ledger(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, (dict, list)):
        return ["ledger payload must be a JSON object or array"]

    payload_mode = "continuous"
    if isinstance(payload, dict):
        mode_value = payload.get("continuity_mode") or payload.get("series_continuity_mode")
        if not _present(mode_value):
            for parent in ("long_form", "series"):
                nested = payload.get(parent)
                if isinstance(nested, dict):
                    mode_value = nested.get("continuity_mode") or nested.get("series_continuity_mode")
                    if _present(mode_value):
                        break
        payload_mode = str(mode_value or "continuous").strip().lower()
    if payload_mode not in {"continuous", "reset", "mixed"}:
        errors.append("continuity_mode must be continuous, reset, or mixed")
        payload_mode = "continuous"

    raw_entries = _entries(payload)
    if not raw_entries:
        return [
            "no ledger entries found; expected episodes/entries/ledger/series_bible_ledger "
            "or a single continuation ledger object"
        ]

    seen_ids: set[str] = set()
    for index, entry in enumerate(raw_entries, start=1):
        label = str(entry.get("episode") or entry.get("scope") or f"entry {index}")
        entry_id = entry.get("id") or entry.get("episode") or entry.get("scope")
        if entry_id is not None:
            normalized_id = str(entry_id)
            if normalized_id in seen_ids:
                errors.append(f"{label}: duplicate ledger id {normalized_id!r}")

        previous = entry.get("previous_entry_id") or entry.get("inherits_from")
        if previous is not None:
            if isinstance(previous, list):
                refs = [str(item) for item in previous]
            else:
                refs = [str(previous)]
            if not any(ref in seen_ids for ref in refs):
                errors.append(
                    f"{label}: previous_entry_id/inherits_from must reference an earlier ledger id"
                )
        if entry_id is not None:
            seen_ids.add(str(entry_id))

        entry_mode = str(entry.get("continuity_mode") or payload_mode).strip().lower()
        if entry_mode not in {"continuous", "reset", "mixed"}:
            errors.append(f"{label}: continuity_mode must be continuous, reset, or mixed")
            entry_mode = payload_mode
        reset_boundary = bool(entry.get("reset_boundary") or entry.get("reset_applied"))
        closes_at_reset = reset_boundary and entry_mode in {"reset", "mixed"}

        if closes_at_reset:
            invariants = _first(entry, ("carried_invariants", "series_invariants", "reset_contract"))
            if not invariants:
                errors.append(
                    f"{label}: reset boundary must name carried_invariants, series_invariants, or reset_contract"
                )
        else:
            if not _first(entry, ("irreversible_change", "last_irreversible_change")):
                errors.append(f"{label}: missing irreversible_change or last_irreversible_change")

            under_load = _first(
                entry,
                (
                    "under_load_tension",
                    "relational_tension_states",
                    "tension_state",
                    "carried_forward_load",
                ),
            )
            if not under_load:
                errors.append(
                    f"{label}: missing under-load state; provide under_load_tension, "
                    "relational_tension_states, or carried_forward_load"
                )

            carried = _first(
                entry,
                (
                    "open_knowledge_gap",
                    "open_knowledge_gaps",
                    "open_loops",
                    "unresolved_residue",
                    "carried_load",
                    "carried_forward_load",
                ),
            )
            if not carried:
                errors.append(
                    f"{label}: missing carried-forward load; provide an open knowledge gap, "
                    "open loop, unresolved residue, or carried_forward_load"
                )

        for key in ("relationship_states", "debts_opened_paid", "per_anchor_audience_knowledge"):
            if key in entry and not isinstance(entry[key], (str, list, dict)):
                errors.append(f"{label}: {key} must be a string, array, or object")

        for key in ("evidence_refs", "source_refs", "scene_refs"):
            if key in entry and not isinstance(entry[key], list):
                errors.append(f"{label}: {key} must be an array when present")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a series continuation ledger")
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable result")
    args = parser.parse_args()
    try:
        with args.input_json.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        message = f"cannot read ledger: {exc}"
        if args.as_json:
            print(json.dumps({"ok": False, "errors": [message]}, ensure_ascii=False))
        else:
            print(f"ledger validation failed: {message}", file=sys.stderr)
        return 2

    errors = validate_ledger(payload)
    result = {"ok": not errors, "errors": errors}
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("ledger validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
    else:
        print("ledger validation passed")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
