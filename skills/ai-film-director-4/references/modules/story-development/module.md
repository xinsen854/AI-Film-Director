# Story Development Adapter

`ADAPTER_ONLY`

## 职责

本模块不再执行第二套故事开发。故事设计唯一权威是 `references/forge/design.md` 的 Forge DESIGN。

本 Adapter 只负责确认：

1. `state/forge_design.json` 已存在且当前阶段为 DESIGN；
2. `state/afd_visual_production.md` 只包含 AFD 视觉/生产规范；
3. 通过 `scripts/compile_forge_handoff.py --stage design` 生成/更新 `PROJECT_CREATIVE_BIBLE.md`；
4. 不把 AFD 视觉设计反向升级成剧情事实。

禁止：自行新增世界观、人物动机、结构、伏笔、反转或第二份 Story Bible。
