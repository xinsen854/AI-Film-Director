# 自适应阶段情绪与全剧总谱模型

## 1. 作用边界

本模型负责把已经完成的剧情理解和锁定正文审计，收束为可视化数据。它不是故事模板，也不是 HTML 的推理规则。

- **分析与判定发生在 Skill/AUDIT 层。**
- **HTML 只读取这里定义的数据并插值显示。**
- 禁止 HTML 根据集数、分钟、场景数、波形、颜色或动画自行判断剧情阶段。
- 禁止预设三幕、四幕、起承转合、压—乱—放、固定六阶段、固定峰值数或固定阶段数量。

## 2. 状态变化，而不是事件数量，决定阶段边界

先记录细粒度事件，再判断这些事件是否共同造成一个持续的状态变化。只有当审计证据支持“旧状态已经不足以描述人物/观众所处的局面”时，才建立新的 `phase_event`。

可形成新阶段的通用变化信号包括，但不限于：

1. **认知变化**：人物相信的事实、因果、身份或责任发生实质改变。
2. **目标变化**：人物从维持、逃避、争取、保护、调查等一种目标转向另一种目标。
3. **关系变化**：信任、依赖、权力、债务、亲近、敌意或误读形成新的稳定状态。
4. **处境/选项变化**：人物可行选择、资源、自由度、安全边界或身份位置发生变化。
5. **价值判断变化**：人物或观众重新判断“这件事是什么”“谁是对的”“什么值得保护”。
6. **行为策略变化**：人物从同一种应对方式切换到新的策略，并改变后续条件。
7. **不可逆后果**：公开、死亡、承诺兑现、关系断裂、身份揭露、权力移交、证据锁定等使旧局面无法完整恢复。

仅有强度增加不必切阶段。例如连续三件事都让同一人物在同一认知、目标和关系结构下“越来越焦虑”，可以保留在同一阶段，以关键帧表现焦虑从 0.25 → 0.45 → 0.70。

## 3. 阶段内部允许复杂连续变化

一个阶段不是一个情绪词。它可以包含：

- 单一情绪增强/减弱；
- A 情绪连续过渡为 B 情绪；
- 两种或多种情绪同时存在；
- 表层行为与有证据支持的底层感受错位；
- 情绪簇分裂、合并、残留；
- 情绪不变但认知、关系或选择已经改变；
- 后来信息对先前阶段产生延迟重估。

阶段内部用 `keyframes[]` 表示材料支持的关键状态，不追求每场戏一个点。关键帧之间的动画插值只为观看连续性，不等于新增剧情事实。

## 4. 人物状态最小结构

对每个进入阶段的重要人物，至少区分：

- `knowledge/cognition`：此刻知道、相信、误解什么；
- `goal`：当前想获得/避免什么；
- `relationship`：与相关人物/系统的关系位置；
- `agency/choice`：此刻能否选择、采取什么策略；
- `emotions[]`：当前可视化情绪混合；
- `evidence_refs[]`：上述判断来自哪里。

情绪数据不能代替认知和选择数据。即使人物从头到尾都“焦虑”，若其认知从“事情可能出错”变成“原来是我信任的人造成”，阶段仍可能发生切换。

## 5. 人物时间与观众时间必须分离

同一作品维护两个顺序：

### Story Time
事情在故事世界中实际发生的先后。

### Audience Time
剧本实际让观众看到、知道、误解或回收信息的先后。

人物情绪依据该人物在当时可获得的信息；观众情绪依据作品当时实际提供给观众的信息。非线性叙事、悬疑、误导、悲剧预知、闪回和延迟揭露均不得把两条时间线压成一条。

## 6. 连续、重置与混合拓扑

`narrative_topology.continuity_mode`：

- `continuous`：人物状态和关系债跨阶段继承，可以生成连续人物总弧。
- `reset`：单元结束后人物状态/世界状态按设定重置，不得伪造跨单元连续成长。全剧总谱总结的是反复出现的人性机制、情绪模式或主题问题。
- `mixed`：部分人物/关系连续，部分单元或时间线重置；全剧总谱必须注明各条弧线的继承范围。

