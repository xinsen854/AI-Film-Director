# Seedance 2.0｜Higgsfield Surface Profile

本文件是 **Seedance 2.0 在 Higgsfield 表面的模型专属执行合同**。事实源为 `references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json`；不得把本文件规则提升为 AFD 全局导演规则。

## 已验证表面事实

- duration：`4–15s`
- resolution：`480p / 720p / 1080p / 4k`
- mode：`std / fast`
- aspect_ratio：`auto / 16:9 / 9:16 / 4:3 / 3:4 / 1:1 / 21:9`
- media roles：`start_image / end_image / image_references / video_references / audio_references`
- 约束：`fast` 不允许 `1080p / 4k`

## 执行边界

1. 模型名不自动证明 `MULTI_SHOT`；仍由当前平台/项目 profile 明确确认。
2. `start_image` / `end_image` 是 2.0 表面的真实媒体角色；只在真实媒体存在时使用，禁止伪造。
3. Reference 仍服从 AFD `CURRENT_GU_ONLY`：只绑定当前 GU 真正需要的媒体与职责。
4. 模型专属经验规则、反射/人群/动作等风险提示只在本 profile / failure-prevention 层生效，不得成为 AFD 全局硬规则。
5. 参数事实发生变化时先更新 source-dated model surface profile，再更新本文件；不得凭模型名字猜新能力。

## FACS prompt heuristic｜经验性，不是平台参数

OSideMedia 的 `higgsfield-facs` 将 FACS Action Unit 文本用于 Seedance 2.0 精细面部控制，但其来源明确标注为 **EMPIRICAL**：当前平台没有 FACS / expression provider 参数或 API 字段。AFD 因此只把它视为 Seedance 2.0 的可选 Prompt heuristic：close-up / hero performance 需要更精细的面部区分时可使用；不保证确定性，不强制所有镜头使用。若 AU notation 不稳定，回退为同一 Beat 的短解剖 / 可观察行为描述。

## Preservation-VFX / source plate lane｜Seedance 2.0

公开 `higgsfield-seedance-vfx` 将 Seedance 2.0 保留为独立的 **preservation-VFX** lane：真实 source clip 是 base，目标是保存原人物/表演/机位/镜头运动，只改变明确命名的元素或环境。

- VFX lane 使用 `mode=std`；不能把 Seedance 2.5 的 `omni_reference` 参数合同直接搬到 2.0；
- source plate 通过真实 `video_references` 进入当前 GU，Prompt 中作为 source master 明确 preserve/change 边界；
- `4k` 是平台真实可用分辨率，公开 FIELD / practitioner 工作流推荐 `std + 4K` 以提高脸、lip-sync 与细节保持；**“4K 更稳”是质量经验，不是 provider 的确定性保证，也不作为所有 2.0 任务的全局硬门**；
- source duration 默认按原片规划，但不同于 2.5 的已锁定 Plate Transform 工作流，本文件不把“必须完全等长”发明成 Seedance 2.0 全局硬规则；
- platform `start_image / end_image`、以及当前 surface 真实支持的其他参数仍服从 source-dated Model Surface Profile，不从 2.5 猜测。

具体 preserve / integration / fallback 见 `AI_VFX_PIPELINE.md`。

### Source runtime discipline

进入 preservation-VFX 时，source runtime 与当前 GU runtime 都必须已知，便于审计 source inheritance。公开 2.0 VFX 工作流**默认按 source runtime**；如果为了 payoff / intro 有意延长，允许偏离，但应作为显式质量 WARN 检查，而不是套用 2.5 的 `duration == source` 硬等式。
