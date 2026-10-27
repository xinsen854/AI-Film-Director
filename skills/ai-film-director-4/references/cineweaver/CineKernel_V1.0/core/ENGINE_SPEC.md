# CineKernel V1.0 — Engine Specification
**状态：FROZEN**

CineKernel 由三个底层引擎组成。它们不是三个独立 Skill，而是同一个 AI Film Director 的基础层。

---

# A. ASSET INTELLIGENCE ENGINE
## 目标
用最少资产实现足够的一致性与空间覆盖。

## A1｜ASSET_NECESSITY_GATE
任何资产生成前先判断：
1. 是否跨多个镜头重复出现？
2. 是否影响身份识别？
3. 是否影响连续性？
4. 模型是否容易混淆？
5. 后续是否会反复调用？

风险不足 → 不生成独立资产。

## A2｜CHARACTER_IDENTITY_MASTER
负责“这个人是谁”：
- 年龄/体型/脸部核心身份
- 发型
- 基础服装
- 关键可识别标志

不负责：
- 当前情绪
- 当前表演
- 当前摄影
- 当前场景光线

## A3｜VISUAL_STATE_ASSET
仅当视觉变化具有持续性或高连续性风险时派生：
- 受伤
- 血迹
- 湿身
- 换装
- 年龄阶段
- 妆容重大变化

## A4｜LOCATION_IDENTITY / LOCATION_STATE
Location 负责：
- 建筑
- 材质
- 地标
- 空间关系
- 基础光线逻辑

昼/夜/雨等持续性差异可拆 Location State。

## A5｜PROP_IDENTITY / PROP_STATE
关键道具可根据剧情需要派生：
- 完整
- 损坏
- 隐藏
- 污损
- 血迹
- 局部展示

## A6｜SPATIAL_ASSET_COVERAGE
先看未来 Shot Plan，再判断地点资产角度是否足够。

优先：
- 3/4 视角
- 可读深度
- 稳定 Anchor
- 必要 reverse view

不默认生产 360° 全套。

## A7｜REFERENCE_ROLE_BINDING
每个资产必须知道自己负责什么。

## A8｜NON_DESTRUCTIVE_ASSET_LINEAGE
Master → 独立 State 分叉。
局部改动优先局部编辑，不整体重绘。

## A9｜ASSET_STRESS_TEST_BY_RISK
测试强度随资产重要度变化：
- Low：普通配角/一次性资产
- Medium：重复出现角色/地点
- High：主角/核心地点/多人同框关键角色

不是所有资产机械执行固定“10次测试”。

---

# B. PERFORMANCE ENGINE
## 目标
让人物“在压力下行动”，而不是“展示情绪”。

## B1｜DRAMATIC_INTENT
- Objective
- Obstacle
- Stakes
- Hidden truth

## B2｜TACTICAL_FLOW
- Current tactic
- Tactic failure
- Tactic shift
- Beat change
- Power shift

## B3｜VISIBLE_PERFORMANCE
可按需要调用：
- Listening
- Reaction
- Eye life
- Breath
- Pause
- Speech rhythm
- Micro-expression
- Physical business

## B4｜RELATIONSHIP_BEHAVIOR
- Distance / proxemics
- Approach / retreat
- Touch
- Eye contact
- Body orientation
- Status
- Spatial dominance

## B5｜CHARACTER_PERFORMANCE_IDENTITY
角色跨场保持稳定的：
- 身体重心
- 行动节奏
- 习惯动作
- 目光方式
- 压力反应
- 声音身份
- 面具与破绽

## B6｜SHOT_ADAPTATION
只把当前镜头需要的表演行为编入 Prompt。
角色主档案不能整段机械粘贴。

---

# C. GENERATION ENGINE
## 目标
把导演意图转成当前模型可执行的镜头控制信号，同时尽量不挤压创造空间。

## C1｜CONTEXT_ISOLATION
当前镜头封闭。

## C2｜REFERENCE_HIERARCHY
身份 > 空间 > 道具 > 风格。
Style 不覆盖 Identity / Space / Action。

## C3｜SPATIAL_MAP
复杂空间才启用。
描述：
- 关键地标
- 人物相对位置
- 摄影机侧
- 移动路径
- 深度关系

## C4｜AXIS / GAZE / BODY
关系重要时分别控制：
- 身体方向
- 头部方向
- 眼睛方向
- 180°轴线
- screen direction

## C5｜FIRST_FRAME_CONTROL
默认 OFF。
仅在：
- 开场空镜误触发风险高
- 人物延迟出现风险高
- 多人位置容易错
时启用。

它是“生成风险规则”，不是“电影语言规则”。

## C6｜FORMAT_DECISION
默认优先单连续镜头。
只有剧情/表演/空间/信息需要时才拆为 controlled multi-shot。

## C7｜OPTICAL_INTENT
总导演层表达“光学结果”，Model Profile 决定用：
- mm
- FOV
- 其他模型专属语言

## C8｜CAMERA_BEHAVIOR
描述摄影机“如何存在”：
- 稳定
- 低干预
- 呼吸感 handheld
- 跟随
- 推近
- 观察
- 静止

## C9｜ACTION_CAPACITY / TIMING
判断动作是否塞得进镜头时长。
复杂镜头才拆 time blocks。

## C10｜PHYSICAL_CAUSALITY
按原因—受力—响应—结果描述关键动作。

## C11｜LIGHT_DIRECTION
只有光线方向关系到镜头成立时才强锁。
普通美感不做硬约束。

## C12｜DIALOGUE_CONTROL
硬锁：
- 台词内容
- 谁说
- 是否允许画外音
- 是否允许临场加词

表演语气属于 Performance Engine。

## C13｜AUDIO
维持必要环境声、对白清晰度和跨镜空间连续性。

## C14｜RISK_DIAGNOSIS
先诊断：
- 身份漂移
- 空间换位
- 轴线错误
- 道具错手
- 动作过载
- 物理漂浮
- 镜头错误开场
- 对白错时
- 灯光跑偏
- 多镜 continuity reset

## C15｜LOCAL_CONSTRAINT
只在风险点旁边加局部锁。
不默认使用巨大 Negative Block。

## C16｜PROMPT_DENSITY_CONTROL
高密度：
- 身份
- 空间
- 关键动作
- 表演关键点
- 物理因果
- 对白
- 已知失败点

低密度：
- 普通美感
- 非关键背景
- 已知参考图中已清晰的细节

## C17｜SILENT_QA
输出前内部检查，不把 QA 文本污染最终 Prompt。

---

# 三引擎协作顺序
```text
ASSET ENGINE
确认“有哪些可靠资产”
        ↓
PERFORMANCE ENGINE
确认“人物为什么这样行动”
        ↓
GENERATION ENGINE
确认“这条镜头怎么交给模型执行”
```

共同受最高原则：
**MINIMUM NECESSARY CONTROL**
