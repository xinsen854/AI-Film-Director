from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / 'tests'))

import production_ledger as production_ledger_module
from build_exports import _verify_delivery_gate
from production_ledger import checkpoint_episode, load_or_initialize
from render_storyboard import render_storyboard, validate_storyboard_payload
from support_pipeline import prepare_upstream_chain


def dump(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def minimal_storyboard(unit_id: str, duration: float = 10.0) -> dict:
    shot_id = 'SH001'
    gu_id = 'GU001'
    payload = {
        'edit_shots': [{
            'edit_shot_id': shot_id,
            'scene_id': 'SC01',
            'edit_shot_duration': duration,
            'generation_unit_id': gu_id,
            'source': {'scene_id': 'SC01', 'story_range': f'{unit_id} test', 'director_beat': 'beat-1'},
            'shot_function': {'primary': '建立当前动作', 'change_after_shot': '人物完成一个明确动作'},
            'shot_type': 'MS',
            'base_frame': {'location_time': '室内白天', 'functional_zone': '桌边', 'framing_and_position': '中景正侧位'},
            'camera_parameters': {'camera_behavior': '固定机位', 'perspective': '正常透视', 'height': '眼平', 'angle': '平视', 'depth_focus': '主体清晰', 'composition': '人物居中偏左', 'layers': '前景空，中景人物，后景墙面', 'look_motion_room': '人物前方留运动空间'},
            'axis_and_gaze': {'axis': '人物与桌面动作轴', 'camera_side': '轴线左侧', 'gaze': '看向桌面', 'screen_direction': '左向右', 'cross_axis_allowed': False, 'cross_axis_transition': '无'},
            'visual_asset_calls': [],
            'spatial_blocking': {'location_asset': '测试场景', 'dramatic_purpose': '完成动作', 'visibility_hearing': '单人可见可听', 'start_positions': '桌旁站立', 'frame_positions': '画面左中', 'movement_path': '向右一步', 'end_positions': '桌前停住', 'needs_space_diagram': False},
            'continuous_visuals': ['人物从站立到桌前停住'],
            'first_last_frame_anchors': {'first_frame': '人物站在桌旁', 'last_frame': '人物停在桌前', 'locked_between': '服装与桌面位置不变'},
            'key_micro_reactions': {'stimulus': '看到桌面物件', 'first_reaction': '视线下落', 'control': '短暂停顿', 'final_action': '伸手靠近'},
            'dialogue_execution': [],
            'sound': {'onscreen': '脚步声', 'ambience': '室内底噪', 'special': '无特殊声', 'bridge': '无声音桥', 'music_policy': '无BGM'},
            'edit_interface': {'cut_in': '动作开始', 'cut_out': '人物停住', 'action_match': False, 'gaze_match': True, 'sound_lead': False},
            'continuity_locks': {'wardrobe': '同一服装', 'injury_wet_dirt': '无变化', 'hair_face': '无变化', 'hand_props': '双手空', 'orientation_screen': '朝右', 'physical_position': '桌前', 'light_time_weather': '室内白天', 'other_state': '无', 'known_information': '只知道桌面物件存在', 'forbidden_future': '不得出现后续剧情', 'world_ability_limits': '现实世界规则'},
            'next_shot_handoff': {'type': '动作衔接', 'start_state': '人物停在桌前', 'do_not_reset': '人物位置与视线'},
        }],
        'generation_units': [{
            'generation_unit_id': gu_id,
            'target_video_model': 'SEEDANCE_2_0',
            'packing_policy': 'SINGLE_SHOT',
            'mode': 'SINGLE_SHOT',
            'duration': duration,
            'member_edit_shots': [shot_id],
            'contains_explicit_cuts': False,
            'active_media_references': [],
            'voice_text_assets': [],
            'phases': [{
                'phase_id': 'PH01',
                'stage_goal': '完成连续动作',
                'image_and_camera': '固定中景记录人物从桌旁走到桌前',
                'action_and_physics': '人物向右一步后停住，身体惯性自然收住',
                'performance_and_microreaction': '视线先落向桌面，停顿后伸手',
                'dialogue_execution': '',
                'end_state': '人物停在桌前，视线仍在桌面',
            }],
            'prompt_sections': {
                'generation_goal': '生成一个完整连续的单人动作镜头',
                'reference_roles': ['当前场景仅使用已声明视觉事实'],
                'initial_state': '人物站在桌旁，双手空',
                'sound': '脚步声与室内底噪，无BGM',
                'keep_consistent': '服装、桌面位置、人物朝向连续',
                'local_constraints': '不得出现后续剧情或未声明人物',
            },
        }],
    }
    errors = validate_storyboard_payload(payload)
    assert errors == [], errors
    return payload


def make_series_root(tmp_path: Path, count: int = 2) -> Path:
    root = tmp_path / 'project'
    (root / 'state').mkdir(parents=True)
    (root / 'storyboard').mkdir(parents=True)
    dump(root / 'state' / 'project_brief.json', {
        'project_id': 'TEST', 'work_format': 'series', 'episode_count': count,
        'target_episode_runtime_seconds': 10,
    })
    dump(root / 'state' / 'pipeline_state.json', {
        'project_id': 'TEST', 'status': 'PRODUCTION_IN_PROGRESS', 'current_phase': 'shot-segment',
        'current_unit': 'EP01', 'completed_units': [], 'runtime_state_version': '2.0',
    })
    dump(root / 'state' / 'runtime_contract.json', {'runtime_state_version': '2.0', 'authority_profile': 'AFD_CW_SINGLE_AUTHORITY'})
    return root


def write_unit(root: Path, unit_id: str, duration: float = 10.0) -> None:
    prepare_upstream_chain(root, unit_id, create_empty_authority=True)
    payload = minimal_storyboard(unit_id, duration)
    dump(root / 'storyboard' / f'{unit_id}_STORYBOARD.json', payload)
    (root / 'storyboard' / f'{unit_id}_STORYBOARD.md').write_text(render_storyboard(payload), encoding='utf-8')


def test_checkpoint_syncs_pipeline_state_and_points_to_next_episode(tmp_path: Path):
    root = make_series_root(tmp_path, count=2)
    write_unit(root, 'EP01')

    ledger = checkpoint_episode(root, 'EP01')
    state = json.loads((root / 'state' / 'pipeline_state.json').read_text(encoding='utf-8'))

    assert ledger['completed_episodes'] == ['EP01']
    assert ledger['next_resume'] == {'episode_id': 'EP02'}
    assert ledger['status'] == 'IN_PROGRESS'
    assert state['completed_units'] == ['EP01']
    assert state['status'] == 'PRODUCTION_IN_PROGRESS'
    assert state['current_unit'] == 'EP02'


def test_duplicate_checkpoint_does_not_reproduce_unit_and_repairs_pipeline_sync(tmp_path: Path):
    root = make_series_root(tmp_path, count=2)
    write_unit(root, 'EP01')
    first = checkpoint_episode(root, 'EP01')

    state_path = root / 'state' / 'pipeline_state.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    state['completed_units'] = []
    state['current_unit'] = 'EP01'
    dump(state_path, state)

    second = checkpoint_episode(root, 'EP01')
    repaired = json.loads(state_path.read_text(encoding='utf-8'))

    assert second == first
    assert len(second['episodes']) == 1
    assert repaired['completed_units'] == ['EP01']
    assert repaired['current_unit'] == 'EP02'


def test_last_episode_checkpoint_marks_pipeline_project_completed(tmp_path: Path):
    root = make_series_root(tmp_path, count=1)
    write_unit(root, 'EP01')

    ledger = checkpoint_episode(root, 'EP01')
    state = json.loads((root / 'state' / 'pipeline_state.json').read_text(encoding='utf-8'))

    assert ledger['status'] == 'COMPLETED'
    assert ledger['coverage']['completed_count'] == 1
    assert state['status'] == 'PROJECT_COMPLETED'
    assert state['current_phase'] == 'quality-delivery'
    assert state['current_unit'] is None


def test_delivery_gate_rejects_visible_units_not_matching_completed_ledger(tmp_path: Path):
    root = tmp_path / 'project'
    for d in ('screenplay', 'director', 'storyboard'):
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / 'FINAL_QC.md').write_text('## Project Result\nPASS\n', encoding='utf-8')
    dump(root / 'PRODUCTION_LEDGER.json', {
        'schema_version': '1.0', 'project_id': 'TEST', 'scope_type': 'episodes', 'status': 'COMPLETED',
        'target_episode_count': 1, 'episodes': [{'episode_id': 'EP01', 'status': 'COMPLETE'}],
        'completed_episodes': ['EP01'], 'coverage': {'completed_count': 1, 'percentage': 100.0},
        'next_resume': {'episode_id': None},
    })
    for unit in ('EP01', 'EP02'):
        (root / 'screenplay' / f'{unit}_LOCKED_SCREENPLAY.md').write_text(unit, encoding='utf-8')
        (root / 'director' / f'{unit}_INTEGRATED_DIRECTOR_SCREENPLAY.md').write_text(unit, encoding='utf-8')
        (root / 'storyboard' / f'{unit}_STORYBOARD.md').write_text(unit, encoding='utf-8')

    with pytest.raises(ValueError, match='生产账本.*不一致|账本.*不一致'):
        _verify_delivery_gate(root)


