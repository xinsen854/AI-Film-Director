from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "scene_geo_lock.py"


def _module():
    assert MODULE_PATH.is_file(), "scene_geo_lock.py must exist"
    spec = importlib.util.spec_from_file_location("scene_geo_lock", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _location() -> dict:
    return {
        "asset_id": "S001",
        "name": "地下仪式厅",
        "architecture_type": "圆形石厅",
        "materials_and_color": "黑色玄武岩",
        "stable_geography": {
            "platform": "中央圆形石台",
            "north_door": "北墙唯一出口",
            "south_pillars": ["PILLAR-L", "PILLAR-R"],
        },
        "functional_zones": ["中央石台", "北门缓冲区"],
        "landmark_anchors": ["中央石台", "北门"],
        "entrances_exits": ["北门"],
        "image_prompt": "当前资产提示词不应改变GEO哈希",
    }


def _shot(lock: dict, *, shot_id: str = "SH001", camera_side: str = "A") -> dict:
    return {
        "edit_shot_id": shot_id,
        "scene_id": "SC01",
        "axis_and_gaze": {"camera_side": camera_side},
        "spatial_blocking": {
            "location_asset": "S001",
            "needs_space_diagram": False,
            "scene_geo_lock_ref": lock["lock_id"],
            "scene_geo_sha256": lock["geo_sha256"],
            "start_positions": {"A001": "北门内侧"},
            "end_positions": {"A001": "中央石台边缘"},
        },
    }


def test_geo_hash_uses_only_stable_location_geometry_not_prompt_or_camera() -> None:
    mod = _module()
    location = _location()
    first = mod.build_scene_geo_lock("SC01", location)
    location["image_prompt"] = "完全不同的图片提示词"
    location["materials_and_color"] = "颜色也改变"
    second = mod.build_scene_geo_lock("SC01", location)
    assert first["geo_sha256"] == second["geo_sha256"]

    location["stable_geography"]["north_door"] = "东墙唯一出口"
    third = mod.build_scene_geo_lock("SC01", location)
    assert third["geo_sha256"] != first["geo_sha256"]


def test_geo_lock_is_pure_scene_geometry_and_does_not_lock_people_or_camera() -> None:
    mod = _module()
    lock = mod.build_scene_geo_lock("SC01", _location())
    assert set(lock["locked_fields"]) == {
        "stable_geography", "functional_zones", "landmark_anchors", "entrances_exits"
    }
    assert "camera_side" not in lock["locked_fields"]
    assert "character_routes" not in lock["locked_fields"]
    assert "object_positions" not in lock["locked_fields"]


def test_meaningful_active_spatial_topology_requires_geo_lock() -> None:
    mod = _module()
    result = {
        "scene_id": "SC01",
        "activation_state": "ACTIVE",
        "space_topology": {"zones": ["中央石台"], "landmarks": ["北门"]},
    }
    errors = mod.validate_scene_geo_contract(
        scene_id="SC01",
        spatial_result=result,
        scene_shots=[{"scene_id": "SC01", "spatial_blocking": {"location_asset": "S001"}}],
        asset_records={"S001": _location()},
    )
    assert any("SCENE_GEO_LOCK_REQUIRED" in error for error in errors), errors


def test_geo_lock_detects_stale_asset_hash_and_shot_level_mismatch() -> None:
    mod = _module()
    location = _location()
    lock = mod.build_scene_geo_lock("SC01", location)
    result = {
        "scene_id": "SC01",
        "activation_state": "ACTIVE",
        "space_topology": {"zones": ["中央石台"]},
        "scene_geo_lock": lock,
    }
    shots = [_shot(lock, shot_id="SH001"), _shot(lock, shot_id="SH002", camera_side="B")]
    assert mod.validate_scene_geo_contract("SC01", result, shots, {"S001": location}) == []

    changed = _location()
    changed["stable_geography"]["north_door"] = "东墙唯一出口"
    errors = mod.validate_scene_geo_contract("SC01", result, shots, {"S001": changed})
    assert any("SCENE_GEO_STALE" in error for error in errors), errors

    shots[1]["spatial_blocking"]["scene_geo_sha256"] = "0" * 64
    errors = mod.validate_scene_geo_contract("SC01", result, shots, {"S001": location})
    assert any("SCENE_GEO_SHOT_MISMATCH" in error for error in errors), errors


def test_geo_lock_does_not_forbid_legitimate_camera_or_character_blocking_changes() -> None:
    mod = _module()
    location = _location()
    lock = mod.build_scene_geo_lock("SC01", location)
    result = {
        "scene_id": "SC01",
        "activation_state": "ACTIVE",
        "space_topology": {"zones": ["中央石台"]},
        "scene_geo_lock": lock,
    }
    first = _shot(lock, shot_id="SH001", camera_side="A")
    second = _shot(lock, shot_id="SH002", camera_side="B")
    second["spatial_blocking"]["start_positions"] = {"A001": "中央石台边缘"}
    second["spatial_blocking"]["end_positions"] = {"A001": "北门"}
    assert mod.validate_scene_geo_contract("SC01", result, [first, second], {"S001": location}) == []


def test_suppressed_or_empty_legacy_spatial_result_is_not_overrestricted() -> None:
    mod = _module()
    for result in (
        {"scene_id": "SC01", "activation_state": "SUPPRESSED"},
        {"scene_id": "SC01", "activation_state": "ACTIVE"},
        {"scene_id": "SC01", "activation_state": "ACTIVE", "space_topology": {}},
    ):
        assert mod.validate_scene_geo_contract("SC01", result, [], {"S001": _location()}) == []


def _wire_real_project(tmp_path: Path, *, with_lock: bool) -> tuple[Path, dict]:
    import json
    import sys
    sys.path.insert(0, str(ROOT / "tests"))
    sys.path.insert(0, str(ROOT / "scripts"))
    from support_pipeline import prepare_scene_chain
    from render_asset_library import render_asset_library
    from render_storyboard import render_storyboard
    from runtime_state import CURRENT_RUNTIME_STATE_VERSION, AUTHORITY_PROFILE

    root = tmp_path / "project"
    for d in ("state", "screenplay", "director", "storyboard", "assets"):
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "state" / "runtime_contract.json").write_text(json.dumps({
        "runtime_state_version": CURRENT_RUNTIME_STATE_VERSION,
        "authority_profile": AUTHORITY_PROFILE,
    }), encoding="utf-8")
    (root / "state" / "pipeline_state.json").write_text(json.dumps({
        "runtime_state_version": CURRENT_RUNTIME_STATE_VERSION,
        "status": "PRODUCTION_IN_PROGRESS",
        "confirmed_brief": False,
        "story_authority_ready": False,
        "asset_library_ready": False,
        "scene_intelligence_ready": False,
        "director_craft_ready": False,
        "completed_units": [],
    }), encoding="utf-8")
    (root / "state" / "project_brief.json").write_text(json.dumps({
        "project_id": "TEST", "work_format": "series", "episode_count": 1,
        "target_episode_runtime_seconds": 10.0, "asset_production_mode": "prompts_only",
    }), encoding="utf-8")
    prepare_scene_chain(root, "EP01", "SC01", per_scene=True, spatial_active=True)

    asset_path = root / "assets" / "ASSET_LIBRARY.json"
    payload = json.loads(asset_path.read_text(encoding="utf-8"))
    payload["ASSET_LIBRARY"]["location_assets"] = [{
        **_location(),
        "image_status": "PROMPT_ONLY",
        "image_file": "",
        "reference_media": [],
        "use_scope": ["EP01-SC01"],
        "dependencies": [],
    }]
    asset_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "assets" / "ASSET_LIBRARY.md").write_text(render_asset_library(payload), encoding="utf-8")

    mod = _module()
    lock = mod.build_scene_geo_lock("SC01", payload["ASSET_LIBRARY"]["location_assets"][0])
    spatial_path = root / "state" / "spatial_narrative" / "EP01_SC01_spatial_narrative.json"
    spatial = json.loads(spatial_path.read_text(encoding="utf-8"))
    result = spatial["SPATIAL_NARRATIVE_RESULT"]
    result["space_topology"] = {"zones": ["中央石台"], "landmarks": ["北门"]}
    if with_lock:
        result["scene_geo_lock"] = lock
    spatial_path.write_text(json.dumps(spatial, ensure_ascii=False, indent=2), encoding="utf-8")

    storyboard_path = root / "storyboard" / "EP01_STORYBOARD.json"
    sb = {
        "edit_shots": [{
            "edit_shot_id": "SH001", "scene_id": "SC01", "edit_shot_duration": 10.0,
            "generation_unit_id": "GU001",
            "source": {"scene_id": "SC01", "story_range": "测试", "director_beat": "B1"},
            "shot_function": {"primary": "推进", "change_after_shot": "完成"}, "shot_type": "MS",
            "base_frame": {"location_time": "室内", "functional_zone": "中央石台", "framing_and_position": "中景"},
            "camera_parameters": {"camera_behavior": "固定", "perspective": "正常", "height": "眼平", "angle": "平视", "depth_focus": "主体清晰", "composition": "居中", "layers": "前中后景", "look_motion_room": "前方留白"},
            "axis_and_gaze": {"axis": "AXIS-1", "camera_side": "A", "gaze": "石台", "screen_direction": "L2R", "cross_axis_allowed": False, "cross_axis_transition": "无"},
            "visual_asset_calls": [],
            "spatial_blocking": {"location_asset": "S001", "dramatic_purpose": "建立空间", "visibility_hearing": "可见可听", "start_positions": "北门", "frame_positions": "中央", "movement_path": "向石台", "end_positions": "石台边缘", "needs_space_diagram": False},
            "continuous_visuals": ["持续动作"],
            "first_last_frame_anchors": {"first_frame": {"position": "北门"}, "last_frame": {"position": "石台边缘"}, "locked_between": "连续"},
            "key_micro_reactions": {"stimulus": "看到石台", "first_reaction": "停顿", "control": "克制", "final_action": "前进"},
            "dialogue_execution": [],
            "sound": {"environment": "室内底噪", "foley": "脚步", "sync_sound": "衣料", "spatial_acoustics": "石厅混响", "music_policy": "无BGM、无配乐、禁止自动情绪音乐"},
            "edit_interface": {"cut_in": "开始", "cut_out": "结束", "action_match": True, "gaze_match": True, "sound_lead": False},
            "continuity_locks": {"wardrobe": "一致", "injury_wet_dirt": "无", "hair_face": "一致", "hand_props": "空", "orientation_screen": "朝右", "physical_position": "石台边缘", "light_time_weather": "室内", "other_state": "无", "known_information": "当前", "forbidden_future": "未来", "world_ability_limits": "现实"},
            "next_shot_handoff": {"type": "动作衔接", "start_state": "石台边缘", "do_not_reset": "位置"},
        }],
        "generation_units": [{
            "generation_unit_id": "GU001", "target_video_model": "SEEDANCE_2_0", "packing_policy": "AUTO",
            "mode": "SINGLE_SHOT", "duration": 10.0, "member_edit_shots": ["SH001"], "contains_explicit_cuts": False,
            "active_media_references": [], "voice_text_assets": [], "starting_state": {"position": "北门"}, "ending_state": {"position": "石台边缘"},
            "phases": [{"phase_id": "PH01", "stage_goal": "完成动作", "image_and_camera": "固定中景", "action_and_physics": "走向石台", "performance_and_microreaction": "停顿后前进", "dialogue_execution": [], "end_state": "石台边缘"}],
            "prompt_sections": {"generation_goal": "建立空间并前进", "reference_roles": ["S001 地下仪式厅：锁定中央石台、北门与稳定空间结构；不锁定当前机位与人物站位"], "initial_state": "北门", "sound": {"environment": "室内底噪", "foley": "脚步", "sync_sound": "衣料", "spatial_acoustics": "石厅混响", "music_policy": "无BGM、无配乐、禁止自动情绪音乐"}, "keep_consistent": "S001稳定空间", "local_constraints": "不提前揭露"},
        }],
    }
    if with_lock:
        sb["edit_shots"][0]["spatial_blocking"]["scene_geo_lock_ref"] = lock["lock_id"]
        sb["edit_shots"][0]["spatial_blocking"]["scene_geo_sha256"] = lock["geo_sha256"]
    storyboard_path.write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "storyboard" / "EP01_STORYBOARD.md").write_text(render_storyboard(sb), encoding="utf-8")
    return root, sb