## 7. 固定情绪色与混色情绪质点

默认核心情绪家族仅用于视觉语言，不宣称是完整心理学分类：

| id | 标签 | 默认色 | 视觉倾向 |
|---|---|---|---|
| `joy` | 喜悦 | `#FFD166` | 温暖、向外舒展 |
| `excitement` | 兴奋 | `#FF9F43` | 高激活、跃动 |
| `affection` | 喜欢 / 亲近 | `#63E6BE` | 靠近、连接 |
| `hope` | 希望 | `#7EDC9A` | 上扬、恢复 |
| `calm` | 平静 | `#66D9EF` | 稳定、低扰动 |
| `surprise` | 惊讶 | `#C3A6FF` | 瞬时扩张 |
| `anxiety` | 焦虑 | `#FF8C8C` | 细密震颤、收紧 |
| `fear` | 恐惧 | `#FF5F76` | 收缩、逃离中心 |
| `anger` | 愤怒 | `#FF4D4D` | 外冲、碰撞增强 |
| `shame` | 羞耻 / 难堪 | `#D86BD0` | 内收、下沉 |
| `sadness` | 悲伤 / 失落 | `#637EE8` | 下沉、稀疏 |
| `disgust` | 厌恶 / 排斥 | `#A6D854` | 推离、分隔 |

细腻状态优先用两个或多个家族的权重混合表达，不无限增加新颜色。例如“喜欢逐渐转为兴奋”可以使用：

- 0.00：`affection 1.00`
- 0.25：`affection 0.75 + excitement 0.25`
- 0.50：`affection 0.50 + excitement 0.50`
- 0.75：`affection 0.25 + excitement 0.75`
- 1.00：`excitement 1.00`

HTML 可以把一个圆形质点画成两色线性/径向渐变；这只是把 Skill 已给出的比例画出来。

## 8. 质点不是诊断单位

人物是诊断单位，质点是视觉采样。一个人物区域可以拥有几十到数百个视觉质点，但：

- 质点数量不等于心理复杂度；
- 粒子大小不等于客观情绪强度；
- 中心粒子更大、更亮、边缘更小更暗只是视觉层次；
- HTML 不得因为质点碰撞、距离或速度反推出新的情绪结论。

粒子可使用这些纯表现型 `motion`：

`cohere | expand | contract | tremor | drift | split | bridge | hold`

`motion` 必须由 Skill 根据已有审计结论给出；HTML 不自动从情绪词猜测。

最终 HTML 的人物质点场采用 **情绪吸引子（emotion attractor）** 作为纯视觉布局：固定情绪家族在人物局部空间拥有稳定方向，相近情绪在色序与空间方向上相邻。Skill 提供的情绪权重改变时，视觉质点按固定采样槽重新分配并向相应吸引子迁移；因此“喜欢 100% → 喜欢/兴奋混合 → 兴奋 100%”不仅换色，还能看到质点群从一个局部区域连续迁移到另一区域。吸引子不生成诊断，不改变权重，也不产生新情绪。

全剧总谱采用 **连续情绪河流带（emotion river）** 而不是离散圆点矩阵：每个角色一条连续带，颜色来自阶段节点的情绪混合；带宽和垂直微位移只作为既有情绪的视觉编码。观众在全剧总谱中仍保留独立河流；在单个阶段的主视觉中，允许使用**观众外围情绪环（audience halo）**：外围由一个整体氛围环和若干观众分群质点弧组成，人物与观众仍是两套独立状态，HTML 不得把观众反应复制自人物。细因果、人物账本、关系、事实边界与断点默认折叠到“审计与证据”二级区域，避免压过主可视化。

## 9. 自适应阶段拓扑、开放语义与观众分群

