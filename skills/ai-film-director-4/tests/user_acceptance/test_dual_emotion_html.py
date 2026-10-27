from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))

from render_emotion_map import render_emotion_html, validate_emotion_payload
from support_pipeline import minimal_forge_locked_audit


def test_locked_forge_audit_requires_adaptive_emotion_contract():
    payload = minimal_forge_locked_audit()
    del payload['phase_events']
    assert any('phase_events' in item for item in validate_emotion_payload(payload))


def test_locked_forge_audit_requires_lock_status():
    payload = minimal_forge_locked_audit()
    payload['script_audit']['lock_status'] = 'DRAFT'
    assert any('LOCKED' in item or 'locked_audit' in item for item in validate_emotion_payload(payload))


def test_html_contains_forge_global_rivers_field_and_halo():
    payload = minimal_forge_locked_audit()
    assert validate_emotion_payload(payload) == []
    html = render_emotion_html(payload)
    for token in ('全剧情情绪总谱', 'Story Time', 'Audience Time', 'CHARACTER + AUDIENCE EMOTION FIELD', 'AUDIENCE HALO'):
        assert token in html
