---
name: emotion-story-forge
description: Use when a user supplies Chinese story material and wants one bundled screenplay pipeline. The entry always starts with a universal intake-only gate, then runs prewriting emotion design, professional human-sounding screenplay writing, quality gates and de-AI revision, locked-script audit, and Markdown-first delivery, with an optional audited adaptive phase / character-particle / global-emotional-arc HTML.
---
> **ARCHIVAL_SOURCE_ONLY / 非执行入口**
> 本文件只保存上游 Forge 原始方法与历史契约，供融合模块按需引用。
> 在 AI Film Director Master 融合环境中，禁止执行本文件自己的 first-turn intake、独立 Skill 路由、独立交付数量、跨 Skill 调用或相对路径命令。
> 唯一可执行融合合同是 `references/forge/design.md`、`human-truth-screenwriter.md`、`gate.md`、`audit.md`、`emotion-renderer.md` 与根 `SKILL.md`。


# 情绪铸剧台

## Purpose

For a full production request, this orchestration layer runs emotion-narrative-engine before and after human-truth-screenwriter. The first pass converts the outline into design constraints; the writer turns those constraints into pages; the second pass audits what the locked pages actually achieved. Scoped planning, diagnosis-only, or rewrite requests follow the dispatch rules below instead of calling unnecessary stages.

The prewriting Emotion Blueprint and diagnosis conclusion library are working contracts, not the final HTML. The default screenplay deliverable is a clean Markdown file, 项目名-完整剧本.md. Do not create a DOCX unless the user explicitly requests it. When the user requests the full bundled production, the second formal deliverable is 情绪图谱-项目名.html generated from the locked-script audit; do not generate that HTML from an outline. Diagnosis data, continuity ledgers, state deltas and the next-AI handoff remain internal or are embedded as machine-readable data in the HTML; they are not separate delivery files.

For long works, these are delivered incrementally under the long-form contract in references/long-form-orchestration.md. Never promise to generate 300,000, 500,000, or 1,400,000 Chinese characters in one response.

## Universal first-turn entry gate

Run this gate whenever the skill is explicitly invoked or this entry receives an outline, treatment, beat sheet, screenplay or other story material. It is project-agnostic: never hardcode a title, character, event ID, episode count, runtime or path in the gate.

On the first turn:

1. Read all supplied material before asking questions.
2. Extract the project name, intended form, scale, existing canon, continuity, user-locked facts, target audience or platform when present, change authority and current requested scope.
3. Resolve form in this order: the user's latest explicit statement; explicit material metadata; structural signals as a provisional inference; otherwise ask. Never decide film versus television from word count, cast size or plot shape alone.
4. Ask only missing choices that materially change production. Do not repeat anything answered by the material or current conversation. Ask at most five bounded questions in the first round.
5. Do not run DESIGN diagnosis, write screenplay pages or render final HTML on this first turn.
6. Present the recognized project contract and questions, then stop for user confirmation. If nothing material is missing, present the recognized contract and ask the user to confirm or correct it; still stop before DESIGN.

Possible question dimensions are form, runtime or episode scale, season/volume scope, primary genre and audience, change authority, ending or continuity locks, factual boundaries and current production unit. They are a menu, not a mandatory questionnaire. Default language is Chinese and the final screenplay file is Markdown; ask about another language or delivery format only when the user requests it or the material requires it.

For a novel-length or ultra-long screenplay request, additionally ask: target total characters, whether the unit is screenplay pages or prose chapters, volume/season count if known, delivery unit (one volume, one chapter, or scene packet), and whether the user wants outline-only, outline plus sample pages, or serialized drafting. If the target is 300,000 characters or more, confirm that the first pass is a locked planning package rather than full-text generation.

After the user answers or confirms the entry contract, continue with the required execution order.

### Route selection after intake

Classify the project as `STANDARD`, `SERIES`, or `S-CANDIDATE` before drafting:

- `STANDARD`: ordinary short/film work or narrow rewrite; use the minimum applicable flow.
- `SERIES`: multi-episode work with inherited relationships, knowledge, resources, or open loops; enable series ledgers and variation scanning.
- `S-CANDIDATE`: the user explicitly targets S level, requests systemic engine redesign, or the project has high-risk long-range architecture; enable the S-level architecture gates below.

