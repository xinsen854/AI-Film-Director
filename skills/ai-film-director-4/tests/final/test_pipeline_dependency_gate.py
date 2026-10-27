from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / 'tests'))

from build_exports import build_exports
from production_ledger import checkpoint_episode
from render_asset_library import render_asset_library
from render_storyboard import render_storyboard
from render_emotion_map import render_emotion_map
from runtime_state import CURRENT_RUNTIME_STATE_VERSION, AUTHORITY_PROFILE


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def storyboard() -> dict:
    return {
        'edit_shots': [{
            'edit_shot_id': 'SH001', 'scene_id': 'SC01', 'edit_shot_duration': 10.0,
            'generation_unit_id': 'GU001',
            'source': {'scene_id': 'SC01', 'story_range': '模型自己编的剧情', 'director_beat': '自造beat'},
            'shot_function': {'primary': '推进', 'change_after_shot': '完成动作'}, 'shot_type': 'MS',
            'base_frame': {'location_time': '室内白天', 'functional_zone': '桌边', 'framing_and_position': '中景'},
            'camera_parameters': {'camera_behavior': '固定', 'perspective': '正常', 'height': '眼平', 'angle': '平视', 'depth_focus': '主体清晰', 'composition': '人物偏左', 'layers': '前中后景', 'look_motion_room': '前方留白'},
            'axis_and_gaze': {'axis': 'AXIS-1', 'camera_side': 'A', 'gaze': '桌面', 'screen_direction': 'L2R', 'cross_axis_allowed': False, 'cross_axis_transition': '无'},
            'visual_asset_calls': [],
            'spatial_blocking': {'location_asset': '测试场景', 'dramatic_purpose': '推进', 'visibility_hearing': '可见可听', 'start_positions': '桌旁', 'frame_positions': '左侧', 'movement_path': '向前一步', 'end_positions': '桌前', 'needs_space_diagram': False},
            'continuous_visuals': ['完成一个连续动作'],
            'first_last_frame_anchors': {'first_frame': '桌旁', 'last_frame': '桌前', 'locked_between': '状态连续'},
            'key_micro_reactions': {'stimulus': '看到桌面', 'first_reaction': '视线下落', 'control': '停顿', 'final_action': '伸手'},
            'dialogue_execution': [],
            'sound': {'onscreen': '脚步', 'ambience': '室内底噪', 'special': '无', 'bridge': '无', 'music_policy': '无BGM'},
            'edit_interface': {'cut_in': '开始', 'cut_out': '结束', 'action_match': True, 'gaze_match': True, 'sound_lead': False},
            'continuity_locks': {'wardrobe': '同一服装', 'injury_wet_dirt': '无', 'hair_face': '无', 'hand_props': '空手', 'orientation_screen': '朝右', 'physical_position': '桌前', 'light_time_weather': '白天', 'other_state': '无', 'known_information': '当前事实', 'forbidden_future': '未来剧情', 'world_ability_limits': '现实规则'},
            'next_shot_handoff': {'type': '动作衔接', 'start_state': '桌前', 'do_not_reset': '位置与轴线'},
        }],
        'generation_units': [{
            'generation_unit_id': 'GU001', 'target_video_model': 'SEEDANCE_2_0', 'packing_policy': 'SINGLE_SHOT',
            'mode': 'SINGLE_SHOT', 'duration': 10.0, 'member_edit_shots': ['SH001'], 'contains_explicit_cuts': False,
            'active_media_references': [], 'voice_text_assets': [],
            'phases': [{'phase_id': 'PH01', 'stage_goal': '完成动作', 'image_and_camera': '固定中景', 'action_and_physics': '自然移动', 'performance_and_microreaction': '视线变化后停顿', 'dialogue_execution': '', 'end_state': '停在桌前'}],
            'prompt_sections': {'generation_goal': '生成连续动作', 'reference_roles': ['当前事实'], 'initial_state': '桌旁', 'sound': '脚步与底噪', 'keep_consistent': '状态连续', 'local_constraints': '不得出现未来剧情'},
        }],
    }



