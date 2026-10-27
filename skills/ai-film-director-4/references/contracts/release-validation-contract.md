# Release Validation Contract

适用于 **AI Film Director 4.7.1 Fusion**。

正式发布前只执行工程验收，不参与创作：

1. Python运行时要求`>=3.10`；运行代码只使用标准库，回归测试依赖由`requirements-test.txt`声明`pytest`、`Pillow`和`PyYAML`；
2. 缺少测试依赖时必须给出`python -m pip install -r requirements-test.txt`，不得只抛出collection error；
3. 禁止 `__pycache__`、`.pytest_cache`、`.pyc` 进入包；
4. `MANIFEST.sha256` 必须与全部发布文件一致；
5. 单卡结构、Manifest声明版本与实际引擎目录必须通过 `validate_skill_package.py`；
6. `scripts/` 与 `tests/` 下全部 Python 必须可编译；
7. `tests/` 为正式回归测试集，发布门必须完整运行；
8. 最终 ZIP 必须用 `verify_release.py --zip-file <zip>` 全新解压后再次执行同一套检查。
9. 4.7.1 必须包含 `references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json` 与 `scripts/model_preflight.py`；模型表面事实必须是 source-dated，未知能力不得由模型名称推断；
10. Asset Engine / Asset Production 必须显式引用 `references/contracts/asset-prompt-contract.md`，保证人物基础资产板合同进入真实执行链；

11. 4.7.1 production baseline must include the existing-authority integrations, not parallel owners: **Size-ref**, **Scene GEO** lock, structured **Reference Role**, **Acting** delta, optional **FACS** precision, **AI-VFX** model lanes, short-lived **Off-screen** carry, and non-blocking **Monotony** audit;
12. `Video API` / direct generation runtime remains **NOT ACTIVE** in this Skill release. No Generation Run / Take Review / Accepted Footage runtime may be claimed as executed capability;
13. Monotony Audit is WARNING-only. Off-screen carry is optional and local to existing `next_shot_handoff`; neither may become a new story/director/continuity authority.
14. 4.7.1 Project-Film release必须包含并登记 `PROJECT_SCOPE`、Production Unit Packet Builder/Validator、Project Asset Requirements/Baseline 与 Project Hard QC；这些必须接入真实运行链，不能只留下Schema/文档。
15. `execution_mode` 与 `production_scope` 必须独立：只有 `FULL + PROJECT` 可以进入正式项目完成声明与八件套导出；`FULL + UNIT`、PILOT、任何 QUICK 均不得冒充项目完成。
16. Project Scope 是锁稿Scene全集的 expected truth；Forge/Story Authority/Packet/Storyboard/Project QC 不得从自己的局部输出反向定义全集。
17. Project电影只有 `planned_units == completed_units`、Ledger连续覆盖确认总时长、Scene/Story Atom全集覆盖、Project Asset Baseline Lock有效时才可进入正式项目PASS/EXPORTS；空集合不得PASS。
18. 4.7.1 Hotfix 必须保留 `EP01/SC01` 与 `PU001/SC001` 的输入编号宽度，不得把三位编号截成两位，也不得把旧两位编号强制扩成三位。
19. 已完成 Film/Series 单元再次 checkpoint 时，必须先按当前 Storyboard/Story Authority 重新生成并验证 Story Coverage；存在 BLOCKING 时不得仅因历史 completed 状态而成功返回。
20. Owner Layer 复跑时，`current_unit_id` 只能从 `planned_units ∩ affected_ids` 恢复；Scene/Asset ID 不得污染当前生产单元，多个受影响PU按计划顺序恢复最早单元。

发布命令：

```bash
python -m pip install -r requirements-test.txt
python scripts/verify_release.py --skill-root <skill_root>
python scripts/verify_release.py --zip-file <release.zip>
```

发布验证不得修改导演、资产、分镜、Prompt或任何创作结果。
