# emotion-story-forge complete v1.1.2｜Visual Hierarchy Renderer

打包日期：2026-09-01

## 包含的三个 Skill

- `emotion-story-forge/`
- `emotion-narrative-engine/`
- `human-truth-screenwriter/`

## v1.1 核心原则

**Skill 负责理解，HTML 负责看见；通用协议负责约束，具体剧本不进入引擎规则。**

本版不是针对某一部剧本修补。所有新增能力都以“换一个题材、结构、长度完全不同的剧本仍然成立”为准入条件。HTML 不自行判断剧情、不创造人物心理、不创造观众反应，也不把动画状态升级为剧情事实。

## v1.1.2 Visual Hierarchy Renderer

本补丁继续遵守 **“分析不动、协议不动、Renderer 单独优化”**。不增加任何剧本、题材、人物或事件特判，只调整 `emotion-story-forge/assets/emotion-map-template.html` 的通用显示层。

- Audience Halo 收紧为双层结构：外层表达总体情绪气候，内层承载各 Audience Lens 质点弧；弧长仍不代表真实人口比例。
- 人物质点群按同屏人物数量自适应放大；人物越少，内部情绪结构越容易被看清，人物较多时自动回落，避免拥挤。
- 新增低透明度 `Emotion Membrane` 情绪膜，只包络人物自己的质点群，不增加新的剧情或心理判断。
- 多 `drivers[]` 统一显示为 `Event Spine` 剧情驱动脊柱；当前 driver 只高亮 Skill 已输出的数据。
- 当前 driver 可向实际绑定 `driver_ref` 的人物显示短暂脉冲；若数据未绑定，则只按阶段受影响人物做中性视觉提示，不创造因果事实。
- 主画面人物名称加大，情绪摘要压缩为当前 Top-3，详细认知/目标/关系/选择继续保留在下方状态卡。
- Audience Lens 粒子运动在不改变情绪权重的前提下，依据当前已给出的激活度、平静、焦虑/恐惧、惊讶等状态调整聚散和微运动；颜色和数值仍完全来自 Skill。
- v1.1.1 的 Smooth Renderer 缓存、分层 Canvas、动态 DPR、自适应帧率和离屏缓存全部保留。

## v1.1.1 Smooth Renderer Patch

本补丁**不修改 Skill、剧情理解、情绪协议、阶段逻辑、Audience Lens、拓扑语义、总谱派生方式或视觉设计**；仅优化 `emotion-story-forge/assets/emotion-map-template.html` 的运行时渲染。

- 静态层与动态粒子层使用独立 DPR：静态文字/边框保持清晰，动态柔性粒子避免无意义超采样。
- 人物情绪吸引云与双色粒子继续使用原视觉参数，但渐变改为预渲染缓存；支持 `OffscreenCanvas` 时优先用于离屏缓存，不支持时自动回退普通 Canvas。
- 核心粒子、普通粒子、外围粒子按不同刷新频率进入离屏层，最终画面仍按原布局合成。
- 人物名称移入静态层；动态情绪文字改为低频缓存层，避免每帧重复 `fillText`。
- 关键帧排序、当前状态、情绪分配、Audience Halo 气候结果增加运行时缓存；不改变任何分析结果。
- 动画根据实际帧耗时自动降低动态 DPR / 背景刷新频率，必要时降至 30 FPS；不改变质点数量和情绪数据。
- HUD / 进度 DOM 降低无意义高频写入；拖动进度条与手动定位仍立即强制完整刷新。
- 所有优化仅影响绘制成本，不生成新事实、不重排阶段、不修改情绪权重。

## 本版通用化加固

### 1. 开放情绪语义 + 稳定视觉底盘

