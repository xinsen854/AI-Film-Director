# 跨集变化与重复风险扫描

## 目的

本扫描用于发现系列中“同一戏剧功能重复而没有状态增量”的风险。它是审计报告和返修提示，不是把相邻集强行改成不同模板的生成器。

## 扫描字段

为每集或场景包记录可追溯标签：

- `hook_source`：人物、任务、关系债、世界规则、信息差或其他来源；
- `pressure_source`：制度、资源、市场、天气、关系、信息、身份或现场条件；
- `defense_strategy`：回避、控制、跟风、讨好、程序化、过度解释、装轻松等；
- `choice_type`：追求、拒绝、延迟、转让责任、协作、承认或退出；
- `reveal_function`：重分类、暴露代价、改变关系、改变危险或只增加事实；
- `relationship_shift`：信任、权力、距离、承诺、债务或误读的变化；
- `ending_load`：下一集继承的关系张力、知识差、资源损失、制度变化、开放回路或选择压力；
- `motif_function`：本集道具、动作、空间或语言的具体新功能。

## 判断规则

1. 相邻集出现相同标签时，先检查是否有 `knowledge`、`leverage`、`cost`、`tactic`、`relationship` 或 `motif_meaning` 的实质增量。
2. 有增量时，记录为“重复中的升级/对照/回声”，保留结构可能性。
3. 无增量时，记录为 `REPETITION_RISK`，给出最小修复：改变承压者、策略、代价、信息位置、关系后果或合并重复单元。
4. 连续两集使用相同微结构不是自动错误；只有当冲突、选择和结尾状态也近似不变时，才升级为结构问题。
5. 同一笑点或母题再次出现时，必须说明它为何此刻意义不同；否则按“功能复用未升级”处理。

## Hook 溯源检查

短剧或高压系列的开集钩子必须能追溯到已建立的人物、关系、任务、世界规则或信息差。找不到来源时标为 `BARE_HOOK_RISK`，不直接要求增加危险或反派。

## Voice 检查

把爆点台词脱离人物名朗读。若它仍能由任何角色说出，检查是否缺少人物的防御策略、身份、关系目的或当场成本。公共口号、仪式语言和故意模仿可保留，但要在审计中说明其剧情功能；不设金句数量配额。

## 输出格式

输出一张风险表或结构化字段：

`unit | repeated_tags | state_delta | classification | evidence_refs | repair_scope`

输入可使用 `units`、`episodes`、`entries` 或 `ledger` 数组；若从 Forge Blueprint 直接读取，也可使用 `episode_distinction_matrix`。

`classification` 使用 `UPGRADED_REPETITION`、`ECHO_BY_DESIGN`、`REPETITION_RISK` 或 `BARE_HOOK_RISK`。扫描只标出需要判断的位置，不替代因果、关系和观众审计。
