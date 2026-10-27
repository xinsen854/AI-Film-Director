from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))

from render_emotion_map import render_emotion_html
from support_pipeline import minimal_forge_locked_audit


def test_forge_global_map_exposes_story_and_audience_time_modes():
    html = render_emotion_html(minimal_forge_locked_audit())
    assert 'Story Time' in html
    assert 'Audience Time' in html


def test_forge_global_map_uses_adaptive_phase_visuals_not_legacy_axis_ticks():
    html = render_emotion_html(minimal_forge_locked_audit())
    assert '全剧情情绪总谱' in html
    assert 'CHARACTER + AUDIENCE EMOTION FIELD' in html
    assert 'AUDIENCE HALO' in html
    assert '观众主波浪' not in html