Do not infer `S-CANDIDATE` from genre prestige or length alone. Do select it when the request explicitly asks for S level or a full-series engine upgrade.

## Required execution order

### 0. Revision / source preflight

Before the Truth ledger, inspect the input container rather than treating every visible run as active canon. For a DOCX that contains tracked changes, strikethrough, reviewer markup, or multiple colored revision layers, run `scripts/resolve_revision_docx.py` first and feed the resolved ACTIVE text plus its revision report into the analysis. Tracked deletions and strikethrough are excluded deterministically. Run color never has a universal meaning: only apply a color policy when the user or the document itself explicitly defines that legend. Preserve unresolved colors/comments as revision metadata instead of guessing which version is canon. Plain Markdown/text or clean DOCX bypasses this step.

### 1. Truth ledger

Read material completely. Classify facts as LOCKED, SUPPORTED, PROPOSED, or VERIFY. Track OUTLINE_COARSE, SCRIPT_FINE, or MIXED precision. Never let an invention look like user fact.

For `S-CANDIDATE`, also read [references/s-class-target.md](references/s-class-target.md) and establish story necessity, series/relationship/world pressure engines, independent opposition, decision chains, form necessity, and the reserve of unresolved future capacity. Do not draft until the architecture gate is `pass` or the user explicitly accepts a `revise` route.

Use `scripts/validate_s_candidate.py` to check the architecture package shape before drafting. It verifies required evidence fields and candidate counts; it cannot certify dramatic quality.

### 2. Prewriting design diagnosis

Run emotion-narrative-engine in DESIGN scope. Produce an Emotion Blueprint and diagnosis conclusion library containing narrative units; pressure to interpretation to defense to choice or avoidance to changed condition to displacement to returning consequence to audience re-estimation; character wants, needs, defenses, debts, costs and aftermath; pressure point, transmission, differential response and purposeful slack; audience knowledge, misreading, expectation, fear, care, release and aftertaste; rhythm nodes tied to causal events; breakpoints, counter-readings, confidence, UNKNOWN and PENDING_*; fact boundary and canonical names.

Coarse inputs do not support micro-performance claims. Proposed inventions must be labelled and passed to the writer as authored invention. Convert only the relevant scope into a production packet: incoming state, required event, character interpretations, relationship transmission, audience knowledge, debts to pay or create, required change within the declared continuity scope and next-unit interface. Do not render the final HTML from an outline or planning blueprint.

When the user supplies a systemic “B+ to A+” or engine-redesign proposal, read [references/a-plus-engine-upgrade.md](references/a-plus-engine-upgrade.md). First classify the proposal into series engine, external pressure, character engine, relationship transmission, unit variation, peak/aftermath and knowledge progression. Keep concrete villains, backstories, deadlines, fixed episode assignments and emotional peak counts as project-level PROPOSED items requiring approval; if the user asked only for evaluation, update the skill or blueprint layer and do not edit screenplay pages.

For short-form or platform-specific requests, load the conditional short-form adapter in `emotion-narrative-engine/references/genre-shortform-brand.md`. For multi-episode batches, load `human-truth-screenwriter/references/series-variation-scan.md` before lock. These are diagnostic routes, not universal templates.

For `S-CANDIDATE`, run the story-necessity gate, character decision-chain pass, independent opposition check, and [references/climax-tournament.md](references/climax-tournament.md) before the scene outline is production-ready. Present the resulting architecture package for one user calibration at this boundary; do not ask for routine approval after every episode unless the user requests that cadence.

### 3. Write screenplay pages

Pass the production packet, not the whole diagnosis report, to human-truth-screenwriter. Map LOCKED and SUPPORTED unchanged; label new inventions as PROPOSED; keep VERIFY open. Select CREATE, UPGRADE, REWRITE or ADAPT and read its relevant references. Write complete filmable Chinese scenes. Emotion appears as behavior, timing, subtext, choice, cost and aftermath, never labels or analysis jargon. Preserve television knowledge states and continuity.

For `SERIES` and `S-CANDIDATE`, draft one formal episode or scene packet at a time. Never batch-generate multiple episode screenplays as a single undifferentiated pass. Continue automatically after a validated checkpoint only when the user has authorized sequential production or `auto-accept`.