def test_project_consistency_enforces_geo_lock_for_real_active_spatial_plan(tmp_path: Path) -> None:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_unit_consistency import validate_project_consistency

    root, _ = _wire_real_project(tmp_path, with_lock=False)
    errors = validate_project_consistency(root, "EP01")
    assert any("SCENE_GEO_LOCK_REQUIRED" in error for error in errors), errors


def test_project_consistency_accepts_correct_geo_lock_without_freezing_camera(tmp_path: Path) -> None:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_unit_consistency import validate_project_consistency

    root, _ = _wire_real_project(tmp_path, with_lock=True)
    errors = validate_project_consistency(root, "EP01")
    assert not any("SCENE_GEO_" in error for error in errors), errors


def test_geo_lock_contains_exact_canonical_geometry_snapshot_and_detects_tamper() -> None:
    mod = _module()
    location = _location()
    lock = mod.build_scene_geo_lock("SC01", location)
    assert lock["locked_geometry"] == mod.canonical_location_geo(location)

    result = {
        "scene_id": "SC01",
        "activation_state": "ACTIVE",
        "space_topology": {"zones": ["中央石台"]},
        "scene_geo_lock": lock,
    }
    shot = _shot(lock)
    tampered = dict(lock)
    tampered["locked_geometry"] = dict(lock["locked_geometry"])
    tampered["locked_geometry"]["stable_geography"] = {"north_door": "东墙"}
    result["scene_geo_lock"] = tampered
    errors = mod.validate_scene_geo_contract("SC01", result, [shot], {"S001": location})
    assert any("SCENE_GEO_STALE" in error for error in errors), errors


