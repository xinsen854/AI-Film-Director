# Forge DESIGN｜内部故事与情绪设计模块

**INTERNAL_MODULE_ONLY**：不得作为独立 Skill 入口，不执行 Forge 原独立 Skill 的 first-turn intake gate，也不负责最终两文件交付。项目确认权只属于 AFD `project-intake`，调度权只属于根 `SKILL.md` 的 AFD MASTER ORCHESTRATOR。

## 权威

本模块是故事设计唯一 Owner。进入本阶段时读取：

- `references/forge/source/emotion-story-forge/source_skill.md` 中 **Truth ledger / Prewriting design diagnosis** 的方法；
- `references/forge/source/emotion-narrative-engine/source_skill.md` 的 `DESIGN` 作用；
- 与当前项目直接相关的 Forge references。

禁止再运行 AFD 旧 Story Development 做第二套故事设计。

## 输入

- `PROJECT_BRIEF.md`
- `state/project_brief.json`
- 用户原始材料
- 已有连续性账本（续作时）

## 输出

生成 `state/forge_design.json`，必须保留 Forge 原 DESIGN 事实边界、Emotion Blueprint、production packet 等信息，并额外提供：

```json
{
  "integration": {
    "afd": {
      "creative_bible_story_markdown": "Forge已经完成的故事母版Markdown"
    }
  }
}
```

这里的 `creative_bible_story_markdown` 由 Forge 语义分析阶段直接写出；`compile_forge_handoff.py` 只复制/拼接，不得补写、推断或改写。

完成后必须运行：

```bash
python scripts/compile_forge_handoff.py \
  --project-root <project_root> \
  --stage design \
  --forge-json <project_root>/state/forge_design.json \
  --afd-visual-source <project_root>/state/afd_visual_production.md
```