def test_existing_resume_contract_remains_sequential(tmp_path: Path):
    root = make_series_root(tmp_path, count=3)
    write_unit(root, 'EP01')
    checkpoint_episode(root, 'EP01')
    ledger = load_or_initialize(root)
    assert ledger['next_resume']['episode_id'] == 'EP02'

    write_unit(root, 'EP03')
    with pytest.raises(ValueError, match='expected EP02'):
        checkpoint_episode(root, 'EP03')


def make_film_root(tmp_path: Path, target: float = 20.0) -> Path:
    root = tmp_path / 'film_project'
    (root / 'state').mkdir(parents=True)
    (root / 'storyboard').mkdir(parents=True)
    dump(root / 'state' / 'project_brief.json', {
        'project_id': 'FILM', 'work_format': 'film', 'target_total_runtime_seconds': target,
    })
    dump(root / 'state' / 'pipeline_state.json', {
        'project_id': 'FILM', 'status': 'PRODUCTION_IN_PROGRESS', 'current_phase': 'shot-segment',
        'current_unit': 'PU01', 'completed_units': [], 'runtime_state_version': '2.0',
    })
    dump(root / 'state' / 'runtime_contract.json', {'runtime_state_version': '2.0', 'authority_profile': 'AFD_CW_SINGLE_AUTHORITY'})
    return root