- 12 个基础情绪家族继续作为**视觉基色**，不再作为封闭诊断词表。
- Skill 可以输出 `semantic_label`、`family`、`blend[]` 与多维 `coordinates`，表达内疚、嫉妒、怀旧、矛盾依恋、释然等未预设细情绪。
- 新语义若不属于基础色谱，必须显式投影到 `family` 或 `blend[]`，避免 HTML 根据文字关键词猜颜色。
- 全局情绪河优先读取语义坐标；人物质点继续使用稳定视觉家族进行高性能投影。

### 2. 情绪置信度与证据层

- 情绪项支持 `confidence: high|medium|low`。
- 支持 `evidence_level: EXPLICIT|SUPPORTED|INFERRED|UNKNOWN`。
- HTML 仅用透明度、清晰度等表达不确定性；不得把低置信度推断显示成确定事实。
- 百分比属于可视化混合权重，不代表心理测量值；UI 使用约数表达。

### 3. 多剧情驱动 `drivers[]`

- 一个阶段允许 0 / 1 / N 个剧情驱动，不再假设“一阶段只有一个 trigger”。
- `trigger` 仅保留为兼容的一句话摘要。
- 人物与观众关键帧可使用 `driver_ref` 绑定具体驱动，从而表达“哪个剧情事实推动了哪一次状态迁移”。
- 多个 driver 并不自动意味着切新阶段；阶段边界仍由人物/关系/认知/选择等实质状态变化决定。

### 4. 通用叙事层 `narrative_layers[]`

- 支持现实、记忆、主观层、假设、记录媒介以及自定义层。
- 梦境、闪回、幻觉、假设画面、录像、故事中故事等不再依赖专用 `if dream` 规则。
- `phase_events[].narrative_layer_id` 仅引用 Skill 已确认的叙事层；HTML 只负责用不同边界/透明度表现。

### 5. 阶段拓扑：稳定 Family + 开放 Mechanism

`phase_links[]` 拆为：

- `family`：稳定视觉语义族，如 `SEQUENCE / BRANCH / MERGE / PARALLEL / RETURN / REFRAME / ECHO / RESET / INTERRUPT / CONSEQUENCE / CUSTOM`；
- `kind` / mechanism：具体剧情语义保持开放。

HTML 只根据 Family 决定线型与视觉语言，不需要为每个新剧本新增 CSS 类型。

### 6. Audience Lens｜模拟观看视角

- v1.1 首选字段 `audience_lenses`；旧 `audience_segments` 继续兼容。
- Lens 表示由剧本信息分配产生的模拟观看立场，不是人口统计分群。
- 外环弧长、质点数量、河流宽度不表示真实观众占比，除非未来有真实研究数据显式提供。

### 7. 全剧情总谱改为派生结果

- 人物和观众的长期情绪节点唯一从 `phase_events` 的阶段状态聚合。
- `global_emotional_arc` 只保留 throughline / major turn / ending residue 等收束语义，并要求 `aggregation_policy=derive_from_phase_states`。
- 禁止再生成第二套独立情绪数值，避免“阶段说 A、总谱说 B”。

### 8. Semantic Zoom｜长剧通用缩放

- 可选 `phase_clusters[]` 由 AUDIT 按实际剧情语义聚合，数量、跨度、名称均不固定。
- 约 12 个以上阶段时，HTML 优先使用阶段簇做 `作品 → 阶段簇 → 阶段 → driver/keyframe` 的阅读缩放。
- 若没有语义阶段簇，HTML 只允许创建无语义技术窗口，不能自行发明“三幕/四幕/固定集数”等结构。
- SVG 会按阶段数量增加真实最小宽度，避免长剧被强行压缩进一屏。

### 9. Revision Resolver｜修订稿前处理

新增：

- `emotion-story-forge/scripts/resolve_revision_docx.py`

用于在剧情理解之前清洗修订密集 DOCX：

- Track Changes 删除与删除线可确定排除；
- Track Changes 插入可确定保留；
- 颜色默认只报告，不具有全局固定含义；
- 只有用户或文档自身明确给出颜色图例时，才允许通过 `--color-policy` 解释颜色；
- 输出 active text + 可选 revision report，避免情绪引擎同时分析废稿与最终稿。

