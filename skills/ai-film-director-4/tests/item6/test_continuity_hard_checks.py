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

_spec = importlib.util.spec_from_file_location('item3_helpers', ROOT / 'tests' / 'item3' / 'test_final_hard_qc.py')
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
make_series_root = _mod.make_series_root
two_shot_storyboard = _mod.two_shot_storyboard
minimal_storyboard = _mod.minimal_storyboard


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def save_storyboard(root: Path, payload: dict) -> None:
    assert validate_storyboard_payload(payload) == []
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', payload)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(payload), encoding='utf-8')


def make_continuous_two_shot_root(tmp_path: Path) -> tuple[Path, dict]:
    root = make_series_root(tmp_path, count=1, runtime=10.0)
    payload = two_shot_storyboard(cross_allowed=True)
    for shot in payload['edit_shots']:
        shot['axis_and_gaze']['camera_side'] = 'A'
        shot['axis_and_gaze']['cross_axis_allowed'] = False
        shot['axis_and_gaze']['cross_axis_transition'] = '无'
    payload['edit_shots'][0]['edit_shot_duration'] = 5.0
    payload['edit_shots'][1]['edit_shot_duration'] = 5.0
    payload['generation_units'][0]['duration'] = 5.0
    payload['generation_units'][1]['duration'] = 5.0
    save_storyboard(root, payload)
    return root, payload


def test_axis_cross_requires_both_permission_and_real_transition(tmp_path: Path):
    root, payload = make_continuous_two_shot_root(tmp_path)
    payload['edit_shots'][1]['axis_and_gaze']['camera_side'] = 'B'
    payload['edit_shots'][1]['axis_and_gaze']['cross_axis_allowed'] = True
    payload['edit_shots'][1]['axis_and_gaze']['cross_axis_transition'] = '无'
    save_storyboard(root, payload)
    with pytest.raises(ValueError, match='CONTINUITY|越轴|camera_side|轴线'):
        _verify_delivery_gate(root)


def test_locked_gaze_mismatch_is_hard_error(tmp_path: Path):
    root, payload = make_continuous_two_shot_root(tmp_path)
    first, second = payload['edit_shots']
    first['axis_and_gaze']['gaze'] = {'许程': '父亲'}
    second['axis_and_gaze']['gaze'] = {'许程': '门口'}
    first['next_shot_handoff']['do_not_reset'] = ['gaze']
    save_storyboard(root, payload)
    with pytest.raises(ValueError, match='CONTINUITY|gaze|视线'):
        _verify_delivery_gate(root)


def test_tail_to_first_character_position_mismatch_is_hard_error(tmp_path: Path):
    root, payload = make_continuous_two_shot_root(tmp_path)
    first, second = payload['edit_shots']
    first['first_last_frame_anchors']['last_frame'] = {'character_positions': {'许程': '柜台左侧'}}
    second['first_last_frame_anchors']['first_frame'] = {'character_positions': {'许程': '门口'}}
    first['next_shot_handoff']['type'] = 'CS'
    first['next_shot_handoff']['do_not_reset'] = ['character_positions']
    save_storyboard(root, payload)
    with pytest.raises(ValueError, match='CONTINUITY|character_positions|位置'):
        _verify_delivery_gate(root)


def test_tail_to_first_hand_prop_mismatch_is_hard_error(tmp_path: Path):
    root, payload = make_continuous_two_shot_root(tmp_path)
    first, second = payload['edit_shots']
    first['first_last_frame_anchors']['last_frame'] = {'hand_props': {'许程右手': '纸袋'}}
    second['first_last_frame_anchors']['first_frame'] = {'hand_props': {'许程右手': '空'}}
    first['next_shot_handoff']['type'] = 'CC'
    first['next_shot_handoff']['do_not_reset'] = ['hand_props']
    save_storyboard(root, payload)
    with pytest.raises(ValueError, match='CONTINUITY|hand_props|道具'):
        _verify_delivery_gate(root)


def test_tail_to_first_persistent_state_mismatch_is_hard_error(tmp_path: Path):
    root, payload = make_continuous_two_shot_root(tmp_path)
    first, second = payload['edit_shots']
    first['first_last_frame_anchors']['last_frame'] = {'persistent_states': {'A001': ['A001-ST001']}}
    second['first_last_frame_anchors']['first_frame'] = {'persistent_states': {'A001': []}}
    first['next_shot_handoff']['type'] = 'CS'
    first['next_shot_handoff']['do_not_reset'] = ['persistent_states']
    save_storyboard(root, payload)
    with pytest.raises(ValueError, match='CONTINUITY|persistent_states|持续状态'):
        _verify_delivery_gate(root)


