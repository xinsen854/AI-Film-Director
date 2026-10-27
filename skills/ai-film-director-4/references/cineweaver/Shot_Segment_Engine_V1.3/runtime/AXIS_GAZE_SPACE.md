# AXIS / GAZE / SPACE

Track only spatial facts needed for continuity and readability.

For each SHOT identify when relevant:
- axis line,
- camera side,
- screen direction,
- character positions,
- foreground/midground/background relation,
- gaze target and gaze-line continuity,
- body orientation,
- landmark anchors,
- approach/retreat path.

Crossing an axis requires an intentional transition or a new spatial logic. Do not let a reference image dictate camera geography by accident.


## Scene GEO 与镜头空间的边界

`scene_geo_lock_ref / scene_geo_sha256` 只锁定 S 场景资产的稳定几何。它**不锁定 `camera_side`、人物位置、movement_path、构图或镜头尺寸**。合法的机位变化、人物走位和经批准的越轴继续由本文件现有规则判断；不得因为 GEO Lock 把动态镜头设计冻结成固定平面图。
