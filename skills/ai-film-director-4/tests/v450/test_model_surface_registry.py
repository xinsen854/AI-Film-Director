from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_release_metadata_is_450_fusion() -> None:
    manifest = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert manifest["edition"] == "AI-Film-Director-4.7.1-Fusion"
    assert manifest["package_version"] == "4.7.1-fusion"
    assert 'version: "4.7.1-fusion"' in skill
    assert "# AI Film Director 4.7.1 Fusion" in skill


def test_higgsfield_model_surface_registry_contains_locked_seedance_facts() -> None:
    registry_path = ROOT / "references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json"
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    profiles = data["profiles"]

    sd20 = profiles["SEEDANCE_2_0_HIGGSFIELD"]
    assert sd20["model_id"] == "seedance_2_0"
    assert sd20["duration_seconds"] == {"min": 4, "max": 15}
    assert sd20["resolutions"] == ["480p", "720p", "1080p", "4k"]
    assert sd20["modes"] == ["std", "fast"]
    assert set(sd20["media_roles"]) == {
        "start_image",
        "end_image",
        "image_references",
        "video_references",
        "audio_references",
    }
    assert "fast forbids resolution 1080p/4k" in sd20["constraints"]

    sd25 = profiles["SEEDANCE_2_5_HIGGSFIELD"]
    assert sd25["model_id"] == "seedance_2_5"
    assert sd25["duration_seconds"] == {"min": 4, "max": 30}
    assert sd25["resolutions"] == ["480p", "720p"]
    assert sd25["modes"] == ["t2v", "omni_reference", "video_edit", "video_extension"]
    assert set(sd25["media_roles"]) == {
        "image_references",
        "video_references",
        "audio_references",
    }
    assert "start_image" not in sd25["media_roles"]
    assert "end_image" not in sd25["media_roles"]


def test_model_surface_registry_is_source_dated_not_unsourced() -> None:
    data = json.loads(
        (ROOT / "references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json").read_text(encoding="utf-8")
    )
    for profile_id in ("SEEDANCE_2_0_HIGGSFIELD", "SEEDANCE_2_5_HIGGSFIELD"):
        source = data["profiles"][profile_id]["source"]
        assert source["verified_date"] == "2026-08-07"
        assert source["repository"] == "OSideMedia/higgsfield-ai-prompt-skill"
        assert source["commit"] == "c0b73ab946df6658cca513db78bdc3909a655bfd"
        assert source["path"] == "specs/MODEL-SPECS.md"
