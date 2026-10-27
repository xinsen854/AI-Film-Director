# PROMPT QC｜V1.5 Current-GU + Content Quality

## Model surface preflight

在最终视频 Prompt 进入交付前，若项目已选定受支持的 model surface profile，应运行：

```bash
python scripts/model_preflight.py --profile <PROFILE_ID> --request-json <REQUEST_JSON>
```

该脚本只检查可机械证明的模型表面事实：duration / resolution / aspect ratio / mode / media role 与 mode-specific 参数冲突。它不调用 Provider，不把经验性导演规则提升为全局硬规则。`FAIL` 阻断对应 GU 的模型执行合同；`WARN/INFO` 只作提示。

最终交付的 preflight `REQUEST_JSON` **必须包含 `prompt_text`**（当前 GU 的最终视频 Prompt），使模型专属 Prompt heuristic 能参与审计。当前实现会扫描 AU/FACS notation：若 AU 文本出现在未验证支持该 heuristic 的模型 profile 上，返回 `WARN / FACS_UNVERIFIED_PROFILE`。这不是硬阻断；应回退为同一 Beat 的解剖/可观察行为，或先补充该模型的验证证据。省略 `prompt_text` 会绕过这一类 Prompt-dialect 检查，因此不属于完整 Final Prompt QC。

## BLOCKER/ERROR gates
- `SEEDANCE_PROMPT_STRUCTURE`: non-trivial GU missing required sections: 生成目标 / 参考素材职责 / 初始状态 / 阶段推进 / 声音 / 保持一致 / 局部限制.
- `SUMMARY_COLLAPSE`: final prompt reduces an information-rich storyboard to a synopsis and drops execution-relevant camera, blocking, micro-performance, dialogue, sound, prop state, continuity, first/last-frame or reference-role facts.
- `FIELD_BOILERPLATE`: a required storyboard/Prompt field is present but mainly contains template language rather than current-shot **具体事实 / 可观察 / 可执行** content. Typical invalid examples include `当前动作中只锁定...`, `按资产库与连续性锁执行`, or a bare `保持克制` without observable behavior.
- `GLOBAL_PROMPT_POLLUTION`: current GU contains unrelated **未来事件 / 无关资产 / 无关声音 / 全局连续性** copied from other scenes or the project ledger.
- `REFERENCE_BINDING_FAILURE`: active media is referenced only by internal shorthand such as `A001 identity` / `使用A001锁定身份`, an `@图片/@视频` role is missing, or a nonexistent media file is presented as a real Seedance reference.
- `VOICE_MEDIA_LEAK`: V001/V-series compiled as @图片/@视频/@音频, given a media file, or counted as a Seedance media reference.
- `MODEL_WINDOW`: GU duration exceeds active adapter: Seedance 2.5 >30s; Seedance 2.0 >15s; OTHER without known adapter limit is blocked.
- locked dialogue mismatch.
- stale shorthand such as 同上 / 继承上一镜 / same as before / as above.

## CURRENT_GU_ONLY audit
For every GU, compare prompt facts against its Member SHs and active assets:
- `【参考素材职责】`: only current uploaded media;
- `【初始状态】`: only first-frame facts of current GU;
- `【阶段推进】`: only actions/performance/dialogue within current GU;
- `【关键时间锚点】`: only current execution-critical timing; omit if none;
- `【声音】`: only current location/action/speakers;
- `【保持一致】`: only continuity required inside current GU;
- `【局部限制】`: only current high-risk failure modes.

Any repeated project-wide bundle of hospital time, future vehicle state, future reveal, unrelated prop, unrelated location sound, or other non-current fact is `GLOBAL_PROMPT_POLLUTION`.

## Reference fallback audit
If a required visual subject has **缺少图片参考**:
- prompt must not fabricate `@图片X`;
- use current-GU **文字视觉身份** from Asset Library when sufficient;
- if project identity requirements cannot be met without an image, surface missing asset instead of pretending consistency.

## Timing
Default PHASE-first. Full second-by-second timelines are not required and must not be added mechanically. Critical time anchors are allowed only when execution depends on them.

## Prompt density
No fixed minimum or maximum character count. A 30s prompt may exceed 5000 Chinese characters. QC evaluates **execution-fact coverage**, not raw length.

## Reference transfer metadata audit

- 结构化 reference binding 若提供 `inherits[] / excludes[]`，Final Prompt 必须保持同一职责边界；不得在渲染时把被排除内容重新写回。
- `fidelity` 只属于内部 Prompt 元数据，**不是 provider 参数**；发现它进入 Higgsfield/Seedance 参数表时按 `REFERENCE_BINDING_FAILURE` 处理。
- `attribute-transfer` 缺少明确 target 时视为职责不完整。


## Failure-prevention guidance boundary
读取 Shot/Segment `runtime/FAILURE_PREVENTION.md` 只用于当前GU风险检查；**不新增 Owner**，不把 `FIELD_HEURISTIC` 自动提升为全局硬错误。平台可机械证明的冲突仍交给 `model_preflight.py`。

## AI-VFX Plate Transform audit｜仅在该工作流启用时

若当前 GU 明确采用 `vfx_plate_transform`，Final Prompt QC 必须把该对象连同 `prompt_text` 一起送入 model preflight；省略 `vfx_plate_transform` 会绕过 Plate Transform 的 route / source-duration / video-master 检查，因此不能声称完成该工作流的模型预检。

除此之外还要做语义检查，不能只看参数 PASS：

- Seedance 2.5 Plate Transform 必须走 `omni_reference` 的 source-video master 路由；普通 scoped edit 才使用 `video_edit`；
- `【参考素材职责】` 必须明确 source master 的 camera / framing / focus / motion-performance timing / background / lighting / grain-compression / prepared duration 继承职责，以及当前允许编辑的 subject / element；
- preserve contract 必须继续服从 `CURRENT_GU_ONLY`，不得用“保持全部一致”掩盖未定义的 edit scope，也不得把全项目事实批量塞入当前 GU；
- source 缺关键 motion anchor 时，不得靠新增剧情或凭空动作绕过，应返回 VFX workflow 的 source 准备 / I2V fallback 判断。

上述 source-master/preserve 检查属于当前 VFX 工作流语义 QC，不创建第二个 VFX Owner，也不把 FIELD 路由升级成所有模型的全局规则。

### Seedance 2.0 preservation-VFX lane

当 `vfx_plate_transform` 绑定 Seedance 2.0 profile 时，Final QC 应验证 source plate 的 `video_references` master 与 `mode=std` 路由；4K 仅作为公开 FIELD 的质量推荐，非 4K 返回质量 WARN 而不是把该 GU 判为平台非法。不得把 2.5 的 `omni_reference + source>=4s + duration==source` 合同机械套给 2.0。