### 4. Gate, revise and de-AI

Review the draft in this order: causality and agency; continuity and knowledge state; relationship transmission; audience information and aftertaste; performance and dialogue; then the de-AI subtraction pass. Do not polish a structurally invalid scene first. Findings must cite scene evidence and request the smallest repair scope. Simulated audience reactions are predictions with confidence and activation conditions, not real audience evidence. After repairs, produce a lock candidate plus a state-delta candidate rather than a prose summary alone.

### 5. Lock the accepted scope

Lock only user-approved pages or pages covered by an explicit auto-accept instruction. A locked scope is read-only until a later approved rewrite. Scan new facts, relationships and character details into a state-delta candidate; classify them before promoting them to canon. If the scope remains DRAFT, do not present its HTML as the final project map.

For a series or multi-unit batch, run the cross-episode variation scan before lock. Repeated structure is not a failure by itself; require a meaningful change in knowledge, leverage, cost, tactic, relationship or motif meaning, and report only `REPETITION_RISK` when that increment is absent. Validate the continuation ledger with `scripts/validate_ledger.py`; the validator checks handoff structure, not whether the claimed change is dramatically earned.

For `SERIES` and `S-CANDIDATE`, commit a checkpoint after each accepted episode/packet containing the continuity mode/group plus the movement, carried state or reset invariants, irreversible changes where applicable, relationship states, knowledge state, debts, open loops, evidence references, and next-unit interface. A checkpoint is the continuation authority; do not reconstruct it from memory or a prose recap.

### 6. Postwriting script audit

Run emotion-narrative-engine again in AUDIT scope on the locked pages at SCRIPT_FINE or MIXED precision. Compare the design blueprint with observable scene evidence: what pressure actually landed, what each character knew and interpreted, which defense and choice appeared on the page, what condition and relationship changed, what consequence remains, and how audience knowledge may be re-estimated. Preserve counter-readings, confidence, UNKNOWN and VERIFY. Update the diagnosis conclusion library and continuation ledger from actual state changes, not intended ones. After the fine event ledger is complete, aggregate it into adaptive `phase_events` using state-change boundaries, generate `narrative_topology` with separate story/audience time, derive open-topology `phase_links`, derive evidence-supported `audience_lenses`, and synthesize `global_emotional_arc` as a summary-only aggregation contract. `global_emotional_arc` must use `aggregation_policy=derive_from_phase_states`; do not duplicate character/audience emotion nodes there because the renderer derives those nodes uniquely from phase exit states / last audience keyframes. For `mixed` continuity, every repeated character state must provide `continuity_group`. Do not use a fixed act, episode, minute, four-stage, six-stage, or fixed audience-persona template. `P01/P02/...` are only stable IDs; labels and mechanisms are generated from the actual locked story.

The audit must include a `script_audit.blueprint_evidence_diff` table. Every design requirement is classified as `realized`, `partial`, `missing`, `contradicted`, or `unknown` with evidence references; do not silently upgrade intended transmission, reveal, or aftermath into page evidence.

For `S-CANDIDATE`, run the bottleneck gates in order: G0 story necessity, G1 engine/opposition, G2 scene vitality and episode distinction, G3 irreplaceable ending, then G4 whole-work bottleneck. Any core `block` prevents S-level labeling until the affected layer is revised and re-audited.

### 7. Render the final HTML

Convert the latest locked-script audit to JSON and run scripts/render_emotion_map.py. Save exactly 情绪图谱-项目名.html, sanitizing only illegal filesystem characters. It must be standalone and offline. The primary visual hierarchy is now: **全剧情情绪总谱 → 阶段事件人物情绪质点场 + 观众外围情绪环 → 证据/因果/关系/断点层**. Keep story contract, evidence boundary, clickable rhythm and causal evidence, audience path, character/relationship audit, breakpoints, repair cards, unknowns, approval flags and reduced-motion fallback. Never add facts or certainty.

The renderer performs dependency-free staged payload validation before embedding data. A final `locked_audit + LOCKED` payload must contain `narrative_topology`, `audience_lenses`, `phase_events`, `phase_links`, and `global_emotional_arc` in addition to the existing audit fields; use `--validate-only` when a report needs checking without rendering.

