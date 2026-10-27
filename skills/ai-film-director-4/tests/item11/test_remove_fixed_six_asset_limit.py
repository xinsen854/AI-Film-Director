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


def test_seven_visual_assets_are_not_rejected_by_a_global_fixed_limit():
    minimal_storyboard = _load_minimal_storyboard()
    payload = minimal_storyboard()
    assets = []
    for index in range(1, 8):
        assets.append({
            'asset_id': f'A{index:03d}',
            'name': f'视觉资产{index}',
            'file': f'assets/generated/A{index:03d}.png',
            'role': '当前镜头必要视觉参考',
            'shot_use': f'只用于当前镜头中的必要身份/物体一致性{index}',
        })
    payload['edit_shots'][0]['visual_asset_calls'] = assets
    payload['generation_units'][0]['active_media_references'] = [item['asset_id'] for item in assets]

    errors = validate_storyboard_payload(payload)
    assert not any('exceeds 6' in error or '最多6' in error for error in errors), errors
    rendered = render_storyboard(payload)
    assert 'A007' in rendered


def test_runtime_contracts_do_not_restate_a_fixed_six_asset_rule():
    files = [
        ROOT / 'references' / 'cineweaver' / 'Shot_Segment_Engine_V1.3' / 'module.md',
        ROOT / 'references' / 'cineweaver' / 'Shot_Segment_Engine_V1.3' / 'runtime' / 'ASSET_BUDGET.md',
        ROOT / 'references' / 'cineweaver' / 'Shot_Segment_Engine_V1.3' / 'templates' / '04_STORYBOARD_SKILL_V5_2_EXECUTABLE_UNIFIED.md',
        ROOT / 'references' / 'modules' / 'quality-delivery' / 'module.md',
    ]
    forbidden = ('最多6', 'at most **6', 'at most 6', '≤6', '共用同一组最多6')
    for path in files:
        text = path.read_text(encoding='utf-8')
        assert not any(token in text for token in forbidden), f'fixed six-asset rule remains in {path}'
