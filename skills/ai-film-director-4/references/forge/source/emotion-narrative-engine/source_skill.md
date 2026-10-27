---
name: emotion-narrative-engine
description: Use when a user supplies a story outline or screenplay and asks for emotional diagnosis, emotional-causality analysis, relationship-field analysis, audience-response analysis, breakpoint identification, canon-safe repair directions, or an optional standalone HTML diagnosis report. Also provides the scoped prewriting DESIGN pass and locked-script AUDIT pass used by emotion-story-forge, including adaptive phase events, dual story/audience time, and global emotional-arc data for visualization.
---
> **ARCHIVAL_SOURCE_ONLY / 非执行入口**
> 本文件只保存上游 Forge 原始方法与历史契约，供融合模块按需引用。
> 在 AI Film Director Master 融合环境中，禁止执行本文件自己的 first-turn intake、独立 Skill 路由、独立交付数量、跨 Skill 调用或相对路径命令。
> 唯一可执行融合合同是 `references/forge/design.md`、`human-truth-screenwriter.md`、`gate.md`、`audit.md`、`emotion-renderer.md` 与根 `SKILL.md`。


# 情绪叙事引擎

## 核心原则

从用户提供的新故事出发，交付有证据的情绪叙事诊断和有边界的修复方向。把情绪理解为压力、解释、防御、选择、关系变化、回返后果与观众重估之间的因果，而不是强度曲线或煽情事件的堆叠。

用户直接扔进大纲或剧本、要的是更好的剧本正文（升级、改写、续写、下一集）时，本技能不是用户入口：改用 `human-truth-screenwriter`；需要完整捆绑交付时使用 `emotion-story-forge`。只有当用户要的是带证据分级的独立诊断、且不要正文时，才单独留在本技能。

仅运行 V0.2 诊断方法。把有边界的修复或验证方向视为诊断的固定组成；“只诊断”“不要改写”排除的是替代正文、场景和对白，不排除该方向。本技能始终不改写、续写、分镜、导演或生成资产。独立调用时不接管其他制作流程；由 `emotion-story-forge` 调用时，只接收明确 scope 并返回结构化诊断，不越权执行写作。独立 HTML 仍只在用户明确要求时生成。

## 两种流水线作用

- **DESIGN：** 输入大纲、treatment 或未锁定规划，按材料精度建立事实边界、情绪因果、人物与关系债、观众知识和断点，输出设计蓝图与诊断结论库。它回答“正文需要怎样成立”，不下 SCRIPT_FINE 结论，也不在完整流水线中生成最终情绪图谱。
- **AUDIT：** 输入已锁定剧本或已接受的当前单元，按 SCRIPT_FINE 或 MIXED 精度核查正文实际写出的压力、解释、防御、选择、条件变化、关系传导、后果与观众重估，并与设计蓝图对照。它回答“正文实际上是否成立”，输出供最终 HTML 和状态账本使用的审计数据。

两种作用使用同一证据纪律，不是两套理论。DESIGN 中的意图不能在 AUDIT 中自动算作已兑现；只有可定位的剧本行为、对白、场景条件和后果可以升级为正文证据。

## 先读取契约

在分析前读取以下一级引用；把它们作为同一套数据契约使用：

- [input-and-fact-boundary.md](references/input-and-fact-boundary.md)：输入精度、事实边界与证据标注。
- [core-emotion-model.md](references/core-emotion-model.md)：叙事单元与情绪因果链。
- [character-relationship-ledger.md](references/character-relationship-ledger.md)：人物账本与双向关系债。
- [emotion-relationship-field.md](references/emotion-relationship-field.md)：多人物情绪关系场。
- [adaptive-emotion-state-model.md](references/adaptive-emotion-state-model.md)：状态变化驱动的阶段聚合、双时间轴、混色情绪质点与全剧情总谱。
- [audience-ledger.md](references/audience-ledger.md)：观众信息与情绪路径。
- [breakpoint-taxonomy.md](references/breakpoint-taxonomy.md)：盲诊断与断点分类。
- [repair-contract.md](references/repair-contract.md)：最小修复方向与设定影响。
- [diagnostic-report-contract.md](references/diagnostic-report-contract.md)：最终报告结构与主张标准。
- [creative-freedom-protocol.md](references/creative-freedom-protocol.md)：创作自由、类型校准与禁止发明边界。

