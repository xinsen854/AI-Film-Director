# 05｜统一资产提取 Skill V4.1｜Asset Engine

## 一、职责

读取：

```text
PROJECT_CREATIVE_BIBLE
+
LOCKED / INTEGRATED SCREENPLAY
+
已有 ASSET_LIBRARY.md（如存在）
```

提取、去重、维护正式制作需要的可复用资产，并始终只输出：

```text
ASSET_LIBRARY.md
```

不得设计分镜、景别、机位、运镜、当前镜站位、当前镜微表情、Timing 或最终视频 Prompt。

---

## 二、资产准入

只有满足以下任一条件才建立正式视觉资产：
- 后续需要复用；
- 身份漂移会破坏剧情；
- 视觉连续性重要；
- 关键人物 / 场景 / 道具 / 生物 / 群体；
- 可见状态跨多个 SHOT 持续；
- 已知模型稳定性需要参考；
- 下游会多次调用同一参考。

普通背景物、一次性杯子/桌椅/手机、单镜表情、临时姿势、一次呼吸变化、当前 Beat 反应默认不建立正式资产。

---

## 三、资产编号

```text
A：核心人物
B：持续次要人物
G：生物 / 非人实体 / 群体 / 群演
S：场景
P：关键道具
```

持续状态不建立重复主资产：

```text
MASTER → STATE
A002 → A002-ST001
S008 → S008-ST001
P003 → P003-ST001
```

Voice Asset 独立使用 V 三位编号：`V001 / V002 / ...`。V系列只保存文字声线，不生成任何图片、视频或音频文件。

---

## 四、资产快速索引

| 编号 | 名称 | 类型 | reference role | visual cost | Seedance槽位 | 图片文件 | 状态 |
|---|---|---|---|---:|---:|---|---|

---

## 五、A / B 人物资产

### A001｜人物名
- 剧情身份：
- 首次出现：
- 复用范围：
- 身形与轮廓：
- 发型：
- 基础服装：
- 主色：
- 身份记忆点：
- 当前持续状态：
- 图片文件：A001_NAME_CHARACTER_BOARD_V01.png
- 图片状态：PROMPT_ONLY / GENERATED / FAILED / MISSING（内部Canonical状态；用户显示可中文化）
- 视图覆盖：
- 正向图片提示词：
- 固定排除：

### 下游调用元数据
- default_reference_role：identity
- visual_cost_units：1
- seedance_reference_slot_cost：1（实际作为媒体参考时）
- generic_eligible：YES / NO

### execution_anchor_summary
- identity：
- silhouette：
- wardrobe：
- persistent_state：
- distinguishing_marks：
- performance_identity：

### 声音资产链接
- voice_asset_id：V001

---

## 六、V 系列声音资产｜纯文字

### V001｜角色名声线
> `TEXT_VOICE_ASSET`。只保存文字描述；不生成音频、不生成图片、不生成视频；不占视觉资产额度；不占 Seedance 参考素材数量。

- character_asset_id：A001
- media_asset：false
- visual_cost_units：0
- seedance_reference_slot_cost：0
- source_status：explicit / inferred / mixed
- confidence：
- perceived_age：
- timbre：
- pitch_tendency：
- texture：
- resonance：
- vocal_weight：
- pace：
- rhythm：
- breath_pattern：
- articulation：
- diction_clarity：
- accent_or_regional_quality：
- speech_habit：
- sentence_shape：
- emotional_leakage：
- pressure_behavior：
- volume_tendency：
- prohibitions：
- evidence：

### V 系列推断限制
- 可根据年龄段、身体状态、人物小传、稳定性格、锁定对白句式与已批准长期表演身份做保守推断；
- 无证据不得创造具体地域口音、方言、病理性声线或发音障碍；
- V 系列只定义长期声线身份，当前镜语气/停顿/情绪泄漏由 SHOT / Seedance Compiler 决定；
- V 系列不得写入【资产调用】图片行，不得变成 `@图片`、`@视频`、`@音频`。

---

## 七、持续状态资产

### A002-ST001｜状态名称
- inherits_from：A002
- 状态类别：服装 / 伤势 / 湿度 / 污损 / 形态 / 其他
- 开始范围：
- 结束范围：持续中 / 指定场景
- 状态事实来源：
- 剧情触发原因：
- 可见变化：
- 必须保持不变：
- compatible_with：
- conflicts_with：
- persistent_scope：
- 图片文件：
- 图片状态：
- 正向图片提示词：
- default_reference_role：state
- visual_cost_units：无独立状态参考图时0；实际调用独立状态图/状态板时1
- generic_eligible：YES / NO

禁止为以下内容建立 STATE：
- 单镜表情；
- 临时姿势；
- 一次呼吸变化；
- 当前 Beat 反应；
- 单句对白里的临时情绪。


### STATE 参考图时间隔离
- `image_prompt` 只允许描述该STATE从 `state_start` 起已经生效的可见Delta；
- 不得把后续兄弟STATE的可见变化提前合并进当前STATE板；
- 如果一个变化发生在同一场景后半段，`state_start` 应精确到对应SH，而不是用宽泛SC范围掩盖先后关系；
- MASTER板保持时间中性，未来状态只在其合法STATE中出现。

