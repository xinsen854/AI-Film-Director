---
name: shot-segment-engine
version: "1.3"
description: >
  Seedance-native storyboard execution engine. Restores the user-supplied V4.8
  storyboard structure as a hard EDIT SHOT contract, separates SH / GU / PH,
  and compiles detailed Seedance prompts without summary collapse.
---

# SHOT / SEGMENT Engine V1.3｜V4.8 Strong Lock + Seedance

## Role
Produce one authoritative `STORYBOARD.md` with:
1. `SH001...` — real EDIT SHOT cards using the V4.8-derived hard template;
2. `GU001...` — one Seedance/model invocation;
3. `PH01...` — state phases inside the final Seedance prompt, not editorial cuts.

# Generation capacity serves film grammar; film grammar never serves generation capacity.

## Inputs
- integrated director screenplay;
- asset library with A/S/P/G/ST visual records and V-series text voice records;
- optional Spatial Narrative current-shot handoff;
- continuity state;
- `generation_packing_policy: 15S | 30S_BLOCK | AUTO`;
- `target_video_model: SEEDANCE_2_5 | SEEDANCE_2_0 | OTHER`.

Non-diegetic analysis artifacts are not storyboard inputs: emotion-map HTML/UI, diagnostic labels, module/Skill names, renderer labels and delivery filenames must not become SH/GU/PH content unless the integrated director screenplay itself contains them as locked story material with Story Authority evidence.

## V4.8 EDIT SHOT hard contract
When applicable each SH must preserve these sections:
`【来源】 【镜头功能】 【镜头类型】 【基础画面】 【摄影参数】 【轴线与视线】 【资产调用】 【空间与站位】 【连续画面】 【首尾帧锚点】 【关键微反应】 【对白执行】 【声音】 【剪辑接口】 【连续性锁】 【下一镜衔接】`.

Do not compress these into a one-line summary when the section contains production-relevant facts.

## IDs
- visual/media assets: `A001 / B001 / G001 / P001 / S001`;
- persistent state: `A001-ST001` etc.;
- voice text: `V001`;
- EDIT SHOT: `SH001`;
- Generation Unit: `GU001`;
- prompt phase: `PH01`.

## EDIT SHOT duration
Narratively free: 2.5s, 3s, 6s, 8s, 9s, 13s, etc. Do not round to 15/30 seconds. Each SH should record a concise `duration_basis` from action, dialogue, performance, reaction, suspense, or edit rhythm. Random numbers and model-window values are not dramatic evidence.

The timing contract is: total runtime follows the confirmed user brief; SH duration follows story and edit grammar; GU duration follows the active model ceiling. `15S` and `30S_BLOCK` mean maximum organization windows, never “make every SH/GU exactly 15/30 seconds.”

## Model Adapter
- Seedance 2.5: one GU ≤30s;
- Seedance 2.0: one GU ≤15s;
- OTHER: require an explicit adapter/profile before assuming limits.

## Packing policy
- `15S`: organize GUs up to 15s; unused capacity is valid.
- `30S_BLOCK`: use at most 30s and also obey a smaller active model window; it never requires filling 30s. A multi-SH GU is allowed only when the current model/platform profile explicitly confirms `model_supports_multi_shot=true`.
- `AUTO`: isolate by default; pack multiple SH only when `model_supports_multi_shot=true` and performance, dialogue, space, physics and continuity risk are also acceptable.
- `unknown`, missing or false MULTI_SHOT capability never becomes permission by inference.

Important micro-performance, exact dialogue/lipsync, complex physics, key reveal/payoff, precise camera path, or high-continuity-risk SH may remain isolated with unused capacity.

## Reference budget
- EDIT SHOT只调用当前镜头真正必要的视觉图片资产；不设置全局固定数量上限，V系列不计入视觉媒体参考。
- After SHs are packed into a GU, deduplicate active media references and verify the GU against the current model/project profile; model/project adapter is the only source of any concrete media-capacity limit.
- `V001...` is text-only, has zero reference-slot cost, and never becomes `@图片/@视频/@音频`.

## Final Seedance Prompt
Every GU compiles to this fixed order:
1. `【生成目标】`
2. `【参考素材职责】`
3. `【初始状态】`
4. `【阶段推进】` with `PH01 / PH02 / ...`
5. `【关键时间锚点｜可选】`
6. `【声音】`
7. `【保持一致】`
8. `【局部限制】`

Default is **PHASE-first, not a full second-by-second timeline**. Exact time anchors are exceptional and used only when execution depends on them.

The final prompt must be detailed enough to execute directly. CineWeaver imposes no fixed character ceiling; a complex 30s prompt may exceed 5000 Chinese characters. Remove redundancy, never execution signal.

## Voice
V-series defines stable voice identity in text. Current SH/GU defines line delivery. V-series is injected only under `【声音】`, does not generate a voice file, and does not count as material/reference quantity.

## Output
Exactly one `STORYBOARD.md` containing complete SH cards, GU plan, and one direct Seedance prompt per GU.


## Model-scoped failure prevention
在模型 Prompt 编译与直接执行 QA 时读取 `runtime/FAILURE_PREVENTION.md`；只按证据强度和当前模型 profile 使用，不建立新 Owner。