阶段编号只使用 `P01/P02/...` 作为稳定引用，不赋予“关系点亮、误读扩大、冲突公开、重估”等固定含义。**固定四阶段、固定六阶段或任何固定阶段名称都禁止成为模板。** 阶段数量由锁定剧情实际状态变化决定，可以为 2、5、8 或更多，也允许一个长阶段后出现很短的瞬时反转。

每个阶段可以提供自由文本 `mechanisms[]`，用于描述该阶段实际发生的认知受击、压力累积、假性缓和、信息差扩大、反转重释、关系回卷等机制；这些标签不是枚举，不用于强迫剧情分类。可选 `relative_span` 只告诉 HTML 当前阶段在总谱/阶段带上应占的相对视觉宽度，不改变剧情判断。

`phase_links[]` 描述阶段之间真实存在的承接、并行、分支、合流、回返或重释关系，不假设所有作品都是严格 `P01 → P02 → P03` 的单线。字段：

```json
[{
  "from":"P03",
  "to":"P05",
  "kind":"reframe",
  "label":"后续事实重写此前意义",
  "evidence_refs":["SC31","SC52"]
}]
```

`kind` 与 `label` 是开放语义；HTML 只把它们作为关系提示，不自行推断“反转”或“分支”。

`audience_segments[]` 定义当前作品确有证据支持的观众观察锚点。它可以只有“整体观众”一组，也可以按作品需要出现情感代入、线索追问、制度警觉、喜剧接受等不同观察立场；**这些名称同样不是固定模板。**

```json
[{
  "id":"AUD_EMPATHY",
  "label":"情感代入观众",
  "perspective":"优先代入人物关系与受伤",
  "question_lens":"谁正在承受这次选择的代价",
  "evidence_refs":["AUD01"]
}]
```

每个 `phase_events[].audience_states[]` 必须通过 `segment_id` 引用一个已声明的观众分群，并继续记录 `knowledge_state`、`misread_or_question`、`reappraisal` 与独立 `keyframes[]`。因此同一时刻允许出现“人物平静、观众焦虑”，或“人物恐惧、观众已知真相而转为期待”等戏剧性反讽。

### 观众外围情绪环

单阶段主视觉可在人物质点场外绘制两层观众环：

1. **整体氛围 Halo**：由当前所有观众分群的已给情绪混合计算纯视觉平均，只做淡色背景，不代替分群数据。
2. **分群质点弧**：每个 `audience_segment` 占外环一段弧，使用与人物相同的混色情绪粒子规则；颜色、速度、密度和迁移只来自该分群 `keyframes[]`。

允许少量“人物 → 观众”的传导粒子作为可视化连线，但只有当阶段数据已有可观察行为/观众反应依据时才显示；它不能创造新的心理因果。

### 性能硬规则

- 静态背景、阶段标签和关系底图与动态粒子分层渲染。
- 人物/观众使用固定粒子槽，不在每帧销毁并重建。
- 动画帧只执行位置/颜色/透明度插值，不重新分析剧情或重新计算阶段。
- 普通粒子禁止逐粒子高成本 `shadowBlur`；用低成本外圈/透明度模拟发光，少数核心节点可保留有限光晕。
- 根据视口与设备能力选择 High/Medium/Low 视觉采样等级；降级只减少视觉粒子数，不改变情绪数据。
- 页面不可见或主视觉离开 viewport 时暂停 requestAnimationFrame。


## 10. 阶段事件数据

`phase_events[]` 是 `rhythm_causality[]` 的语义聚合层，不替代细粒度因果账本。每个阶段至少包含：

```json
{
  "id": "P01",
  "label": "由剧情生成的阶段名",
  "scope_label": "00:18:30–00:27:10 或 EP31–EP36",
  "story_order": 1,
  "audience_order": 1,
  "trigger": "可观察的触发变化",
  "state_change_reason": "为什么必须切成新阶段",
  "summary": "阶段因果摘要",
  "mechanisms": ["由剧情自由生成的机制标签"],
  "relative_span": 1.0,
  "character_states": [],
  "audience_states": [{"segment_id":"AUD_EMPATHY","segment":"情感代入观众","knowledge_state":"...","misread_or_question":"...","reappraisal":"...","keyframes":[],"evidence_refs":[]}],
  "relationship_changes": [],
  "irreversible_changes": [],
  "evidence_refs": [],
  "confidence": "high|medium|low"
}
```