def valid_emotion_payload() -> dict:
    return {
        'project_title': 'TEST',
        'project_type': 'series',
        'axis': {'type': 'episode', 'max': 1, 'unit_label': '集'},
        'summary': {},
        'phases': [{
            'phase_id': 'P1', 'range_label': 'EP01', 'start': 0, 'end': 1,
            'name': '建立', 'primary_emotion': '关注',
            'entry_intensity': 2, 'peak_intensity': 5, 'exit_intensity': 3,
        }],
        'nodes': [], 'fatigue_zones': [], 'paragraphs': [],
    }


def set_valid_emotion(root: Path, *, render_html: bool) -> None:
    dump(root / 'state' / 'audience_emotion_architecture.json', valid_emotion_payload())
    if render_html:
        render_emotion_map(root)

def make_bypass_project(tmp_path: Path) -> Path:
    root = tmp_path / 'project'
    for d in ('state', 'screenplay', 'director', 'storyboard', 'assets'):
        (root / d).mkdir(parents=True, exist_ok=True)
    dump(root / 'state' / 'runtime_contract.json', {'runtime_state_version': CURRENT_RUNTIME_STATE_VERSION, 'authority_profile': AUTHORITY_PROFILE})
    dump(root / 'state' / 'pipeline_state.json', {
        'runtime_state_version': CURRENT_RUNTIME_STATE_VERSION, 'status': 'PRODUCTION_IN_PROGRESS',
        'confirmed_brief': False, 'story_authority_ready': False, 'asset_library_ready': False,
        'scene_intelligence_ready': False, 'director_craft_ready': False, 'completed_units': [],
    })
    dump(root / 'state' / 'project_brief.json', {'project_id': 'TEST', 'work_format': 'series', 'episode_count': 1, 'target_episode_runtime_seconds': 10.0, 'asset_production_mode': 'prompts_only'})
    data = storyboard()
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', data)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(data), encoding='utf-8')
    return root


def test_storyboard_alone_cannot_checkpoint_as_complete(tmp_path: Path):
    root = make_bypass_project(tmp_path)
    with pytest.raises(ValueError, match='PIPELINE_DEPENDENCY|上游|依赖'):
        checkpoint_episode(root, 'EP01')


def test_fake_upstream_shells_and_manual_final_qc_cannot_export(tmp_path: Path):
    root = make_bypass_project(tmp_path)
    # Force a completed ledger and add only shell visible files: this reproduced the pre-4.0 bypass.
    dump(root / 'PRODUCTION_LEDGER.json', {
        'schema_version': '1.0', 'project_id': 'TEST', 'scope_type': 'episodes', 'status': 'COMPLETED',
        'target_episode_count': 1, 'target_episode_runtime_seconds': 10.0,
        'episodes': [{'episode_id': 'EP01', 'unit_id': 'EP01', 'status': 'COMPLETE', 'actual_runtime_seconds': 10.0}],
        'completed_episodes': ['EP01'], 'coverage': {'completed_count': 1, 'percentage': 100.0}, 'next_resume': {'episode_id': None},
    })
    (root / 'screenplay' / 'EP01_LOCKED_SCREENPLAY.md').write_text('# 空壳剧本\n', encoding='utf-8')
    (root / 'director' / 'EP01_INTEGRATED_DIRECTOR_SCREENPLAY.md').write_text('# 空壳导演稿\n', encoding='utf-8')
    (root / 'FINAL_QC.md').write_text('## Project Result\nPASS\n', encoding='utf-8')
    (root / 'SCRIPT_REVIEW.md').write_text('# 空壳审查\n', encoding='utf-8')
    (root / 'AUDIENCE_EMOTION_MAP.html').write_text('<html>空壳</html>', encoding='utf-8')
    asset_payload = {'ASSET_LIBRARY': {
        'contract_version': '4.3',
        'project_asset_policy': {'world_and_visual_style': '现实主义', 'character_face_policy': '稳定', 'image_prompt_policy': '可复现', 'voice_asset_policy': 'V-series text only'},
        'quick_index': [], 'character_assets': [], 'location_assets': [], 'prop_assets': [], 'g_assets': [], 'persistent_states': [], 'voice_assets': [],
    }}
    dump(root / 'assets' / 'ASSET_LIBRARY.json', asset_payload)
    (root / 'assets' / 'ASSET_LIBRARY.md').write_text(render_asset_library(asset_payload), encoding='utf-8')
    with pytest.raises(Exception, match='PIPELINE_DEPENDENCY|Scene Intelligence|pipeline_state|上游|项目Brief|创作母版'):
        build_exports(root)

