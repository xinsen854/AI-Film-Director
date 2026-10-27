from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_exports import DELIVERY_FILES


EXPECTED = [
    "01_项目需求确认单.md",
    "02_剧本审查与修改结论.md",
    "03_正式编剧剧本.md",
    "04_整合导演剧本.md",
    "05_双层情绪规划图.html",
    "06_资产总表与详细生成提示词.md",
    "07_正式分镜与视频模型最终Prompt.md",
    "08_Story_Coverage_Ledger.html",
]


def test_export_contract_contains_exactly_eight_files() -> None:
    assert DELIVERY_FILES == EXPECTED


def test_skill_contract_records_approved_intake_language_aspect_and_defaults() -> None:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for token in (
        "一次性完整提问", "只确认一次", "不得要求用户再次点击", "Seedance 2.0",
        "21:9", "9:16", "单一画幅", "国外项目", "英语对白", "电子UI", "中英双语",
        "电影", "连续剧", "短剧", "动画", "观众情绪", "演员情绪", "空间占位图",
        "上一 GU 的 ending state = 下一 GU 的 starting state",
    ):
        assert token in text


def test_package_manifest_is_current_release_and_matches_eight_deliveries() -> None:
    data = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    assert data["edition"] == "AI-Film-Director-4.7.1-Fusion"
    assert data["delivery_files"] == EXPECTED


def test_declared_engine_versions_match_real_directory_labels() -> None:
    data = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    assert data["cineweaver_engines"][-3:] == [
        "Asset_Engine_V4.1",
        "Shot_Segment_Engine_V1.3",
        "Final_QC_Engine_V1.3",
    ]
    for engine in data["cineweaver_engines"]:
        assert (ROOT / "references" / "cineweaver" / engine / "module.md").is_file()
    assert "asset_engine_source_directory_label" not in data
    assert "shot_segment_engine_source_directory_label" not in data


def test_skill_states_media_execution_boundary_and_story_driven_duration() -> None:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for token in (
        "不直接调用视频生成模型",
        "不直接生成TTS或最终音频",
        "总时长服从用户",
        "SH时长服从剧情",
        "GU时长服从模型上限",
        "30S_BLOCK",
        "最大窗口",
    ):
        assert token in text
