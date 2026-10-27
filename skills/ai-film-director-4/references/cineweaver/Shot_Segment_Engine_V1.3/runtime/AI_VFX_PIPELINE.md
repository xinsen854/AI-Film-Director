# AI-VFX Pipeline｜Optional Plate-Transform Guidance

本文件是 AFD 现有 Shot / Segment / Model Adapter 体系中的**可选执行指导**，不是新的 Owner、不是第二套资产系统，也**不新增 API / 视频生成执行层**。当前 AFD 仍负责资产、分镜与最终 Prompt 编译；宿主没有视频生成能力时，本文件只影响 Prompt 规划、模型路由和生成前 QC。

## 证据边界

- `PLATFORM`：来自已锁定的 Higgsfield model surface，例如 Seedance 2.5 的 `omni_reference`、`video_edit`、4–30s 与 video reference 能力。
- `FIELD`：来自 Higgsfield/OSide 公开 AI-vs-VFX 生产案例。它说明某种工作流在公开制作中如何使用，不等于新增 provider parameter / API parameter，也不自动升级为所有模型的全局规则。
- AFD 只把可机械证明的平台事实做硬 preflight；FIELD 工作流只有在用户/上游明确选择该工作流时才形成局部合同。

## 1. Reuse existing authorities｜不重复造轮子

本文件**复用**现有能力，不重新实现：

- 人物 Face-lock / headless full-body board：继续服从 `asset-prompt-contract.md`；
- Size-ref：继续使用既有 `downstream_metadata.scale_reference`；
- Reference Role：继续使用 `prompt_sections.reference_roles` 的 `role / inherits / excludes / fidelity`；
- Scene GEO、SH/GU/PH、Director Craft、Asset Authority 均保持原 Owner。

不得建立第二套资产库、第二套 VFX reference registry 或平行 Scale/Character 系统。

## 2. Model-specific VFX lanes｜两条不同路线

当前公开证据里至少有两条**不同**的 preservation-VFX / Plate Transform 路线，不能互相覆盖：

- **Seedance 2.0 preservation-VFX**：真实 source clip 是 base；公开 VFX skill 使用 `mode=std`，并把 4K 作为高质量推荐。它适合需要 4K、2.0 source-plate grammar、平台 start/end frame 或 2.0 特有参数的工作。
- **Seedance 2.5 Plate Transform**：source plate 作为 `video_references`，走 `omni_reference`；公开 FIELD 工作流要求 prepared source >=4s 且生成 duration 与 prepared source duration 匹配。

两者共享“preserve source / change only named element”的思想，但 mode、duration 与媒体参数合同按各自 Model Profile 执行。

### Seedance 2.5 Plate Transform｜原片替换 / 元素加入

当任务是：**替换原片中的主体，或加入一个元素，同时尽可能继承原片已有机位、构图、焦点、动作节奏、表演时机、背景、光线、颗粒与时长**，Seedance 2.5 的公开 FIELD 工作流使用：

```text
mode = omni_reference
source plate = video_references
GU duration = prepared source duration
```

这类任务不是默认 `video_edit`。`video_edit` 仍用于“同一 master 时间线内改一个明确范围/属性”的 scoped edit；不要因为输入是视频就把所有 V2V 工作混成一个 mode。

### Source master role

当前 source video 的职责必须明确：

```text
SOURCE VIDEO MASTER
inherits:
- camera
- framing
- focus behavior
- motion / performance timing
- background
- lighting
- grain / compression character
- prepared duration

excludes / editable scope:
- 只列当前明确要替换或新增的主体/元素
```

Plate Transform 的 Prompt 应正向写出 preserve contract：变更范围之外的画面关系、节奏和时序保持 source master。不要把“preserve everything”当成无边界口号；具体 preserve 内容服从当前 GU 的 reference role 与 edit intent。

## 3. Source duration preparation

公开 FIELD 工作流要求 `omni_reference` 的生成时长与 source plate 匹配；超过 source 的额外时长会让模型开始猜测不存在的素材。Seedance 2.5 平台本身的 duration floor 是 4s。

因此在 **Plate Transform 工作流明确启用时**：

- source >= 4s：`GU duration == prepared source duration`；
- source < 4s：先在外部准备 source（例如冻结末帧补足到模型 floor），再进入 Prompt 编译；
- 这不是所有 `omni_reference` 的全局规则，只属于需要逐时继承原片的 Plate Transform。

## 4. Motion anchor gate

V2V 可以继承 source 中已有的动作/机位锚点，但不应假定它能稳定发明 source 从未出现的关键动作。如果目标动作在 source 没有可继承 anchor，继续堆描述或无限重抽不是优先方案。

按需 fallback：

1. 从 source / location 取可用地点帧；
2. 改为 image-to-video / I2V，从头写目标动作；
3. 与原 V2V 镜头在剪辑中拼接；
4. 当场景允许且能服务节奏时，可在 Prompt 中设计一个**可选 clean cut / empty-frame beat**（约一小段只有环境、无主体的画面）作为接缝。它是可选剪辑手段，不是每个 VFX 镜头的强制结构。

## 5. Batch failure diagnosis

公开 FIELD 案例使用了“同一缺陷连续出现在四个 batch”作为 prompt/source fault 的诊断信号：此时继续批量重抽通常只会继续烧资源。

AFD 保留这个经验意义，但**不把 four-batch 变成全局固定尝试次数**。如果项目、模型或宿主只有 1–3 次结果，也可以根据一致性故障证据提前判断；如果四次失败原因各不相同，也不能机械宣布 source 一定有问题。

## 6. Location / integration checks

VFX source 或 location still 的光线必须与目标镜头可整合。Location 的选择优先检查：主光方向、软硬、曝光、关键区域是否可读，以及它是否与 plate 的环境光逻辑冲突。

“批量多生成再按光选”是 FIELD 生产策略，不是 AFD 固定 batch 数，也不锁死某一个图像模型。若用户已有合格 location asset，直接复用；不要为了套流程强制重做。

## 7. Slop diagnosis｜把“更自然”翻译成可执行物理

VFX 镜头出现 CG-double、折纸式肢体/翼面、被拖拽式运动等问题时，避免只写“更自然”。改写成可观察的物理图景：重心如何转移、速度是否加速、衣料/皮肤/膜面如何受力、动作向哪个方向传播、落点/结束状态是什么。

这继续服从 AFD 现有 Physics / Performance / Completion Endpoint，不新增 VFX 专属剧情解释层。