以上是盲诊断所需的核心契约。完成工作流第 8 步并记录候选断点之前，不读取下面的案例或类型资料。

## 盲诊断后的选择性路由

- 扩充语料、引用研究或说明案例证据时，先读 [research-corpus-protocol.md](references/research-corpus-protocol.md)，保持剧本、公映成片、页到银幕、主创陈述、观众/接受证据与分析者解释分层。研究资料是结构化存储，不是模型权重训练。
- 需要正向对照时，按已证明的戏剧问题读取 [positive-case-index.md](references/positive-case-index.md)，绝不按片名或表面类型模仿。只有索引条件与当前诊断问题实质匹配时，才读取一个最相关的 `DEEP` 案例；跨案例问题才读取综合文件。
- 使用弱效应/负向对照时，先读取 [negative-case-protocol.md](references/negative-case-protocol.md)，再按已证明的机制问题查询 [negative-case-index.md](references/negative-case-index.md)，最后才读取条件匹配的 `CARD`。只在机制层面描述弱效应，不把个人不喜欢写成接受证据或整部作品判决。
- 只有格式或类型承诺会实质改变诊断镜头、受众效应或修复风险时才读取类型适配器：[家庭/亲密](references/genre-family.md)、[悬疑/恐怖](references/genre-suspense.md)、[喜剧](references/genre-comedy.md)、[复仇/权力](references/genre-revenge-power.md)、[短篇/品牌](references/genre-shortform-brand.md)。默认选择一个主适配器；若不同的已证实断点或真实交付约束需要不可互相替代的镜头，则读取满足诊断所需的最小相关集合。不要预设数字上限，也不要因“混合类型”本身堆叠适配器。
- 对多集短剧或系列批次，读取 [genre-shortform-brand.md](references/genre-shortform-brand.md) 的条件式 Hook、微结构、连续性和平台差异检查；不要把固定秒数、反转数、金句数或峰值数当作全局硬门。
- 所有研究文件都只为本技能提供可选证据。本技能不调用、不要求或依赖其他编剧或制作技能。
- 用户明确要求 HTML、网页报告或可视化诊断时，读取 [html-report-contract.md](references/html-report-contract.md)，并使用内置离线模板与渲染器；未请求时不要自动生成文件。

## 执行工作流

按以下分析顺序推进；不要把这个顺序投射成故事结构。

