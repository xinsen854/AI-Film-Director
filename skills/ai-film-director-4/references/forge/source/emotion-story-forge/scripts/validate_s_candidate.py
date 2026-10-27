#!/usr/bin/env python3
"""Validate the required architecture package for an S-CANDIDATE route."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple)):
        return bool(value)
    return bool(value)


def validate(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["S-CANDIDATE payload must be a JSON object"]
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        return ["meta must be an object"]
    if meta.get("quality_route") != "S-CANDIDATE":
        return ["meta.quality_route must be S-CANDIDATE"]

    errors: list[str] = []
    necessity = payload.get("story_necessity")
    if not isinstance(necessity, dict):
        errors.append("story_necessity must be an object")
    else:
        for key in ("why_now", "why_this_protagonist", "no_rational_exit", "inaction_cost", "form_necessity"):
            if not _present(necessity.get(key)):
                errors.append(f"story_necessity.{key} is required")
        if necessity.get("verdict") not in {"pass", "revise", "block"}:
            errors.append("story_necessity.verdict must be pass, revise, or block")

    opposition = payload.get("opposition_engine")
    if not isinstance(opposition, dict):
        errors.append("opposition_engine must be an object")
    else:
        for key in ("goal", "rules", "resources", "victory_condition", "independent_motion", "status"):
            if not _present(opposition.get(key)):
                errors.append(f"opposition_engine.{key} is required")

    decisions = payload.get("decision_chains")
    if not isinstance(decisions, list) or not decisions:
        errors.append("decision_chains must be a non-empty array")
    else:
        for index, decision in enumerate(decisions, start=1):
            if not isinstance(decision, dict):
                errors.append(f"decision_chains[{index}] must be an object")
                continue
            for key in ("id", "character_id", "pressure", "available_options", "chosen_action", "immediate_cost", "state_change", "future_debt", "counterfactual_without_choice", "evidence_refs"):
                if key not in decision or not _present(decision.get(key)):
                    errors.append(f"decision_chains[{index}].{key} is required")

    endings = payload.get("ending_tournament")
    if not isinstance(endings, list) or len(endings) < 3:
        errors.append("ending_tournament must contain at least three candidates")
    else:
        open_or_selected = [item for item in endings if isinstance(item, dict) and item.get("decision") in {"selected", "open"}]
        if not open_or_selected:
            errors.append("ending_tournament must retain at least one selected or open candidate")

    matrix = payload.get("episode_distinction_matrix")
    if not isinstance(matrix, list) or not matrix:
        errors.append("episode_distinction_matrix must be a non-empty array")

    peaks = payload.get("peak_aftermath_ledger")
    if not isinstance(peaks, list):
        errors.append("peak_aftermath_ledger must be an array")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an S-CANDIDATE architecture package")
    parser.add_argument("input_json", type=Path)
    args = parser.parse_args()
    try:
        with args.input_json.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"S-CANDIDATE validation failed: {exc}", file=sys.stderr)
        return 2
    errors = validate(payload)
    if errors:
        print("S-CANDIDATE validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    print("S-CANDIDATE architecture validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
