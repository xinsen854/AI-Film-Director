# CineKernel V1.0 — Evidence Ledger
**用途：记录“为什么这条规则存在”。**  
本文件是冻结内核的证据账本，不是美化版理论总结。

---

## Evidence levels
- **A｜Strong production evidence**：原始 Skill + production brief + 真实 Prompt 均能看到。
- **B｜Supported**：至少两个独立来源支持。
- **C｜Conditional**：有效，但只适用于特定失败风险/戏型。
- **D｜Rejected as universal**：可作为技巧，但不能进入通用 Core。

---

| Rule / Capability | Source evidence | Real production evidence | Decision | Level | Notes |
|---|---|---|---|---|---|
| Minimum Necessary Control | CINEDANCE: prompt density + local negatives | Orphanage 后期结构化 Prompt 只强化高风险段 | KEEP | A | 上升为最高哲学 |
| Signal > Volume | LIRA: precision beats verbosity；CINEDANCE: stronger signal, not bloat | 真实 Prompt 中关键约束反复集中于身份/空间/动作 | KEEP | A | 不锁具体字数 |
| Asset ≠ Performance | Hell Grind state assets + ACTING scene adaptation | 视觉 state 独立，情绪由表演 Prompt 处理 | KEEP | A | 严禁 HAPPY/SAD 静态资产化 |
| Current Shot Isolation | CINEDANCE D1 / context isolation | 后期 Prompt 明确 active references / current shot | KEEP | A | Universal |
| Reference Role Binding | Production brief + CINEDANCE reference hierarchy | Scene 36: CHARACTER REF / SCENE REF / PROP REF | KEEP | A | Universal when refs exist |
| Separate Visual State Assets | Hell Grind production brief | roko / wet / blood 等生产方法 | ADAPT | A | 仅持续性视觉状态 |
| Location 3/4 + anchors | Production brief | Orphanage front + reverse views + fixed bed anchors | ADAPT | A | 不强制每个地点固定角度 |
| Reverse view on demand | Production brief + LIRA | Orphanage 使用 complementary room refs | CONDITIONAL | B | 未来 Shot Plan 需要才补 |
| Non-destructive asset lineage | Production brief local edits + LIRA surgical edit | 生产方法明确避免整图多次过模型 | KEEP | A | 核心资产版本原则 |
| Asset stress testing | Production brief | 明确跨姿势、光线、多人测试 | ADAPT | B | 不锁“10次”，按风险 |
| Objective / Obstacle / Stakes | ACTING five pillars | Scene 18 冲突结构清晰对应 | KEEP | B | 多用于戏剧性场景 |
| Tactic / Tactic Shift | ACTING | 文戏结构可映射，但不总显式写出 | CONDITIONAL | B | 内部导演推理优先 |
| Beat Change | ACTING + checklist | Orphanage reaction / eye / pause 按 beat 显性变化 | KEEP | A | 表演引擎核心 |
| Subtext | ACTING | Scene 18 restrained grief / no breakdown | KEEP | A | 条件触发 |
| Listening / Reaction | ACTING | Orphanage eye-line leads reaction, half-beat pause | KEEP | A | 对白/群戏高价值 |
| Eye Life | ACTING | Orphanage later prompts explicitly use eye-first reaction | CONDITIONAL | A | closeup/死眼风险时强化 |
| FACS Action Unit facial precision | higgsfield-facs 1.1.1 | AU vocabulary is standard; Seedance AU-text interpretation is explicitly EMPIRICAL, not an API field | ADAPT | C | Optional close-up precision only; adapter-gated, anatomical fallback; no new Story/Acting Owner |
| Proxemics | ACTING | Scene 18 2m→3m 迭代 | KEEP | A | 关系/权力变化时调用 |
| Physical Business | ACTING | Orphanage 大量使用；Scene 18 并非必需 | CONDITIONAL | A | 不能强制每个人都忙 |
| Body baseline: center of gravity / tempo / openness / breath | ACTING 1.2.0 | 最新 Acting 明确四项身体基线；AFD仅强制评估，不强制四句都进Prompt | ADAPT | B | 受当前身体状态与最小必要表达约束 |
| Silent-listener playable task | ACTING 1.2.0 | 对白/双人戏可减少死脸；任务必须来自已有目标/关系/信息/Beat | ADAPT | B | 禁止为“让人活”发明新动机 |
| Interrupted business as Beat accent | ACTING 1.2.0 | 与现有 interrupted action / physical business 一致 | KEEP | B | 已有business时才有意义，不反向强制business |
| Ensemble scene direction + motive | ACTING 1.2.0 DEMO | 上游明确标注 DEMO / UNPROVEN HERE | TECHNIQUE_ONLY | C | 可选凝聚技术，不进入Story Authority或必填Schema |
| States not transitions | ACTING / LIRA | Jaxx Fall 大量连续动作过程 | ADAPT | A | 改为“状态节点 + 物理因果链” |
| Strong = quiet / weak = shout | ACTING | 非普遍 | REJECT_AS_UNIVERSAL | D | 仅 Technique Library |
| First frame must contain subject | CINEDANCE | Orphanage 后期明确使用 | CONDITIONAL | A | 仅错误开场风险时 |
| Spatial measurable anchors | CINEDANCE | Scene 18 2m/3m；Orphanage 0.3m/床位 | CONDITIONAL | A | 关系/位置风险时 |
| FOV degrees over mm | CINEDANCE V4 | Orphanage 后期有 FOV；早期大量 50/85mm | MODEL_PROFILE | A | 不进入 Core |
| Physical causality | CINEDANCE physics module | Jaxx Fall impact chain | KEEP | A | 动作戏核心 |
| Time blocks | CINEDANCE | Orphanage 后期/复杂动作使用 | CONDITIONAL | B | 复杂镜头才需要 |
| Giant negative blocks | LIRA/CINEDANCE反对 | 真实早期 Prompt 有大量 negatives，后期趋向局部锁 | REJECT_AS_DEFAULT | A | 失败历史明确时才局部使用 |
| 60/30/10 palette | LIRA / Hell Grind style blocks | 真实 Prompt 常见 | TECHNIQUE_ONLY | C | 非 Universal |
| Rule of thirds everywhere | LIRA /旧 Prompt | 真实 Prompt 常见但属风格选择 | REJECT_AS_UNIVERSAL | D | Director Method/Technique |
| 8K IMAX / named DPs | 旧 Hell Grind Prompt | 大量出现 | PROJECT_STYLE_ONLY | D | 不进入 Core |
| Fixed model routing (Soul/NBP/etc.) | LIRA | 当前生产工具链 | MODEL_PROFILE | C | 与模型版本绑定 |

---

# Frozen interpretation
任何未来规则若想进入 CineKernel Frozen Core，至少满足其一：
1. 多项目反复出现并解决同类失败；
2. 被多个独立生产系统验证；
3. 对“资产 / 表演 / 生成工程”的底层边界具有稳定解释力。

仅仅“看起来专业”或“某个模型暂时有效”不足以进入 Core。
