# Runtime State Migration Contract

目标：旧项目续作时，不允许旧权威结构、未知Schema或半新半旧状态静默混入当前2.0单一权威运行链。

## 当前运行状态合同

```text
runtime_state_version = 2.0
authority_profile = AFD_CW_SINGLE_AUTHORITY
```

新项目由 `scripts/init_runtime.py` 自动写入：

```text
state/runtime_contract.json
state/pipeline_state.json.runtime_state_version
```

## 旧项目处理

续作旧项目之前先执行：

```bash
python scripts/migrate_project_state.py --project-root <project_root>
```

只允许自动迁移一种情况：项目文件结构已经符合当前2.0单一权威，只是缺少运行版本标记。迁移只补版本状态，并先备份原 `pipeline_state.json`；不得改写既有剧本、导演稿、资产、Storyboard、Ledger或Coverage。

Master+Forge 融合版还要求 `state/master_orchestrator.json`。已经声明2.0运行合同但缺少该文件时，必须返回 `MIGRATION_BLOCKED`；不得自动伪造 Forge DESIGN、锁稿或 AUDIT 状态。

以下情况必须阻断，禁止猜测迁移：

- 检测到旧 `assets/asset_registry.json` / `state/asset_registry.json`；
- 检测到旧 `state/storyboard/` 或独立 `prompts/` 运行产物；
- `PRODUCTION_LEDGER.json` 或 `state/STORY_COVERAGE_LEDGER.json` 使用未知Schema版本；
- 当前 `runtime_contract.json` 已声明2.0，但 `pipeline_state` 缺少或使用不同版本；
- 当前2.0项目中重新出现旧权威运行产物。

阻断只阻止继续生产，不自动删除或覆盖旧项目文件。
