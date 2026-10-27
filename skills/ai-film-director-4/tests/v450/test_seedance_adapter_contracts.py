from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "references/cineweaver/Shot_Segment_Engine_V1.3"


def test_generation_profiles_point_to_source_dated_surface_profiles() -> None:
    data = yaml.safe_load((ENGINE / "registry/GENERATION_PROFILES.yaml").read_text(encoding="utf-8"))
    sd20 = data["model_profiles"]["SEEDANCE_2_0"]
    sd25 = data["model_profiles"]["SEEDANCE_2_5"]
    assert sd20["surface_profile"] == "SEEDANCE_2_0_HIGGSFIELD"
    assert sd25["surface_profile"] == "SEEDANCE_2_5_HIGGSFIELD"
    assert sd20["dialect_contract"].endswith("SEEDANCE_2_0_PROFILE.md")
    assert sd25["dialect_contract"].endswith("SEEDANCE_2_5_PROFILE.md")


def test_seedance_20_profile_is_scoped_and_not_global() -> None:
    text = (ENGINE / "runtime/SEEDANCE_2_0_PROFILE.md").read_text(encoding="utf-8")
    assert "4–15" in text
    assert "480p" in text and "4k" in text.lower()
    assert "std" in text and "fast" in text
    assert "start_image" in text and "end_image" in text
    assert "fast" in text and "1080p" in text and "4k" in text.lower()
    assert "不得提升为 AFD 全局" in text or "不得成为 AFD 全局" in text


def test_seedance_25_profile_has_four_mode_router_and_mode_semantics() -> None:
    text = (ENGINE / "runtime/SEEDANCE_2_5_PROFILE.md").read_text(encoding="utf-8")
    for mode in ("t2v", "omni_reference", "video_edit", "video_extension"):
        assert mode in text
    assert "video_edit" in text and "duration" in text and "aspect_ratio" in text
    assert "video_extension" in text and "extension_mode" in text
    assert "forward" in text and "backward" in text
    assert "start_image" in text and "不支持" in text
    assert "end_image" in text and "不支持" in text
    assert "角色" in text or "职责" in text
    assert "排除" in text or "不继承" in text


def test_model_adapter_links_profiles_without_claiming_model_name_implies_multishot() -> None:
    text = (ENGINE / "runtime/MODEL_ADAPTER.md").read_text(encoding="utf-8")
    assert "SEEDANCE_2_0_PROFILE.md" in text
    assert "SEEDANCE_2_5_PROFILE.md" in text
    assert "must be explicitly confirmed" in text.lower() or "必须明确确认" in text
    assert "model surface profile" in text.lower() or "模型表面配置" in text


def test_video_prompt_compiler_routes_25_modes_before_prompt_compilation() -> None:
    text = (ENGINE / "runtime/VIDEO_PROMPT_COMPILER.md").read_text(encoding="utf-8")
    assert "Seedance 2.5" in text
    assert "先选 mode" in text or "先确定 mode" in text or "mode router" in text.lower()
    assert "omni_reference" in text
    assert "video_edit" in text
    assert "video_extension" in text
