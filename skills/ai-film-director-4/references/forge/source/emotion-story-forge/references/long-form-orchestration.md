# 长篇调度协议

## 1. 先判断交付单位

“字数”不是单独的交付规格。先确认它是：

- 影视剧本字数（场景、动作、对白）；
- 小说/网文正文字符数；
- 规划文档字符数；
- 多季电视剧或多卷系列的总量。

没有明确时，按“中文长篇叙事总字符数”理解，并声明这是估算，不把字数伪装成镜头时长。

## 2. 四级约束树

| 层级 | 作用 | 必填字段 | 何时冻结 |
|---|---|---|---|
| 项目圣经 | 统一世界、主题、人物、语言、事实边界 | premise、human question、format、audience、canon、VERIFY | 开始写章前 |
| 卷纲 | 控制一卷/一季的主要压力和不可逆变化 | volume promise、主冲突、关系债、7–12 个大转折、卷尾余波 | 开始写该卷前 |
| 章纲 | 控制章节功能、进入状态、选择、代价、退出钩子 | chapter purpose、POV、knowledge state、pressure、choice、cost、next hook | 开始写该章前 |
| 场景/段落包 | 把因果写成可读/可拍文本 | scene goal、阻力、行为、对白、后果、continuity delta | 每次交付后 |

“卷纲”不是章节标题堆叠；“章纲”不是剧情摘要堆叠。每一层都必须写清楚选择怎样改变下一层的条件。

## 2.1 S级项目的前置架构包

当项目路由为 `S-CANDIDATE` 时，在进入场景/段落包之前增加一层架构门：

- `story_necessity`：why now、why this protagonist、no rational exit、inaction cost、form necessity；
- `series_engine`、`relationship_engine`、`world_pressure_engine` 与 `opposition_engine`；
- 每名核心人物的重大 `decision_chains` 及反事实结果；
- 至少三个经五项测试的 `ending_tournament` 候选；
- `episode_distinction_matrix` 与 `peak_aftermath_ledger`；
- `future_capacity`：结尾后哪些新冲突仍可在不重置的前提下继续。

使用 `emotion-story-forge/scripts/validate_s_candidate.py` 检查结构。校验通过只表示字段和候选存在，不表示故事已经达到 S 级；仍需证据型 G0-G4 审查。

## 3. 字数档位与默认批次

### 30 万字

建议拆成 3–5 卷，每卷 6–12 万字；每卷 25–60 章，按类型调整。首轮只锁项目圣经 + 总卷纲 + 第一卷章纲；随后每次交付 1–3 章或约 8,000–20,000 字正文。每完成 3–5 章做一次局部审计，每卷正文锁定后做卷级精细审计并刷新 HTML；不根据未写完的卷纲生成最终 HTML。

### 50 万字

建议拆成 5–8 卷，每卷 6–10 万字；每卷必须有独立情绪承诺、关系债增量、卷尾不可逆变化。首轮锁项目圣经 + master卷纲 + 第一卷章纲；正文默认 1–2 章/批次，约 8,000–18,000 字。跨卷只带当前生产包、相关角色状态、关系债、观众/读者知识与开放回路，不把全书重新塞回上下文。HTML 只在已锁定卷级审计后刷新。

### 140 万字

建议拆成 10–16 卷、每卷 8–15 万字；每卷再分 3–5 个篇章段，每段有自己的压力曲线和余波。首轮只交“系列 bible + master卷纲 + 第一卷卷纲 + 第一篇章章纲 + 试写样章”；用户确认后逐卷推进。正文默认 1 章或一个场景包/批次，约 5,000–15,000 字。项目级 HTML 来自已锁定项目里程碑审计，卷级 HTML 来自已锁定当前卷审计，不为每个小段重复生成完整报告。

## 4. 调用矩阵

| 请求 | 情绪引擎 | 编剧 skill | HTML |
|---|---|---|---|
| 要总规划 | DESIGN 项目/卷级 | 不调用 | 不生成最终 HTML |
| 要卷纲 | DESIGN 卷级 | 不调用 | 不生成最终 HTML |
| 要章纲 | DESIGN 章级轻诊断 | 不调用 | 不生成最终 HTML |
| 要正文 | 使用生产包；锁定后 AUDIT | 调用 | 仅锁定里程碑刷新 |
| 要续写 | 检查上次 state delta | 调用 | 不重复生成，除非形成锁定里程碑 |
| 要审计 | AUDIT 指定已写范围 | 不调用 | 锁定范围可生成审计图谱 |
| 要改写 | DESIGN/AUDIT 受影响范围 | 调用 | 重新锁定后只更新受影响节点 |

