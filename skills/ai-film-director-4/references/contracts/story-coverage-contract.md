# Story Coverage Contract

本合同只负责证明锁定故事有没有真正进入正式SH/GU，不参与导演创作，也不改变CineWeaver分镜权威。

每个结构化SH允许增加一个**内部机器字段** `coverage`，Renderer不向用户展示：

```json
{
  "coverage": {
    "story_atom_ids": ["ST001", "ST002"],
    "revealed_info_ids": ["I001"]
  }
}
```

- `story_atom_ids`：当前SH真实覆盖的Story Authority锁定原子；不能为了通过检查虚挂。
- 锁定对白原子除挂载ID外，逐字对白还必须真实进入SH `dialogue_execution` 与所属GU Phase的 `dialogue_execution`。
- `revealed_info_ids`：只在当前SH真实完成该信息的正式Reveal时填写；未揭露不得提前标记。
- `protected_literals` 在计划Reveal之前不得以画面、对白、Prompt或负面限制中的精确原文出现。

Coverage类别包括：剧情原子、场景、关键动作、关键对白、信息揭示、Reveal、伏笔和回收。每项必须具有唯一`coverage_id`、内容、所属单元/场景、证据SH/GU及生产状态：

- `UNCOVERED`：尚未进入任何正式分镜；
- `PLANNED`：已进入结构化SH/GU，但生产单元未完成；
- `PRODUCED`：生产单元已完成，等待最终核销；
- `CONFIRMED`：对应单元通过Story Coverage校验并Checkpoint确认。

Checkpoint只核销当前生产单元；未到未来单元的剧情不会因为“尚未生产”而阻断当前Checkpoint。最终交付时再核销全项目。`state/STORY_COVERAGE_LEDGER.json`是机器权威，必须由`render_story_coverage.py`生成正式`STORY_COVERAGE_LEDGER.html`，HTML不是装饰性报告。

重复检查必须分析连续单元的`dramatic_engine`与`hook_structure`。只改人物、地点或台词表面措辞仍视为同一公式；只有后续存在明确的关系、信息、权力或风险推进，才允许作为有意motif重复。
