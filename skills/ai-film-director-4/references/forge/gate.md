# Forge Gate / QC / De-AI｜内部剧本质量门

**INTERNAL_MODULE_ONLY**。

按 Forge 原顺序检查：

1. causality + agency
2. continuity + knowledge state
3. relationship transmission
4. audience information + aftertaste
5. performance + dialogue
6. de-AI subtraction

只返工最小责任层；结构性 FAIL 时禁止进入 `SCRIPT_LOCK` 之后的任何阶段。

通过后输出：
- lock candidate
- state-delta candidate
- Forge QC findings
- `PASS` / `FAIL`

锁稿由 AFD MASTER ORCHESTRATOR 的 `script_lock_policy` 决定，本模块不得绕过锁稿控制器。
## 锁候选文件合同

Gate/QC/De-AI PASS 不是只返回文字 `PASS`。必须把最终候选正文保存为项目内真实 `lock_candidates/<unit>_LOCK_CANDIDATE.md`（或同等项目内路径），并把该路径作为 `FORGE_GATE_QC_DEAI` 的 `artifact` 交给 Master。Master 在此时计算 SHA256；之后任何字节变化都会使锁稿失效。

