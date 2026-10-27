# AFD 4.7.1 Fusion GitHub Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a verifiable, emotion-centered, bilingual open-source release of AFD 4.7.1 Fusion.

**Architecture:** Keep the supplied skill self-contained below `skills/ai-film-director-4/`. Place all new public-facing assets and documentation outside it so the package's own integrity validator remains meaningful. Publish through the authenticated GitHub connection.

**Tech Stack:** Markdown, Mermaid, Python release validator, YAML, GitHub Git objects API.

**Spec:** `docs/superpowers/specs/2026-10-27-github-release-design.md`

## Global Constraints

- Preserve the supplied production logic byte-for-byte.
- Only change the unsupported product restriction and its integrity hash inside the skill.
- Do not claim direct video/TTS generation or empirical emotional prediction accuracy.
- Use Apache-2.0 and the approved scheme A.

## Review Focus

- README images and links must resolve to committed paths.
- The nested skill must pass its packaged release checker.
- Public files must not contain credentials or private user data.
- The plugin manifest and skill metadata must parse successfully.
- GitHub must contain the intended source tree and the final public README.

---

### Task 1: Preserve and validate source

**Files:** `skills/ai-film-director-4/**`

- [ ] Extract the authoritative archive and verify its initial release gate.
- [ ] Apply only the known metadata compatibility change.
- [ ] Verify the updated release gate and source-file count.

### Task 2: Create the public identity and documentation

**Files:** `README.md`, `README.zh-CN.md`, `docs/ARCHITECTURE.md`, `docs/COMPARISON.md`, `docs/assets/emotion-causality-hero.png`, `LICENSE`, `plugin.json`, `.gitignore`, `.github/workflows/validate.yml`

- [ ] Create the original hero and bilingual README, grounded in the installed skill.
- [ ] Explain emotion causality, authority, gates, and limitations.
- [ ] Add license, portable manifest, and CI; inspect links and files.

### Task 3: Publish and verify

**Files:** the full prepared repository tree.

- [ ] Recheck permissions and public-file safety.
- [ ] Upload the full tree using the user's connected GitHub account.
- [ ] Read back repository metadata and representative files; compare expected paths.
