from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from render_asset_library import render_asset_library, validate_asset_library_payload  # noqa: E402
from validate_asset_files import validate_generated_asset_files  # noqa: E402


def _payload() -> dict:
    return {
        "ASSET_LIBRARY": {
            "contract_version": "4.3",
            "project_asset_policy": {
                "world_and_visual_style": "写实电影",
                "character_face_policy": "身份稳定",
                "image_prompt_policy": "最少必要资产",
                "voice_asset_policy": "V系列仅文字",
            },
            "character_assets": [{
                "asset_id": "A001",
                "name": "骑手",
                "image_prompt": "人物身份母板",
                "image_status": "PROMPT_ONLY",
                "image_file": "",
                "reference_media": [],
                "use_scope": ["EP01-SC01"],
                "dependencies": [],
                "downstream_metadata": {"default_reference_role": "identity"},
            }],
            "location_assets": [],
            "prop_assets": [],
            "g_assets": [{
                "asset_id": "G001",
                "name": "巨龙",
                "image_prompt": "巨龙身份母板",
                "image_status": "PROMPT_ONLY",
                "image_file": "",
                "reference_media": [],
                "use_scope": ["EP01-SC01"],
                "dependencies": [],
                "downstream_metadata": {
                    "default_reference_role": "identity",
                    "scale_reference": {
                        "reference_id": "SCALE-A001-G001",
                        "reference_role": "scale",
                        "subject_asset_ids": ["A001", "G001"],
                        "activation_reason": "骑手与巨龙存在极端跨主体比例，宽景中比例漂移会破坏可信度",
                        "relative_scale": "巨龙体长约为骑手身高的12倍，骑手位于颈根肩部低位",
                        "image_prompt": "同一骑手骑乘同一巨龙的比例参考板，只证明骑手与巨龙相对尺寸和骑乘位置",
                        "image_status": "PROMPT_ONLY",
                        "image_file": "",
                        "inherits": ["relative_scale", "mounting_position"],
                        "excludes": ["background", "lighting", "grade", "camera"],
                        "use_scope": ["EP01-SC01"],
                        "dependencies": ["A001", "G001"],
                    },
                },
            }],
            "persistent_states": [],
            "voice_assets": [],
        }
    }


def test_size_ref_is_optional_and_does_not_create_new_asset_family() -> None:
    payload = _payload()
    assert validate_asset_library_payload(payload) == []
    assert "scale_reference_assets" not in payload["ASSET_LIBRARY"]
    payload["ASSET_LIBRARY"]["g_assets"][0]["downstream_metadata"].pop("scale_reference")
    assert validate_asset_library_payload(payload) == []


def test_size_ref_requires_real_existing_subjects_and_owner_participation() -> None:
    payload = _payload()
    scale = payload["ASSET_LIBRARY"]["g_assets"][0]["downstream_metadata"]["scale_reference"]
    scale["subject_asset_ids"] = ["A999", "G001"]
    errors = validate_asset_library_payload(payload)
    assert any("scale_reference" in error and "A999" in error for error in errors), errors

    payload = _payload()
    scale = payload["ASSET_LIBRARY"]["g_assets"][0]["downstream_metadata"]["scale_reference"]
    scale["subject_asset_ids"] = ["A001", "P001"]
    errors = validate_asset_library_payload(payload)
    assert any("owner asset G001" in error for error in errors), errors


def test_size_ref_requires_role_scope_transfer_and_exclusion_but_not_specific_background_words() -> None:
    for key in ("reference_role", "activation_reason", "relative_scale", "image_prompt", "image_status", "inherits", "excludes", "use_scope", "dependencies"):
        payload = _payload()
        del payload["ASSET_LIBRARY"]["g_assets"][0]["downstream_metadata"]["scale_reference"][key]
        errors = validate_asset_library_payload(payload)
        assert any("scale_reference" in error and key in error for error in errors), (key, errors)

    payload = _payload()
    scale = payload["ASSET_LIBRARY"]["g_assets"][0]["downstream_metadata"]["scale_reference"]
    scale["excludes"] = ["unrelated_staging"]
    assert validate_asset_library_payload(payload) == []


