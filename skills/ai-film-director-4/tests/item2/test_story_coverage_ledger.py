from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / 'tests'))

from build_exports import _verify_delivery_gate
from production_ledger import checkpoint_episode
from render_storyboard import render_storyboard, validate_storyboard_payload
from story_coverage import build_story_coverage
from support_pipeline import prepare_upstream_chain


def dump(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def make_root(tmp_path: Path, count: int = 1) -> Path:
    root = tmp_path / 'project'
    for d in ('state', 'storyboard', 'screenplay', 'director'):
        (root / d).mkdir(parents=True, exist_ok=True)
    dump(root / 'state' / 'project_brief.json', {
        'project_id': 'TEST', 'work_format': 'series', 'episode_count': count,
        'target_episode_runtime_seconds': 10,
    })
    dump(root / 'state' / 'pipeline_state.json', {
        'project_id': 'TEST', 'status': 'PRODUCTION_IN_PROGRESS', 'current_phase': 'shot-segment',
        'current_unit': 'EP01', 'completed_units': [], 'runtime_state_version': '2.0', 'story_authority_ready': True,
    })
    dump(root / 'state' / 'runtime_contract.json', {'runtime_state_version': '2.0', 'authority_profile': 'AFD_CW_SINGLE_AUTHORITY'})
    return root


def minimal_storyboard(
    unit_id: str,
    *,
    scene_id: str = 'SC01',
    story_atom_ids: list[str] | None = None,
    revealed_info_ids: list[str] | None = None,
    dialogue: str = '',
    extra_prompt_text: str = '',
) -> dict:
    shot_id = 'SH001'
    gu_id = 'GU001'
    payload = {
        'edit_shots': [{
            'edit_shot_id': shot_id,
            'scene_id': scene_id,
            'edit_shot_duration': 10.0,
            'generation_unit_id': gu_id,
            'source': {'scene_id': scene_id, 'story_range': f'{unit_id} test', 'director_beat': 'beat-1'},
            'coverage': {
                'story_atom_ids': list(story_atom_ids or []),
                'revealed_info_ids': list(revealed_info_ids or []),
            },
            'shot_function': {'primary': '完成锁定剧情动作', 'change_after_shot': '剧情状态发生明确变化'},
            'shot_type': 'MS',
            'base_frame': {'location_time': '室内白天', 'functional_zone': '桌边', 'framing_and_position': '中景正侧位'},
            'camera_parameters': {'camera_behavior': '固定机位', 'perspective': '正常透视', 'height': '眼平', 'angle': '平视', 'depth_focus': '主体清晰', 'composition': '人物居中偏左', 'layers': '前景空，中景人物，后景墙面', 'look_motion_room': '人物前方留运动空间'},
            'axis_and_gaze': {'axis': '人物与桌面动作轴', 'camera_side': '轴线左侧', 'gaze': '看向桌面', 'screen_direction': '左向右', 'cross_axis_allowed': False, 'cross_axis_transition': '无'},
            'visual_asset_calls': [],
            'spatial_blocking': {'location_asset': '测试场景', 'dramatic_purpose': '完成动作', 'visibility_hearing': '单人可见可听', 'start_positions': '桌旁站立', 'frame_positions': '画面左中', 'movement_path': '向右一步', 'end_positions': '桌前停住', 'needs_space_diagram': False},
            'continuous_visuals': ['人物从站立到桌前停住'],
            'first_last_frame_anchors': {'first_frame': '人物站在桌旁', 'last_frame': '人物停在桌前', 'locked_between': '服装与桌面位置不变'},
            'key_micro_reactions': {'stimulus': '看到桌面物件', 'first_reaction': '视线下落', 'control': '短暂停顿', 'final_action': '伸手靠近'},
            'dialogue_execution': ([{'speaker': '父亲', 'verbatim': dialogue, 'mode': '画内', 'lip_sync': True, 'delivery': '停顿后说出'}] if dialogue else []),
            'sound': {'onscreen': '脚步声', 'ambience': '室内底噪', 'special': '无特殊声', 'bridge': '无声音桥', 'music_policy': '无BGM'},
            'edit_interface': {'cut_in': '动作开始', 'cut_out': '人物停住', 'action_match': False, 'gaze_match': True, 'sound_lead': False},
            'continuity_locks': {'wardrobe': '同一服装', 'injury_wet_dirt': '无变化', 'hair_face': '无变化', 'hand_props': '双手空', 'orientation_screen': '朝右', 'physical_position': '桌前', 'light_time_weather': '室内白天', 'other_state': '无', 'known_information': '只知道当前事实', 'forbidden_future': '不得出现后续剧情', 'world_ability_limits': '现实世界规则'},
            'next_shot_handoff': {'type': '动作衔接', 'start_state': '人物停在桌前', 'do_not_reset': '人物位置与视线'},
        }],
        'generation_units': [{
            'generation_unit_id': gu_id,
            'target_video_model': 'SEEDANCE_2_0',
            'packing_policy': 'SINGLE_SHOT',
            'mode': 'SINGLE_SHOT',
            'duration': 10.0,
            'member_edit_shots': [shot_id],
            'contains_explicit_cuts': False,
            'active_media_references': [],
            'voice_text_assets': [],
            'phases': [{
                'phase_id': 'PH01',
                'stage_goal': '完成连续动作',
                'image_and_camera': '固定中景记录当前动作',
                'action_and_physics': '人物完成动作并自然停住',
                'performance_and_microreaction': '视线先落下，短暂停顿后完成动作',
                'dialogue_execution': ([{'speaker': '父亲', 'verbatim': dialogue, 'mode': '画内', 'lip_sync': True, 'delivery': '停顿后说出'}] if dialogue else []),
                'end_state': '人物停住，当前剧情状态成立',
            }],
            'prompt_sections': {
                'generation_goal': '生成当前锁定剧情对应的连续镜头',
                'reference_roles': ['当前场景仅使用已声明视觉事实'],
                'initial_state': '人物位于当前场景起始位置',
                'sound': '环境声与当前对白，无BGM',
                'keep_consistent': '人物、位置、道具与剧情信息连续',
                'local_constraints': '不得出现后续剧情或未揭露信息' + extra_prompt_text,
            },
        }],
    }
    errors = validate_storyboard_payload(payload)
    assert errors == [], errors
    return payload


def write_storyboard(root: Path, unit_id: str, payload: dict) -> None:
    prepare_upstream_chain(root, unit_id, create_empty_authority=False)
    dump(root / 'storyboard' / f'{unit_id}_STORYBOARD.json', payload)
    (root / 'storyboard' / f'{unit_id}_STORYBOARD.md').write_text(render_storyboard(payload), encoding='utf-8')


def write_authority(root: Path, atoms: list[dict], info_items: list[dict] | None = None) -> None:
    dump(root / 'state' / 'story_authority.json', {'atoms': atoms})
    dump(root / 'state' / 'information_ledger.json', {'items': list(info_items or [])})


def atom(atom_id: str, scene_id: str, kind: str, content: str, *, unit_id: str = 'EP01', visual: bool = True) -> dict:
    return {
        'atom_id': atom_id, 'unit_id': unit_id, 'scene_id': scene_id, 'type': kind,
        'content': content, 'story_basis': '测试锁定事实', 'locked': True,
        'visual_coverage_required': visual,
    }


def info(info_id: str, *, status: str, planned: str | None, actual: str | None, literals: list[str]) -> dict:
    return {
        'info_id': info_id,
        'truth': '测试真相',
        'character_knowledge': {},
        'audience_state': {'knows': [], 'believes': [], 'suspects': [], 'misbeliefs': [], 'hopes': [], 'fears': []},
        'earliest_fair_reveal': planned,
        'planned_reveal': planned,
        'actual_reveal': actual,
        'visible_clues': [],
        'concealment_reason': '测试',
        'protected_literals': literals,
        'status': status,
        'reveal_stage': 'READABLE' if status in {'REVEALED', 'REINTERPRETED'} else 'LATENT',
    }


def test_checkpoint_writes_story_coverage_for_atoms_scenes_dialogue_and_reveal(tmp_path: Path):
    root = make_root(tmp_path)
    write_authority(root, [
        atom('ST001', 'SC01', 'action', '儿子把牌子放在柜台上'),
        atom('ST002', 'SC01', 'dialogue', '医院号没退吧？'),
    ], [info('I001', status='REVEALED', planned='EP01/SC01', actual='EP01/SC01', literals=['医院号'])])
    write_storyboard(root, 'EP01', minimal_storyboard(
        'EP01', story_atom_ids=['ST001', 'ST002'], revealed_info_ids=['I001'], dialogue='医院号没退吧？'
    ))

    checkpoint_episode(root, 'EP01')
    ledger_path = root / 'state' / 'STORY_COVERAGE_LEDGER.json'
    assert ledger_path.is_file()
    ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    assert ledger['story_atoms']['covered_atom_ids'] == ['ST001', 'ST002']
    assert ledger['scenes']['missing_scene_ids'] == []
    assert ledger['dialogues']['missing_dialogue_atom_ids'] == []
    assert ledger['information']['uncovered_reveal_info_ids'] == []
    assert ledger['information']['early_reveal_info_ids'] == []


def test_three_digit_pu_and_scene_ids_preserve_width_for_reveal_coverage(tmp_path: Path):
    root = make_root(tmp_path)
    write_authority(root, [
        atom('ST001', 'SC001', 'action', '母亲正在输液', unit_id='PU001'),
    ], [info(
        'I001', status='REVEALED', planned='PU001/SC001',
        actual='PU001/SC001', literals=[],
    )])
    write_storyboard(root, 'PU001', minimal_storyboard(
        'PU001', scene_id='SC001', story_atom_ids=['ST001'],
        revealed_info_ids=['I001'],
    ))

    coverage = build_story_coverage(root, confirm_unit='PU001')

    assert coverage['information']['uncovered_reveal_info_ids'] == []
    item = next(row for row in coverage['items'] if row['coverage_id'] == 'I001')
    assert item['unit_id'] == 'PU001'
    assert item['status'] == 'CONFIRMED'


def test_checkpoint_rejects_missing_locked_story_atom_and_scene(tmp_path: Path):
    root = make_root(tmp_path)
    write_authority(root, [
        atom('ST001', 'SC01', 'action', '第一场动作'),
        atom('ST003', 'SC02', 'event', '第二场关键事件'),
    ])
    write_storyboard(root, 'EP01', minimal_storyboard('EP01', story_atom_ids=['ST001']))

    with pytest.raises(ValueError, match='ST003|SC02|Story Coverage|STORY_COVERAGE'):
        checkpoint_episode(root, 'EP01')


def test_checkpoint_rejects_important_dialogue_that_is_only_tagged_but_not_executed(tmp_path: Path):
    root = make_root(tmp_path)
    write_authority(root, [atom('ST002', 'SC01', 'dialogue', '医院号没退吧？')])
    write_storyboard(root, 'EP01', minimal_storyboard('EP01', story_atom_ids=['ST002'], dialogue=''))

    with pytest.raises(ValueError, match='ST002|对白|dialogue'):
        checkpoint_episode(root, 'EP01')


def test_checkpoint_rejects_protected_literal_before_planned_reveal(tmp_path: Path):
    root = make_root(tmp_path, count=2)
    write_authority(root, [atom('ST001', 'SC01', 'action', '第一集动作')], [
        info('I002', status='HIDDEN', planned='EP02/SC02', actual=None, literals=['暂停营业'])
    ])
    write_storyboard(root, 'EP01', minimal_storyboard(
        'EP01', story_atom_ids=['ST001'], extra_prompt_text='；牌子上清晰写着“暂停营业”'
    ))

    with pytest.raises(ValueError, match='I002|提前|Reveal|REVEAL'):
        checkpoint_episode(root, 'EP01')


def test_checkpoint_does_not_overrestrict_hidden_information_when_it_is_not_exposed(tmp_path: Path):
    root = make_root(tmp_path, count=2)
    write_authority(root, [atom('ST001', 'SC01', 'action', '第一集动作')], [
        info('I002', status='HIDDEN', planned='EP02/SC02', actual=None, literals=['暂停营业'])
    ])
    write_storyboard(root, 'EP01', minimal_storyboard('EP01', story_atom_ids=['ST001']))

    ledger = checkpoint_episode(root, 'EP01')
    assert ledger['completed_episodes'] == ['EP01']


def test_delivery_gate_rejects_stale_or_uncovered_story_coverage_when_story_authority_is_active(tmp_path: Path):
    root = make_root(tmp_path)
    write_authority(root, [atom('ST001', 'SC01', 'action', '必须拍到的动作')])
    payload = minimal_storyboard('EP01', story_atom_ids=['ST001'])
    write_storyboard(root, 'EP01', payload)
    (root / 'screenplay' / 'EP01_LOCKED_SCREENPLAY.md').write_text('EP01', encoding='utf-8')
    (root / 'director' / 'EP01_INTEGRATED_DIRECTOR_SCREENPLAY.md').write_text('EP01', encoding='utf-8')
    checkpoint_episode(root, 'EP01')
    (root / 'FINAL_QC.md').write_text('## Project Result\nPASS\n', encoding='utf-8')

    coverage_path = root / 'state' / 'STORY_COVERAGE_LEDGER.json'
    coverage = json.loads(coverage_path.read_text(encoding='utf-8'))
    coverage['story_atoms']['uncovered_atom_ids'] = ['ST001']
    coverage['story_atoms']['covered_atom_ids'] = []
    dump(coverage_path, coverage)

    with pytest.raises(ValueError, match='Story Coverage|STORY_COVERAGE|剧情覆盖|覆盖账本'):
        _verify_delivery_gate(root)


def test_completed_episode_recheckpoint_revalidates_current_story_coverage(tmp_path: Path):
    root = make_root(tmp_path)
    write_authority(root, [atom('ST001', 'SC01', 'action', '必须持续覆盖的动作')])
    write_storyboard(root, 'EP01', minimal_storyboard('EP01', story_atom_ids=['ST001']))

    checkpoint_episode(root, 'EP01')

    # Simulate a rerun/regression after the episode was previously checkpointed.
    write_storyboard(root, 'EP01', minimal_storyboard('EP01', story_atom_ids=[]))

    with pytest.raises(ValueError, match='ST001|Story Coverage|STORY_COVERAGE|锁定剧情原子'):
        checkpoint_episode(root, 'EP01')
