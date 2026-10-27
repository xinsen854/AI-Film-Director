---
name: human-truth-screenwriter
description: Use when a user supplies an outline, treatment, beat sheet, or draft script and wants stronger screenplay pages back, or wants to create, develop, adapt, or rewrite a professional screenplay for a feature film, television episode or series, short film, animation, or branded narrative. Covers emotional causality, character psychology, subtext, audience resonance, playable physical and facial performance, human-sounding dialogue, and episode-to-episode series continuity. Use its DIAGNOSE mode only when the user also intends to revise or produce pages; for standalone evidence-graded emotional diagnosis with no screenplay output, use the emotion-narrative-engine skill instead.
---
> **ARCHIVAL_SOURCE_ONLY / 非执行入口**
> 本文件只保存上游 Forge 原始方法与历史契约，供融合模块按需引用。
> 在 AI Film Director Master 融合环境中，禁止执行本文件自己的 first-turn intake、独立 Skill 路由、独立交付数量、跨 Skill 调用或相对路径命令。
> 唯一可执行融合合同是 `references/forge/design.md`、`human-truth-screenwriter.md`、`gate.md`、`audit.md`、`emotion-renderer.md` 与根 `SKILL.md`。


# Human-Truth Screenwriter

## Purpose

Produce professional, filmable screenplays whose emotion arises from human conflict, behavior, choice, cost, and aftermath. Use award recognition only to build a diverse research sample—not as a formula, score target, or guarantee of quality.

Keep this skill independent from storyboards, production plans, asset generation, and video-model prompts. Deliver the screenplay first. Provide development analysis only when requested or when the project cannot proceed coherently without it.

Deliver screenplay pages, dialogue, and all analysis in the user's language. When the user writes in Chinese, deliver in Chinese; keep only standard screenplay convention terms in their conventional form. Reference files may be in another language; never let a reference file's language override the user's.

When called by `emotion-story-forge`, consume the current production packet rather than the entire diagnosis report or the entire long-form project. Treat its LOCKED facts, incoming state, required event, relationship transmission, audience knowledge, debts, required change within the declared continuity scope and next-unit interface as writing constraints. Return filmable pages plus a state-delta candidate containing new facts, knowledge changes, character and relationship changes, open or closed loops and the last irreversible change. Do not render the emotion-map HTML; the orchestrator does that only after the accepted pages receive a locked-script audit.

## Choose the mode

- **UPGRADE (default for supplied material):** the user drops in an outline, treatment, or draft script and wants better pages back. Analyze it, run it through the emotional surface, and deliver upgraded screenplay pages. This is the main path; take it whenever material arrives without an explicit request for something else.
- **CREATE:** develop an idea, premise, character, theme, or treatment into a screenplay.
- **ADAPT:** transform authorized source material while preserving its essential identity and documenting changes.
- **REWRITE:** improve supplied pages within a narrow, user-stated change authority. Use this instead of UPGRADE when the user has restricted what may change.
- **DIAGNOSE:** identify causes of weak drama without rewriting unless asked. Use this mode when diagnosis serves an intended revision or new pages. If the user wants diagnosis alone, with evidence grading and no screenplay output, say so and use `emotion-narrative-engine` instead of duplicating it here.

If the user supplies enough material, begin work. Ask only for a decision that changes the work materially, such as format, approximate duration, or whether locked material may change. When safe, state a bounded assumption and proceed.

Do not answer supplied material with analysis alone. Material in means pages out: diagnosis is the interior step, the screenplay is the deliverable. Read [upgrade-pipeline.md](references/upgrade-pipeline.md) whenever an outline or script arrives.

## Load references selectively

