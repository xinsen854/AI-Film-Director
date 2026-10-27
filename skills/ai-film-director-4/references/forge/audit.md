# Forge AUDIT｜锁稿后故事与情绪事实审计

**INTERNAL_MODULE_ONLY**。只有 `state/master_orchestrator.json.lock_status=LOCKED` 且锁定剧本文件 SHA256 仍与 Master 记录一致时才允许执行。

完整读取：
- `state/master_orchestrator.json` 中 `locked_screenplay_path + locked_screenplay_sha256`；
- `references/forge/source/emotion-narrative-engine/source_skill.md` 的 AUDIT 契约；
- `references/forge/source/emotion-narrative-engine/references/adaptive-emotion-state-model.md`；
- Forge blueprint；
- 当前 LOCKED SCREENPLAY；
- 当前 Continuation Ledger。

## 唯一权威

Forge AUDIT 是：
- 锁稿后的故事证据审计权威；
- 情绪语义唯一事实源；
- `phase_events / phase_links / audience_lenses / narrative_topology / global_emotional_arc` 唯一来源。

AFD 不得重新分析出第二套情绪模型。

## AFD integration namespace

除 Forge 原 locked-audit payload 外，必须由本次 AUDIT 的语义理解直接生成：

```json
{
  "integration": {
    "afd": {
      "unit_id": "EP01",
      "locked_screenplay_path": "lock_candidates/EP01.md",
      "script_version": "...",
      "script_review_markdown": "...",
      "story_authority": {},
      "information_ledger": {},
      "audience_emotion_compat_projection": {},
      "scene_handoffs": [
        {
          "scene_id": "SC01",
          "story_atom_refs": [],
          "information_refs": [],
          "must_be_perceptible": [],
          "must_remain_implicit": [],
          "must_not_be_revealed": [],
          "key_reaction_requests": [],
          "key_listener_or_third_party_response": [],
          "environmental_pressure_or_release": [],
          "important_object_or_space_evidence": [],
          "emotion_capacity_note": ""
        }
      ]
    }
  }
}
```

`audience_emotion_compat_projection` 只是旧 AFD 下游接口兼容状态，不是第二情绪权威，也不得用于正式 HTML。

完成后运行：

```bash
python scripts/compile_forge_handoff.py --project-root <project_root> --stage locked-audit --forge-json <locked-audit.json>
```