from support_pipeline import prepare_scene_chain, prepare_project_prerequisites
from validate_unit_consistency import validate_project_consistency
import copy


def _two_scene_storyboard() -> dict:
    data = storyboard()
    first = data['edit_shots'][0]
    first['edit_shot_duration'] = 5.0
    first['generation_unit_id'] = 'GU001'
    data['generation_units'][0]['duration'] = 5.0
    second = copy.deepcopy(first)
    second['edit_shot_id'] = 'SH002'
    second['scene_id'] = 'SC02'
    second['source']['scene_id'] = 'SC02'
    second['generation_unit_id'] = 'GU002'
    second['first_last_frame_anchors']['first_frame'] = '第二场开始状态'
    second['first_last_frame_anchors']['last_frame'] = '第二场结束状态'
    gu2 = copy.deepcopy(data['generation_units'][0])
    gu2['generation_unit_id'] = 'GU002'
    gu2['member_edit_shots'] = ['SH002']
    data['edit_shots'].append(second)
    data['generation_units'].append(gu2)
    return data


def test_storyboard_scene_must_match_scene_specific_upstream_result(tmp_path: Path):
    root = make_bypass_project(tmp_path)
    prepare_scene_chain(root, 'EP01', 'SC01', per_scene=False)
    data = storyboard()
    data['edit_shots'][0]['scene_id'] = 'SC02'
    data['edit_shots'][0]['source']['scene_id'] = 'SC02'
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', data)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(data), encoding='utf-8')
    with pytest.raises(ValueError, match='SC02|Scene Intelligence|PIPELINE_DEPENDENCY'):
        checkpoint_episode(root, 'EP01')


def test_multiscene_unit_requires_upstream_chain_for_every_scene(tmp_path: Path):
    root = make_bypass_project(tmp_path)
    prepare_scene_chain(root, 'EP01', 'SC01', per_scene=True)
    data = _two_scene_storyboard()
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', data)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(data), encoding='utf-8')
    with pytest.raises(ValueError, match='SC02|PIPELINE_DEPENDENCY'):
        checkpoint_episode(root, 'EP01')


def test_router_spatial_activation_requires_spatial_result(tmp_path: Path):
    root = make_bypass_project(tmp_path)
    prepare_scene_chain(root, 'EP01', 'SC01', per_scene=True, spatial_active=True, create_spatial=False)
    data = storyboard()
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', data)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(data), encoding='utf-8')
    with pytest.raises(ValueError, match='Spatial|空间|SPATIAL|PIPELINE_DEPENDENCY'):
        checkpoint_episode(root, 'EP01')


def test_valid_multiscene_scene_specific_chain_is_not_overrestricted(tmp_path: Path):
    root = make_bypass_project(tmp_path)
    prepare_scene_chain(root, 'EP01', 'SC01', per_scene=True)
    prepare_scene_chain(root, 'EP01', 'SC02', per_scene=True)
    data = _two_scene_storyboard()
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', data)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(data), encoding='utf-8')
    ledger = checkpoint_episode(root, 'EP01')
    assert ledger['status'] == 'COMPLETED'

from story_coverage import write_story_coverage



def test_checkpoint_rejects_emotion_html_not_rendered_from_current_architecture(tmp_path: Path):
    root = make_bypass_project(tmp_path)
    prepare_scene_chain(root, 'EP01', 'SC01', per_scene=True)
    set_valid_emotion(root, render_html=False)
    (root / 'AUDIENCE_EMOTION_MAP.html').write_text('<html>手写空壳情绪图</html>', encoding='utf-8')
    with pytest.raises(ValueError, match='观众情绪|Emotion|Renderer|PIPELINE_DEPENDENCY'):
        checkpoint_episode(root, 'EP01')