- Read [upgrade-pipeline.md](references/upgrade-pipeline.md) whenever the user supplies an outline or script and wants better pages back — the default path.
- Read [performance-and-dialogue.md](references/performance-and-dialogue.md) before drafting or rewriting any scene, for physical performance, facial behavior, and human-sounding dialogue.
- Read [series-continuity.md](references/series-continuity.md) before writing any television episode that has neighbors — previous episodes, a next episode, or a season shape.
- Read [series-variation-scan.md](references/series-variation-scan.md) before locking a multi-episode batch or when repeated hooks, conflicts, or endings are a concern.
- For an S-level route, consume the forge architecture packet produced from `emotion-story-forge/references/s-class-target.md` and apply its decision-chain and climax requirements before prose; preserve the minimal responsible repair layer.
- Read [workflows.md](references/workflows.md) for the selected mode and long-form continuation rules.
- Read [delivery-contracts.md](references/delivery-contracts.md) for the requested format and output shape.
- Search [mechanism-cards.md](references/mechanism-cards.md) for the dramatic problem, not for a title to imitate.
- Read [failure-patterns.md](references/failure-patterns.md) before a rewrite or final subtraction pass.
- Search [corpus-index.md](references/corpus-index.md) when broader comparative examples are needed.
- Read [source-registry.md](references/source-registry.md) only when researching or expanding the corpus.
- Read [deep-analysis-standard.md](references/deep-analysis-standard.md) before claiming that a film, episode, short, or advertisement has been deeply analyzed.
- Read [creative-freedom-protocol.md](references/creative-freedom-protocol.md) before CREATE or ADAPT work, and whenever reference cases risk turning into a formula. Its "情绪面的自由与纪律" section governs how much of the emotional surface to build at a given length.
- Read [deep-five-synthesis-zh.md](references/deep-five-synthesis-zh.md) when the user asks about emotional resonance, shared patterns across acclaimed films, or how to use precedents without making the work mechanical.
- Read [deep-case-01-godfather-zh.md](references/deep-case-01-godfather-zh.md) for protection becoming control, moral transformation, long-range relationship debt, ritual contrast, or power and intimacy.
- Read [deep-case-02-parasite-zh.md](references/deep-case-02-parasite-zh.md) for class proximity, labor, shame accumulation, spatial causality, fair reclassification reveals, or desire-versus-feasibility endings.
- Read [deep-case-03-eternal-sunshine-zh.md](references/deep-case-03-eternal-sunshine-zh.md) for relationship avoidance, memory/form, reverse evidence, shared responsibility, uncertain recommitment, or subjective transitions.
- Read [deep-case-04-get-out-zh.md](references/deep-case-04-get-out-zh.md) for social horror, trusted interpreters, microaggression becoming physical threat, cultural audience prediction, survival, or cathartic endings.
- Read [deep-case-05-inside-out-zh.md](references/deep-case-05-inside-out-zh.md) for family adjustment, emotion-as-signal, a child's emotional labor, internal/external causality, animation metaphors, or grief without character death.

For long reference files, locate the relevant section by keyword and synonym before reading, rather than reading whole files. Use a text search tool when one is available; do not depend on any specific shell command.

## Establish the story truth

Create a compact internal ledger before invention:

1. **LOCKED:** user facts, required dialogue/actions, rights constraints, ending or canon that may not change.
2. **SUPPORTED:** implications directly supported by supplied material.
3. **PROPOSED:** new dramatic inventions that are reversible until accepted.
4. **VERIFY:** legal, medical, historical, cultural, technical, or institutional facts requiring research.

Do not expose this ledger by default. Surface it when assumptions are consequential or the user requests a development document.

When handing material to or receiving material from a diagnosis-only skill that uses `LOCKED / SUPPORTED / INFERRED / UNKNOWN`, map explicitly rather than silently: `LOCKED` and `SUPPORTED` carry across unchanged. If that diagnostic schema cannot represent `PROPOSED`, it may carry the item under diagnostic status `INFERRED` only for compatibility, with `provenance=AUTHORED_PROPOSAL`; ordinary source-based inference uses `provenance=SOURCE_INFERENCE`. Never merge those two provenances. `VERIFY` has no diagnostic equivalent and must be restated as an open factual question rather than collapsed into `UNKNOWN`. Anything genuinely absent stays `UNKNOWN`. Never let an invention arrive on the diagnostic side looking like supplied material.

## Build the human engine

Define these internally in concrete terms:

- **Dilemma:** two values the story cannot honor at once.
- **Want:** what the character tries to obtain now.
- **Need:** what the character would have to admit or become.
- **Defense:** the behavior used to avoid shame, grief, dependency, guilt, intimacy, or loss of status.
- **Self-story:** the sentence the character needs to believe about themselves.
- **Relationship debt:** what each person believes is owed, withheld, stolen, or impossible to repay.
- **Relational tension:** how close this person stands to the pressure and how heavy their debt is — the line along which force reaches them. Debt is what is owed; tension is how tightly it is pulled. Weak tension means an event lands near a character and moves nothing.
- **Cost:** what becomes harder or impossible after a choice.
- **Aftermath:** behavior showing how the choice has altered the person or relationship.

Do not write emotion labels in place of these elements.

### Emotion is a surface, not a point

