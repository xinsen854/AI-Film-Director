from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from build_exports import _verify_delivery_gate
from render_storyboard import render_storyboard, validate_storyboard_payload


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def minimal_storyboard(*, camera_side: str = 'A', cross_axis_allowed: bool = False) -> dict:
    shot = {
        'edit_shot_id': 'SH001',
        'scene_id': 'SC01',
        'edit_shot_duration': 10.0,
        'generation_unit_id': 'GU001',
        'source': {'scene_id': 'SC01', 'story_range': '测试剧情', 'director_beat': 'beat-1'},
        'shot_function': {'primary': '推进剧情', 'change_after_shot': '人物完成明确动作'},
        'shot_type': 'MS',
        'base_frame': {'location_time': '室内白天', 'functional_zone': '桌边', 'framing_and_position': '中景'},
        'camera_parameters': {'camera_behavior': '固定', 'perspective': '正常', 'height': '眼平', 'angle': '平视', 'depth_focus': '主体清晰', 'composition': '人物偏左', 'layers': '前中后景明确', 'look_motion_room': '前方留白'},
        'axis_and_gaze': {'axis': 'AXIS-1', 'camera_side': camera_side, 'gaze': '看向桌面', 'screen_direction': 'L2R', 'cross_axis_allowed': cross_axis_allowed, 'cross_axis_transition': '明确过渡' if cross_axis_allowed else '无'},
        'visual_asset_calls': [],
        'spatial_blocking': {'location_asset': '测试场景', 'dramatic_purpose': '推进动作', 'visibility_hearing': '可见可听', 'start_positions': '桌旁', 'frame_positions': '左侧', 'movement_path': '向前一步', 'end_positions': '桌前', 'needs_space_diagram': False},
        'continuous_visuals': ['人物完成一个连续动作'],
        'first_last_frame_anchors': {'first_frame': '人物在桌旁', 'last_frame': '人物在桌前', 'locked_between': '服装和道具连续'},
        'key_micro_reactions': {'stimulus': '看到桌面', 'first_reaction': '视线下落', 'control': '短暂停顿', 'final_action': '伸手'},
        'dialogue_execution': [],
        'sound': {'onscreen': '脚步', 'ambience': '室内底噪', 'special': '无', 'bridge': '无', 'music_policy': '无BGM'},
        'edit_interface': {'cut_in': '动作开始', 'cut_out': '动作结束', 'action_match': True, 'gaze_match': True, 'sound_lead': False},
        'continuity_locks': {'wardrobe': '同一服装', 'injury_wet_dirt': '无变化', 'hair_face': '无变化', 'hand_props': '双手空', 'orientation_screen': '朝右', 'physical_position': '桌前', 'light_time_weather': '室内白天', 'other_state': '无', 'known_information': '当前信息', 'forbidden_future': '未来剧情', 'world_ability_limits': '现实规则'},
        'next_shot_handoff': {'type': '动作衔接', 'start_state': '人物在桌前', 'do_not_reset': '人物位置、轴线与道具'},
    }
    gu = {
        'generation_unit_id': 'GU001',
        'target_video_model': 'SEEDANCE_2_0',
        'packing_policy': 'SINGLE_SHOT',
        'mode': 'SINGLE_SHOT',
        'duration': 10.0,
        'member_edit_shots': ['SH001'],
        'contains_explicit_cuts': False,
        'active_media_references': [],
        'voice_text_assets': [],
        'phases': [{
            'phase_id': 'PH01', 'stage_goal': '完成动作',
            'image_and_camera': '固定中景记录人物动作',
            'action_and_physics': '人物自然移动并停下',
            'performance_and_microreaction': '视线变化后短暂停顿',
            'dialogue_execution': '', 'end_state': '人物停在桌前',
        }],
        'prompt_sections': {
            'generation_goal': '生成完整连续动作',
            'reference_roles': ['仅使用当前已声明事实'],
            'initial_state': '人物在桌旁',
            'sound': '脚步与室内底噪，无BGM',
            'keep_consistent': '服装、位置、轴线连续',
            'local_constraints': '不得出现未来剧情',
        },
    }
    data = {'edit_shots': [shot], 'generation_units': [gu]}
    assert validate_storyboard_payload(data) == []
    return data