“不调用”是硬规则：不需要写正文时，不调用编剧；只要 HTML 刷新，不重新发明诊断；只做章节标签，不启动任何创作 skill。

## 4.1 S级与系列的原子生产循环

`S-CANDIDATE` 或 `SERIES` 项目按以下最小循环推进：

`读取上一 checkpoint → 生成当前 production packet → 写一个 episode/scene packet → 运行因果/人物/对白/自然度检查 → 运行跨集变化扫描 → 形成 state delta → 写入新 checkpoint`

一个 checkpoint 至少记录：不可逆变化、仍在负载的关系/知识/资源/制度/选择压力、下一单元接口、设计/正文差集、新事实边界和证据引用。用户明确授权 `auto-accept` 时可以自动进入下一单元，但不能跳过 checkpoint 或审计。

## 5. 每批次状态包

每次长篇交付后保存一个 continuation ledger，至少包含：

~~~yaml
project_id: 项目名
scope: volume-01/chapter-003/scene-02
source_blueprint_version: EB-01.03
source_script_version: DRAFT-01.03
lock_status: DRAFT|LOCKED
locked_changes: []
new_facts: []
knowledge_state: {}
character_state: {}
relationship_debt: []
open_loops: []
closed_loops: []
verify_items: []
last_irreversible_change: “...”
next_unit: “...”
pending_user_decisions: []
~~~

对于 \`S-CANDIDATE\`，建议额外记录：

~~~yaml
quality_route: S-CANDIDATE
story_necessity_verdict: pass|revise|block
opposition_engine_status: LOCKED|PROPOSED|UNKNOWN
decision_chain_ids: []
ending_candidate_ids: []
episode_distinction_status: pass|revise|unknown
peak_aftermath_ids: []
blueprint_evidence_diff_status: pending|complete
~~~

如果没有这个状态包，不允许直接从“上一批”续写，因为续写会依赖不可见记忆。正文扫描出的新事实先进入候选状态；只有用户批准或已明确授权自动接受时，才进入 LOCKED canon。

## 6. 长篇情绪控制

长篇不是把同一条情绪曲线拉长。每卷要有主情绪问题，每章要有局部压力与选择，每个场景要留下关系或知识状态的变化。卷与卷之间允许换主情绪，但必须保留可追踪的关系债、主题问题或代价回声。任何“高潮”若没有改变后续条件，只是声量，不算有效转折。

S级额外检查：若删掉某个核心人物的选择，故事仍在大致同一时间以相近代价发生，则该转折的因果所有权不足；若相邻单元重复却没有知识、杠杆、代价、策略、关系或母题意义增量，标记 `REPETITION_RISK` 并回到最小负责层。

## 7. 用户可选调度命令

用户可以用以下短命令改变调度，不必重新解释项目：

- 只做项目圣经
- 只做总卷纲
- 只做第N卷卷纲
- 只做第N章章纲
- 写第N卷第M章
- 续写上一批
- 只审计连续性
- 只刷新情绪图谱
- 按当前蓝图改写这一章

命令未指定范围时，选择最小可交付范围并先复述 scope。
## 8. 长篇全剧情情绪总谱刷新规则

`global_emotional_arc` 只从已锁定里程碑审计刷新，不从尚未写出的卷纲/集纲伪造完成态。

- 连续长篇：新锁定范围可以追加/修正阶段节点，但不得重算未受影响的旧阶段。
- 多季/多卷：项目总谱引用季/卷级阶段摘要；局部粒子场仍读取当前锁定阶段的细关键帧。
- 非线性作品：保留 story time 与 audience time 两套顺序。
- 单元重置作品：总谱总结单元间反复出现的人性/情绪机制，不生成虚假的连续人物成长线。
- 超长项目允许 HTML 默认只展开当前里程碑，同时保留项目级总谱摘要，避免把每一集机械画成一个节点。



## 9. v1.1 Semantic Zoom

当锁定范围产生超过约 12 个 `phase_events` 时，AUDIT 应判断是否存在有证据支持的 `phase_clusters[]`。阶段簇只用于阅读缩放：

`作品总览 → 阶段簇 → phase_event → drivers/keyframes`

阶段簇的数量、跨度和名称均由当前作品状态变化聚合，不能复用固定三幕、四幕、季中点或固定集数。若证据不足以形成语义簇，HTML 只能按 12 个阶段左右生成技术窗口分页，并明确“技术窗口不代表剧情结构”。
