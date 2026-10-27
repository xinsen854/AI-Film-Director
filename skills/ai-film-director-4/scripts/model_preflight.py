#!/usr/bin/env python3
"""Local, deterministic preflight for AFD model surface execution metadata."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

VOICE_ID_RE = re.compile(r"^V\d+$", re.IGNORECASE)
FACS_AU_RE = re.compile(r"(?<![A-Za-z0-9])AU\s*\d{1,3}(?![A-Za-z0-9])", re.IGNORECASE)


def load_profiles(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        raise ValueError("profile registry must contain object field 'profiles'")
    return profiles


def _diag(severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def preflight(
    profile_id: str,
    request: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    profile = profiles.get(profile_id)
    if not isinstance(profile, dict):
        return [_diag("FAIL", "PROFILE_UNKNOWN", f"unknown model surface profile: {profile_id}")]

    if profile_id == 'OTHER_EXPLICIT' and not profile.get('model_id'):
        return [_diag('FAIL', 'PROFILE_FACTS_REQUIRED', 'OTHER_EXPLICIT requires a concrete verified adapter profile before execution')]

    duration = request.get("gu_duration_seconds")
    duration_range = profile.get("duration_seconds")
    if isinstance(duration_range, dict) and duration is not None:
        low = duration_range.get("min")
        high = duration_range.get("max")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool):
            diagnostics.append(_diag("FAIL", "DURATION_TYPE", "gu_duration_seconds must be numeric"))
        elif isinstance(low, (int, float)) and isinstance(high, (int, float)) and not (low <= duration <= high):
            diagnostics.append(
                _diag("FAIL", "DURATION_RANGE", f"duration {duration}s is outside {low}–{high}s for {profile_id}")
            )

    params = request.get("provider_params") or {}
    if not isinstance(params, dict):
        diagnostics.append(_diag("FAIL", "PROVIDER_PARAMS_TYPE", "provider_params must be an object"))
        params = {}

    mode = params.get("mode")
    supported_modes = profile.get("modes")
    if supported_modes is not None and mode is not None and mode not in supported_modes:
        diagnostics.append(_diag("FAIL", "MODE_UNSUPPORTED", f"mode {mode!r} is not supported by {profile_id}"))

    resolution = params.get("resolution")
    resolutions = profile.get("resolutions")
    if resolutions is not None and resolution is not None and resolution not in resolutions:
        diagnostics.append(
            _diag("FAIL", "RESOLUTION_UNSUPPORTED", f"resolution {resolution!r} is not supported by {profile_id}")
        )

    aspect_ratio = params.get("aspect_ratio")
    aspect_ratios = profile.get("aspect_ratios")
    if aspect_ratios is not None and aspect_ratio is not None and aspect_ratio not in aspect_ratios:
        diagnostics.append(
            _diag("FAIL", "ASPECT_RATIO_UNSUPPORTED", f"aspect_ratio {aspect_ratio!r} is not supported by {profile_id}")
        )

    media_roles = request.get("media_roles") or []
    if not isinstance(media_roles, list):
        diagnostics.append(_diag("FAIL", "MEDIA_ROLES_TYPE", "media_roles must be an array"))
        media_roles = []
    supported_roles = set(profile.get("media_roles") or [])
    for role in media_roles:
        if isinstance(role, str) and VOICE_ID_RE.fullmatch(role):
            diagnostics.append(_diag("FAIL", "VOICE_MEDIA_LEAK", f"{role} is a text voice asset, not a media role"))
            continue
        if not isinstance(role, str) or role not in supported_roles:
            diagnostics.append(_diag("FAIL", "MEDIA_ROLE_UNSUPPORTED", f"media role {role!r} is not supported by {profile_id}"))

    prompt_text = request.get("prompt_text")
    model_id = profile.get("model_id")
    if isinstance(prompt_text, str) and FACS_AU_RE.search(prompt_text) and model_id != "seedance_2_0":
        diagnostics.append(
            _diag(
                "WARN",
                "FACS_UNVERIFIED_PROFILE",
                "AU/FACS prompt notation is only evidenced here as a Seedance 2.0 empirical heuristic; use anatomical observable cues or verify the active model profile before relying on AU codes",
            )
        )
    if model_id == "seedance_2_0" and mode == "fast" and resolution in {"1080p", "4k"}:
        diagnostics.append(
            _diag("FAIL", "MODE_RESOLUTION_CONFLICT", "Seedance 2.0 fast forbids 1080p/4k on the locked Higgsfield profile")
        )

    vfx_plate_transform = request.get("vfx_plate_transform")
    if vfx_plate_transform is not None:
        if not isinstance(vfx_plate_transform, dict):
            diagnostics.append(_diag("FAIL", "VFX_CONTEXT_TYPE", "vfx_plate_transform must be an object when provided"))
        elif model_id == "seedance_2_5":
            source_duration = vfx_plate_transform.get("source_duration_seconds")
            gu_duration_valid = isinstance(duration, (int, float)) and not isinstance(duration, bool) and math.isfinite(float(duration))
            source_duration_valid = isinstance(source_duration, (int, float)) and not isinstance(source_duration, bool) and math.isfinite(float(source_duration))
            if not gu_duration_valid:
                diagnostics.append(
                    _diag(
                        "FAIL",
                        "VFX_GU_DURATION_REQUIRED",
                        "Seedance 2.5 Plate Transform requires finite numeric gu_duration_seconds so source-duration matching cannot be skipped",
                    )
                )
            if not source_duration_valid:
                diagnostics.append(_diag("FAIL", "VFX_SOURCE_DURATION_REQUIRED", "Seedance 2.5 Plate Transform requires finite numeric source_duration_seconds"))
            else:
                if source_duration < 4:
                    diagnostics.append(
                        _diag(
                            "FAIL",
                            "VFX_SOURCE_PREP_REQUIRED",
                            "Seedance 2.5 Plate Transform source is below the 4s duration floor; prepare/pad the source before compiling this workflow",
                        )
                    )
                if gu_duration_valid and abs(float(duration) - float(source_duration)) > 1e-6:
                    diagnostics.append(
                        _diag(
                            "FAIL",
                            "VFX_SOURCE_DURATION_MISMATCH",
                            "Seedance 2.5 Plate Transform requires GU duration to match the prepared source duration",
                        )
                    )
            if mode != "omni_reference":
                diagnostics.append(
                    _diag(
                        "FAIL",
                        "VFX_ROUTE_CONFLICT",
                        "Seedance 2.5 Plate Transform uses omni_reference with a source video master; video_edit remains the scoped-edit lane",
                    )
                )
            active_roles = {role for role in media_roles if isinstance(role, str)}
            if "video_references" not in active_roles:
                diagnostics.append(_diag("FAIL", "VFX_VIDEO_MASTER_REQUIRED", "Seedance 2.5 Plate Transform requires video_references as the source master"))
        elif model_id == "seedance_2_0":
            gu_duration_valid = isinstance(duration, (int, float)) and not isinstance(duration, bool) and math.isfinite(float(duration))
            source_duration = vfx_plate_transform.get("source_duration_seconds")
            source_duration_valid = isinstance(source_duration, (int, float)) and not isinstance(source_duration, bool) and math.isfinite(float(source_duration))
            if not gu_duration_valid:
                diagnostics.append(
                    _diag(
                        "FAIL",
                        "VFX_GU_DURATION_REQUIRED",
                        "Seedance 2.0 preservation-VFX requires finite numeric gu_duration_seconds for auditable source-runtime planning",
                    )
                )
            if not source_duration_valid:
                diagnostics.append(
                    _diag(
                        "FAIL",
                        "VFX_SOURCE_DURATION_REQUIRED",
                        "Seedance 2.0 preservation-VFX requires finite numeric source_duration_seconds",
                    )
                )
            if mode != "std":
                diagnostics.append(
                    _diag(
                        "FAIL",
                        "VFX_SD20_ROUTE_CONFLICT",
                        "Seedance 2.0 preservation-VFX uses the documented std lane; do not inherit the Seedance 2.5 omni_reference contract or use fast as if it were equivalent",
                    )
                )
            active_roles = {role for role in media_roles if isinstance(role, str)}
            if "video_references" not in active_roles:
                diagnostics.append(_diag("FAIL", "VFX_VIDEO_MASTER_REQUIRED", "Seedance 2.0 preservation-VFX requires video_references as the source plate master"))
            if resolution is not None and resolution != "4k":
                diagnostics.append(
                    _diag(
                        "WARN",
                        "VFX_SD20_4K_RECOMMENDED",
                        "The public Seedance 2.0 VFX workflow recommends std 4K for preserved face/lip-sync/fine-detail quality; this is a practitioner quality recommendation, not a universal platform hard block",
                    )
                )
            if gu_duration_valid and source_duration_valid and abs(float(duration) - float(source_duration)) > 1e-6:
                diagnostics.append(
                    _diag(
                        "WARN",
                        "VFX_SD20_SOURCE_DURATION_DRIFT",
                        "Seedance 2.0 preservation-VFX defaults to source-matched runtime; a different GU duration can be intentional for payoff room, so verify the deviation instead of treating it as the Seedance 2.5 hard equality contract",
                    )
                )
        else:
            diagnostics.append(
                _diag(
                    "WARN",
                    "VFX_PROFILE_UNVERIFIED",
                    "vfx_plate_transform has no locked workflow evidence for this active model profile; verify the model-specific VFX lane instead of inheriting Seedance 2.0/2.5 rules globally",
                )
            )

    if model_id == "seedance_2_5":
        extension_mode = params.get("extension_mode")
        if mode == "video_extension":
            if extension_mode not in {"forward", "backward"}:
                diagnostics.append(
                    _diag("FAIL", "EXTENSION_MODE_REQUIRED", "video_extension requires extension_mode=forward|backward")
                )
        elif extension_mode is not None:
            diagnostics.append(
                _diag("FAIL", "EXTENSION_MODE_FORBIDDEN", "extension_mode is only valid for video_extension")
            )

        active_roles = {role for role in media_roles if isinstance(role, str)}
        if mode == "t2v" and active_roles:
            diagnostics.append(
                _diag("FAIL", "MODE_MEDIA_CONFLICT", "Seedance 2.5 t2v is the no-material route; use omni_reference when references are supplied")
            )
        if mode in {"video_edit", "video_extension"} and "video_references" not in active_roles:
            diagnostics.append(
                _diag("FAIL", "VIDEO_MASTER_REQUIRED", f"{mode} requires a video reference master")
            )

        ignored: list[str] = []
        if mode == "video_edit":
            ignored.extend(field for field in ("duration", "aspect_ratio") if field in params)
        elif mode == "video_extension" and "aspect_ratio" in params:
            ignored.append("aspect_ratio")
        if ignored:
            diagnostics.append(
                _diag(
                    "FAIL",
                    "MODE_IGNORED_FIELD",
                    f"{mode} must not present inherited/ignored provider fields as settable: " + ", ".join(ignored),
                )
            )

    return diagnostics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--request-json", required=True)
    parser.add_argument(
        "--profiles",
        default=str(Path(__file__).resolve().parents[1] / "references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json"),
    )
    args = parser.parse_args()

    profiles = load_profiles(Path(args.profiles))
    request = json.loads(Path(args.request_json).read_text(encoding="utf-8"))
    diagnostics = preflight(args.profile, request, profiles)
    print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    return 1 if any(item["severity"] == "FAIL" for item in diagnostics) else 0


if __name__ == "__main__":
    raise SystemExit(main())
