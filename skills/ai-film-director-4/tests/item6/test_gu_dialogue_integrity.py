from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from render_storyboard import render_storyboard, validate_storyboard_payload
from validate_unit_consistency import _validate_storyboard_authority

_spec = importlib.util.spec_from_file_location('item3_helpers_for_dialogue', ROOT / 'tests' / 'item3' / 'test_final_hard_qc.py')
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
minimal_storyboard = _mod.minimal_storyboard


def _dialogue_lines(*, include_voice: bool = True) -> list[dict]:
    first = {
        'speaker': '许程',
        'verbatim': '明天九点二十。',
        'mode': '画内',
        'lip_sync': True,
        'delivery': '平静直接',
    }
    second = {
        'speaker': '许国安',
        'verbatim': '什么？',
        'mode': '画内',
        'lip_sync': True,
        'delivery': '短促，不拖尾',
    }
    if include_voice:
        first['voice_profile_id'] = 'V001'
        second['voice_profile_id'] = 'V002'
    return [first, second]


def _payload_with_sh_dialogue() -> dict:
    payload = minimal_storyboard()
    payload['edit_shots'][0]['dialogue_execution'] = _dialogue_lines(include_voice=False)
    payload['generation_units'][0]['voice_text_assets'] = ['V001', 'V002']
    return payload


def test_gu_rejects_flattened_dialogue_when_member_sh_has_locked_lines():
    payload = _payload_with_sh_dialogue()
    payload['generation_units'][0]['phases'][0]['dialogue_execution'] = '明天九点二十。 什么？'

    errors = validate_storyboard_payload(payload)

    assert any('GU_DIALOGUE_STRUCTURE' in error for error in errors), errors


def test_gu_structured_dialogue_renders_speaker_voice_verbatim_and_lipsync():
    payload = _payload_with_sh_dialogue()
    payload['generation_units'][0]['phases'][0]['dialogue_execution'] = _dialogue_lines(include_voice=True)

    assert validate_storyboard_payload(payload) == []
    rendered = render_storyboard(payload)

    assert '许程【V001】：“明天九点二十。”' in rendered
    assert '许国安【V002】：“什么？”' in rendered
    assert '口型同步：是' in rendered
    assert '表演：平静直接' in rendered
    assert '表演：短促，不拖尾' in rendered


def test_gu_dialogue_voice_id_must_be_declared_by_current_unit():
    payload = _payload_with_sh_dialogue()
    payload['generation_units'][0]['voice_text_assets'] = ['V001']
    payload['generation_units'][0]['phases'][0]['dialogue_execution'] = _dialogue_lines(include_voice=True)

    errors = validate_storyboard_payload(payload)

    assert any('GU_DIALOGUE_VOICE' in error and 'V002' in error for error in errors), errors


def test_gu_dialogue_must_preserve_member_sh_speaker_verbatim_order_and_metadata():
    payload = _payload_with_sh_dialogue()
    lines = _dialogue_lines(include_voice=True)
    lines[0]['speaker'] = '许国安'
    lines[0]['delivery'] = '被改写的表演'
    payload['generation_units'][0]['phases'][0]['dialogue_execution'] = lines

    errors = validate_storyboard_payload(payload)

    assert any('GU_DIALOGUE_MISMATCH' in error for error in errors), errors


def test_character_voice_asset_requires_matching_voice_id_in_final_gu(tmp_path: Path):
    root = tmp_path / 'project'
    (root / 'storyboard').mkdir(parents=True)
    payload = minimal_storyboard()
    payload['edit_shots'][0]['dialogue_execution'] = [{
        'speaker': '许程', 'verbatim': '明天九点二十。', 'mode': '画内', 'lip_sync': True, 'delivery': '平静直接'
    }]
    payload['generation_units'][0]['phases'][0]['dialogue_execution'] = [{
        'speaker': '许程', 'verbatim': '明天九点二十。', 'mode': '画内', 'lip_sync': True, 'delivery': '平静直接'
    }]
    payload['generation_units'][0]['voice_text_assets'] = []

    (root / 'storyboard' / 'EP01_STORYBOARD.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(payload), encoding='utf-8')

    records = {
        'A001': {'asset_id': 'A001', 'name': '许程', 'voice_asset_id': 'V001'},
        'V001': {'asset_id': 'V001', 'asset_class': 'TEXT_VOICE_ASSET', 'name': '许程声线'},
    }
    errors: list[str] = []

    _validate_storyboard_authority(root, 'EP01', records, {'V001'}, errors)

    assert any('GU_DIALOGUE_VOICE' in error and 'V001' in error for error in errors), errors


def test_no_dialogue_gu_remains_valid_and_unforced():
    payload = minimal_storyboard()
    assert validate_storyboard_payload(payload) == []
