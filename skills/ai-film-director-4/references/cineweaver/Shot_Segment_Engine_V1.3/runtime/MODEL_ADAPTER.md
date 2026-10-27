# MODEL ADAPTER｜V1.6

## Model Surface Profile

AFD 的 Capability Router 仍是唯一能力路由 Owner；本层只消费 `references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json` 的 source-dated 模型事实，并映射到对应 dialect contract。

- `SEEDANCE_2_0` → `SEEDANCE_2_0_HIGGSFIELD` → `SEEDANCE_2_0_PROFILE.md`
- `SEEDANCE_2_5` → `SEEDANCE_2_5_HIGGSFIELD` → `SEEDANCE_2_5_PROFILE.md`
- `OTHER` → 必须有显式已验证 adapter facts

模型名、版本号、时长窗口或 `AUTO/30S_BLOCK` **都不能自动推断能力**。未知事实保持 unknown。

## MULTI_SHOT capability gate

- MULTI_SHOT support must be explicitly confirmed by the current model/platform/project profile before packing more than one EDIT SHOT into one GU.
- A model name, duration window, or `AUTO/30S_BLOCK` policy does **not** imply MULTI_SHOT support.
- `unknown`, missing, or explicitly unsupported capability means use an isolated/single-SH GU instead of guessing.

## SEEDANCE_2_5

读取 `SEEDANCE_2_5_PROFILE.md`。先确定 `t2v / omni_reference / video_edit / video_extension`，再编译 Prompt；不得把 2.0 的 start/end-image 或 4K 能力套到 2.5。

## SEEDANCE_2_0

读取 `SEEDANCE_2_0_PROFILE.md`。保留 2.0 自己的 `std / fast`、start/end-frame 和分辨率表面；不得把 2.5 mode router 套到 2.0。

## OTHER

- requires explicit model_name and adapter facts
- if max duration, mode, resolution or reference behavior is unknown, mark execution BLOCKED instead of inventing a limit
