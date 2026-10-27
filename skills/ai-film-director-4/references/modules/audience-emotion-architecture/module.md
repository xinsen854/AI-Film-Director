# Audience Emotion Compatibility Projection

`COMPATIBILITY_PROJECTION_ONLY`

## 职责

Forge AUDIT 是唯一情绪事实源。`state/audience_emotion_architecture.json` 仅保留给现有 AFD 下游接口读取，不再进行独立情绪设计，也不再拥有 HTML Renderer 权威。

兼容投影必须来自 `state/forge_locked_audit.json -> integration.afd.audience_emotion_compat_projection`，由 `compile_forge_handoff.py` 原样落盘。

禁止：

- 重新生成一套 0–10 情绪曲线；
- 从兼容投影反推 Forge phase；
- 用本 JSON 渲染 `AUDIENCE_EMOTION_MAP.html`；
- 把兼容投影与 Forge 情绪语义合成第三套模型。

正式可视化只读取 `references/forge/emotion-renderer.md`。
