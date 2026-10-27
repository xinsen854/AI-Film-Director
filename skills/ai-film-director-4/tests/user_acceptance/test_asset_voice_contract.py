from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from render_asset_library import render_asset_library, validate_asset_library_payload


def _payload() -> dict:
    return {
        "ASSET_LIBRARY": {
            "contract_version": "4.3",
            "project_asset_policy": {
                "world_and_visual_style": "现实主义21:9悬疑电影",
                "character_face_policy": "同一人物身份稳定",
                "image_prompt_policy": "只用GPT生成视觉资产，最少必要资产数量",
                "voice_asset_policy": "V系列仅文字，不占视觉资产数量",
            },
            "quick_index": [],
            "character_assets": [{
                "asset_id": "A001",
                "name": "周岩",
                "image_prompt": "45岁中国男性，河北县城生活痕迹，短黑发夹灰，深色旧夹克，写实电影人物母板",
                "image_status": "PROMPT_ONLY",
                "image_file": "",
                "reference_media": [],
                "use_scope": ["EP01-EP12"],
                "dependencies": [],
                "voice_asset_id": "V001",
            }],
            "location_assets": [],
            "prop_assets": [{
                "asset_id": "P001",
                "name": "旧面包车",
                "prop_type": "VEHICLE",
                "image_prompt": "1990年代国产旧面包车，灰白漆面，右侧车门有长划痕，写实车辆多视图母板",
                "image_status": "PROMPT_ONLY",
                "image_file": "",
                "reference_media": [],
                "use_scope": ["EP03-SC04", "EP04-SC01"],
                "dependencies": [],
            }],
            "g_assets": [],
            "persistent_states": [{
                "state_id": "A001-ST001",
                "inherits_from": "A001",
                "state_category": "costume_and_injury",
                "visible_change": "左肩包扎渗血，深色夹克左肩破损",
                "image_prompt": "严格继承A001身份，增加左肩包扎渗血和夹克破损，不改变脸、年龄和体型",
                "image_status": "PROMPT_ONLY",
                "image_file": "",
                "reference_media": [],
                "use_scope": ["EP05-SC02至EP06-SC03"],
                "dependencies": ["A001"],
            }],
            "voice_assets": [{
                "asset_id": "V001",
                "name": "周岩稳定声线",
                "asset_class": "TEXT_VOICE_ASSET",
                "media_asset": False,
                "visual_cost_units": 0,
                "seedance_reference_slot_cost": 0,
                "character_asset_id": "A001",
                "image_file": None,
                "audio_file": None,
                "video_file": None,
                "use_scope": ["全项目"],
                "dependencies": ["A001"],
                "voice_profile": {
                    "perceived_age": "45岁",
                    "gender_presentation": "男性",
                    "accent_or_regional_quality": "河北口音，不夸张喜剧化",
                    "register": "中低音域",
                    "timbre": "低沉",
                    "texture": "轻微沙哑",
                    "resonance": "胸腔共鸣明显",
                    "pace": "常态语速偏慢",
                    "rhythm": "句间留白多",
                    "volume_tendency": "低至中低",
                    "emotional_leakage": "压力从换气和句尾失稳泄出",
                    "pressure_behavior": "压怒时不抬音量，语尾收紧",
                    "prohibitions": ["不变成播音腔", "不夸张方言", "不怒吼"],
                },
            }],
        }
    }


def test_complete_asset_and_voice_contract_renders_canonical_fields() -> None:
    payload = _payload()
    assert validate_asset_library_payload(payload) == []
    rendered = render_asset_library(payload)
    for token in ("Canonical Prompt", "Reference", "使用范围", "依赖关系", "稳定声线", "不占视觉资产数量"):
        assert token in rendered


def test_visual_asset_requires_status_reference_scope_and_dependencies() -> None:
    for key in ("image_status", "reference_media", "use_scope", "dependencies"):
        payload = _payload()
        del payload["ASSET_LIBRARY"]["character_assets"][0][key]
        assert any(key in item for item in validate_asset_library_payload(payload))


def test_voice_profile_requires_stable_identity_dimensions() -> None:
    payload = _payload()
    del payload["ASSET_LIBRARY"]["voice_assets"][0]["voice_profile"]["accent_or_regional_quality"]
    assert any("accent_or_regional_quality" in item for item in validate_asset_library_payload(payload))


def test_voice_profile_never_counts_as_media() -> None:
    payload = _payload()
    voice = payload["ASSET_LIBRARY"]["voice_assets"][0]
    voice["visual_cost_units"] = 1
    assert any("VOICE_MEDIA_LEAK" in item for item in validate_asset_library_payload(payload))
