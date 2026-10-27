# Production Ledger Contract

## 目的

`PRODUCTION_LEDGER.json` 是长项目“到底做完多少、下一次从哪里继续”的唯一项目级生产账本。它只负责**交付覆盖与断点续作**，不评价导演创作。

## 最高硬规则

- 用户确认90分钟电影，最终必须覆盖完整 `0:00 → 90:00`。60分钟、80分钟都不能声明项目完成。
- 用户确认60集，最终必须存在并完成 `EP01 → EP60`。40/60、59/60都只能是 `IN_PROGRESS`。
- 每完成一个电影Production Unit或一集，必须立即写入账本和Tail State；不能等整个项目最后一次性保存。
- 任务因上下文、时间或宿主限制中断时，下一次从账本 `next_resume` 继续，不重新生产已完成单元。
- 账本是生产完整性硬约束，不参与镜头、美术、表演和节奏审美判断。

## 电影账本

核心字段：

```text
scope_type: film_timeline
target_runtime_seconds
film_units[]: unit_id / start_seconds / end_seconds / status
completed_units[]
coverage.covered_seconds
coverage.percentage
coverage.gaps[]
next_resume.start_seconds
status: IN_PROGRESS / COMPLETED
```

电影单元按真实时间线连续登记。当前单元必须从上一完整单元尾点继续；最终完成时最后一个单元必须收敛到已确认总时长。内部规划可调整场次和单元长短，但最终账本不能有未生产缺口，也不能用超长总时长冒充完成。

例如90分钟电影做到53:00：

```json
{
  "target_runtime_seconds": 5400,
  "coverage": {"covered_seconds": 3180, "percentage": 58.8889, "gaps": []},
  "next_resume": {"start_seconds": 3180},
  "status": "IN_PROGRESS"
}
```

下一次直接从53:00对应的下一自然戏剧单元继续。

## 剧集账本

核心字段：

```text
scope_type: episodes
target_episode_count
target_episode_runtime_seconds
episodes[]: episode_id / status / actual_runtime_seconds
completed_episodes[]
coverage.completed_count
coverage.percentage
next_resume.episode_id
status: IN_PROGRESS / COMPLETED
```

剧集必须按集号连续Checkpoint。做到EP40后中断：

```text
completed_episodes = EP01 ... EP40
next_resume.episode_id = EP41
status = IN_PROGRESS
```

不得重新从EP01开始，也不得跳过EP41继续EP42。

## 完成声明

只有以下条件满足才允许 `COMPLETED`：

### 电影
- 账本目标时长与已确认Brief完全一致；
- 从0秒到目标总时长连续覆盖；
- 无未解释生产缺口；
- 最后覆盖点等于目标总时长。

### 剧集
- 账本目标集数与Brief一致；
- EP01至目标集数全部完成且无缺集；
- `completed_episodes` 数量等于目标集数。

任何未达到上述条件的项目都必须保持 `IN_PROGRESS`，即使当前请求的单个生产单元已经成功交付。
