# ACTIVE REFERENCE BUDGET｜V1.5

Budget is checked at two levels:

## EDIT SHOT working budget
Each `SH001...` uses only the visual image assets genuinely required by the current shot. There is no universal fixed per-SH image count in this runtime. `V001...` text voice assets do not count as visual media references.

## GENERATION UNIT model budget
When one or more SHs are packed into `GU001...`, deduplicate the active media-reference set and validate it against the current Seedance/model/project profile. Do not present an internal working budget as an official platform limit when the adapter does not define one.

`V001 / V002...` have `seedance_reference_slot_cost: 0`, never become `@图片/@视频/@音频`, and are excluded from all media-reference counts.
