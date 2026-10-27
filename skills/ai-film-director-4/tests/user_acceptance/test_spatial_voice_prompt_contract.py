from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from render_storyboard import render_storyboard, validate_storyboard_payload


def _dialogue() -> dict:
    return {
        "speaker": "A001",
        "verbatim": "你……早就知道？",
        "voice_profile_id": "V001",
        "performance_strategy": "压住怒气，不愿先暴露恐惧",
        "audible_emotion": "表面冷静，句尾开始发紧",
        "volume": "近距离低声",
        "distance": "人物相距一臂，近讲收音",
        "pace": "前半稳定，后半略加快",
        "emphasis": "早就知道",
        "breath": "开口前短促吸气",
        "pause": "你之后停顿，知道后留半拍",
    }


def _sound() -> dict:
    return {
        "environment": "仓库深夜低频风声与远处金属共振",
        "foley": "鞋底摩擦水泥地、衣料蹭过货架",
        "sync_sound": "A001画内对白和受伤后的短促呼吸",
        "spatial_acoustics": "大仓库长混响，东门声源偏画面右侧",
        "bridge": "尾部金属轻响延续到下一镜",
        "music_policy": "无BGM、无配乐、禁止自动情绪音乐",
    }


def _diagram() -> dict:
    return {
        "north": "↑",
        "axis_line": "AXIS-01：A001↔A003",
        "camera_side": "SOUTH_SIDE",
        "ascii_map": [
            "┌────────────────────────────┐",
            "│ 北墙  A003↓       [货架/A002→] │",
            "│       ──AXIS-01────────     │",
            "│   CAM↗                 东门>A001←│",
            "└────────────────────────────┘",
        ],
        "characters": [
            {"asset_id": "A001", "start": "东门外", "end": "东侧通道", "facing": "西", "gaze": "A003"},
            {"asset_id": "A002", "start": "货架后", "end": "货架后", "facing": "东", "gaze": "门缝"},
            {"asset_id": "A003", "start": "北墙", "end": "北墙", "facing": "南", "gaze": "A001"},
        ],
        "camera": "主轴南侧，镜头朝东北",
        "props": ["A001右手手枪", "中央货架"],
        "entrances_exits": ["东门=入口/可撤离出口"],
        "visibility_hearing": "A001与A003互相可见可听；A002可听但被遮挡",
    }