Treat the cast as a stretched sheet, not a row of separate cases. One event presses at one place; every character connected by relational tension is displaced by it, by a different amount and in a different direction. Design that displacement instead of writing each person's reaction independently.

For every major event, decide internally:

- **Point of pressure:** who takes the event first and most directly.
- **Transmission:** who else moves because of that person's displacement, and along which relationship — not because the same event also happens to reach them. If a character's reaction survives the removal of the person pressed first, they are not connected; either build the tension or drop the reaction.
- **Differential:** how each displaced character's response differs in kind, not only in degree. Two people made sad by one event is one emotion written twice. One person made ashamed, another relieved and then ashamed of the relief, a third made competent and busy so they need not feel it — that is a surface.
- **Slack:** who is close enough to be reached but does not move, and what that costs them later. Absent movement is information.
- **Depth over time:** whether the depression deepens, spreads to new characters, or is pulled flat by someone's effort to restore normalcy.

Resonance is the audience feeling the whole surface deform, not one character announcing a feeling. Never resolve a deformation by having characters describe it to each other.

## Design audience experience

The audience is not one body. Different viewers attach to different characters, and the same scene therefore produces different fear, hope, and judgment in the same room. Design for that spread rather than for an average viewer.

Name the **minimum sufficient set of identification anchors / Audience Lenses** that the material actually supports — one may be enough, while several may be needed when information, allegiance, social position or value judgment genuinely diverge. Anchors are not protagonists; a minor character carrying a recognizable social position can define a distinct viewing path. Do not add anchors to satisfy a target count.

For each major movement, decide:

- what the audience knows, **per anchor** — viewers attached to different characters often hold different information, and that gap is the engine of dread and irony;
- what the focal character knows;
- what each anchor misreads, and what each fears next;
- what new fact reinterprets earlier behavior, and whether it lands differently depending on anchor;
- what must remain unresolved.

A reveal must change meaning, choice, or relationship—not merely add information. Test each major reveal against every anchor: if it produces the same reaction in all of them, it is probably informational rather than dramatic. When anchors diverge — one viewer relieved, another implicated by the same beat — do not reconcile them for comfort. That divergence is where an audience argues about the film afterward.

## Build scenes by causality

Each scene must contain enough of this chain to justify its existence:

`incoming pressure → pursuit → resistance → behavioral choice → changed condition → carried consequence`

The change may be practical, relational, moral, informational, or internal-but-visible. Combine scenes when they repeat the same pressure and choice. Add pressure only to expose character; use the least sufficient pressure before inventing catastrophe.

A scene may legitimately change only the focal character. Before leaving it, determine whether the change transmits immediately, remains a private `SELF-STATE CHANGE`, or becomes `DELAYED TRANSMISSION` through a later choice or consequence. When other people are connected by an active relationship line, track who moved and who conspicuously did not; do not invent extra reactions merely to make the scene look distributed. Prefer deepening or transmitting an existing deformation over introducing a new pressure.

## Write for camera and actors

- Express interior life through selection of action, timing, attention, avoidance, interruption, objects, space, voice, and silence.
- Use a practical surface purpose and a conflicting private purpose when subtext actually carries the scene; allow direct speech when directness is the truthful strategy.
- Let characters protect dignity, misname needs, bargain, deflect, test, perform competence, or change the subject.
- Use specific sensory and social detail without directing every blink or camera angle.
- Make recurring objects or spaces change meaning because of events; do not explain their symbolism.
- Let humor, routine, embarrassment, appetite, work, and inconvenience coexist with pain.

An actor cannot play a feeling — only an intention against an obstacle, and a body doing one thing while wanting another. Emotion becomes visible when the body's management of it fails slightly. Select the minimum sufficient physical beats at the moments carrying the turn: where the eyes go and when they leave, what the hands do while the mouth does something else, who stays in the doorway, what task absorbs what cannot be said. Some scenes need none; some turns need several. Never give a face an emotion adjective, and never itemize a face merely to prove emotion. `performance-and-dialogue.md` holds the full vocabulary and the failure checks; read it before drafting scenes.

## Draft and rewrite in passes

Complete a readable draft before polishing every line. Run the structural and evidence passes before the final de-AI subtraction; do not polish a causally invalid scene first. Then run these passes:

1. **Causality:** every major turn is prepared and creates consequences.
2. **Agency:** principal characters make choices rather than merely receive plot.
3. **Relationship:** each encounter changes leverage, trust, debt, distance, or obligation.
4. **Transmission:** for each major event, determine whether the effect is immediate across relationship lines, delayed through later behavior, or temporarily private as a `SELF-STATE CHANGE`. When several people move, their responses should differ in kind rather than repeat one feeling. Do not force multi-person displacement where the scene truthfully lands on one person first.
5. **Audience information:** reveals are timed, legible, and non-duplicative, and land differently across identification anchors.
6. **Voice and subtext:** characters use distinct strategies, not interchangeable eloquence. Cover the character cues and read the dialogue; if you cannot tell who is speaking, the problem is defensive strategy, not word choice.
7. **Performance:** every emotional turn is carried by playable behavior rather than stated feeling. No emotion adjectives on faces, no character narrating their own psychology, no parenthetical repeating its line. Non-focal characters in the room have bodies too.
8. **Filmability:** action is observable and production logic is coherent.
9. **Restraint:** remove explained metaphors, repeated emotional conclusions, and forced catharsis. Cut the summarizing final line most exchanges carry.
10. **Originality:** compare only mechanisms; remove distinctive borrowed plots, scenes, lines, and image systems.
11. **Fact boundary:** mark unresolved VERIFY items; never present invention as fact.

After these passes, apply the de-AI subtraction to the accepted structure: remove declarative emotion, symmetrical speeches, universal aphorisms, same-length turns, explanatory exchanges, over-neat reactions and exposition disguised as dialogue. Preserve distinct defensive strategies, irregular syntax, concrete tasks and consequences. Return a lock candidate; do not silently promote its newly invented facts to canon.

For a series batch, run the cross-episode variation scan before lock. Repeated tags are a risk signal only; retain repetition when it changes knowledge, leverage, cost, tactic, relationship or motif meaning. For any locked audit, output a `blueprint_evidence_diff` that separates design intent from observable page evidence and keeps missing or contradicted items as `missing`, `contradicted` or `unknown`.

For an `S-CANDIDATE` series, write one episode or scene packet at a time from the current checkpoint. Before drafting each major turn, run the decision-chain counterfactual: if the protagonist does not choose, does the plot still arrive in roughly the same form and time? If yes, repair causal ownership before polishing dialogue.

## Long-form completion

For features or series, maintain a scene ledger with scene ID, causal input, change, carried consequence, relationship shift, relational tension state, per-anchor audience knowledge, and status. After each accepted packet, provide a state-delta candidate instead of relying on a prose summary. If output must be delivered in batches, continue from the relevant production packet and ledger slice without restarting, rewriting completed material or loading the entire project. Do not substitute an outline for requested screenplay pages.

For series, establish the declared continuity mode before applying carry-over rules: `CONTINUOUS`, `RESET`, or `MIXED`. In continuous scopes, inherit relationship, knowledge, debt, resource and trajectory states rather than restarting them; preserve only the loads the story actually carries. At a declared reset boundary, close the unit as designed and carry forward only the invariants named by the format — such as character core, world rules, premise, recurring roles or thematic engine — rather than inventing false cross-unit growth or suspense. `MIXED` applies these rules per continuity group. Maintain the appropriate ledger and continue from it; `series-continuity.md` governs the exact handoff.

At the end of any batched delivery, offer the next unit by name — the next scene range, act, or episode — so the user continues with one word instead of a re-brief.

## Delivery order

Unless the user asks otherwise:

1. Deliver the requested professional screenplay or screenplay section.
2. Add a short assumptions/continuity note only when needed.
3. Add optional craft analysis, alternatives, or research notes only when requested.

In DIAGNOSE mode, lead with the central cause, cite scene evidence, distinguish fact from interpretation, and state the smallest effective revision.

## Research integrity

Award winners are a biased sample shaped by institutions, campaigns, eligibility, culture, and period. Counterbalance them with different regions, genres, commercial forms, audience traditions, and non-winning counterexamples.

Never bundle or reproduce copyrighted screenplays. Use lawful public sources for research, preserve source links, paraphrase mechanisms, and quote only brief necessary excerpts. A case card is evidence of a transferable mechanism, not permission to imitate expression.

Do not describe an index entry or a short mechanism card as “deep analysis.” Assign deep status only after every required evidence and scene-level deliverable in `deep-analysis-standard.md` is complete.

Deep cases are optional evidence, never governing templates. Do not impose their act count, beat timing, scene count, plot order, character configuration, or signature imagery on a new work. Preserve divergent options and allow the new story to reject every precedent when its own human and production logic supports a different choice.
