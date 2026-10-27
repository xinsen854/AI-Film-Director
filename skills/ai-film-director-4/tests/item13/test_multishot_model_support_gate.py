from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from render_storyboard import validate_storyboard_payload


def _load_minimal_storyboard():
    helper_path = ROOT / 'tests' / 'item3' / 'test_final_hard_qc.py'
    spec = importlib.util.spec_from_file_location('item3_helpers_for_item13', helper_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.minimal_storyboard


def _multi_shot_payload() -> dict:
    minimal_storyboard = _load_minimal_storyboard()
    data = minimal_storyboard()
    first = data['edit_shots'][0]
    first['edit_shot_duration'] = 5.0

    second = copy.deepcopy(first)
    second['edit_shot_id'] = 'SH002'
    second['edit_shot_duration'] = 5.0
    second['generation_unit_id'] = 'GU001'
    second['source']['director_beat'] = 'beat-2'
    data['edit_shots'].append(second)

    gu = data['generation_units'][0]
    gu['packing_policy'] = 'AUTO'
    gu['mode'] = 'MULTI_SHOT'
    gu['duration'] = 10.0
    gu['member_edit_shots'] = ['SH001', 'SH002']
    gu['contains_explicit_cuts'] = True
    return data


def test_multishot_without_explicit_model_support_is_blocked():
    data = _multi_shot_payload()
    errors = validate_storyboard_payload(data)
    assert any('MULTI_SHOT_MODEL_SUPPORT_NOT_CONFIRMED' in error for error in errors), errors


def test_multishot_unknown_model_support_is_blocked():
    data = _multi_shot_payload()
    data['generation_units'][0]['model_supports_multi_shot'] = None
    errors = validate_storyboard_payload(data)
    assert any('MULTI_SHOT_MODEL_SUPPORT_NOT_CONFIRMED' in error for error in errors), errors


def test_multishot_explicitly_unsupported_is_blocked():
    data = _multi_shot_payload()
    data['generation_units'][0]['model_supports_multi_shot'] = False
    errors = validate_storyboard_payload(data)
    assert any('MULTI_SHOT_MODEL_SUPPORT_NOT_CONFIRMED' in error for error in errors), errors


def test_multishot_explicitly_supported_is_allowed():
    data = _multi_shot_payload()
    data['generation_units'][0]['model_supports_multi_shot'] = True
    errors = validate_storyboard_payload(data)
    assert not any('MULTI_SHOT_MODEL_SUPPORT' in error for error in errors), errors


def test_isolated_gu_does_not_require_multishot_support_flag():
    minimal_storyboard = _load_minimal_storyboard()
    data = minimal_storyboard()
    assert 'model_supports_multi_shot' not in data['generation_units'][0]
    errors = validate_storyboard_payload(data)
    assert not any('MULTI_SHOT_MODEL_SUPPORT' in error for error in errors), errors


def test_contract_does_not_assume_seedance_model_name_implies_multishot_support():
    model_adapter = (ROOT / 'references' / 'cineweaver' / 'Shot_Segment_Engine_V1.3' / 'runtime' / 'MODEL_ADAPTER.md').read_text(encoding='utf-8')
    assert 'must be explicitly confirmed' in model_adapter.lower() or '必须明确确认' in model_adapter
