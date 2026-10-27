# Screenplay Authority Projection Adapter

`PROJECTION_ONLY`

## 职责

正式编剧权属于 Human-Truth Screenwriter；锁稿后故事证据权属于 Forge AUDIT。本模块不写、不重写、不润色剧本。

它只消费 `state/forge_locked_audit.json` 中已经由 Forge 生成的 `integration.afd`，通过确定性桥接落盘：

- `screenplay/<unit>_LOCKED_SCREENPLAY.md`
- `SCRIPT_REVIEW.md`
- `state/story_authority.json`
- `state/information_ledger.json`
- `state/forge_alignment.json`

`compile_forge_handoff.py` 发现字段缺失必须 BLOCK，不得根据剧本自行补 Story Atom、Reveal、角色知识或事实。

## 成熟剧本保护

若 `source_maturity=screenplay`，Human-Truth Screenwriter 在上游必须服从用户改写权限。未授权改变的正式动作、逐字对白与顺序仍受保护；投影层不得掩盖非法改写。