def test_export_rerenders_emotion_html_from_locked_forge_audit_after_tamper(tmp_path: Path):
    root = make_bypass_project(tmp_path)
    prepare_scene_chain(root, 'EP01', 'SC01', per_scene=True)
    set_valid_emotion(root, render_html=True)
    checkpoint_episode(root, 'EP01')
    (root / 'PROJECT_BRIEF.md').write_text('# 已确认项目Brief\n', encoding='utf-8')
    (root / 'PROJECT_CREATIVE_BIBLE.md').write_text('# 项目创作母版\n', encoding='utf-8')
    (root / 'SCRIPT_REVIEW.md').write_text('# 剧本审查\n', encoding='utf-8')
    (root / 'FINAL_QC.md').write_text('## Project Result\nPASS\n', encoding='utf-8')
    write_story_coverage(root, confirm_unit='EP01')
    (root / 'AUDIENCE_EMOTION_MAP.html').write_text('<html>篡改后的空壳情绪图</html>', encoding='utf-8')
    result = build_exports(root)
    assert result['delivery_files'] == 8
    html = (root / '交付包' / '05_双层情绪规划图.html').read_text(encoding='utf-8')
    assert '全剧情情绪总谱' in html
    assert 'CHARACTER + AUDIENCE EMOTION FIELD' in html
    assert 'AUDIENCE HALO' in html
    assert '篡改后的空壳情绪图' not in html

def test_valid_full_chain_can_export(tmp_path: Path):
    root = make_bypass_project(tmp_path)
    prepare_scene_chain(root, 'EP01', 'SC01', per_scene=True)
    data = storyboard()
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', data)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(data), encoding='utf-8')
    dump(root / 'PRODUCTION_LEDGER.json', {
        'schema_version': '1.0', 'project_id': 'TEST', 'scope_type': 'episodes', 'status': 'COMPLETED',
        'target_episode_count': 1, 'target_episode_runtime_seconds': 10.0,
        'episodes': [{'episode_id': 'EP01', 'unit_id': 'EP01', 'status': 'COMPLETE', 'actual_runtime_seconds': 10.0}],
        'completed_episodes': ['EP01'], 'coverage': {'completed_count': 1, 'percentage': 100.0}, 'next_resume': {'episode_id': None},
    })
    state = json.loads((root / 'state' / 'pipeline_state.json').read_text(encoding='utf-8'))
    state.update({'status': 'PROJECT_COMPLETED', 'completed_units': ['EP01']})
    dump(root / 'state' / 'pipeline_state.json', state)
    (root / 'PROJECT_BRIEF.md').write_text('# 已确认项目Brief\n', encoding='utf-8')
    (root / 'PROJECT_CREATIVE_BIBLE.md').write_text('# 项目创作母版\n', encoding='utf-8')
    (root / 'SCRIPT_REVIEW.md').write_text('# 剧本审查\n', encoding='utf-8')
    set_valid_emotion(root, render_html=True)
    (root / 'FINAL_QC.md').write_text('## Project Result\nPASS\n', encoding='utf-8')
    write_story_coverage(root, confirm_unit='EP01')
    result = build_exports(root)
    assert result['delivery_files'] == 8
    assert (root / '交付包' / '07_正式分镜与视频模型最终Prompt.md').is_file()
    assert (root / '交付包' / '08_Story_Coverage_Ledger.html').is_file()


def test_storyboard_blocks_internal_forge_analysis_artifact_when_not_in_locked_screenplay(tmp_path: Path):
    root = make_bypass_project(tmp_path)
    prepare_scene_chain(root, 'EP01', 'SC01', per_scene=True)
    data = storyboard()
    data['edit_shots'][0]['base_frame']['framing_and_position'] = '进入 EMOTION STORY FORGE / Audience Halo 情绪图谱UI'
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', data)
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(render_storyboard(data), encoding='utf-8')
    errors = validate_project_consistency(root, 'EP01')
    assert any('ANALYSIS_ARTIFACT_LEAK' in item for item in errors)
