# SEEDANCE VIDEO PROMPT COMPILER｜V1.6 CURRENT-GU STRONG LOCK

The compiler converts the full V4.8-derived EDIT SHOT contract into a Seedance-native Generation Unit prompt **without discarding execution detail and without importing unrelated project facts**.

## 0. Model dialect gate｜先确定模型表面再编译

先读取 `MODEL_ADAPTER.md` 与当前 model surface profile。Seedance 2.0 与 Seedance 2.5 不共享一套参数/Mode 语法。

**Seedance 2.5：先选 mode 再写 Prompt。**
- `t2v`：场景执行 brief；
- `omni_reference`：参考素材 role map + 当前场景执行 brief；
- `video_edit`：editing master + edit scope + preserve list；
- `video_extension`：source boundary + `extension_mode` + 新内容。

2.5 的 `video_edit` 不把 `duration / aspect_ratio` 当作可设置执行事实；`video_extension` 继承 source aspect ratio。2.5 不得伪造 2.0 的 `start_image / end_image` provider 角色。

Seedance 2.0 则读取 `SEEDANCE_2_0_PROFILE.md`，使用其 `std / fast` 与真实媒体角色。模型专属规则不得提升为 AFD 全局规则。

## 1. SUMMARY_COLLAPSE forbidden
The Final Prompt is not a synopsis. Active camera, blocking, axis/gaze, micro-performance, dialogue, sound, prop state, physics, first/last-frame, continuity and reference-role facts must survive when execution-relevant.

CineWeaver sets **no fixed prompt-character ceiling**. A detailed 30-second prompt may exceed **5000 Chinese characters** when needed. Remove redundancy, not execution signal.

## 2. CURRENT_GU_ONLY｜当前GU隔离
最终 Prompt 只允许包含**当前 GU 真正需要执行或保持的事实**。

必须从当前 Member EDIT SHOTs 反向收集：
- 当前可见人物/实体；
- 当前实际使用的视觉媒体资产；
- 当前空间、站位、轴线、视线；
- 当前道具与持续状态；
- 当前动作、物理、表演、对白；
- 当前声音与 Voice Profile；
- 当前首帧、阶段结束状态与下一 Cut 所需的直接连续性。

禁止把以下内容为了“保险”批量复制进每条 GU：
- **未来事件**、未来场景结果、未来揭示；
- 当前 GU 未出现的**无关资产**；
- 当前空间不存在的**无关声音**；
- 整个项目的**全局连续性**清单；
- 其他场景的医院时间、车内座位、协议日期、门牌状态、天气、服装等与当前 GU 无关事实。

若某全局事实确实影响当前 GU，必须把它改写成**当前可执行的局部事实**，而不是复制全局账本。

## 3. Fixed structure
1. `【生成目标】`
2. `【参考素材职责】`
3. `【空间占位图】` — only when a Member SH has `needs_space_diagram=true`; copy the complete SH block unchanged
4. `【初始状态】`
5. `【阶段推进】`
6. `【关键时间锚点｜可选】` — omit unless critical
7. `【声音】`
8. `【保持一致】`
9. `【局部限制】`

每个栏目都必须写当前 GU 的**具体事实**。不得用模板套话占位。

## 4. Reference binding｜显式Seedance素材职责
只列当前 GU 实际上传/绑定的媒体引用。

正确：
- `@图片1 对应 A001｜许程：只负责脸型、发型、年龄感、体型和当前服装；不采用参考图背景与原姿态。`
- `@图片2 对应 S001｜钟表店：只负责当前可见区域的空间结构、柜台/玻璃门/钟墙与材质；不采用资产板中的人物和多视图拼贴。`
- `@图片3 对应 P001｜营业木牌：只负责木牌形状、材质、旧化、绳结和当前文字状态；不负责构图。`

错误：
- 仅写 `A001 identity`；
- 仅写 `使用A001锁定身份`；
- 列出资产库全部 A/S/P；
- 列出并未真正上传的媒体为 `@图片`。

内部编号可以保留作追踪，但**不能替代 Seedance 的实际媒体引用与职责描述**。当前 Member SH 已调用的视觉资产，只要进入当前 GU，就必须在 `prompt_sections.reference_roles` 中得到当前GU级职责绑定；真实媒体已激活时必须明确到 `@图片N`。违反触发 `REFERENCE_BINDING_FAILURE`。

## 4.1 Structured reference transfer metadata｜兼容增强

现有 `prompt_sections.reference_roles` 继续保持兼容：旧字符串条目原样合法，**不强制迁移，也不新增第二套 Reference Authority**。需要机器校验时，可在同一个 `reference_roles` 列表中直接使用可选结构化条目；Renderer 最终仍把它编译成人类可读职责句：

