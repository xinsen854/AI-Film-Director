from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_execution_entry_precedes_project_confirmation_and_forbids_advisory_fallback():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    entry = skill.index("## 强制生产入口（最高优先级）")
    confirmation = skill.index("第一次调用与项目确认")
    assert entry < confirmation
    assert "用户说“测试”默认表示用所给材料实际跑一轮" in skill
    assert "不得用能力介绍、流程讲解、教程" in skill
    assert "不阻断当前阶段的缺项不得阻止先执行可完成部分" in skill


def test_401_metadata_and_default_prompt_are_execution_oriented():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    agent = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    package = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))

    assert 'version: "4.7.1-fusion"' in skill
    assert package["edition"] == "AI-Film-Director-4.7.1-Fusion"
    assert "$ai-film-director-4" in agent
    assert "进入生产执行模式" in agent
    assert "不要介绍能力或流程" in agent
