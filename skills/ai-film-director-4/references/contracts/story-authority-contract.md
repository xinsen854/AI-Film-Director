# Story Authority Contract

## 目的

让导演、资产、分镜和Prompt都能自由发挥专业能力，同时不会在不知不觉中把故事改掉。

## 进入权威层前的证据边界

`SOURCE_FACT` 可以进入Immutable Story Facts。`SAFE_INFERENCE` 只能作为解释性证据，除非用户确认或后续剧情明确证明，否则不能升级为Story Authority。`CREATIVE_DESIGN` 可以进入美术/资产制作Canon，但不能反向改写剧情事实。

## 三类事实

### 1. Immutable Story Facts

当前生产阶段不可被下游改变：

- 已发生事件；
- 事件结果；
- 人物已经做出的决定；
- 对白核心意义；
- 关键物件/证据是否已经出现；
- 谁知道什么；
- 观众是否已经知道/怀疑；
- 计划揭露顺序；
- 世界规则对当前剧情的约束；
- 当 `source_maturity=screenplay` 时，用户原剧本正式动作、逐字对白及其先后关系（除非剧本审查已明确授权具体修改）。

成熟剧本的合法改动必须写入 `SCRIPT_REVIEW.md` 的“已经合法处理的修改”，明确对应场景并引用受影响原文；该授权只覆盖被明确指出的改动，不自动扩展成整场或整部剧本的重写权限。

### 2. Director-Expandable Facts

导演可以增加但不能改变上层意义：

- 沉默；
- 呼吸；
- 视线；
- 微表情；
- 手部动作；
- 人物在合理范围内的走位；
- 对对白的节奏/重音处理；
- 环境互动；
- 不改变结果的过程细节。

### 3. Production Decisions

由导演/分镜自由决定：

- 景别；
- 摄影机位置；
- 焦段倾向；
- 构图；
- 运镜；
- Coverage；
- 剪辑；
- 光线细节；
- 声音组织。

但必须服从空间、信息和持续状态。

## 故事原子覆盖

一个重要故事原子可以：

- 由一个SHOT完整覆盖；
- 被多个SHOT分担；
- 通过画外声音+画面反应共同覆盖。

最终应能追踪：

`story atom → director beat → SHOT → final video prompt`

如果一个必须视觉覆盖的故事原子在最终分镜里没有任何对应，应视为生产缺失。


## Reveal Stage合同

每个重要信息除了认知 `status` 外，还记录当前允许展示程度：`OFFSCREEN / LATENT / PARTIAL / READABLE / EMPHASIZED / PAYOFF`。下游Visibility/Geometry只能在该级别以内执行。Reveal Stage不是摄影机自由发挥项；如果需要从PARTIAL升级到READABLE，必须先由Story Authority在正确剧情节点更新。
