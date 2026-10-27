# Project Intake｜融合版项目入口

## 职责

把用户提供的想法、大纲、剧本、设定文档或已有项目整理为一个稳定的生产 Brief。这个模块只负责确认项目范围和生产条件，不提前导演、不提前拆镜，也不擅自推测未知模型能力。

正式生产前只进行一次集中确认。用户材料里已经明确的信息直接识别并预选；只有会改变生产路线、且材料中无法确定的事项才需要用户选择。

## 输入成熟度

- `idea`：概念、主题、人物关系或一句话故事。
- `outline`：已有主要事件和结构，但没有完整场景/对白。
- `treatment`：故事流程和人物较完整，但还不是正式拍摄剧本。
- `screenplay`：已有场景、动作、对白和事件结果。
- `existing_project`：已有生产成果，需要续作、修订或接续。

成熟度只用于路由，不评价作品好坏。

## 一次确认：原固定八组 + 锁稿策略

### 1. 项目形态

电影 / 短片 / 连续剧 / 短剧 / 其他。先显示AI从材料中识别的结果，用户只需确认或改选。

### 2. 项目规模

- 电影/短片：确认目标总时长。
- 连续剧/短剧：确认总集数与单集目标时长。

项目规模是最终覆盖契约，不是单镜时长规则。不得为了模型窗口擅自压缩用户确认的电影时长或剧集数量。

### 3. 画幅

21:9 / 16:9 / 9:16 / 1.85:1 / 用户已明确的其他画幅。用户选择`21:9`时原样保存，不擅自换写为`2.39:1`。

### 4. 目标视频模型与生成组织

必须确认或识别：

- `target_video_model = SEEDANCE_2_5 | SEEDANCE_2_0 | OTHER`
- `generation_organization = 15S | 30S_BLOCK | AUTO`
- `model_call_max_seconds`

规则：

- Seedance 2.5：单个 GU 最长 30 秒。
- Seedance 2.0：单个 GU 最长 15 秒。
- OTHER：只有用户材料或已知项目配置明确给出真实 `model_call_max_seconds` 时才锁定；未知就保持 `unknown`，不得凭印象编数字。

**总时长服从用户，SH时长服从剧情，GU时长服从模型上限。** `15S / 30S_BLOCK`是最大窗口/组织策略，不是固定镜头时长，也不要求GU填满。SH按动作、对白、表演、反应和剪辑节奏形成非定长时长并记录`duration_basis`；不把SH机械切成固定10/15/30秒，也不以无依据随机数替代剧情判断。

### 5. 资产生产方式

- 只输出必要资产Prompt；
- 生成核心必要资产；
- 生成全部必要资产；
- 用户已有资产，AI只补缺失必要资产。

该选项控制生产方式，不改变 CineWeaver Asset Engine 的 Asset Necessity Gate，也不要求为了数量建立无用资产。

### 6. 视觉方向

完整读取当前项目后生成三个真正可执行的视觉方向，并标出推荐项。候选应涉及摄影、美术、光线、色彩、空间或表演取向，不能只写“电影感、质感、高级感”等空词。

用户确认一个方向后写入项目 Brief；后续资产、导演、分镜继承该选择。

### 7. 用户已有媒体与引用事实

集中确认当前项目已经真实存在的：

- 人物图、场景图、道具图或其他视觉资产；
- 用户指定的参考媒体；
- 已经生成成功并可被视频模型实际调用的媒体；
- 只有文字身份、还不存在真实媒体的资产。

内部 Canonical ID 不能冒充真实上传媒体。V-series 是文字 Voice Asset，不创建伪音频，不进入视觉媒体引用槽。

### 8. 执行、交付与音乐策略

