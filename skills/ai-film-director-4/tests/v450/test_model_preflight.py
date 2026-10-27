from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from model_preflight import load_profiles, preflight  # type: ignore  # noqa: E402

PROFILES_PATH = ROOT / "references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json"


def codes(diags: list[dict]) -> set[str]:
    return {item["code"] for item in diags if item["severity"] == "FAIL"}


def test_seedance20_valid_std_4k_request_passes() -> None:
    profiles = load_profiles(PROFILES_PATH)
    req = {
        "gu_duration_seconds": 12,
        "provider_params": {"mode": "std", "resolution": "4k", "aspect_ratio": "16:9"},
        "media_roles": ["start_image", "image_references"],
    }
    assert codes(preflight("SEEDANCE_2_0_HIGGSFIELD", req, profiles)) == set()


def test_seedance20_fast_rejects_1080p_and_4k() -> None:
    profiles = load_profiles(PROFILES_PATH)
    for resolution in ("1080p", "4k"):
        req = {
            "gu_duration_seconds": 8,
            "provider_params": {"mode": "fast", "resolution": resolution},
            "media_roles": [],
        }
        assert "MODE_RESOLUTION_CONFLICT" in codes(
            preflight("SEEDANCE_2_0_HIGGSFIELD", req, profiles)
        )


def test_seedance25_rejects_duration_resolution_mode_and_media_role_outside_surface() -> None:
    profiles = load_profiles(PROFILES_PATH)
    req = {
        "gu_duration_seconds": 31,
        "provider_params": {"mode": "not_a_mode", "resolution": "1080p"},
        "media_roles": ["start_image"],
    }
    found = codes(preflight("SEEDANCE_2_5_HIGGSFIELD", req, profiles))
    assert "DURATION_RANGE" in found
    assert "MODE_UNSUPPORTED" in found
    assert "RESOLUTION_UNSUPPORTED" in found
    assert "MEDIA_ROLE_UNSUPPORTED" in found


def test_seedance25_video_extension_requires_extension_mode() -> None:
    profiles = load_profiles(PROFILES_PATH)
    req = {
        "gu_duration_seconds": 8,
        "provider_params": {"mode": "video_extension", "resolution": "720p"},
        "media_roles": ["video_references"],
    }
    assert "EXTENSION_MODE_REQUIRED" in codes(
        preflight("SEEDANCE_2_5_HIGGSFIELD", req, profiles)
    )


def test_seedance25_extension_mode_is_forbidden_outside_video_extension() -> None:
    profiles = load_profiles(PROFILES_PATH)
    req = {
        "gu_duration_seconds": 8,
        "provider_params": {
            "mode": "omni_reference",
            "resolution": "720p",
            "extension_mode": "forward",
        },
        "media_roles": ["image_references"],
    }
    assert "EXTENSION_MODE_FORBIDDEN" in codes(
        preflight("SEEDANCE_2_5_HIGGSFIELD", req, profiles)
    )


def test_seedance25_video_edit_rejects_ignored_provider_fields() -> None:
    profiles = load_profiles(PROFILES_PATH)
    req = {
        "gu_duration_seconds": 10,
        "provider_params": {
            "mode": "video_edit",
            "resolution": "720p",
            "duration": 10,
            "aspect_ratio": "16:9",
        },
        "media_roles": ["video_references"],
    }
    assert "MODE_IGNORED_FIELD" in codes(
        preflight("SEEDANCE_2_5_HIGGSFIELD", req, profiles)
    )


def test_seedance25_valid_omni_reference_passes() -> None:
    profiles = load_profiles(PROFILES_PATH)
    req = {
        "gu_duration_seconds": 30,
        "provider_params": {
            "mode": "omni_reference",
            "resolution": "720p",
            "aspect_ratio": "21:9",
        },
        "media_roles": ["image_references", "video_references", "audio_references"],
    }
    assert codes(preflight("SEEDANCE_2_5_HIGGSFIELD", req, profiles)) == set()


def test_v_series_is_never_a_media_role() -> None:
    profiles = load_profiles(PROFILES_PATH)
    req = {
        "gu_duration_seconds": 8,
        "provider_params": {"mode": "omni_reference", "resolution": "720p"},
        "media_roles": ["V001"],
    }
    assert "VOICE_MEDIA_LEAK" in codes(
        preflight("SEEDANCE_2_5_HIGGSFIELD", req, profiles)
    )


def test_cli_exits_one_on_fail(tmp_path: Path) -> None:
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "gu_duration_seconds": 40,
                "provider_params": {"mode": "t2v", "resolution": "720p"},
                "media_roles": [],
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "model_preflight.py"),
            "--profile",
            "SEEDANCE_2_5_HIGGSFIELD",
            "--request-json",
            str(request),
            "--profiles",
            str(PROFILES_PATH),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1
    assert "DURATION_RANGE" in result.stdout


def test_other_explicit_profile_blocks_without_verified_adapter_facts() -> None:
    profiles = load_profiles(PROFILES_PATH)
    req = {"gu_duration_seconds": 8, "provider_params": {}, "media_roles": []}
    assert "PROFILE_FACTS_REQUIRED" in codes(preflight("OTHER_EXPLICIT", req, profiles))


def test_seedance25_t2v_rejects_reference_media_roles() -> None:
    profiles = load_profiles(PROFILES_PATH)
    req = {
        "gu_duration_seconds": 8,
        "provider_params": {"mode": "t2v", "resolution": "720p"},
        "media_roles": ["image_references"],
    }
    assert "MODE_MEDIA_CONFLICT" in codes(preflight("SEEDANCE_2_5_HIGGSFIELD", req, profiles))


def test_seedance25_edit_and_extension_require_video_reference_master() -> None:
    profiles = load_profiles(PROFILES_PATH)
    edit_req = {
        "gu_duration_seconds": 8,
        "provider_params": {"mode": "video_edit", "resolution": "720p"},
        "media_roles": ["image_references"],
    }
    extension_req = {
        "gu_duration_seconds": 8,
        "provider_params": {
            "mode": "video_extension",
            "resolution": "720p",
            "extension_mode": "forward",
        },
        "media_roles": ["image_references"],
    }
    assert "VIDEO_MASTER_REQUIRED" in codes(preflight("SEEDANCE_2_5_HIGGSFIELD", edit_req, profiles))
    assert "VIDEO_MASTER_REQUIRED" in codes(preflight("SEEDANCE_2_5_HIGGSFIELD", extension_req, profiles))


def test_seedance25_extension_rejects_explicit_aspect_ratio_because_source_is_inherited() -> None:
    profiles = load_profiles(PROFILES_PATH)
    req = {
        "gu_duration_seconds": 8,
        "provider_params": {
            "mode": "video_extension",
            "resolution": "720p",
            "extension_mode": "backward",
            "aspect_ratio": "16:9",
        },
        "media_roles": ["video_references"],
    }
    assert "MODE_IGNORED_FIELD" in codes(preflight("SEEDANCE_2_5_HIGGSFIELD", req, profiles))