def test_existing_film_resume_and_no_duplicate_remain_intact(tmp_path: Path):
    from production_ledger import checkpoint_film_unit

    root = make_film_root(tmp_path, target=20)
    write_unit(root, 'PU01', duration=10)
    first = checkpoint_film_unit(root, 'PU01', 0, 10)
    assert first['status'] == 'IN_PROGRESS'
    assert first['completed_units'] == ['PU01']
    assert first['next_resume'] == {'start_seconds': 10.0}

    second = checkpoint_film_unit(root, 'PU01', 0, 10)
    assert second['film_units'] == first['film_units']
    assert len(second['film_units']) == 1


def test_existing_film_checkpoint_reconfirms_story_coverage(tmp_path: Path, monkeypatch):
    from production_ledger import checkpoint_film_unit

    root = make_film_root(tmp_path, target=20)
    write_unit(root, 'PU01', duration=10)
    checkpoint_film_unit(root, 'PU01', 0, 10)

    calls = []
    monkeypatch.setattr(production_ledger_module, 'story_coverage_enabled', lambda _root: True)
    monkeypatch.setattr(
        production_ledger_module,
        'write_story_coverage',
        lambda _root, confirm_unit=None: calls.append(confirm_unit),
    )

    checkpoint_film_unit(root, 'PU01', 0, 10)

    assert calls == [None, 'PU01']


def test_delivery_gate_accepts_exact_ledger_unit_set(tmp_path: Path):
    root = tmp_path / 'delivery_ok'
    for d in ('screenplay', 'director', 'storyboard'):
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / 'FINAL_QC.md').write_text('## Project Result\nPASS\n', encoding='utf-8')
    dump(root / 'PRODUCTION_LEDGER.json', {
        'schema_version': '1.0', 'project_id': 'TEST', 'scope_type': 'episodes', 'status': 'COMPLETED',
        'target_episode_count': 1,
        'episodes': [{'episode_id': 'EP01', 'status': 'COMPLETE', 'unit_id': 'EP01', 'actual_runtime_seconds': 10}],
        'completed_episodes': ['EP01'], 'coverage': {'completed_count': 1, 'percentage': 100.0},
        'next_resume': {'episode_id': None},
    })
    (root / 'screenplay' / 'EP01_LOCKED_SCREENPLAY.md').write_text('EP01', encoding='utf-8')
    (root / 'director' / 'EP01_INTEGRATED_DIRECTOR_SCREENPLAY.md').write_text('EP01', encoding='utf-8')
    payload = minimal_storyboard('EP01', 10)
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', payload)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(payload), encoding='utf-8')

    _verify_delivery_gate(root)


def test_existing_episode_checkpoint_revalidates_then_reconfirms_story_coverage(tmp_path: Path, monkeypatch):
    root = make_series_root(tmp_path, count=2)
    write_unit(root, 'EP01')
    checkpoint_episode(root, 'EP01')

    calls = []
    monkeypatch.setattr(production_ledger_module, 'story_coverage_enabled', lambda _root: True)
    monkeypatch.setattr(
        production_ledger_module,
        'write_story_coverage',
        lambda _root, confirm_unit=None: calls.append(confirm_unit),
    )
    monkeypatch.setattr(production_ledger_module, 'validate_story_coverage', lambda _root, unit_id=None: [])

    checkpoint_episode(root, 'EP01')

    assert calls == [None, 'EP01']
