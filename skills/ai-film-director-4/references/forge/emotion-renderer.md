# Forge Emotion Renderer｜正式 05 唯一渲染权威

**INTERNAL_MODULE_ONLY**。

正式情绪图只允许从：

```text
state/forge_locked_audit.json
```

生成。运行：

```bash
python scripts/render_emotion_map.py \
  <project_root>/state/forge_locked_audit.json \
  <project_root>/AUDIENCE_EMOTION_MAP.html
```

该脚本直接来自 Forge v1.1.4 `emotion-story-forge/scripts/render_emotion_map.py`；模板直接来自 Forge `assets/emotion-map-template.html`。

正式 HTML 的主视觉契约必须是 Forge：

- 全剧情情绪总谱；
- Character / Audience emotion rivers；
- `Audience Time / Story Time` 双时间轴；
- adaptive `phase_events`；
- CHARACTER + AUDIENCE EMOTION FIELD；
- 人物独立质点云；
- AUDIENCE HALO；
- phase topology；
- evidence / causal / relationship / breakpoint 层。

AFD `state/audience_emotion_architecture.json` 只做兼容投影，严禁拿它生成正式 05。
