from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from hard_delivery_qc import detect_repeated_dramatic_patterns
from render_story_coverage import render_story_coverage_html


def _coverage() -> dict:
    return {
        "project_id": "TEST",
        "summary": {"total": 4, "confirmed": 1, "blocking": 1},
        "items": [
            {"coverage_id": "COV001", "category": "story_atom", "content": "A001收到匿名信", "unit_id": "EP01", "scene_id": "SC01", "status": "UNCOVERED", "evidence": []},
            {"coverage_id": "COV002", "category": "dialogue", "content": "你早就知道？", "unit_id": "EP01", "scene_id": "SC02", "status": "PLANNED", "evidence": ["SH003"]},
            {"coverage_id": "COV003", "category": "reveal", "content": "匿名信来自A003", "unit_id": "EP02", "scene_id": "SC04", "status": "PRODUCED", "evidence": ["GU010"]},
            {"coverage_id": "COV004", "category": "payoff", "content": "旧钥匙打开仓库暗门", "unit_id": "EP03", "scene_id": "SC06", "status": "CONFIRMED", "evidence": ["SH021", "GU021"]},
        ],
        "risks": [{"code": "EARLY_REVEAL", "coverage_id": "COV003", "detail": "不得早于EP02-SC04"}],
    }


def test_story_coverage_html_is_formal_and_shows_four_statuses() -> None:
    html = render_story_coverage_html(_coverage())
    for token in ("Story Coverage Ledger", "未覆盖", "已规划", "已生产", "已确认", "剧情原子", "关键对白", "Reveal", "回收"):
        assert token in html


def test_repeated_dramatic_engine_and_hook_formula_are_blocked() -> None:
    rows = [
        {"unit_id": f"EP0{i}", "dramatic_engine": "主角收到匿名消息并误判亲人", "hook_structure": "未知来信+戛然而止问句", "relationship_change": "", "information_change": "", "power_change": "", "stakes_change": ""}
        for i in range(1, 4)
    ]
    errors = detect_repeated_dramatic_patterns(rows)
    assert any("HARD_REPEATED_PLOT_ENGINE" in item for item in errors)
    assert any("HARD_MECHANICAL_HOOK" in item for item in errors)


def test_intentional_motif_with_real_progression_is_allowed() -> None:
    rows = [
        {"unit_id": "EP01", "dramatic_engine": "门外脚步迫使主角隐藏证据", "hook_structure": "脚步逼近+切黑", "relationship_change": "开始怀疑A002", "information_change": "知道有人跟踪", "power_change": "", "stakes_change": "证据可能暴露"},
        {"unit_id": "EP02", "dramatic_engine": "门外脚步迫使主角隐藏证据", "hook_structure": "脚步逼近+切黑", "relationship_change": "确认A002在保护他", "information_change": "跟踪者改为A003", "power_change": "主角获得反制证据", "stakes_change": "从自保升级为保护家人"},
        {"unit_id": "EP03", "dramatic_engine": "门外脚步迫使主角隐藏证据", "hook_structure": "脚步逼近+切黑", "relationship_change": "与A002结盟", "information_change": "知道幕后主使", "power_change": "转为主动设伏", "stakes_change": "准备公开真相"},
    ]
    assert detect_repeated_dramatic_patterns(rows) == []
