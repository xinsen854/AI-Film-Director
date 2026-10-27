from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from render_storyboard import render_storyboard, validate_storyboard_payload


def _load_minimal_storyboard():
    helper_path = ROOT / 'tests' / 'item3' / 'test_final_hard_qc.py'
    spec = importlib.util.spec_from_file_location('item3_helpers', helper_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.minimal_storyboard


def test_four_continuous_visual_segments_are_not_rejected_by_a_global_fixed_limit():
    minimal_storyboard = _load_minimal_storyboard()
    payload = minimal_storyboard()
    payload['edit_shots'][0]['continuous_visuals'] = [
        '人物保持坐姿，右手停在表盖上，视线停在秒针。',
        '他抬眼看向门口，手指仍压着表盖，没有换位。',
        '门外脚步靠近，他收回视线，呼吸短暂停顿。',
        '门铃响起，他才松开表盖，身体转向入口。',
    ]

    errors = validate_storyboard_payload(payload)
    assert not any('continuous_visuals exceeds maximum' in error or '最多3个连续画面' in error for error in errors), errors
    rendered = render_storyboard(payload)
    assert '门铃响起' in rendered


def test_runtime_contract_does_not_restate_a_fixed_three_segment_rule():
    path = ROOT / 'references' / 'cineweaver' / 'Shot_Segment_Engine_V1.3' / 'templates' / '04_STORYBOARD_SKILL_V5_2_EXECUTABLE_UNIFIED.md'
    text = path.read_text(encoding='utf-8')
    forbidden = ('最多3个连续画面', 'continuous_visuals最多3', 'continuous_visuals ≤ 3', 'continuous_visuals<=3')
    assert not any(token in text for token in forbidden), 'fixed three-segment rule remains in storyboard template'