- `asset_id`：当前 A/S/P/G/B 等现有资产 ID；
- `media_ref`：可选真实媒体句柄（如 `@图片1`）；文字回退时省略，禁止伪造；
- `role`：该参考负责什么；
- `inherits[]`：允许继承的可见属性；
- `excludes[]`：明确不继承什么；真实媒体存在污染可能时必须非空；
- `fidelity`：可选 Prompt 元数据；
- `fidelity_target`：仅 `attribute-transfer` 时指定目标。

兼容边界：全旧式字符串 GU 继续合法；但一个 GU 一旦使用结构化媒体职责，该 GU 的其他 `@图片/@视频/@音频` 媒体职责也必须结构化，不能用旧字符串选择性绕开 `inherits/excludes/fidelity` 校验。无媒体的文字视觉身份回退仍可保留旧字符串。

最终仍渲染成自然语言职责句。存在人物、背景、构图、动作、声音等污染可能时，一条 reference role 必须同时说明**负责什么**以及**排除什么 / 不继承什么**，不能只写“参考图2”。

Seedance 2.5 可选 `fidelity` 值：`full-preserve / partial-preserve / attribute-transfer / loose-guide`。它只是 AFD 内部 Prompt 元数据，**不是 Higgsfield / Seedance provider 参数**，不得进入 provider parameter map。`attribute-transfer` 必须带 `fidelity_target`，明确属性要转移到哪个目标。

## 5. 缺少图片参考时的文字视觉身份回退
如果当前 GU 的重要人物/场景/道具**缺少图片参考**：
- 不得假装已有参考图；
- 不得写不存在的 `@图片X`；
- 从 ASSET_LIBRARY 的文字资产中展开**文字视觉身份**：年龄感、脸型、发型、体型、服装、显著识别特征、当前状态，或场景/道具的当前执行外观；
- 只展开当前 GU 需要辨认的细节，不复制人物传记或无关资产信息；
- 文字回退必须至少让执行模型知道“这是哪个当前资产 + 当前要锁定的具体外观”，仅写 `A001 identity`、`保持一致`、`按资产库执行` 等内部缩写不算身份锚；
- 当前资产没有真实激活媒体时，禁止为了格式好看伪造 `@图片N`。

如果缺失参考导致身份一致性无法达到项目硬要求，应由 QC 标记资产缺失，而不是用一句“保持一致”掩盖。缺少当前资产的具体文字身份锚触发 `GU_ASSET_IDENTITY_ANCHOR`；未激活真实媒体却伪造 `@图片N` 触发 `FAKE_MEDIA_REFERENCE`。

## 5.1 Locked dialogue identity｜最终GU不得压平说话人
若当前 Member SH 含锁定对白，GU Phase 的 `dialogue_execution` 必须继续使用结构化条目，并按原顺序保留：
- `speaker`；
- `verbatim`；
- SH已有的 `mode / lip_sync / delivery`；
- 若该说话角色在 ASSET_LIBRARY 已绑定 `V001 / V002...`，必须写入同一条对白的 `voice_profile_id`，并把该V-ID列入当前GU `voice_text_assets`。
- 本句必须保留 `performance_strategy / audible_emotion / volume / distance / pace / emphasis / breath / pause`；这些是当前句表演，不得压进一句“有情绪地说”。

禁止把多人对白压成匿名连续字符串，例如 `A句。B句。C句。`。Final Prompt 必须可直接看出**谁说哪一句**；有Voice Profile时必须显示对应V-ID。没有Voice Profile的角色仍保留 `speaker + verbatim`，不得伪造V-ID。

## 6. V-series voice assets
`V001 / V002...` are **TEXT_VOICE_ASSET** records. 禁止把V系列编译成 `@图片`、`@视频`、`@音频`。They create no media file and cost zero Seedance reference slots.

只注入当前 GU **实际说话或声音身份需要出现的人物** Voice Profile。其他人物的 V 资产不得批量复制。

## 7. PHASE-first timing
默认不用完整逐秒时间轴。Use `PH01 / PH02 / PH03...` as state progression. Each phase may include stage goal, camera/image, action/physics, performance/microreaction, dialogue, and **specific end state**.

Use `【关键时间锚点｜可选】` only for execution-critical delayed reveal, reaction delay, prop entry, required close-up/spatial event, lipsync/action synchronization, or similarly critical timing.

若当前 GU 没有需要精确时机的事件，**删除该栏目**，不得复制项目其他镜头的时间锚点示例或事件清单。

## 8. Sound｜当前GU声音隔离
`【声音】`只包含当前空间和当前动作真实存在的：
- environment；
- Foley；
- sync sound；
- spatial acoustics；
- locked dialogue；
- 当前说话人的 V-series stable voice text；
- current-line delivery；
- music/silence policy。

全项目默认禁止BGM、配乐和自动情绪音乐；只有导演剧本明确指定音乐时才允许。当前GU未获得这种明确音乐指令时，在 `【声音】` 中落实禁用，不自行添加情绪铺底音乐。