- `execution_mode = FULL | QUICK`：生产严格度；FULL 使用正式生产规则，QUICK用于快速验证。
- `production_scope = PROJECT | UNIT | PILOT`：本次生产声明范围，与 `execution_mode` 独立。正式八件套只有 `FULL + PROJECT` 可以宣称项目完成；`FULL + UNIT` 可按正式规则生产局部单元，但不得宣称整片完成；PILOT/QUICK 均不得冒充项目完成。
- 4.7 新确认 brief 必须显式写出 `production_scope`；旧项目缺失时运行时仅为兼容推断为 `PROJECT`，不得把这个兼容行为当成新项目默认省略字段的理由。
- `delivery_target = PLANNING_AND_PROMPTS | PLANNING_PROMPTS_AND_IMAGES`：本Skill不直接生成视频、TTS或最终音频。
- `music_strategy = NO_BGM | LOCKED_CUE | DESIGN_ALLOWED`：默认NO_BGM；LOCKED_CUE必须引用锁定剧本/导演稿中的具体音乐来源；DESIGN_ALLOWED才允许设计新音乐。

### 9. 剧本锁定策略

- `script_lock_policy = REVIEW_BEFORE_LOCK | AUTO_ACCEPT_AFTER_QC`。
- 默认 `REVIEW_BEFORE_LOCK`：Forge Gate/QC/De-AI PASS 后停在锁稿候选，等待一次明确批准。
- 只有用户在本次项目确认中明确授权时，才可使用 `AUTO_ACCEPT_AFTER_QC`。
- 该字段只控制 Forge QC 后是否自动锁稿，不允许绕过 Forge Gate/QC/De-AI，也不允许未锁稿直接进入 Forge AUDIT。

## 自动识别但不强迫用户填写

以下信息材料中明确就写入，未明确且不阻断生产时允许保持未知：

- 年代、地域、现实/架空程度；
- 世界规则；
- 主要人物；
- 已有资产；
- `supports_multishot`；
- `supports_image_reference`；
- `supports_video_reference`；
- `supports_native_audio`；
- `model_reference_capacity`；
- 其他目标模型能力。

未知能力必须保持 `unknown`。

## 确认后写入

### `PROJECT_BRIEF.md`

至少包含：

- 项目类型与规模；
- 输入成熟度；
- 画幅；
- 世界/年代基准；
- 三个视觉方向与最终选择；
- 目标视频模型；
- 生成组织 `15S / 30S_BLOCK / AUTO`；
- 执行模式、交付目标与音乐策略；
- 模型单次调用上限（已知时）；
- 资产生产方式；
- 已有真实媒体清单；
- 仍未知但不阻断当前生产的事项。

### `state/project_brief.json`

面向下游模块保存结构化事实，至少能够表达：

```text
confirmation_status = confirmed
confirmed_brief = true
work_format
project_scale
aspect_ratio
target_video_model
generation_organization
model_call_max_seconds
execution_mode
production_scope
delivery_target
music_strategy
script_lock_policy
asset_production_mode
visual_style_candidates = exactly 3
visual_style_choice
existing_media
```

确认完成后初始化或读取 `PRODUCTION_LEDGER.json`，并初始化唯一总控状态：

```bash
python scripts/master_orchestrator.py --project-root <project_root> init --lock-policy <script_lock_policy>
```

总控创建后当前阶段必须为 `PROJECT_INTAKE`；项目入口完成并落盘上述状态后才可将该阶段标记 `PASS`。如果是已有项目，先执行运行状态迁移门：

```bash
python scripts/migrate_project_state.py --project-root <project_root>
python scripts/production_ledger.py status --project-root <project_root>
```

只有“结构已经符合当前2.0、只是缺版本标记”的旧项目允许自动迁移；检测到旧资产权威、旧Storyboard/Prompt运行结构、未知Schema或半新半旧状态时必须阻断，禁止猜测转换。已有账本必须保留既有Checkpoint。新Brief与既有账本目标冲突时报告冲突，不自动覆盖已完成工作。

## 边界

- 不让用户回答“镜头怎么拍”“情绪曲线怎么走”等专业内部问题。
- 不要求用户自己发明视觉风格描述。
- 不因为宿主具备某工具就假定用户一定要使用。
- 不以SH固定时长或Prompt固定字符范围替代真实导演与分镜判断。
- 不把内部资产ID、V-series或PROMPT_ONLY记录伪装成真实媒体。
- 确认完成后，除非用户主动修改参数或新材料与已锁参数发生硬冲突，不重复启动确认。
