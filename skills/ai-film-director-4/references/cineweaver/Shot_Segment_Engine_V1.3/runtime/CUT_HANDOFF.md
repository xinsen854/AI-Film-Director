# CUT HANDOFF

Allowed handoff codes:
- `CS` State Carry — preserve state into next SHOT.
- `RC` Reaction Cut — next SHOT prioritizes receiver reaction.
- `AR` Action Result Cut — next SHOT begins on consequence/result.
- `CC` Coverage Cut — same dramatic moment, new coverage.
- `AB` Action Bridge — one action continues across separate generation units.
- `ST` Scene/Time Transition — new scene/time state.

The code explains continuity intent; it does not itself dictate a specific lens or edit duration.


## Off-screen carry｜刚离画人物的轻量连续性

当人物在当前 SH 明确离画、且下一 SH 仍在同一场景但该人物不在画面内时，可在现有 `next_shot_handoff.offscreen_carry` 记录：`asset_id + exit_side + last_visible_state`。它只服务下一段连续性与再入画方向，不建立新的 Continuity Owner。

- 只记录角色，不记录场景、道具或分析对象；
- 角色若下一 SH 已重新入画，不再把它标为 off-screen；
- 不因“上一镜有角色、下一镜没有角色”就自动强制填写：cutaway、coverage、场景构图变化都可能合法；
- 公开 Shotlist 方法建议只短期携带刚离画状态，避免离画信息长期污染后续 Prompt。AFD 将其作为短期连续性工具，不把“固定携带几镜”升级为全局硬规则。
