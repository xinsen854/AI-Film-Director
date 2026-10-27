# ASSET TAXONOMY

## Three-digit numbered families

### Visual / media-reference families
- `A001...` — core character
- `B001...` — recurring secondary character
- `G001...` — creature / entity / crowd / extra group
- `S001...` — location
- `P001...` — key prop

### Text-only voice family
- `V001...` — stable character voice identity, **TEXT_VOICE_ASSET**

V-series is never an image/video/audio reference in the current version and costs zero Seedance reference slots.

## Persistent state

Persistent state inherits a master visual asset and uses three-digit master IDs:
- `A002-ST001`
- `S008-ST001`
- `P003-ST001`

`ST001` denotes persistent state identity; it is not a free-standing master object.

## Default reference roles

- A / B: `identity`
- character STATE: `state`
- S: `location`
- P: `prop`
- G CROWD / EXTRA_GROUP: `crowd`
- G CREATURE / ENTITY: `identity`
- V: `voice_text` only; never `@图片/@视频/@音频`

## Supporting Scale Reference｜比例参考，不是新资产家族

`SCALE-...` 是已有 A/B/G/S/P 主资产之间的**生产辅助比例参考**，不是新的主资产编号家族，也不得建立 `scale_reference_assets` 平行资产库。

仅在**极端跨主体比例**会明显漂移、且文字/单一人体地标难以稳定表达时创建，例如人物与巨型生物、超大型机械与人物、悬殊尺度组合。普通近人体道具、栏杆、桌椅等不因“存在尺寸”就强制创建 Size-ref；可用可靠尺寸与经计算的人体地标表达时保持文字即可。不得为了套规则全局强制资产化。

保存位置：挂在一个现有视觉主资产的 `downstream_metadata.scale_reference` 下，`reference_id` 使用可追踪的 `SCALE-<subject...>`，并列出全部 `subject_asset_ids`。它只证明明确写入的 `relative_scale / mounting_position` 等比例事实；背景、灯光、调色、机位等是否排除由 `excludes[]` 明确声明，不把比例板当作场景或构图权威。

当比例参考尚未有真实图片时保持 `PROMPT_ONLY`，不得伪造 `@图片N`。标记 `GENERATED` 时，其文件与 SHA/宽高/MIME 等必须经过与其他视觉资产相同的真实媒体校验。