def two_shot_storyboard(*, cross_allowed: bool = False) -> dict:
    data = minimal_storyboard(camera_side='A')
    first = data['edit_shots'][0]
    first['edit_shot_duration'] = 5.0
    first['next_shot_handoff'] = {'type': '连续切换', 'start_state': '人物仍在桌前', 'do_not_reset': 'AXIS-1与camera side'}
    data['generation_units'][0]['duration'] = 5.0

    second = copy.deepcopy(first)
    second['edit_shot_id'] = 'SH002'
    second['generation_unit_id'] = 'GU002'
    second['axis_and_gaze']['camera_side'] = 'B'
    second['axis_and_gaze']['cross_axis_allowed'] = cross_allowed
    second['axis_and_gaze']['cross_axis_transition'] = '人物运动中明确越轴' if cross_allowed else '无'
    second['first_last_frame_anchors']['first_frame'] = '人物仍在桌前'

    gu2 = copy.deepcopy(data['generation_units'][0])
    gu2['generation_unit_id'] = 'GU002'
    gu2['member_edit_shots'] = ['SH002']
    data['edit_shots'].append(second)
    data['generation_units'].append(gu2)
    assert validate_storyboard_payload(data) == []
    return data


def test_story_driven_variable_sh_durations_can_fill_a_30_second_total():
    data = two_shot_storyboard(cross_allowed=True)
    durations = (11.5, 18.5)
    for shot, unit, duration in zip(data['edit_shots'], data['generation_units'], durations):
        shot['edit_shot_duration'] = duration
        shot['duration_basis'] = '由当前剧情动作、演员反应和剪辑节奏决定'
        unit['target_video_model'] = 'SEEDANCE_2_5'
        unit['duration'] = duration
    assert sum(shot['edit_shot_duration'] for shot in data['edit_shots']) == 30.0
    assert validate_storyboard_payload(data) == []


def test_mechanical_30_second_quantization_across_shots_is_blocked():
    data = two_shot_storyboard(cross_allowed=True)
    for shot, unit in zip(data['edit_shots'], data['generation_units']):
        shot['edit_shot_duration'] = 30.0
        unit['target_video_model'] = 'SEEDANCE_2_5'
        unit['duration'] = 30.0
    errors = validate_storyboard_payload(data)
    assert any('MECHANICAL_DURATION_QUANTIZATION' in item for item in errors)


def test_equal_long_takes_are_allowed_when_each_has_a_dramatic_duration_basis():
    data = two_shot_storyboard(cross_allowed=True)
    reasons = ('完整保留第一次人物选择与沉默后的反应', '不中断第二次对峙直到权力关系翻转')
    for shot, unit, reason in zip(data['edit_shots'], data['generation_units'], reasons):
        shot['edit_shot_duration'] = 30.0
        shot['duration_basis'] = reason
        unit['target_video_model'] = 'SEEDANCE_2_5'
        unit['duration'] = 30.0
    assert validate_storyboard_payload(data) == []