def test_geo_lock_rejects_attempt_to_freeze_camera_or_character_fields() -> None:
    mod = _module()
    location = _location()
    lock = mod.build_scene_geo_lock("SC01", location)
    lock["locked_fields"].append("camera_side")
    result = {
        "scene_id": "SC01", "activation_state": "ACTIVE",
        "space_topology": {"zones": ["中央石台"]}, "scene_geo_lock": lock,
    }
    errors = mod.validate_scene_geo_contract("SC01", result, [_shot(lock)], {"S001": location})
    assert any("SCENE_GEO_OVERLOCK" in error for error in errors), errors


def test_scene_geo_contract_is_wired_into_spatial_and_shot_authority_docs() -> None:
    spatial_schema = (ROOT / "references/cineweaver/Spatial_Narrative_Engine_V1.0/schema/SPATIAL_NARRATIVE_RESULT.yaml").read_text(encoding="utf-8")
    topology = (ROOT / "references/cineweaver/Spatial_Narrative_Engine_V1.0/runtime/SPACE_TOPOLOGY.md").read_text(encoding="utf-8")
    shot_schema = (ROOT / "references/cineweaver/Shot_Segment_Engine_V1.3/schema/STORYBOARD_SHOT_RESULT.yaml").read_text(encoding="utf-8")
    axis_doc = (ROOT / "references/cineweaver/Shot_Segment_Engine_V1.3/runtime/AXIS_GAZE_SPACE.md").read_text(encoding="utf-8")
    input_contract = (ROOT / "references/cineweaver/Shot_Segment_Engine_V1.3/interfaces/INPUT_CONTRACT.md").read_text(encoding="utf-8")

    for token in ("scene_geo_lock", "geo_sha256", "locked_geometry"):
        assert token in spatial_schema
    for token in ("scene_geo_lock_ref", "scene_geo_sha256"):
        assert token in shot_schema
    assert "不包含人物" in topology or "不得包含人物" in topology
    assert "不锁定机位" in topology or "不得锁定机位" in topology
    assert "scene_geo_lock" in input_contract
    assert "camera_side" in axis_doc and "scene_geo" in axis_doc


