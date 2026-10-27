# 离线 HTML 诊断报告契约

## 触发与边界

仅在用户明确要求 HTML、网页报告、可视化诊断或科技感情绪报告时生成。先完成正常诊断，再把同一诊断数据交给渲染器。HTML 是展示副本，不是新的分析阶段；不得新增事实、断点、评分、人物心理、修复方向或确定性，也不得连接 AFD、分镜或制作流程。

## 单一数据源

将诊断整理为一个 UTF-8 JSON 对象。允许字段为空数组，但不要为了填满版面制造条目：

```json
{
  "meta": {"title": "项目名｜情绪诊断", "precision": "OUTLINE_COARSE", "mode": "diagnosis-only", "summary": "有证据的总判断"},
  "characters": [{"name": "人物", "role": "关系位置", "state": "当前状态或UNKNOWN", "want": "目标", "pressure": "压力", "observable": "可观察行为", "relationship_shift": "位移或UNKNOWN", "confidence": "high|medium|low"}],
  "audience_path": [{"label": "节点", "effect": "可能体验", "basis": "证据位置", "confidence": "high|medium|low", "intensity": 60}],
  "relationship_shifts": [{"from": "A", "to": "B", "kind": "关系机制", "status": "SUPPORTED|INFERRED|UNKNOWN", "basis": "证据位置"}],
  "breakpoints": [{"code": "E03或PENDING_E03", "title": "标题", "severity": "high|medium|low|pending", "confidence": "high|medium|low", "source": "证据或缺口", "effect": "可能效应", "counter_reading": "替代解释", "activation_condition": "待验证项升级条件"}],
  "unknowns": ["证据缺口"],
  "directions": [{"type": "PRESERVE|OBSERVE|VALIDATE|REPAIR", "title": "方向", "changes": "none或功能级改变", "basis": "证据", "risk": "风险", "canon_impact": "none|low|medium|high|REQUIRES_APPROVAL"}]
}
```

`audience_path[].intensity` 可省略。只有定量位置确实帮助阅读，并且文本已说明它是分析者的辅助序位时才使用 0—100；它不是客观情绪测量，也不能替代压力、信息、选择、后果和重估的因果说明。没有强度证据时省略，模板会显示顺序路径而非伪造高低曲线。

## 生成方式

使用技能内置渲染器：

```bash
python3 scripts/render_emotion_report.py diagnosis.json emotion-report.html
```

渲染器使用 `assets/emotion-report-template.html`，生成单文件、响应式、可打印的深色科技风报告。它不依赖外部字体、脚本、图片、CDN 或网络请求；用户文本通过 DOM 文本节点显示，不作为 HTML 执行。

## 内容对应

生成前后核对：

- 人物数量、名称和称谓与诊断一致；
- 观众节点、关系位移、正式断点、`PENDING_*`、未知项和方向逐项对应；
- 空节显示“暂无有证据支持的条目”，不自动补齐；
- HTML 中的严重度、置信度和设定影响不高于文本诊断；
- 科技感来自排版、颜色、信息层级和交互展示，不来自虚构数据或机械评分。