def make_series_root(tmp_path: Path, count: int = 1, *, runtime: float = 10.0, bounds: tuple[float, float] | None = None) -> Path:
    root = tmp_path / 'project'
    for d in ('state', 'screenplay', 'director', 'storyboard', 'assets'):
        (root / d).mkdir(parents=True, exist_ok=True)
    brief = {
        'project_id': 'TEST', 'work_format': 'series', 'episode_count': count,
        'target_episode_runtime_seconds': 10.0, 'asset_production_mode': 'prompts_only',
    }
    if bounds:
        brief['minimum_episode_runtime_seconds'], brief['maximum_episode_runtime_seconds'] = bounds
    dump(root / 'state' / 'project_brief.json', brief)
    (root / 'FINAL_QC.md').write_text('## Project Result\nPASS\n', encoding='utf-8')

    episodes = []
    completed = []
    for n in range(1, count + 1):
        uid = f'EP{n:02d}'
        payload = minimal_storyboard()
        payload['edit_shots'][0]['edit_shot_duration'] = runtime
        payload['generation_units'][0]['duration'] = runtime
        dump(root / 'storyboard' / f'{uid}_STORYBOARD.json', payload)
        (root / 'storyboard' / f'{uid}_STORYBOARD.md').write_text(render_storyboard(payload), encoding='utf-8')
        (root / 'screenplay' / f'{uid}_LOCKED_SCREENPLAY.md').write_text(f'# {uid}\n', encoding='utf-8')
        (root / 'director' / f'{uid}_INTEGRATED_DIRECTOR_SCREENPLAY.md').write_text(f'# {uid}\n', encoding='utf-8')
        episodes.append({'episode_id': uid, 'unit_id': uid, 'status': 'COMPLETE', 'actual_runtime_seconds': runtime})
        completed.append(uid)
    dump(root / 'PRODUCTION_LEDGER.json', {
        'schema_version': '1.0', 'project_id': 'TEST', 'scope_type': 'episodes', 'status': 'COMPLETED',
        'target_episode_count': count, 'target_episode_runtime_seconds': 10.0,
        'episodes': episodes, 'completed_episodes': completed,
        'coverage': {'completed_count': count, 'percentage': 100.0}, 'next_resume': {'episode_id': None},
    })
    return root


def test_quick_mode_cannot_claim_formal_eight_file_export(tmp_path: Path):
    root = tmp_path / 'quick-project'
    dump(root / 'state' / 'project_brief.json', {'execution_mode': 'QUICK'})
    with pytest.raises(ValueError, match='QUICK_MODE_FORMAL_EXPORT_FORBIDDEN'):
        _verify_delivery_gate(root)


def write_asset_library(root: Path, *, mode: str, status: str = 'PROMPT_ONLY') -> None:
    brief = json.loads((root / 'state' / 'project_brief.json').read_text(encoding='utf-8'))
    brief['asset_production_mode'] = mode
    dump(root / 'state' / 'project_brief.json', brief)
    dump(root / 'assets' / 'ASSET_LIBRARY.json', {
        'ASSET_LIBRARY': {
            'contract_version': '4.3',
            'project_asset_policy': {
                'world_and_visual_style': '现实主义', 'character_face_policy': '身份稳定',
                'image_prompt_policy': '可复现', 'voice_asset_policy': 'V-series text only',
            },
            'quick_index': [],
            'character_assets': [{
                'asset_id': 'A001', 'asset_class': 'VISUAL_ASSET', 'name': '主角',
                'image_prompt': '主角稳定身份资产', 'image_status': status, 'image_file': '',
                'downstream_metadata': {'default_reference_role': 'identity', 'generic_eligible': False},
            }],
            'voice_assets': [], 'persistent_states': [], 'location_assets': [], 'prop_assets': [], 'g_assets': [],
        }
    })


def write_scene_intelligence(root: Path, unit_id: str, *, intentional: str = '') -> None:
    result = {
        'scene_id': 'SC01', 'scene_core': '同一冲突结构',
        'dramatic_function': {'primary': '冲突升级', 'secondary': []},
        'interaction_form': ['双人对峙'],
        'character_objectives': {'甲': '逼对方让步', '乙': '拒绝'},
        'emotional_mechanism': {'primary': '压力升级', 'causal_chain': [], 'secondary': [], 'confidence': 0.9},
        'relationship_dynamic': {'start': '僵持', 'end': '僵持', 'delta': '无变化', 'confidence': 0.9},
        'power_dynamic': {'start_controller': '甲', 'shift_points': [], 'end_controller': '甲', 'direction': '无变化', 'confidence': 0.9},
        'subtext': {'explicit_layer': '争执', 'hidden_layer': '争夺控制权', 'confidence': 0.9},
        'information_state': {'characters': {}, 'audience_knows': [], 'audience_misbelief': [], 'reveal_in_scene': []},
        'space_function': [], 'energy_profile': {},
        'beat_map': [{'beat_id': 'B1', 'change_basis': ''}],
        'generation_risk_profile': {}, 'confidence_overall': 0.9, 'ambiguities': [],
    }
    if intentional:
        result['intentional_repetition_reason'] = intentional
    dump(root / 'state' / 'scene_intelligence' / f'{unit_id}_scene_intelligence.json', {'SCENE_INTELLIGENCE_RESULT': result})