def _payload(*, complex_space: bool = True) -> dict:
    spatial = {
        "location_asset": "S001",
        "dramatic_purpose": "显性对峙掩护隐性偷听",
        "visibility_hearing": "A002能听见但不被看见",
        "start_positions": {"A001": "东门外", "A002": "货架后", "A003": "北墙"},
        "frame_positions": {"A001": "右", "A002": "中后景遮挡", "A003": "左上"},
        "movement_path": {"A001": "东门→东侧通道", "A002": "不移动", "A003": "不移动"},
        "end_positions": {"A001": "东侧通道", "A002": "货架后", "A003": "北墙"},
        "needs_space_diagram": complex_space,
    }
    if complex_space:
        spatial["space_diagram"] = _diagram()
    shot = {
        "edit_shot_id": "SH001",
        "scene_id": "SC01",
        "edit_shot_duration": 10.0,
        "generation_unit_id": "GU001",
        "source": {"scene_id": "SC01", "story_range": "仓库对峙", "director_beat": "A001逼问"},
        "shot_function": {"primary": "揭示关系裂缝", "change_after_shot": "A001确认对方知情"},
        "shot_type": "MS",
        "base_frame": {"location_time": "仓库深夜", "functional_zone": "东门至北墙", "framing_and_position": "21:9中广景"},
        "camera_parameters": {"camera_behavior": "缓慢推近", "perspective": "正常", "height": "眼平", "angle": "平视", "depth_focus": "三层焦点", "composition": "三角构图", "layers": "门/货架/北墙", "look_motion_room": "A001前方留白"},
        "axis_and_gaze": {"axis_line": "AXIS-01：A001↔A003", "camera_side": "SOUTH_SIDE", "gaze": {"A001": "A003", "A002": "门缝", "A003": "A001"}, "screen_direction": "A001 R2L", "cross_axis_allowed": False, "cross_axis_transition": "无"},
        "visual_asset_calls": [],
        "spatial_blocking": spatial,
        "continuous_visuals": ["A001右手持枪进入并停下"],
        "first_last_frame_anchors": {"first_frame": {"character_positions": spatial["start_positions"], "hand_props": {"A001": "右手手枪"}, "persistent_states": ["A001-ST001"]}, "last_frame": {"character_positions": spatial["end_positions"], "hand_props": {"A001": "右手手枪"}, "persistent_states": ["A001-ST001"]}, "locked_between": "持枪手、伤势、轴线、遮挡关系"},
        "key_micro_reactions": {"stimulus": "A003沉默", "first_reaction": "A001瞳孔短暂收紧", "control": "下颌收紧压住怒意", "final_action": "低声逼问"},
        "dialogue_execution": [_dialogue()],
        "sound": _sound(),
        "edit_interface": {"cut_in": "东门声先入", "cut_out": "知道后停顿", "action_match": True, "gaze_match": True, "sound_lead": True},
        "continuity_locks": {"wardrobe": "A001深色夹克", "injury_wet_dirt": "A001左肩受伤", "hair_face": "额头薄汗", "hand_props": {"A001": "右手手枪"}, "orientation_screen": {"A001": "R2L", "A003": "L2R"}, "physical_position": spatial["end_positions"], "light_time_weather": "仓库深夜冷白顶光", "other_state": ["A001-ST001"], "known_information": "A001怀疑A003知情", "forbidden_future": "A002身份尚未揭露", "world_ability_limits": "现实物理"},
        "next_shot_handoff": {"type": "CS", "start_state": {"character_positions": spatial["end_positions"], "hand_props": {"A001": "右手手枪"}, "persistent_states": ["A001-ST001"]}, "do_not_reset": ["character_positions", "hand_props", "persistent_states", "axis_line", "camera_side"]},
    }
    gu = {
        "generation_unit_id": "GU001",
        "target_video_model": "SEEDANCE_2_0",
        "packing_policy": "SINGLE_SHOT",
        "mode": "SINGLE_SHOT",
        "duration": 10.0,
        "member_edit_shots": ["SH001"],
        "contains_explicit_cuts": False,
        "active_media_references": [],
        "voice_text_assets": ["V001"],
        "starting_state": shot["first_last_frame_anchors"]["first_frame"],
        "ending_state": shot["first_last_frame_anchors"]["last_frame"],
        "phases": [{"phase_id": "PH01", "stage_goal": "完成逼问", "image_and_camera": "中广景缓慢推近", "action_and_physics": "A001进入后停下", "performance_and_microreaction": "先压怒再漏出恐惧", "dialogue_execution": [_dialogue()], "end_state": shot["first_last_frame_anchors"]["last_frame"]}],
        "prompt_sections": {"generation_goal": "生成仓库复杂对峙", "reference_roles": ["A001文字身份锚，不冒充媒体"], "initial_state": "A001在东门外，A002货架后，A003北墙", "sound": _sound(), "keep_consistent": "右手持枪、左肩伤、轴线南侧、A002遮挡", "local_constraints": "不提前揭露A002"},
    }
    return {"storyboard_contract_version": "4.3", "edit_shots": [shot], "generation_units": [gu]}


def test_complex_space_diagram_is_rendered_inside_sh_and_final_gu_prompt() -> None:
    payload = _payload(complex_space=True)
    assert validate_storyboard_payload(payload) == []
    rendered = render_storyboard(payload)
    assert rendered.count("【空间占位图】") == 2
    for token in ("A001", "A002", "A003", "CAM", "AXIS-01", "东门", "右手手枪"):
        assert token in rendered
    gu_prompt = rendered.split("## GU001｜视频模型最终 Prompt", 1)[1]
    assert "【空间占位图】" in gu_prompt
    assert "┌────────────────────────────┐" in gu_prompt


def test_simple_scene_does_not_emit_space_diagram() -> None:
    payload = _payload(complex_space=False)
    assert validate_storyboard_payload(payload) == []
    assert "【空间占位图】" not in render_storyboard(payload)


def test_complex_scene_without_diagram_fails_validation() -> None:
    payload = _payload(complex_space=True)
    del payload["edit_shots"][0]["spatial_blocking"]["space_diagram"]
    assert any("SPACE_DIAGRAM_REQUIRED" in item for item in validate_storyboard_payload(payload))


def test_dialogue_requires_all_line_performance_dimensions() -> None:
    payload = _payload()
    del payload["edit_shots"][0]["dialogue_execution"][0]["breath"]
    assert any("breath" in item for item in validate_storyboard_payload(payload))


def test_sound_requires_four_layers_and_explicit_no_bgm() -> None:
    payload = _payload()
    del payload["edit_shots"][0]["sound"]["foley"]
    assert any("foley" in item for item in validate_storyboard_payload(payload))
    payload = _payload()
    payload["edit_shots"][0]["sound"]["music_policy"] = "自动生成悬疑配乐"
    assert any("BGM" in item or "音乐" in item for item in validate_storyboard_payload(payload))


def test_gu_starting_and_ending_states_are_structured() -> None:
    payload = _payload()
    del payload["generation_units"][0]["starting_state"]
    assert any("starting_state" in item for item in validate_storyboard_payload(payload))
