from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from render_storyboard import render_storyboard, validate_storyboard_payload
from validate_unit_consistency import _validate_storyboard_authority

_spec = importlib.util.spec_from_file_location(
    "item3_helpers_for_v460_refs", ROOT / "tests" / "item3" / "test_final_hard_qc.py"
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
minimal_storyboard = _mod.minimal_storyboard


def _character_record(*, status: str = "PROMPT_ONLY", image_file: str = "") -> dict:
    return {
        "asset_id": "A001",
        "asset_class": "VISUAL_ASSET",
        "name": "许程",
        "visual_identity": {
            "silhouette": "中等身材",
            "hair": "短黑发",
            "base_wardrobe": "深灰夹克",
            "distinguishing_marks": ["眉骨略高"],
        },
        "execution_anchor_summary": {
            "identity": "成熟中国男性",
            "silhouette": "中等身材",
            "wardrobe": "深灰夹克",
            "distinguishing_marks": ["眉骨略高"],
        },
        "image_prompt": "成熟中国男性，短黑发，中等身材，深灰夹克，眉骨略高",
        "image_status": status,
        "image_file": image_file,
    }


def _payload(reference_roles) -> dict:
    payload = minimal_storyboard()
    payload["edit_shots"][0]["visual_asset_calls"] = [{
        "asset_id": "A001",
        "name": "许程",
        "file": "PROMPT_ONLY",
        "role": "人物身份",
        "shot_use": "保持人物身份与当前服装",
    }]
    payload["generation_units"][0]["prompt_sections"]["reference_roles"] = reference_roles
    return payload


def _write(root: Path, payload: dict) -> None:
    (root / "storyboard").mkdir(parents=True, exist_ok=True)
    (root / "storyboard" / "EP01_STORYBOARD.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (root / "storyboard" / "EP01_STORYBOARD.md").write_text(render_storyboard(payload), encoding="utf-8")


def _structured(*, media_ref: str | None = "@图片1", fidelity: str | None = "partial-preserve") -> dict:
    entry = {
        "asset_id": "A001",
        "role": "人物视觉身份",
        "inherits": ["短黑发", "中等身材", "深灰夹克", "眉骨略高"],
        "excludes": ["参考图背景", "原姿态", "原构图"],
    }
    if media_ref is not None:
        entry["media_ref"] = media_ref
    if fidelity is not None:
        entry["fidelity"] = fidelity
    return entry


def test_legacy_reference_role_strings_remain_valid_and_render_unchanged() -> None:
    payload = _payload(["A001｜许程｜文字身份锚：短黑发，中等身材，深灰夹克，眉骨略高。"])
    assert not any("REFERENCE_ROLE_STRUCTURE" in e for e in validate_storyboard_payload(payload))
    rendered = render_storyboard(payload)
    assert "- A001｜许程｜文字身份锚：短黑发，中等身材，深灰夹克，眉骨略高。" in rendered


def test_structured_reference_role_renders_as_natural_language_responsibility() -> None:
    payload = _payload([_structured()])
    errors = validate_storyboard_payload(payload)
    assert not any("REFERENCE_ROLE_" in e for e in errors), errors
    rendered = render_storyboard(payload)
    assert "@图片1" in rendered
    assert "A001" in rendered
    assert "人物视觉身份" in rendered
    assert "短黑发" in rendered and "深灰夹克" in rendered
    assert "参考图背景" in rendered and "原构图" in rendered
    assert "partial-preserve" in rendered
    assert "{'asset_id'" not in rendered


def test_structured_media_reference_requires_role_inherits_and_excludes() -> None:
    for missing in ("role", "inherits", "excludes"):
        entry = _structured()
        entry.pop(missing)
        errors = validate_storyboard_payload(_payload([entry]))
        assert any("REFERENCE_ROLE_STRUCTURE" in e and missing in e for e in errors), (missing, errors)


def test_prompt_only_structured_text_anchor_does_not_require_fake_media_reference(tmp_path: Path) -> None:
    payload = _payload([_structured(media_ref=None, fidelity=None)])
    _write(tmp_path, payload)
    errors: list[str] = []
    _validate_storyboard_authority(tmp_path, "EP01", {"A001": _character_record()}, set(), errors)
    assert not any("FAKE_MEDIA_REFERENCE" in e or "GU_ASSET_IDENTITY_ANCHOR" in e for e in errors), errors


def test_real_active_media_accepts_structured_explicit_media_binding(tmp_path: Path) -> None:
    media = tmp_path / "assets" / "generated" / "A001.png"
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(b"fixture")
    payload = _payload([_structured()])
    payload["generation_units"][0]["active_media_references"] = ["A001"]
    _write(tmp_path, payload)
    errors: list[str] = []
    _validate_storyboard_authority(
        tmp_path, "EP01", {"A001": _character_record(status="GENERATED", image_file="assets/generated/A001.png")}, set(), errors
    )
    assert not any("REFERENCE_BINDING_FAILURE" in e or "GU_ASSET_IDENTITY_ANCHOR" in e for e in errors), errors


def test_prompt_only_structured_binding_cannot_smuggle_fake_media_ref(tmp_path: Path) -> None:
    payload = _payload([_structured(media_ref="@图片9")])
    _write(tmp_path, payload)
    errors: list[str] = []
    _validate_storyboard_authority(tmp_path, "EP01", {"A001": _character_record()}, set(), errors)
    assert any("FAKE_MEDIA_REFERENCE" in e for e in errors), errors


def test_fidelity_enum_is_closed_and_attribute_transfer_requires_named_target() -> None:
    bad = _structured(fidelity="pixel-perfect")
    errors = validate_storyboard_payload(_payload([bad]))
    assert any("REFERENCE_ROLE_FIDELITY" in e for e in errors), errors

    transfer = _structured(fidelity="attribute-transfer")
    errors = validate_storyboard_payload(_payload([transfer]))
    assert any("REFERENCE_ROLE_FIDELITY_TARGET" in e for e in errors), errors

    transfer["fidelity_target"] = "A001 的夹克"
    errors = validate_storyboard_payload(_payload([transfer]))
    assert not any("REFERENCE_ROLE_FIDELITY" in e for e in errors), errors


def test_non_attribute_transfer_rejects_fidelity_target_to_avoid_hidden_semantics() -> None:
    entry = _structured(fidelity="partial-preserve")
    entry["fidelity_target"] = "A002"
    errors = validate_storyboard_payload(_payload([entry]))
    assert any("REFERENCE_ROLE_FIDELITY_TARGET" in e for e in errors), errors


def test_structured_role_rejects_unknown_fields_instead_of_hiding_provider_parameters() -> None:
    entry = _structured()
    entry["duration"] = 30
    errors = validate_storyboard_payload(_payload([entry]))
    assert any("REFERENCE_ROLE_UNKNOWN_FIELD" in e and "duration" in e for e in errors), errors


def test_reference_roles_schema_and_compiler_document_optional_structured_form_without_forcing_migration() -> None:
    schema = (ROOT / "references/cineweaver/Shot_Segment_Engine_V1.3/schema/STORYBOARD_SHOT_RESULT.yaml").read_text(encoding="utf-8")
    compiler = (ROOT / "references/cineweaver/Shot_Segment_Engine_V1.3/runtime/VIDEO_PROMPT_COMPILER.md").read_text(encoding="utf-8")
    for token in ("asset_id", "media_ref", "role", "inherits", "excludes", "fidelity", "fidelity_target"):
        assert token in schema
    assert "旧" in compiler and "兼容" in compiler
    assert "不" in compiler and ("迁移" in compiler or "强制" in compiler)


def test_structured_mode_cannot_be_partially_bypassed_with_legacy_media_role_string() -> None:
    roles = [
        _structured(),
        "@图片2 对应 S001｜场景参考：只负责空间结构；不采用人物。",
    ]
    errors = validate_storyboard_payload(_payload(roles))
    assert any("REFERENCE_ROLE_MIXED_MODE" in e for e in errors), errors


def test_structured_active_media_requires_specific_inherited_visual_facts(tmp_path: Path) -> None:
    media = tmp_path / "assets" / "generated" / "A001.png"
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(b"fixture")
    entry = _structured()
    entry["inherits"] = ["identity"]
    payload = _payload([entry])
    payload["generation_units"][0]["active_media_references"] = ["A001"]
    _write(tmp_path, payload)
    errors: list[str] = []
    _validate_storyboard_authority(
        tmp_path, "EP01", {"A001": _character_record(status="GENERATED", image_file="assets/generated/A001.png")}, set(), errors
    )
    assert any("GU_ASSET_IDENTITY_ANCHOR" in e for e in errors), errors


def test_structured_prompt_only_anchor_with_one_generic_visual_fact_is_not_enough(tmp_path: Path) -> None:
    entry = _structured(media_ref=None, fidelity=None)
    entry["inherits"] = ["短黑发"]
    payload = _payload([entry])
    _write(tmp_path, payload)
    errors: list[str] = []
    _validate_storyboard_authority(tmp_path, "EP01", {"A001": _character_record()}, set(), errors)
    assert any("GU_ASSET_IDENTITY_ANCHOR" in e for e in errors), errors