人物状态：

```json
{
  "character": "人物名",
  "continuity_group": "mixed 模式必填；continuous 可省略；reset 由渲染器自动逐阶段断开",
  "entry_state": {
    "cognition": "...",
    "goal": "...",
    "relationship": "...",
    "agency": "...",
    "emotions": [{"emotion":"hope","weight":0.55},{"emotion":"anxiety","weight":0.45}]
  },
  "keyframes": [
    {"at":0.0,"label":"阶段进入","emotions":[...],"intensity":0.42,"motion":"hold","evidence_ref":"SC12"},
    {"at":0.55,"label":"认知受击","emotions":[...],"intensity":0.73,"motion":"contract","evidence_ref":"SC15"},
    {"at":1.0,"label":"阶段退出","emotions":[...],"intensity":0.61,"motion":"bridge","evidence_ref":"SC18"}
  ],
  "exit_state": {...},
  "cognition_shift": "...",
  "goal_shift": "...",
  "relationship_shift": "...",
  "choice_shift": "...",
  "evidence_refs": []
}
```

观众状态结构与人物类似，但必须额外记录 `knowledge_state`、`misread_or_question` 和 `reappraisal`。

## 11. 全剧情情绪总谱

`global_emotional_arc` 是**收束语义，不再是第二套情绪事实源**。人物与观众的全剧河流节点必须由渲染器从 `phase_events[].character_states` 与 `phase_events[].audience_states` 自动聚合，避免“局部状态说 A、总谱又说 B”。因此 AUDIT 只填写以下摘要字段：

```json
{
  "aggregation_policy":"derive_from_phase_states",
  "summary":"全剧收束判断",
  "phase_ids":["P01","P02","P03"],
  "character_throughlines":[
    {"character":"人物名","throughline":"长期认知/关系/选择变化摘要"}
  ],
  "audience_throughlines":[
    {"segment_id":"AUD_EMPATHY","throughline":"该观看立场的长期体验/问题摘要"}
  ],
  "major_turns":[{"phase_id":"P02","label":"关键认知/关系/选择转折","evidence_refs":[]}],
  "ending_residue":"最终留给观众的情绪余味"
}
```

渲染器按当前显示时间轴（Audience Time 或 Story Time）重新排序阶段；人物河流的情绪、认知、关系和主动性只取阶段退出状态/最后关键帧。观众长期河流按 `audience_segments` 分群独立聚合，不再压回一条匿名“总体观众”线。淡色总体 Halo 仍可把分群状态做纯视觉平均，但不能反向成为新的审计事实。

连续性规则：

- `continuous`：同一人物的相邻有证据阶段默认属于同一连续组；若某阶段没有该人物状态，河流必须留空断开。
- `reset`：每个阶段/单元自动成为独立连续组，禁止跨单元连线。
- `mixed`：人物状态必须提供 `continuity_group`；仅相同 group 的相邻有证据节点连接。

时间与拓扑显示：

- HTML 必须提供 `Audience Time` / `Story Time` 切换，阶段带、全剧情人物河和观众分群河随之重排。
- `phase_links` 必须进入实际 SVG 拓扑图，而不是只显示文字标签；回返/重释允许逆向边，并行阶段允许共享时间序位。

## 12. 最终硬检