def test_runtime_out_of_explicit_bounds_blocks_final_delivery(tmp_path: Path):
    root = make_series_root(tmp_path, runtime=5.0, bounds=(8.0, 12.0))
    with pytest.raises(ValueError, match='HARD_EPISODE_RUNTIME_OUT_OF_RANGE|时长'):
        _verify_delivery_gate(root)


def test_no_runtime_bounds_does_not_invent_a_new_limit(tmp_path: Path):
    root = make_series_root(tmp_path, runtime=5.0, bounds=None)
    _verify_delivery_gate(root)


def test_missing_generation_unit_or_final_prompt_blocks_delivery(tmp_path: Path):
    root = make_series_root(tmp_path)
    path = root / 'storyboard' / 'EP01_STORYBOARD.json'
    payload = json.loads(path.read_text(encoding='utf-8'))
    payload['generation_units'] = []
    dump(path, payload)
    with pytest.raises(ValueError, match='HARD_SH_GU_PROMPT_MISSING|GU|Prompt|分镜'):
        _verify_delivery_gate(root)


def test_required_core_asset_status_missing_blocks_delivery(tmp_path: Path):
    root = make_series_root(tmp_path)
    write_asset_library(root, mode='core_assets', status='PROMPT_ONLY')
    with pytest.raises(ValueError, match='HARD_REQUIRED_ASSET_MISSING|资产'):
        _verify_delivery_gate(root)


def test_prompts_only_mode_does_not_force_image_generation(tmp_path: Path):
    root = make_series_root(tmp_path)
    write_asset_library(root, mode='prompts_only', status='PROMPT_ONLY')
    _verify_delivery_gate(root)


def test_clear_axis_side_jump_without_permission_is_hard_continuity_error(tmp_path: Path):
    root = make_series_root(tmp_path)
    payload = two_shot_storyboard(cross_allowed=False)
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', payload)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(payload), encoding='utf-8')
    with pytest.raises(ValueError, match='HARD_CONTINUITY_BREAK|连续|越轴'):
        _verify_delivery_gate(root)


def test_explicitly_allowed_axis_crossing_does_not_get_overblocked(tmp_path: Path):
    root = make_series_root(tmp_path)
    payload = two_shot_storyboard(cross_allowed=True)
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', payload)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(payload), encoding='utf-8')
    _verify_delivery_gate(root)


def test_three_consecutive_units_same_structure_without_progression_is_blocked(tmp_path: Path):
    root = make_series_root(tmp_path, count=3)
    for uid in ('EP01', 'EP02', 'EP03'):
        write_scene_intelligence(root, uid)
    with pytest.raises(ValueError, match='HARD_REPEATED_PLOT_TEMPLATE|重复|模板'):
        _verify_delivery_gate(root)


def test_two_similar_units_are_not_enough_to_block_creative_parallel_structure(tmp_path: Path):
    root = make_series_root(tmp_path, count=2)
    for uid in ('EP01', 'EP02'):
        write_scene_intelligence(root, uid)
    _verify_delivery_gate(root)


def test_intentional_repetition_reason_prevents_false_positive(tmp_path: Path):
    root = make_series_root(tmp_path, count=3)
    for uid in ('EP01', 'EP02', 'EP03'):
        write_scene_intelligence(root, uid, intentional='有意平行结构，用于主题回收')
    _verify_delivery_gate(root)
