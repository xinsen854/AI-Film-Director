# Seedance 2.5｜Higgsfield Omni-Reference Profile

本文件是 **Seedance 2.5 在 Higgsfield 表面的模型专属执行合同**。2.5 与 2.0 是不同 dialect，不是简单版本覆盖。

## 已验证表面事实

- duration：`4–30s`
- resolution：`480p / 720p`
- mode：`t2v / omni_reference / video_edit / video_extension`
- aspect_ratio：`auto / 21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16`
- media roles：`image_references / video_references / audio_references`
- Higgsfield 2.5 表面**不支持**平台 `start_image` 角色，也**不支持**平台 `end_image` 角色；首尾帧若需要，在 `omni_reference` 中通过参考素材职责表达，而不是伪造媒体参数。

## Mode Router｜先选 mode 再写 Prompt

### `t2v`
无参考素材的新生成。Prompt 是场景执行 brief。

### `omni_reference`
由图片 / 视频 / 音频参考素材共同构建新视频。Prompt 必须先做 role map：每个素材写清**负责什么**，并在存在污染风险时写清**排除 / 不继承什么**，然后再写当前 GU 的场景、动作、镜头、声音和结束状态。

### `video_edit`
已有视频内部的局部修改。必须指定唯一 editing master、edit scope、preserve list。该模式下 `duration` 与 `aspect_ratio` 不作为可设置执行参数；不得把它们写成模型参数事实。

### `video_extension`
对已有视频向前或向后续写。必须指定 `extension_mode: forward | backward`；其他 mode 不得携带 `extension_mode`。扩展继承 source aspect ratio，Prompt 负责边界状态和新增内容。

## Reference Role

推荐结构化保存：

- `role`
- `inherits[]`
- `excludes[]`
- 可选 `fidelity`
- 可选 `fidelity_target`

`fidelity` 仅是 AFD Prompt 元数据，不是 Higgsfield / Seedance provider 参数。可用值：`full-preserve / partial-preserve / attribute-transfer / loose-guide`；`attribute-transfer` 必须指出目标。

## 长时段组织

30 秒是窗口，不是填满目标。按当前任务拆 Stage：一个 Stage 一个主要变化，并写明确 end state。若同一生成同时承担互相竞争的复杂 JOB（例如高强度物理 + 细腻表演），按 JOB 拆 GU，而不是只看秒数。

## AI-VFX Plate Transform｜FIELD 路由补充

当当前任务明确是 **Plate Transform / 原片替换**：替换或加入主体，同时继承 source video 的机位、framing、focus、motion/performance timing、背景、光线、颗粒和时长，公开 FIELD 工作流使用 `omni_reference + video_references`，而不是把它当作普通 `video_edit`。

- `omni_reference` Plate Transform：source video 是 motion/timeline master，`duration` 必须与**已准备好的 source duration**匹配；
- `video_edit`：仍负责已有 master 内明确 edit scope 的局部修改，且该 mode 自身忽略 `duration / aspect_ratio`；
- source < 4s 时先在外部把 source 准备到平台 duration floor，再进入该工作流；
- 以上是 FIELD 生产工作流 + PLATFORM duration floor 的组合合同，不代表新增 Seedance provider 参数，也不适用于所有 `omni_reference` 任务。

完整 Prompt 约束见 `AI_VFX_PIPELINE.md`。