### 10. 当前时刻 Dynamic Top-N

人物/观众情绪卡不再固定显示“整个阶段历史最高的几个情绪”。播放过程中，当前关键帧中新出现并变强的情绪可以自动进入 Top-N；已经归零的历史情绪不会继续占用槽位。

## v1.0 能力继续保留

- Audience Time / Story Time 真正双时间轴；
- `phase_links` SVG 开放拓扑；
- continuous / reset / mixed 连续性断线规则；
- 人物独立混色情绪质点系统；
- 观众外围 Halo + Audience Lens 质点弧；
- `phase_events` 自适应阶段，不固定数量、名称、跨度或类型；
- 静态/动态双 Canvas、固定粒子槽、后台暂停与设备采样等级。

## 主要运行脚本

- `emotion-story-forge/scripts/validate_ledger.py`
- `emotion-story-forge/scripts/validate_s_candidate.py`
- `emotion-story-forge/scripts/scan_variation.py`
- `emotion-story-forge/scripts/render_emotion_map.py`
- `emotion-story-forge/scripts/resolve_revision_docx.py`

## HTML 模板

- `emotion-story-forge/assets/emotion-map-template.html`

主视觉顺序：

1. 全剧情派生情绪总谱
2. Audience Time / Story Time + Semantic Zoom + 开放阶段拓扑
3. 阶段事件 · 人物情绪质点场 + Audience Lens 外围情绪环
4. 当前阶段 driver / 人物 / 观众状态
5. 审计与证据（默认折叠）

模板仍为单文件离线 HTML，不依赖外部字体、脚本、图片、CDN 或网络请求。

## 关键参考协议

- `emotion-narrative-engine/references/adaptive-emotion-state-model.md`
- `emotion-narrative-engine/references/core-emotion-model.md`
- `emotion-narrative-engine/references/emotion-relationship-field.md`
- `emotion-narrative-engine/references/diagnostic-report-contract.md`
- `emotion-story-forge/references/blueprint-schema.md`
- `emotion-story-forge/references/long-form-orchestration.md`

## 向后兼容

- v1.0 的基础 palette emotion、`trigger`、`audience_segments` 等旧字段继续可读。
- v1.1 新输出应优先使用开放情绪语义、`drivers[]`、`audience_lenses`、叙事层与 topology family。

## 不包含

- 任何项目剧本或项目数据
- 针对某一个故事、人物、疾病、年代、题材的特判规则
- 测试报告、测试 JSON、测试 HTML、截图
- 设计过程文档
- HTML 备份模板
- `__pycache__`、`.pyc` 或其他运行缓存

## 安装

将三个 Skill 目录复制到目标 Codex skills 根目录。若已有同名目录，请先备份旧版，再替换为本包内容。

默认剧本交付为 Markdown；只有用户明确要求时才生成 DOCX。最终情绪图谱 HTML 必须从锁定剧本审计数据生成，不能从尚未锁定的大纲伪造最终总谱。


## v1.1.3 Ambient Aura Patch
- 仅修改通用 Renderer 显示层，不修改 Skill、协议、剧情分析或阶段逻辑。
- 人物情绪膜改为环境融合渐变 Aura，取消明显硬边圈线。
- 强化人物内部情绪吸引子与核心粒子可见度。
- 提升观众情绪带粒子数量与外层气候可见度。


## v1.1.4 Minimal Writer Generalization Patch
- Minimal rule-only patch; HTML/renderer and emotion-analysis architecture unchanged.
- Distinguishes authored proposals from source inference by provenance.
- Removes fixed Audience Lens count and fixed dialogue/performance beat counts.
- Adds continuity-aware CONTINUOUS/RESET/MIXED writing and ledger handoff.
- Allows immediate, delayed, or private/self-state emotional transmission without forcing multi-person movement.