The old project-wide wave/deform `emotion_field` is deprecated for the final map. The final map uses two primary visual systems: **per-character emotion rivers plus per-audience-segment long-form rivers for the whole-work arc**, and **separate character-owned particle clouds inside an audience emotion halo for the selected phase**. The global section must expose an `Audience Time / Story Time` toggle; phase rail and all long-form rivers reorder with that selection. `phase_links` must render as an actual SVG topology graph rather than text-only chips. `continuous` rivers may connect only adjacent evidenced states, `reset` rivers must break per unit, and `mixed` rivers connect only matching `continuity_group` values; a phase with no state for that character creates a visible gap. The halo has a faint overall audience climate ring plus audience-segment particle arcs; equal arc lengths are viewing lenses, not audience-share measurements. Phase particles use stable visual emotion attractors so audited emotion-weight changes produce visible migration between emotion regions instead of recoloring one homogeneous cloud. A particle may blend two supplied emotion colors and continuously change their ratio; cluster-center particles are larger/brighter than edge particles. The phase trigger is shown as a driver node, while evidence/audit modules are secondary collapsible content. These are presentation effects only. HTML may interpolate supplied values but must not choose phase boundaries, invent emotion mixtures, derive psychology from motion, overwrite UNKNOWN, or substitute visual inference for script evidence.

### 8. Deliver

By default deliver one formal Markdown file, 项目名-完整剧本.md, containing only the complete clean screenplay. For a full bundled production request, deliver exactly two formal files: 项目名-完整剧本.md and 情绪图谱-项目名.html. The HTML contains the locked-script audit plus embedded machine-readable handoff data. Do not create a DOCX unless explicitly requested. The embedded handoff contains premise, human question, competing values, character engines, relationship debts, causal rhythm table, audience-information strategy, fact ledger, state delta, motifs, ending aftertaste and a next-AI prompt. Do not create a third handoff, ledger, JSON, report or screenplay file in the formal delivery folder.

For long-form work, deliver the current unit only and update the ledgers. The next unit must be selectable without rereading the entire project. A completed unit is not the same as a completed project.

## Long-form dispatch rules

Select a route by total target length:

- Up to 80,000 Chinese characters: project bible, one global outline, chapter/scene outline, then draft in scene packets. Run a global design diagnosis once, a local audit on each locked packet, and the screenwriter for each drafted packet.
- 80,001–300,000: project bible, volume/act map, 卷纲, 章纲, scene packets. Freeze a versioned continuity ledger after each locked volume. Run design diagnosis at project and volume level; run local script audit for a locked unit, major relationship reversal, ending or flagged breakpoint. Do not regenerate unchanged volumes.
- 300,001–500,000: mandatory multi-volume route. First deliver a Series/Project Bible, then a locked master卷纲, then one volume's章纲. Draft only the approved volume/chapters. The default response is a 1–3 chapter or 1–2 scene packet, not the whole book. Refresh final HTML only from a locked project or volume audit, not when an outline changes.
- 500,001–1,400,000: treat as a serialized saga, not a single screenplay. Require project bible, world/canon ledger, character relationship ledger, master卷纲, per-volume卷纲, per-chapter章纲, and a continuation ledger. Process one planning or drafting unit per turn. Run design diagnosis at project and volume scopes, script audit at locked packets and breakpoints, and the screenwriter only for requested pages/scenes. Never load every chapter into active context; use summaries plus the relevant ledger slice.
- Above 1,400,000: stop and ask for a staged production decision. Offer a season/arc pilot package first; do not silently expand scope.

## What to dispatch and what not to dispatch

- Need to decide story architecture: use emotion-narrative-engine in DESIGN scope and update the blueprint. Do not call the screenwriter or render final HTML yet.
- Need chapter or scene pages: extract the production packet, call human-truth-screenwriter, run the gates, then audit the accepted locked scope. Do not rerun global design diagnosis unless a breakpoint or continuity contradiction is found.
- Need continuity audit, character state, or canon check: use the ledger and a focused emotion pass; do not draft prose.
- Need only HTML refresh: render only from the latest locked-script audit JSON; do not diagnose an outline again or call the writer to invent content.
- Need only a synopsis, title list, or chapter labels: use the project ledger; do not call either skill unless emotional causality is being diagnosed.
- Need to assess a user-supplied systemic improvement proposal without changing pages: read the A+ engine upgrade protocol, report reusable principles versus project candidates, and edit only the skill/blueprint layer when explicitly asked.
- Need a rewrite after user feedback: diagnose only the affected scope, map approved changes, draft and gate the smallest changed packet, then replace the locked audit and HTML nodes only after approval.