def test_size_ref_renders_as_supporting_reference_not_master_asset() -> None:
    rendered = render_asset_library(_payload())
    assert "SCALE-A001-G001" in rendered
    assert "比例参考" in rendered
    assert "scale_reference" not in rendered.split("## 资产快速索引", 1)[1].split("## A / B", 1)[0].lower() or "SCALE-A001-G001" in rendered


def test_generated_size_ref_cannot_bypass_real_file_validation(tmp_path: Path) -> None:
    payload = _payload()
    scale = payload["ASSET_LIBRARY"]["g_assets"][0]["downstream_metadata"]["scale_reference"]
    scale["image_status"] = "GENERATED"
    scale["image_file"] = "assets/generated/G001_SCALE_A001.png"
    scale.update({"file_size": 1, "width": 1, "height": 1, "mime_type": "image/png", "sha256": "0" * 64})

    assets = tmp_path / "assets"
    assets.mkdir(parents=True)
    (assets / "ASSET_LIBRARY.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    errors = validate_generated_asset_files(tmp_path)
    assert any("SCALE-A001-G001" in error and "不存在" in error for error in errors), errors


def test_size_ref_contract_explicitly_avoids_global_mandatory_assetization() -> None:
    text = (ROOT / "references/cineweaver/Asset_Engine_V4.1/runtime/ASSET_TAXONOMY.md").read_text(encoding="utf-8")
    assert "极端" in text
    assert "普通" in text
    assert "不" in text and "强制" in text
    assert "SCALE-" in text


def test_size_ref_cannot_bypass_contract_via_parallel_top_level_family_or_state_metadata() -> None:
    payload = _payload()
    payload["ASSET_LIBRARY"]["scale_reference_assets"] = [
        payload["ASSET_LIBRARY"]["g_assets"][0]["downstream_metadata"]["scale_reference"]
    ]
    errors = validate_asset_library_payload(payload)
    assert any("parallel" in error.lower() or "scale_reference_assets" in error for error in errors), errors

    payload = _payload()
    scale = payload["ASSET_LIBRARY"]["g_assets"][0]["downstream_metadata"].pop("scale_reference")
    payload["ASSET_LIBRARY"]["persistent_states"] = [{
        "state_id": "G001-ST001",
        "inherits_from": "G001",
        "visible_change": "受伤",
        "image_prompt": "受伤状态",
        "image_status": "PROMPT_ONLY",
        "image_file": "",
        "reference_media": [],
        "use_scope": ["EP01-SC01"],
        "dependencies": ["G001"],
        "downstream_metadata": {"scale_reference": scale},
    }]
    errors = validate_asset_library_payload(payload)
    assert any("scale_reference" in error and "master" in error.lower() for error in errors), errors


def test_size_ref_reference_id_must_be_unique() -> None:
    payload = _payload()
    duplicate = dict(payload["ASSET_LIBRARY"]["g_assets"][0])
    duplicate["asset_id"] = "G002"
    duplicate["name"] = "第二巨型实体"
    duplicate["downstream_metadata"] = {
        "default_reference_role": "identity",
        "scale_reference": dict(payload["ASSET_LIBRARY"]["g_assets"][0]["downstream_metadata"]["scale_reference"]),
    }
    duplicate["downstream_metadata"]["scale_reference"]["subject_asset_ids"] = ["A001", "G002"]
    duplicate["downstream_metadata"]["scale_reference"]["dependencies"] = ["A001", "G002"]
    payload["ASSET_LIBRARY"]["g_assets"].append(duplicate)
    errors = validate_asset_library_payload(payload)
    assert any("duplicate" in error.lower() and "SCALE-A001-G001" in error for error in errors), errors
