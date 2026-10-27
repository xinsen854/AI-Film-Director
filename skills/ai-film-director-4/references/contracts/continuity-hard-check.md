# 连续性硬检查合同

本检查只阻断**明确、可结构化证明的连续性冲突**，不替导演决定机位、视线、动作或剪辑。

检查范围：
- 同一轴线的 camera side 跳边；允许越轴时必须有真实过渡/新空间逻辑；
- `next_shot_handoff.do_not_reset` 明确锁定后，结构化 gaze / character_positions / hand_props / persistent_states 的尾态→首态冲突；
- 同一 SH 同时激活 `conflicts_with` 声明为互斥的持续状态。

防过度限制：
- ST/换场换时后不继承上一场位置、道具或状态；
- 新轴线允许建立新的 camera side；
- 未显式锁定的视线变化不判错；
- 自由文本不做语义猜测式硬比较，只有结构化事实明确矛盾才阻断。