---

## 八、S 场景资产

### S001｜场景名
- 剧情功能：
- 首次出现：
- 复用范围：
- 建筑类型：
- 材质与色彩：
- 功能区：
- stable_geography：
- landmark_anchors：
- 主入口 / 主要出口：
- 固定结构：
- 视图覆盖：
- 鸟瞰 / 空间结构：
- 图片文件：
- 图片状态：
- 正向图片提示词：
- 固定排除：
- default_reference_role：location
- visual_cost_units：1
- seedance_reference_slot_cost：1（实际作为媒体参考时）
- generic_eligible：YES / NO

场景资产只回答“这个地方是什么、空间怎样连接”，不得规定当前镜头景别、机位、镜头运动或构图。

---

## 九、P 关键道具资产

### P001｜道具名
- 剧情功能：
- 结构：
- 材质：
- 尺寸关系：
- 正常功能：
- 明确不能做什么：
- 启用条件：
- 使用限制或代价：
- state_sensitive：
- hand_contact_relevance：
- scale_anchor：
- 图片文件：
- 图片状态：
- 正向图片提示词：
- 固定排除：
- default_reference_role：prop
- visual_cost_units：1
- seedance_reference_slot_cost：1（实际作为媒体参考时）
- generic_eligible：YES / NO

---

## 十、G 生物 / 实体 / 群体资产

### G001｜资产名
- G_ASSET_TYPE：CREATURE / ENTITY / CROWD / EXTRA_GROUP
- 体型 / 解剖 / 材质 / 运动方式（生物/实体）：
- 能力与形态边界：
- group_count_range（群体）：
- 服装 / 阵营 / 队形 / 活动方式（群体）：
- lead_member_policy：
- 图片文件：
- 图片状态：
- 正向图片提示词：
- 固定排除：
- default_reference_role：identity / crowd
- visual_cost_units：1
- seedance_reference_slot_cost：1（实际作为媒体参考时）
- generic_eligible：YES / NO

---

## 十一、图片 Prompt 策略

每个视觉主资产和STATE都必须保存：

```yaml
asset_id_or_state_id:
name: 标准名称
image_prompt: Canonical Prompt
image_status: GENERATED / PROMPT_ONLY / FAILED / MISSING
reference_media: []       # 仅真实存在媒体；文字ID和待生成文件名不得填入
use_scope: []             # 非空
dependencies: []          # 可为空列表，但字段必须存在
```

车辆沿用P系列并写`prop_type: VEHICLE`；服装、伤势、污渍等持续状态使用所属人物的`-ST###`，不另建一套资产编号。只创建保证跨镜一致性或复用所需的最少资产。

人物母板：身份中性、可复用，不写死当前镜表情、当前镜姿势、当前镜摄影和当前镜灯光。

场景板：负责场景身份、功能区、空间结构、landmark，不负责当前镜构图。

道具板：负责形状、尺度、材质、持久状态，不负责当前镜动作。

项目风格以 PROJECT_CREATIVE_BIBLE 为准。旧项目若明确锁定“人物面部彩铅/弱识别处理”则继承；其他项目不得自动叠加该规则。

---

## 十二、供 SHOT / Seedance Compiler 调用

下游可直接读取：
- asset_id / name；
- asset_class；
- image_file / image_status；
- reference_media / use_scope / dependencies；
- default_reference_role；
- visual_cost_units；
- generic_eligible；
- execution_anchor_summary；
- voice_asset_id 与 V 系列 voice_profile 文字字段；
- STATE lineage；
- S 场景 stable_geography / landmarks；
- P 道具结构 / 状态；
- G 群体定义。

`generic_eligible` 只是下游预算角色，不建立新的“通用资产编号体系”。

---

## 十三、05 最终验证

- 是否始终只维护一个 ASSET_LIBRARY.md：YES / NO
- 是否复用已有主编号：YES / NO
- 是否只建立真正需要复用/一致性的正式资产：YES / NO
- 是否把单镜表情或临时姿势错误资产化：NO
- STATE 是否全部明确 inherits_from：YES / 不适用
- 每个需要声线资产的人物是否链接 V 三位编号：YES / 不适用
- V 系列是否全部为纯文字、media_asset=false：YES / NO
- V 系列 visual_cost_units 与 seedance_reference_slot_cost 是否始终为0：YES / NO
- V 系列是否未生成/挂接图片、视频、音频文件：YES / NO
- 是否无证据创造具体地域口音/方言：NO
- 视觉资产 visual_cost_units 是否默认为1：YES / NO
- generic_eligible 是否只作为预算元数据：YES / NO
- 是否输出当前镜景别/机位/站位/Timing：NO
- S 场景是否只定义稳定空间，不替当前镜构图：YES / NO
- 图片 Prompt 是否避免写死当前镜表演：YES / NO
- 当前可调用的 MASTER / STATE 图片Prompt 是否未提前包含 Information Ledger 受保护Reveal：YES / NO
- MASTER 是否未混装未来持续状态，STATE 是否未混装未来兄弟STATE Delta：YES / NO
- 项目风格是否严格继承上游而非强制统一彩铅：YES / NO
- 是否输出最终视频 Prompt：NO