1. **声明输入精度。** 将整体或各单元标为 `OUTLINE_COARSE`、`SCRIPT_FINE` 或 `MIXED`。只在材料支持的分辨率上判断；粗粒度材料不下表演、对白质量、微观节奏或镜头层面的结论。对 `OUTLINE_COARSE`，先区分“用户未提供”与“完整材料明确不存在”；前者默认 `UNKNOWN`，不得直接升级为正式断点。
2. **建立事实边界。** 将每项材料区分为 `LOCKED`、`SUPPORTED`、`INFERRED` 或 `UNKNOWN`。仅锁定用户事实、权利/安全/事实边界、已建立连续性与真实交付约束。V0.2 不设发明层。若发现并纠正人物身份、性别、亲属或其他实体属性，立即建立统一称谓表，供最终全文复扫。
3. **检查故事必要性。** 仅在 forge 路由为 `S-CANDIDATE` 或用户明确要求 S级诊断时，核查 why now、why this protagonist、退出代价、不行动代价和形式必要性。证据不足写 `UNKNOWN/PENDING_G0`，不为通过门槛擅加灾难、反派或创伤。
4. **划分叙事单元。** 依作品自身粒度记录位置、可观察事件、焦点人物、进入压力、选择或回避、改变条件与携带后果；不要追求固定单元数。
5. **建立人物与关系账本。** 分别记录每名重要人物的欲望、保护价值、未言明需要、防御、短期真实收益、选择、代价与余波。对关系双方分别记债，不把关系压成单边标签。
6. **核查重大决策链。** 对结构转折和高潮记录压力、可行选项、选择、立即代价、状态变化、未来债与反事实结果。若人物不选择，剧情仍会原样推进，则把因果所有权问题列为正式断点或待验证项。
7. **绘制情绪关系场。** 围绕同一重要事件并列映射所有受影响人物和观众，区分事件结果、各自解释、内在可能、可观察行为、对他人影响、关系位移与后续后果。
8. **读出情绪面。** 对最重的二到三个事件，把关系场读成一个受力面：定位承压点，沿材料已建立的关系债追踪力传导到谁，比较各主体位移在种类上的差异，记录谁在场却未位移以及后续是否向其收取代价。传导路径没有材料依据时写 `UNKNOWN`，不要用因果套语补全，也不要把并列反应当作传导。
9. **建立观众账本。** 记录观众已知、未知、误读、期待、恐惧、关心理由，以及新信息如何改变意义、进入、脱离、释放与余留。材料支持时区分锚点分别记录，并记录锚点之间如何相互牵动；只有单一锚点时写 `anchor: SINGLE`，不虚构对立立场。
10. **追踪情绪因果链。** 使用“压力 → 解释 → 防御 → 选择/回避 → 条件改变 → 关系/自我位移 → 回返后果 → 观众重估”，允许证据支持的隐含环节和跨单元延伸。
11. **先做盲断点诊断。** 在查阅任何案例前形成候选断点、证据、受众效应、反向解读、置信度与严重度。只有材料直接呈现了问题，或用户确认输入是完整可评估版本且相关功能确实不存在，才将“缺少某功能”列为正式断点。否则列为 `PENDING_*` 待验证项，写明升级条件，不赋予确定严重度。把分类当作观察镜头，不当作配额。
12. **条件式查阅案例。** 仅当盲诊断已完成并出现需要对照的证据化问题时，才按上述路由读取最少资料：先协议，再按戏剧问题查索引，最后才读取条件匹配的具体案例。只借用机制，不套用情节、台词、人物配置或标志性意象。
13. **校准反向解读与类型。** 为每个高严重度主张写出至少一个可信反向解读，并将受众效应表述为与证据匹配的可能性。仅当格式/类型实质改变诊断镜头时读取适配器；默认一个主适配器，不可替代的已证实断点或真实交付约束才扩展为最小相关集合，没有实质变化就跳过。
14. **给出修复或验证方向。** 始终保留这一节。证据支持改变时，只提供彼此实质不同且有证据需求的最小方向；可调整行为、关系后果或观众信息。证据不支持改变时，明确写“不建议改变”，再给出保持、观察或验证方向，不制造缺陷。逐项写清改变项或保持项、条件、风险、设定影响与预期观众变化；任何对用户提供事实的改变都标为 `REQUIRES_APPROVAL`。
15. **按契约交付并硬检。** 使用诊断报告契约的顺序，随后逐条执行其最终 QC。材料不足时输出限制和 `UNKNOWN`，不要以想象补齐。若本轮纠正过人物或实体属性，全文复扫标题、表格、关系称谓、代词和总结，消除与统一称谓表冲突的残留表达。
16. **按作用交接 HTML 数据。** 独立调用且用户明确要求可视化时，从本次结构化诊断生成离线诊断 HTML；它必须标明当前材料精度。由 `emotion-story-forge` 以 DESIGN scope 调用时不生成最终 HTML；以 AUDIT scope 调用时，除原有锁定剧本审计数据外必须返回 `narrative_topology`、`audience_lenses`、`phase_events`、`phase_links` 与 `global_emotional_arc`，由总控渲染最终情绪图谱。阶段和总谱只能从锁定正文证据聚合；HTML 不得增加正文没有的事实、断点、评分、修复方向、情绪转换或确定性。

## 自适应阶段与全剧情总谱硬规则

AUDIT 在完成细粒度 `rhythm_causality`、人物账本、关系场和观众账本之后，必须再执行一次**语义聚合**：把多个细事件收束为由状态变化驱动的 `phase_events`，生成开放拓扑 `phase_links`，按当前作品真实观看立场生成 `audience_lenses`，并生成 `global_emotional_arc` 的收束摘要。`global_emotional_arc` 只提供 throughline / major turn / ending residue 等收束语义，必须标记 `aggregation_policy=derive_from_phase_states`；人物与观众的情绪河节点由渲染器从阶段状态唯一聚合，不在这里再生成第二套情绪节点。详细字段见 `adaptive-emotion-state-model.md`。