禁止把住宅、钟表店、车内、街道等不同场景的声音菜单复制到每条 GU。当前 GU 没有的声音必须删除。

## 9. Keep-consistent｜局部连续性
`【保持一致】`只列当前 GU 需要跨 PH/跨 Member SH 保持的事实，例如：
- 当前人物身份/服装/伤势；
- 当前手持道具和左右手；
- 当前空间位置、朝向、轴线、屏幕方向；
- 当前灯光/天气；
- 当前已揭示且仍会影响画面的状态。

禁止复制整部电影的全局连续性账本。

GU必须显式写`starting_state`与`ending_state`；相邻GU执行硬等式：上一GU `ending_state ==` 下一GU `starting_state`。任何位置、左右手道具、伤势/污损、服装、轴线、视线、光照时间或动作尾态差异都需要当前剧情中的可见原因，不能静默重置。

## 10. Local locks
`【局部限制】`只写当前 GU 高风险失败项。先正向锁定，再列必要排除。禁止大而全的通用负面词库，禁止写与当前 GU 无关的未来信息。

## 11. Direct execution QA
Verify:
- mandatory structure;
- `CURRENT_GU_ONLY` isolation;
- explicit active-media roles;
- no internal-ID-only binding;
- V-series text-only handling;
- missing-reference fallback honesty;
- every current Member SH visual asset has either explicit active-media binding or a specific current-GU text identity anchor;
- no fabricated `@图片N` when the asset is not active media;
- model-window compliance;
- phase-state continuity;
- verbatim locked dialogue;
- no stale shorthand;
- no `GLOBAL_PROMPT_POLLUTION`;
- enough execution detail to run without another rewrite.

## 4.2 Supporting scale reference｜按需比例参考

若当前 GU 同时使用某 `scale_reference.subject_asset_ids`、该比例关系对当前镜头成立且真实 Size-ref 媒体已经激活，可在 `【参考素材职责】` 中增加一个独立媒体职责：只继承 `inherits[]` 中的相对比例/安装位置等事实，并显式排除 `excludes[]`。比例板不负责身份、背景、灯光、调色或当前构图，除非上游明确把对应属性列入 `inherits[]`。

Size-ref 不是全局必选项：普通近人体尺度、单主体镜头、文字地标足以稳定的场景不强制绑定。`PROMPT_ONLY / FAILED / MISSING` 时不得伪造 `@图片N`；是否占用当前模型参考槽仍服从 Model Surface Profile 和 CURRENT_GU_ONLY。

## 12. AI-VFX Plate Transform｜按需 source-master 编译

仅当当前 GU 明确选择 Plate Transform / preservation-VFX 工作流时启用；普通 `omni_reference` 与普通 Seedance 2.0 生成不受此段额外约束。读取 `AI_VFX_PIPELINE.md` 及当前 `SEEDANCE_2_0_PROFILE.md / SEEDANCE_2_5_PROFILE.md`，先选模型 lane 再编译。

- Seedance 2.0 preservation-VFX：source plate 使用真实 `video_references`，model lane 为 `std`；4K 是该公开工作流的质量推荐，不冒充全局硬参数。
- Seedance 2.5 Plate Transform：source plate 使用 `video_references`，model lane 为 `omni_reference`，prepared source duration 与 GU duration 匹配。

Source video 必须作为当前 GU 的实际 `@视频N / video_references` master，并在 `【参考素材职责】` 中说明它负责的 source facts：**camera、framing、focus、motion / performance timing、background、lighting、grain / compression character、prepared duration**。被替换/新增的主体资产继续走现有结构化 Reference Role，不能用新的 VFX registry 取代它。

Prompt 的 preserve contract 只锁当前 source master 中与目标编辑无关的可见/可听事实；明确指出 editable subject / element。不要为了 VFX 把整个项目全局事实复制进 Prompt，继续服从 `CURRENT_GU_ONLY`。

Plate Transform 使用 `omni_reference` 时，生成 duration 与 prepared source duration 匹配；若 source 低于当前模型 floor，先准备 source，不得靠延长 Prompt 让模型自行补不存在的原片。缺关键 motion anchor 时，返回 `AI_VFX_PIPELINE.md` 的 I2V fallback / clean-cut 方案，而不是增加未来剧情或无依据动作。


## 13. Off-screen carry｜按需离画连续性

若当前 SH 的直接前序 `next_shot_handoff.offscreen_carry` 有记录，且角色当前仍未入画，可在当前 GU 的局部连续性中加入一行简短 Off-screen 说明：角色、退出侧、最后可见状态。该信息用于保持后续合法再入画方向/手持状态，不把离画角色重新注入 `active_media_references`，也不把它写成当前画面主体。角色一旦重新入画，转由当前 SH 的 `start_positions / frame_positions / visual_asset_calls` 接管。