def test_spatial_topology_capability_cannot_bypass_geo_lock_by_omitting_topology() -> None:
    mod = _module()
    errors = mod.validate_scene_geo_contract(
        "SC01",
        {"scene_id": "SC01", "activation_state": "ACTIVE", "space_topology": {}},
        [],
        {"S001": _location()},
        require_topology=True,
    )
    assert any("SCENE_GEO_TOPOLOGY_REQUIRED" in error for error in errors), errors


def test_router_enabled_spatial_result_cannot_bypass_geo_validation_with_missing_activation_state(tmp_path: Path) -> None:
    import json
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_unit_consistency import validate_project_consistency

    root, _ = _wire_real_project(tmp_path, with_lock=True)
    spatial_path = root / "state" / "spatial_narrative" / "EP01_SC01_spatial_narrative.json"
    payload = json.loads(spatial_path.read_text(encoding="utf-8"))
    payload["SPATIAL_NARRATIVE_RESULT"].pop("activation_state", None)
    spatial_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    errors = validate_project_consistency(root, "EP01")
    assert any("SPATIAL_ACTIVATION_STATE_INVALID" in error for error in errors), errors


def test_router_enabled_spatial_result_rejects_unknown_activation_state(tmp_path: Path) -> None:
    import json
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_unit_consistency import validate_project_consistency

    root, _ = _wire_real_project(tmp_path, with_lock=True)
    spatial_path = root / "state" / "spatial_narrative" / "EP01_SC01_spatial_narrative.json"
    payload = json.loads(spatial_path.read_text(encoding="utf-8"))
    payload["SPATIAL_NARRATIVE_RESULT"]["activation_state"] = "UNKNOWN"
    spatial_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    errors = validate_project_consistency(root, "EP01")
    assert any("SPATIAL_ACTIVATION_STATE_INVALID" in error for error in errors), errors


def test_spatial_qc_declares_semantic_geo_consistency_check_without_camera_aesthetic_lock() -> None:
    qc = (ROOT / "references/cineweaver/Final_QC_Engine_V1.3/runtime/SPATIAL_QC.md").read_text(encoding="utf-8")
    assert "scene_geo_lock.locked_geometry" in qc
    assert "语义" in qc or "semantic" in qc.lower()
    assert "Hash" in qc or "hash" in qc
    assert "camera" in qc.lower() or "机位" in qc
    assert ("must not" in qc.lower() or "不得" in qc or "不应" in qc) and ("aesthetic" in qc.lower() or "cinematic" in qc.lower() or "审美" in qc)