- 阶段不是场景、集数、幕或固定节拍的别名。只有认知、目标、关系、处境/选项、价值判断、行为策略或不可逆后果发生足够大的变化，才建立新阶段。
- 如果多个事件只让同一状态变强/变弱，而没有改变人物怎样理解、选择或相处，保留在同一阶段，用情绪关键帧表达连续变化。
- 同一人物可同时拥有多种情绪。最终可视化数据使用固定情绪家族 + 权重混合，不把细腻状态强行压成一个主色。
- 必须分离 `story time` 与 `audience time`。人物状态只根据人物当时知道的内容；观众状态只根据当时实际呈现和误导的信息。
- 对单元重置、选集式或多世界结构，标记 `continuity_mode=reset|mixed`，禁止把重复人物外观误写成连续成长。
- `global_emotional_arc` 是对整个锁定范围的收束摘要，不是第二套情绪账本；它只引用已有 `phase_id`，不得重复生成与 `phase_events` 竞争的 emotion nodes。
- 禁止把“关系点亮→误读扩大→冲突公开→重估选择”等任何示例固化为四阶段；阶段标签、数量、跨度与机制由当前剧情生成。
- `phase_links` 允许并行、分支、合流、回返与后续重释；`audience_lenses` 允许 1 个整体观众或多个有证据支持的观看立场，不固定人格类型。`mixed` 连续性下，重复出现的人物状态必须显式给出 `continuity_group`。
- HTML 只负责插值与绘制；任何阶段名、边界、情绪混合、认知位移、关系位移、观众问题和全剧弧线，都必须由 AUDIT 数据明确提供。

## 工作纪律

- 让每个重大主张引用用户材料中的单元或位置；无法定位时标为 `UNKNOWN`。
- 让每个高严重度主张同时包含反向解读与置信度。
- 让每个修复方向解释机制并显式检查 `LOCKED` 与连续性。
- 把并列反应和力的传导分开：多人同时有情绪不等于压力已在他们之间传递，缺少关系债依据时写 `UNKNOWN`。
- 判断“在场未位移”前先分清材料未写后续与材料明确给出后续却无代价；前者是 `PENDING_*`，后者才可作为断点，并同时给出这是刻意留白的反向解读。
- 面对 `OUTLINE_COARSE`，情绪面读数只到关系与位移种类的层级，不下表演、对白与微观节奏结论。
- AUDIT 必须区分“设计蓝图要求发生”与“锁定正文已有证据发生”，未兑现项保持断点、PENDING 或 UNKNOWN，不用设计意图补齐。
- AUDIT 完成后必须输出“蓝图意图 vs 正文证据”差集表，逐项标明 `realized`、`partial`、`missing`、`contradicted` 或 `unknown`，并附证据位置；设计意图不能升级为正文事实。
- 保持幕数、节拍时点、场景数、视角、情绪路径、母题数量、类型表达和结局开放，除非用户明确锁定。
- 把定量强度视为可选辅助；始终以因果说明为主。
- 交付诊断，不附改写场景、替代对白或制作提示。
- 把人物称谓一致性和“缺失输入不等于负向证据”作为最终硬检，不用更多结构处方替代这两项证据纪律。


## v1.1 Generalization Pass

- Do not add project-specific conditions, titles, character names, diagnoses, genre beats, dream rules or event IDs to the Skill. Every new rule must still make sense when the next screenplay belongs to a different genre and structure.
- For revision-heavy DOCX input, resolve OOXML revisions before story diagnosis with `emotion-story-forge/scripts/resolve_revision_docx.py`. Track deletions and strikethrough are deterministic; colors are interpreted only from an explicit document/user legend.
- Emotion semantics are open. The base palette is a visual projection layer, not the diagnosis vocabulary. Semantic emotions must carry a visual `family` or `blend`; inferred states should carry `confidence` and `evidence_level`.
- A phase may contain multiple `drivers[]`; keyframes may bind `driver_ref`. Do not split a phase merely because it has multiple drivers if the underlying state remains one continuous state.
- Use `narrative_layers` for reality/memory/subjective/hypothesis/recorded/custom presentation layers. Do not create special-case logic for “dream”, “flashback”, “video”, etc.
- Use `phase_links.family` for stable visual topology and keep `kind` open. Unknown mechanisms use `CUSTOM`, not a new HTML patch.
- Long works may provide evidence-based `phase_clusters[]` for Semantic Zoom. Without clusters, the renderer may paginate technically but must not invent semantic grouping.
- All whole-work emotion river nodes remain derived from `phase_events`; only narrative summaries may be separately authored.

Legacy payloads may still use `audience_segments`; v1.1 output should prefer `audience_lenses`.


## Revision / source preflight

For revision-heavy DOCX, resolve tracked deletions/insertions and strikethrough before diagnosis. Colors are metadata unless explicitly defined by the document/user.
