# Human-Truth Screenwriter｜内部正式编剧模块

**INTERNAL_MODULE_ONLY**。只负责把 Forge DESIGN production packet 写成可拍剧本页，不接管导演、资产、分镜或最终交付。

读取：
- `references/forge/source/human-truth-screenwriter/source_skill.md`
- 当前 production packet 与事实边界
- `PROJECT_CREATIVE_BIBLE.md`
- 当前连续性/上一单元尾态

## 模式路由

必须服从 AFD `source_maturity` 与用户修改权限：

- `idea`：CREATE
- `outline`：CREATE / UPGRADE
- `treatment`：UPGRADE
- `screenplay + 已授权改写`：REWRITE
- `screenplay + 未授权改变正式动作/逐字对白`：PASS_THROUGH / 最小合法修复，保留成熟剧本原文锁
- `existing_project`：仅在授权范围内局部 REWRITE

不得因为 Forge 原独立 Writer 默认 UPGRADE 就覆盖 AFD 的成熟剧本保护。

输出当前单元的 **lock candidate** 与 `state_delta_candidate`，不得自行标记为 LOCKED。
