#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

# Item 7 deliberately uses only explicit error-code routing.
# No Chinese/English message keyword inference is allowed.
ERROR_OWNER_MAP: dict[str, str] = {
    # Story authority / coverage
    'STORY_COVERAGE': 'AUTHORITY',
    'HARD_REPEATED_PLOT_TEMPLATE': 'STORY',
    # Asset production / file truth
    'HARD_REQUIRED_ASSET_MISSING': 'ASSET',
    'ASSET_FILE_INVALID': 'ASSET',
    'ASSET_STATUS_INVALID': 'ASSET',
    # Current-GU compiler isolation; in 2.0 this belongs to CW Shot/Segment, not an AFD Prompt Compiler.
    'CURRENT_GU_ONLY_STORY': 'SHOT_SEGMENT',
    'CURRENT_GU_ONLY_DIALOGUE': 'SHOT_SEGMENT',
    'CURRENT_GU_ONLY_SOUND': 'SHOT_SEGMENT',
    'CURRENT_GU_ONLY_STATE': 'SHOT_SEGMENT',
    'CURRENT_GU_ONLY_REVEAL': 'SHOT_SEGMENT',
    # Continuity produced/handed off by SH/GU planning.
    'CONTINUITY_AXIS_BREAK': 'SHOT_SEGMENT',
    'CONTINUITY_AXIS_TRANSITION_MISSING': 'SHOT_SEGMENT',
    'CONTINUITY_GAZE_MISMATCH': 'SHOT_SEGMENT',
    'CONTINUITY_CHARACTER_POSITIONS_MISMATCH': 'SHOT_SEGMENT',
    'CONTINUITY_HAND_PROPS_MISMATCH': 'SHOT_SEGMENT',
    'CONTINUITY_PERSISTENT_STATES_MISMATCH': 'SHOT_SEGMENT',
    'CONTINUITY_STATE_CONFLICT': 'SHOT_SEGMENT',
    'HARD_CONTINUITY_BREAK': 'SHOT_SEGMENT',
    # SH/GU/Prompt structure is one CW Shot/Segment authority in 2.0.
    'HARD_SH_GU_PROMPT_MISSING': 'SHOT_SEGMENT',
    'ANALYSIS_ARTIFACT_LEAK': 'SHOT_SEGMENT',
    # Project-volume / export gates.
    'HARD_EPISODE_RUNTIME_OUT_OF_RANGE': 'DELIVERY',
    'HARD_FILM_RUNTIME_OUT_OF_RANGE': 'DELIVERY',
    'HARD_RUNTIME_BOUNDS_INVALID': 'DELIVERY',
    'HARD_PROJECT_MISSING': 'DELIVERY',
    'DELIVERY_GATE_ERROR': 'DELIVERY',
}