def test_mutually_exclusive_persistent_states_cannot_be_active_in_same_shot(tmp_path: Path):
    root = make_series_root(tmp_path, count=1, runtime=10.0)
    payload = minimal_storyboard()
    payload['edit_shots'][0]['visual_asset_calls'] = [
        {'asset_id': 'A001-ST001', 'name': '湿透状态', 'file': 'assets/generated/A001-ST001.png', 'role': '持续状态', 'shot_use': '当前湿透'},
        {'asset_id': 'A001-ST002', 'name': '完全干燥状态', 'file': 'assets/generated/A001-ST002.png', 'role': '持续状态', 'shot_use': '当前干燥'},
    ]
    save_storyboard(root, payload)
    dump(root / 'assets' / 'ASSET_LIBRARY.json', {
        'ASSET_LIBRARY': {
            'contract_version': '4.3',
            'project_asset_policy': {'world_and_visual_style': '现实主义', 'character_face_policy': '稳定', 'image_prompt_policy': '可复现', 'voice_asset_policy': 'V text only'},
            'quick_index': [], 'character_assets': [], 'voice_assets': [], 'location_assets': [], 'prop_assets': [], 'g_assets': [],
            'persistent_states': [
                {'state_id': 'A001-ST001', 'inherits_from': 'A001', 'state_category': 'wetness', 'state_start': 'SC01', 'state_end': 'ongoing', 'source_fact': '淋雨', 'trigger_cause': '雨', 'visible_change': '湿透', 'unchanged_facts': ['身份'], 'compatible_with': [], 'conflicts_with': ['A001-ST002'], 'persistent_scope': ['SC01'], 'image_file': '', 'image_status': 'PROMPT_ONLY', 'image_prompt': '湿透状态', 'downstream_metadata': {'default_reference_role': 'state', 'visual_cost_units': 0, 'seedance_reference_slot_cost': 0, 'generic_eligible': False}},
                {'state_id': 'A001-ST002', 'inherits_from': 'A001', 'state_category': 'wetness', 'state_start': 'SC01', 'state_end': 'ongoing', 'source_fact': '烘干', 'trigger_cause': '换衣', 'visible_change': '完全干燥', 'unchanged_facts': ['身份'], 'compatible_with': [], 'conflicts_with': ['A001-ST001'], 'persistent_scope': ['SC01'], 'image_file': '', 'image_status': 'PROMPT_ONLY', 'image_prompt': '干燥状态', 'downstream_metadata': {'default_reference_role': 'state', 'visual_cost_units': 0, 'seedance_reference_slot_cost': 0, 'generic_eligible': False}},
            ],
        }
    })
    with pytest.raises(ValueError, match='CONTINUITY|STATE_CONFLICT|互斥'):
        _verify_delivery_gate(root)


def test_scene_transition_allows_position_prop_and_state_change(tmp_path: Path):
    root, payload = make_continuous_two_shot_root(tmp_path)
    first, second = payload['edit_shots']
    first['next_shot_handoff']['type'] = 'ST'
    first['next_shot_handoff']['do_not_reset'] = ['character_positions', 'hand_props', 'persistent_states']
    first['first_last_frame_anchors']['last_frame'] = {
        'character_positions': {'许程': '钟表店柜台'}, 'hand_props': {'许程右手': '纸袋'}, 'persistent_states': {'A001': ['A001-ST001']}
    }
    second['scene_id'] = 'SC02'
    second['source']['scene_id'] = 'SC02'
    second['first_last_frame_anchors']['first_frame'] = {
        'character_positions': {'许程': '医院走廊'}, 'hand_props': {'许程右手': '挂号单'}, 'persistent_states': {'A001': []}
    }
    save_storyboard(root, payload)
    _verify_delivery_gate(root)


def test_unlocked_gaze_change_is_creatively_allowed(tmp_path: Path):
    root, payload = make_continuous_two_shot_root(tmp_path)
    first, second = payload['edit_shots']
    first['axis_and_gaze']['gaze'] = {'许程': '父亲'}
    second['axis_and_gaze']['gaze'] = {'许程': '桌面'}
    first['next_shot_handoff']['do_not_reset'] = ['character_positions']
    save_storyboard(root, payload)
    _verify_delivery_gate(root)


def test_new_axis_logic_allows_camera_side_change_without_false_positive(tmp_path: Path):
    root, payload = make_continuous_two_shot_root(tmp_path)
    payload['edit_shots'][1]['axis_and_gaze']['axis'] = 'AXIS-2'
    payload['edit_shots'][1]['axis_and_gaze']['camera_side'] = 'B'
    save_storyboard(root, payload)
    _verify_delivery_gate(root)