- 没有固定阶段数量、固定四阶段、固定阶段名称或固定阶段机制枚举。
- `phase_links` 能表达必要的并行/分支/合流/回返/重释，不强迫单线。
- `audience_segments` 来自作品实际观看立场，不使用固定观众人格模板。
- 阶段人物场有独立观众外围情绪环时，观众状态仍不复制人物状态。
- 小事件仅增强同一状态时没有被强行切碎。
- 阶段边界能回答“什么状态实质改变了”。
- 人物与观众各自拥有独立知识状态和情绪数据。
- 非线性作品区分 story time 与 audience time，最终 HTML 可在两种时间顺序之间切换。
- `phase_links` 在最终 HTML 中形成实际拓扑边，不只是一排关系文字。
- reset 作品没有伪造跨单元连续成长；mixed 作品只连接相同 `continuity_group`，阶段缺失人物状态时保留断口。
- `global_emotional_arc` 不再重复输出人物/观众 emotion nodes；渲染节点唯一从 `phase_events` 聚合。
- 每个全剧总谱节点都能回指 `phase_id` 和证据。
- HTML 只插值已给关键帧，不新增剧情判断。


## 12. v1.1 开放情绪语义与证据置信度

12 个基础情绪家族只保留为视觉色谱。AUDIT 可以生成任意细情绪语义 ID，例如 `guilt`、`nostalgia`、`relief`、`jealousy`、`ambivalent_attachment`，但必须通过以下至少一种方式映射到视觉层：

- `family`: 一个基础色谱 ID；
- `blend[]`: 两个或多个基础色谱及内部比例；
- `coordinates`: 可选语义坐标 `valence/arousal/approach/agency/connection/certainty`，范围 -1..1，用于稳定布局。

示例：

```json
{"emotion":"guilt","semantic_label":"内疚","weight":0.35,"blend":[{"emotion":"sadness","weight":0.55},{"emotion":"shame","weight":0.30},{"emotion":"hope","weight":0.15}],"coordinates":{"valence":-0.65,"arousal":0.45,"agency":-0.30,"connection":0.30,"certainty":0.25},"confidence":"medium","evidence_level":"SUPPORTED"}
```

`confidence` 与 `evidence_level` 属于分析证据层。HTML 可以降低透明度、虚化边缘或添加标识，但不得把 `INFERRED/UNKNOWN` 变成确定事实。百分比是视觉混合权重，不是心理测量值。

## 13. 多剧情驱动 `drivers[]`

一个长阶段可由多个剧情事实逐步推动。`trigger` 仅保留为兼容的一句话摘要；v1.1 优先使用：

```json
"drivers":[
  {"id":"DRV01","at":0.18,"label":"新事实进入","observable_event":"...","evidence_refs":["SC08"]},
  {"id":"DRV02","at":0.63,"label":"选择产生后果","observable_event":"...","evidence_refs":["SC12"]}
]
```

人物与 Audience Lens 的关键帧可用 `driver_ref` 指向对应 driver。没有证据的 driver 不得为了动画节奏虚构。

## 14. 通用叙事层与拓扑语义族

`narrative_topology.narrative_layers[]` 不列举题材模板，只定义视觉层：`reality | memory | subjective | hypothesis | recorded | custom`。具体作品可命名“梦境”“证词回忆”“监控录像”“假设未来”等，统一引用 `narrative_layer_id`。

`phase_links` 分为：

- `family`: `SEQUENCE|BRANCH|MERGE|PARALLEL|RETURN|REFRAME|ECHO|RESET|INTERRUPT|CONSEQUENCE|CUSTOM`，只控制通用视觉语法；
- `kind`: 作品开放机制，如 `memory_reframe`、`delayed_reveal`、`motif_return`。

HTML 只理解 family；新的 kind 不需要改渲染器。

## 15. Audience Lens 与 Semantic Zoom

首选字段名为 `audience_lenses`。它表示多个模拟观看立场，不是人口统计分群；弧长、河宽和质点数不表示真实观众占比。旧 `audience_segments` 仅为向后兼容。

长篇若阶段过多，可由 AUDIT 生成 `phase_clusters[]` 供 Semantic Zoom 使用。阶段簇同样按状态/因果语义聚合，不允许固定三幕、四幕或固定集数。HTML 没拿到 `phase_clusters` 时，只能做技术窗口分页，不能创造新的剧情解释。