## Non-negotiable long-form gates

Do not draft a chapter until its parent volume/act and chapter purpose are locked or explicitly marked PROPOSED. Do not draft a volume until its emotional promise, relationship load, irreversible turn, and ending aftertaste are recorded. Do not draft a unit without its production packet. After each locked packet, update new facts, knowledge state, desire/defense, relationship debt, open and closed loops, factual VERIFY items, last irreversible change and next-unit interface. If a later request conflicts with a locked ledger item, surface the conflict before writing.

## High-strength de-AI pass

Subtract declarative emotion, symmetrical speeches, universal aphorisms, same-length turns, repeated explanatory exchanges, over-neat reactions, exposition disguised as dialogue, characters always saying the smart thing, and consequence-free harm. Use interruption, evasion, concrete objects, status behavior, misremembering, competing wants, silence with a task, uneven syntax, specific detail and later costs. Keep human irregularity in important scenes.

## Hard QC

- For a full production request, design diagnosis preceded pages and script audit followed the locked pages.
- Final HTML and the locked-script audit share names, counts, statuses, confidence, unknowns and directions.
- Major movements contain pressure, interpretation, defense, choice, changed condition and consequence; unsupported links stay UNKNOWN.
- Transmission is not confused with simultaneous reaction.
- No locked fact, canon, ending or proper name changed silently.
- Pages contain observable behavior and playable dialogue, not emotion labels.
- Causality, continuity and audience-information gates ran before the de-AI pass.
- No outline-only blueprint is presented as the final HTML.
- Simulated audience response remains prediction, not acceptance evidence.
- High-severity claims include counter-reading and confidence.
- Proposed inventions and VERIFY items are explicit.
- After AUDIT, the “蓝图意图 vs 正文证据” diff is present; missing or contradicted design items remain `missing`, `contradicted`, or `unknown`.
- Series ledger and cross-episode variation checks ran when the requested scope is episodic; repeated tags are reported as risks, not treated as automatic failures.
- The default formal delivery is one complete Markdown screenplay; a full bundled request has exactly one Markdown screenplay and one final HTML; internal artifacts are not presented as extra deliverables.
- Output uses the user language and follows the current requested delivery format; never create DOCX by default.

Read references/question-framework.md and references/blueprint-schema.md when intake or payload details are needed. Use assets/emotion-map-template.html and scripts/render_emotion_map.py for rendering.


## v1.1 Generalization Pass

- Do not add project-specific conditions, titles, character names, diagnoses, genre beats, dream rules or event IDs to the Skill. Every new rule must still make sense when the next screenplay belongs to a different genre and structure.
- For revision-heavy DOCX input, resolve OOXML revisions before story diagnosis with `emotion-story-forge/scripts/resolve_revision_docx.py`. Track deletions and strikethrough are deterministic; colors are interpreted only from an explicit document/user legend.
- Emotion semantics are open. The base palette is a visual projection layer, not the diagnosis vocabulary. Semantic emotions must carry a visual `family` or `blend`; inferred states should carry `confidence` and `evidence_level`.
- A phase may contain multiple `drivers[]`; keyframes may bind `driver_ref`. Do not split a phase merely because it has multiple drivers if the underlying state remains one continuous state.
- Use `narrative_layers` for reality/memory/subjective/hypothesis/recorded/custom presentation layers. Do not create special-case logic for “dream”, “flashback”, “video”, etc.
- Use `phase_links.family` for stable visual topology and keep `kind` open. Unknown mechanisms use `CUSTOM`, not a new HTML patch.
- Long works may provide evidence-based `phase_clusters[]` for Semantic Zoom. Without clusters, the renderer may paginate technically but must not invent semantic grouping.
- All whole-work emotion river nodes remain derived from `phase_events`; only narrative summaries may be separately authored.

Legacy payloads may still use `audience_segments`; v1.1 output should prefer `audience_lenses`.
