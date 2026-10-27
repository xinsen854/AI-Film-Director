# Failure Prevention｜Model-Scoped Guidance

本文件用于**生成前预防**，不新增 Owner，不替代 Final QC，也不得把经验性规则提升为 AFD 全局硬规则。

## 证据强度

- `PLATFORM`：来自当前已锁定的平台模型表面事实；可做机械 preflight。
- `MODEL_DIALECT`：来自具体 Seedance dialect / 生产规则；只在对应模型 profile 中使用。
- `FIELD_HEURISTIC`：公开生产案例与经验总结；用于风险提示和 Prompt 修正，不自动形成全局 BLOCKER。

## P0 prevention set

### 1. source/keyframe absence
`MODEL_DIALECT`

如果当前 source/keyframe 没有某个必须在本 GU 首次出现的元素，Prompt 要明确这是**新增元素**，不要把“来源中不存在”误写成“来源已经包含”。缺失结构无法由 Reference Role 自动补齐时，优先回到资产/首帧准备，而不是堆更多形容词。

### 2. adjacent-object invariant
`FIELD_HEURISTIC`

相邻物体容易被模型当成一起运动。当前动作只移动其中一个物体时，写清 adjacent-object 不变量：谁移动、谁保持原位、接触关系何时结束。该规则是风险预防，不是所有镜头都必须填写的固定字段。

### 3. action reversal risk
`FIELD_HEURISTIC`

动作过早完成而片段仍有大量剩余时间时，模型可能用反向动作或无意义回摆填时间。让当前动作覆盖真实需要的时长，或给同方向的后续动作；若剧情动作已经完成，应缩短 GU，而不是机械填满模型窗口。

### 4. dominant camera motion
`MODEL_DIALECT`

优先一个 dominant camera motion。确有 compound move 时按阶段写清先后与 end state；不要把多个互相竞争的机位运动堆在同一时刻。是否拆 GU 仍由 Shot/Segment 的任务复杂度与模型 profile 决定。

### 5. spatial geometry
`MODEL_DIALECT`

门口进入、走廊方向、绕家具、多人物接近等 historically fragile 场景，应显式给出 spatial geometry：相机起点、关键 landmark、屏幕方向、移动路径。已有 Spatial Narrative / SH 空间字段时直接消费，不建立第二套空间系统。

### 6. completion endpoint
`FIELD_HEURISTIC`

当前 SH/GU 的关键动作要有可见 completion endpoint，例如“门完全闭合并稳定”“杯子落桌后静止”“手完全抓住把手”。若切点故意落在动作中途，应把这种中途状态作为明确 ending state，禁止让模型自行猜动作是否已经完成。

## Enforcement boundary

`PLATFORM` 事实由 `scripts/model_preflight.py` 机械检查；`MODEL_DIALECT` 与 `FIELD_HEURISTIC` 由 Prompt Compiler / Final QC 结合当前 GU 判断。除非另有可机械证明的 Validator，本文件内容不得升级为 AFD 全局硬规则。

### 7. VFX repeated-batch signal
`FIELD_HEURISTIC`

公开 AI-vs-VFX 案例里，同一 defect 在**四个 batch**持续重复，被用作“prompt 或 source 有系统性问题”的诊断信号。该数字保留来源语境，**不是 AFD 全局固定尝试次数 / global fixed attempt limit**：可以更早因强证据停下，也不能因为达到四次就忽略每次失败其实不同的情况。命中时优先检查 source 是否缺 motion anchor、Reference Role 是否冲突、preserve contract 是否过宽/过窄，再决定重写或改为 I2V fallback。