RERUN_MATRIX: dict[str, tuple[list[str], list[str]]] = {
    'STORY': (
        ['STORY', 'AUTHORITY', 'EMOTION', 'SCENE_INTELLIGENCE', 'ROUTER', 'DIRECTOR', 'ASSET', 'SPATIAL', 'SHOT_SEGMENT', 'QUALITY'],
        [],
    ),
    'AUTHORITY': (
        ['AUTHORITY', 'EMOTION', 'SCENE_INTELLIGENCE', 'ROUTER', 'DIRECTOR', 'ASSET', 'SPATIAL', 'SHOT_SEGMENT', 'QUALITY'],
        ['STORY'],
    ),
    'EMOTION': (
        ['EMOTION', 'DIRECTOR', 'SHOT_SEGMENT', 'QUALITY'],
        ['STORY', 'AUTHORITY'],
    ),
    'SCENE_INTELLIGENCE': (
        ['SCENE_INTELLIGENCE', 'ROUTER', 'DIRECTOR', 'SPATIAL', 'SHOT_SEGMENT', 'QUALITY'],
        ['STORY', 'AUTHORITY', 'EMOTION', 'ASSET'],
    ),
    'ROUTER': (
        ['ROUTER', 'DIRECTOR', 'SPATIAL', 'SHOT_SEGMENT', 'QUALITY'],
        ['STORY', 'AUTHORITY', 'EMOTION', 'ASSET'],
    ),
    'DIRECTOR': (
        ['DIRECTOR', 'ASSET', 'SPATIAL', 'SHOT_SEGMENT', 'QUALITY'],
        ['STORY', 'AUTHORITY', 'EMOTION', 'SCENE_INTELLIGENCE', 'ROUTER'],
    ),
    'ASSET': (
        ['ASSET', 'SHOT_SEGMENT', 'QUALITY'],
        ['STORY', 'AUTHORITY', 'EMOTION', 'SCENE_INTELLIGENCE', 'ROUTER', 'DIRECTOR', 'SPATIAL'],
    ),
    'SPATIAL': (
        ['SPATIAL', 'SHOT_SEGMENT', 'QUALITY'],
        ['STORY', 'AUTHORITY', 'EMOTION', 'SCENE_INTELLIGENCE', 'ROUTER', 'DIRECTOR', 'ASSET'],
    ),
    'SHOT_SEGMENT': (
        ['SHOT_SEGMENT', 'QUALITY'],
        ['STORY', 'AUTHORITY', 'EMOTION', 'SCENE_INTELLIGENCE', 'ROUTER', 'DIRECTOR', 'ASSET', 'SPATIAL'],
    ),
    'DELIVERY': (
        ['DELIVERY', 'QUALITY'],
        ['STORY', 'AUTHORITY', 'EMOTION', 'SCENE_INTELLIGENCE', 'ROUTER', 'DIRECTOR', 'ASSET', 'SPATIAL', 'SHOT_SEGMENT'],
    ),
}

_CODE_RE = re.compile(r'^\s*([A-Z][A-Z0-9_]{3,})(?=[：:])')
# Full affected-id families inherited from 3.0: production, story, dialogue, information, shot/GU and assets.
_ID_RE = re.compile(r'(?<![A-Za-z0-9])(?:GU|SH|PU|EP|SC|ST|DB|I)\d+|(?<![A-Za-z0-9])(?:A|B|G|S|P|V)\d+(?:-ST\d+)?', re.I)


def extract_error_code(message: str) -> str:
    match = _CODE_RE.match(str(message or '').upper())
    return match.group(1) if match else 'DELIVERY_GATE_ERROR'


def affected_ids(message: str, unit_id: str | None = None) -> list[str]:
    found = list(dict.fromkeys(token.upper() for token in _ID_RE.findall(str(message or ''))))
    if not found and unit_id:
        found = [str(unit_id).upper()]
    return found or ['PROJECT']


def route_for_code(error_code: str) -> tuple[str, list[str], list[str]]:
    owner = ERROR_OWNER_MAP.get(str(error_code or '').upper(), 'DELIVERY')
    rerun_path, do_not_rerun = RERUN_MATRIX[owner]
    return owner, list(rerun_path), list(do_not_rerun)


def build_issue(
    message: str,
    severity: str = 'HARD',
    unit_id: str | None = None,
    issue_id: str = 'QC001',
) -> dict:
    code = extract_error_code(message)
    owner, rerun_path, do_not_rerun = route_for_code(code)
    return {
        'issue_id': issue_id,
        'severity': str(severity or 'HARD').upper(),
        'error_code': code,
        'owner_layer': owner,
        'affected_ids': affected_ids(message, unit_id),
        'reason': str(message),
        'rerun_path': rerun_path,
        'do_not_rerun': do_not_rerun,
    }


def write_qc_issues(
    project_root: str | Path,
    messages: Iterable[str],
    severity: str = 'HARD',
    unit_id: str | None = None,
) -> Path:
    root = Path(project_root).resolve()
    issues = [
        build_issue(message, severity=severity, unit_id=unit_id, issue_id=f'QC{index:03d}')
        for index, message in enumerate(messages, 1)
    ]
    target = root / 'state' / 'qc' / 'QC_ISSUES.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({'issues': issues}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return target
