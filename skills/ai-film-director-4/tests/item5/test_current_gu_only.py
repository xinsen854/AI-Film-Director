from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from build_exports import _verify_delivery_gate
from render_storyboard import render_storyboard, validate_storyboard_payload

# Reuse the already-validated minimal project fixture from item 3 without changing production code.
_spec = importlib.util.spec_from_file_location('item3_helpers', ROOT / 'tests' / 'item3' / 'test_final_hard_qc.py')
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
make_series_root = _mod.make_series_root
two_shot_storyboard = _mod.two_shot_storyboard


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def make_two_shot_root(tmp_path: Path) -> tuple[Path, dict]:
    root = make_series_root(tmp_path, count=1, runtime=10.0)
    payload = two_shot_storyboard(cross_allowed=True)
    payload['edit_shots'][0]['edit_shot_duration'] = 5.0
    payload['edit_shots'][1]['edit_shot_duration'] = 5.0
    payload['generation_units'][0]['duration'] = 5.0
    payload['generation_units'][1]['duration'] = 5.0
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', payload)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(payload), encoding='utf-8')
    return root, payload


def save_storyboard(root: Path, payload: dict) -> None:
    assert validate_storyboard_payload(payload) == []
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', payload)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(payload), encoding='utf-8')


def test_future_story_event_cannot_leak_into_current_gu(tmp_path: Path):
    root, payload = make_two_shot_root(tmp_path)
    future = '父亲把关店钥匙正式交给儿子'
    payload['edit_shots'][1]['source']['story_range'] = future
    payload['generation_units'][0]['prompt_sections']['generation_goal'] = f'当前镜头提前表现：{future}'
    save_storyboard(root, payload)
    with pytest.raises(ValueError, match='CURRENT_GU_ONLY|未来剧情|剧情'):
        _verify_delivery_gate(root)


def test_future_dialogue_cannot_leak_into_current_gu(tmp_path: Path):
    root, payload = make_two_shot_root(tmp_path)
    line = '医院号没退吧？'
    payload['edit_shots'][1]['dialogue_execution'] = [{'speaker': '许国安', 'verbatim': line}]
    payload['generation_units'][1]['phases'][0]['dialogue_execution'] = [{'speaker': '许国安', 'verbatim': line}]
    payload['generation_units'][0]['prompt_sections']['local_constraints'] = f'当前限制错误地提前写入未来对白：{line}'
    save_storyboard(root, payload)
    with pytest.raises(ValueError, match='CURRENT_GU_ONLY|未来对白|对白'):
        _verify_delivery_gate(root)


def test_future_sound_cannot_leak_into_current_gu(tmp_path: Path):
    root, payload = make_two_shot_root(tmp_path)
    sound = '远处救护车鸣笛逐渐靠近'
    payload['edit_shots'][1]['sound']['special'] = sound
    payload['generation_units'][0]['prompt_sections']['sound'] = f'室内底噪，同时出现{sound}'
    save_storyboard(root, payload)
    with pytest.raises(ValueError, match='CURRENT_GU_ONLY|未来声音|声音'):
        _verify_delivery_gate(root)


def test_future_asset_state_cannot_leak_into_current_gu(tmp_path: Path):
    root, payload = make_two_shot_root(tmp_path)
    state_id = 'A001-ST001'
    payload['edit_shots'][1]['visual_asset_calls'] = [{
        'asset_id': state_id, 'name': '许国安雨淋湿状态', 'file': 'assets/generated/A001-ST001.png',
        'role': '持续状态', 'shot_use': '后续雨中场景才激活',
    }]
    payload['generation_units'][0]['prompt_sections']['keep_consistent'] = f'当前就保持{state_id}的湿衣状态'
    save_storyboard(root, payload)
    with pytest.raises(ValueError, match='CURRENT_GU_ONLY|未来资产状态|状态'):
        _verify_delivery_gate(root)


def test_future_reveal_literal_cannot_leak_even_as_negative_constraint(tmp_path: Path):
    root, payload = make_two_shot_root(tmp_path)
    secret = '父亲已经决定永久关店'
    dump(root / 'state' / 'information_ledger.json', {
        'items': [{
            'info_id': 'I001', 'truth': secret, 'character_knowledge': {}, 'audience_state': {},
            'reveal_stage': 'LATENT', 'status': 'HIDDEN', 'planned_reveal': 'EP01/SC01/SH002',
            'protected_literals': [secret],
        }]
    })
    payload['generation_units'][0]['prompt_sections']['local_constraints'] = f'不要提前告诉观众：{secret}'
    save_storyboard(root, payload)
    with pytest.raises(ValueError, match='CURRENT_GU_ONLY|未来Reveal|未揭露|I001'):
        _verify_delivery_gate(root)


def test_current_gu_facts_are_allowed_and_not_overrestricted(tmp_path: Path):
    root, payload = make_two_shot_root(tmp_path)
    current_line = '先把饭吃了。'
    current_sound = '柜台机械表滴答声'
    current_state = 'A001-ST000'
    payload['edit_shots'][0]['dialogue_execution'] = [{'speaker': '许国安', 'verbatim': current_line}]
    payload['edit_shots'][0]['sound']['special'] = current_sound
    payload['edit_shots'][0]['visual_asset_calls'] = [{
        'asset_id': current_state, 'name': '许国安当前服装状态', 'file': 'assets/generated/A001-ST000.png',
        'role': '当前持续状态', 'shot_use': '当前镜头使用',
    }]
    payload['generation_units'][0]['phases'][0]['dialogue_execution'] = [{'speaker': '许国安', 'verbatim': current_line}]
    payload['generation_units'][0]['prompt_sections']['sound'] = current_sound
    payload['generation_units'][0]['prompt_sections']['keep_consistent'] = f'{current_state}当前服装状态保持一致'
    # The same dialogue may recur later; if it is already a current-GU fact it must not be treated as pollution.
    payload['edit_shots'][1]['dialogue_execution'] = [{'speaker': '许国安', 'verbatim': current_line}]
    payload['generation_units'][1]['phases'][0]['dialogue_execution'] = [{'speaker': '许国安', 'verbatim': current_line}]
    save_storyboard(root, payload)
    _verify_delivery_gate(root)


def test_unrelated_future_facts_not_mentioned_do_not_block(tmp_path: Path):
    root, payload = make_two_shot_root(tmp_path)
    payload['edit_shots'][1]['source']['story_range'] = '后续医院检查结果公布'
    payload['edit_shots'][1]['dialogue_execution'] = [{'speaker': '医生', 'verbatim': '检查结果出来了。'}]
    payload['generation_units'][1]['phases'][0]['dialogue_execution'] = [{'speaker': '医生', 'verbatim': '检查结果出来了。'}]
    payload['edit_shots'][1]['sound']['special'] = '医院广播声'
    save_storyboard(root, payload)
    _verify_delivery_gate(root)
