# Forge workflow schema

同一项目 JSON 贯穿设计、写作、锁定与审计。最终 HTML 只读取**已锁定剧本最新 AUDIT**，HTML 本身不重新理解剧情。

`rhythm_causality` 保持细粒度事件/因果账本；`phase_events` 是其状态变化驱动的语义聚合；`global_emotional_arc` 是对已锁定范围的全剧情收束。三者职责不同，禁止互相替代。

~~~json
{
  "meta": {"title":"情绪图谱-项目名","format":"feature|tv|short|animation|branded","runtime":"UNKNOWN","precision":"OUTLINE_COARSE|SCRIPT_FINE|MIXED","mode":"forge","workflow_stage":"design|draft|locked_audit","quality_route":"STANDARD|SERIES|S-CANDIDATE","summary":"..."},
  "fact_boundary": {"locked":[],"supported":[],"proposed":[],"verify":[]},
  "canonical_names": [{"name":"...","aliases":[],"role":"..."}],

  "rhythm_causality": [
    {"id":"EVENT_ID","label":"细事件节点","beat":"setup|load|turn|compression|reversal|consequence|afterimage","event":"...","pressure":"...","interpretation":"...","defense":"...","choice":"...","changed_condition":"...","relationship_shift":"...","returning_consequence":"...","audience_reestimate":"...","basis":"...","confidence":"high|medium|low"}
  ],

  "emotion_palette": [
    {"id":"joy","label":"喜悦","color":"#FFD166"},
    {"id":"excitement","label":"兴奋","color":"#FF9F43"},
    {"id":"affection","label":"喜欢 / 亲近","color":"#63E6BE"},
    {"id":"hope","label":"希望","color":"#7EDC9A"},
    {"id":"calm","label":"平静","color":"#66D9EF"},
    {"id":"surprise","label":"惊讶","color":"#C3A6FF"},
    {"id":"anxiety","label":"焦虑","color":"#FF8C8C"},
    {"id":"fear","label":"恐惧","color":"#FF5F76"},
    {"id":"anger","label":"愤怒","color":"#FF4D4D"},
    {"id":"shame","label":"羞耻 / 难堪","color":"#D86BD0"},
    {"id":"sadness","label":"悲伤 / 失落","color":"#637EE8"},
    {"id":"disgust","label":"厌恶 / 排斥","color":"#A6D854"}
  ],

  "narrative_topology": {
    "continuity_mode":"continuous|reset|mixed",
    "story_time_basis":"故事世界真实先后依据",
    "audience_time_basis":"剧本呈现/观众获知先后依据",
    "narrative_layers":[
      {"id":"REAL","label":"现实层","family":"reality|memory|subjective|hypothesis|recorded|custom","description":"..."}
    ],
    "notes":[]
  },

  "audience_lenses": [
    {"id":"AUD_MAIN","label":"模拟观看视角","perspective":"本作品当前证据支持的观看立场","question_lens":"该观看视角此刻主要在判断什么","evidence_refs":[]}
  ],

  "phase_events": [
    {
      "id":"P01",
      "label":"由当前剧情生成的阶段名",
      "scope_label":"00:18:30–00:27:10 | EP31–EP36 | 第15计",
      "story_order":1,
      "audience_order":1,
      "trigger":"兼容字段；当 drivers[] 已给出时可作为阶段一句话摘要",
      "narrative_layer_id":"REAL",
      "drivers":[
        {"id":"DRV01","at":0.30,"label":"新信息进入","observable_event":"可观察剧情事实","evidence_refs":["SC03"]}
      ],
      "state_change_reason":"为什么旧状态已经不足以描述人物/观众处境",
      "summary":"阶段因果摘要",
      "mechanisms":["开放语义机制，不使用固定枚举"],
      "relative_span":1.0,
      "character_states":[
        {
          "character":"人物名",
          "continuity_group":"仅 mixed 模式必填；相同值才允许在总谱中跨阶段连成一条河",
          "entry_state":{"cognition":"...","goal":"...","relationship":"...","agency":"...","emotions":[{"emotion":"affection","weight":0.65,"confidence":"high","evidence_level":"EXPLICIT"},{"emotion":"ambivalent_attachment","semantic_label":"矛盾依恋","weight":0.35,"blend":[{"emotion":"affection","weight":0.6},{"emotion":"anxiety","weight":0.4}],"coordinates":{"valence":0.1,"arousal":0.62,"approach":0.2,"agency":-0.1,"connection":0.7,"certainty":-0.2},"confidence":"medium","evidence_level":"SUPPORTED"}]},
          "keyframes":[
            {"at":0.0,"label":"进入","emotions":[{"emotion":"affection","weight":1.0}],"intensity":0.40,"motion":"hold","evidence_ref":"SC01"},
            {"at":0.5,"label":"过渡","driver_ref":"DRV01","emotions":[{"emotion":"affection","weight":0.5},{"emotion":"excitement","weight":0.5}],"intensity":0.65,"motion":"expand","confidence":"medium","evidence_level":"SUPPORTED","evidence_ref":"SC03"},
            {"at":1.0,"label":"退出","emotions":[{"emotion":"excitement","weight":1.0}],"intensity":0.78,"motion":"cohere","evidence_ref":"SC05"}
          ],
          "exit_state":{"cognition":"...","goal":"...","relationship":"...","agency":"...","emotions":[{"emotion":"excitement","weight":1.0}]},
          "cognition_shift":"...",
          "goal_shift":"...",
          "relationship_shift":"...",
          "choice_shift":"...",
          "evidence_refs":[]
        }
      ],
      "audience_states":[
        {
          "segment_id":"AUD_MAIN",
          "segment":"整体观众或有证据区分的观众锚点",
          "knowledge_state":"观众此刻知道什么",
          "misread_or_question":"观众此刻可能误读/追问什么",
          "reappraisal":"新信息如何改变前文意义",
          "keyframes":[],
          "evidence_refs":[]
        }
      ],
      "relationship_changes":[],
      "irreversible_changes":[],
      "evidence_refs":[],
      "confidence":"high|medium|low"
    }
  ],

  "phase_links": [
    {"from":"P01","to":"P02","family":"SEQUENCE|BRANCH|MERGE|PARALLEL|RETURN|REFRAME|ECHO|RESET|INTERRUPT|CONSEQUENCE|CUSTOM","kind":"开放语义 mechanism","label":"具体关系说明","evidence_refs":[]}
  ],

  "phase_clusters": [
    {"id":"CL01","label":"由剧情语义聚合的阶段簇","phase_ids":["P01","P02"],"summary":"仅用于超长作品 Semantic Zoom，不是幕式模板","evidence_refs":[]}
  ],

  "global_emotional_arc": {
    "aggregation_policy":"derive_from_phase_states",
    "summary":"整个已锁定范围的情绪/认知/关系收束",
    "phase_ids":["P01"],
    "character_throughlines":[{"character":"人物名","throughline":"长期变化摘要；不重复填写情绪节点"}],
    "audience_throughlines":[{"segment_id":"AUD_MAIN","throughline":"该观看立场的长期问题/体验摘要；不重复填写情绪节点"}],
    "major_turns":[{"phase_id":"P01","label":"关键认知/关系/选择转折","evidence_refs":[]}],
    "ending_residue":"最终情绪余味"
  },

  "story_necessity": {"why_now":"...","why_this_protagonist":"...","no_rational_exit":"...","inaction_cost":"...","form_necessity":"...","verdict":"pass|revise|block","evidence_refs":[],"strongest_counterexample":"...","confidence":"high|medium|low","responsible_layer":"..."},
  "opposition_engine": {"goal":"...","rules":"...","resources":"...","victory_condition":"...","independent_motion":"...","counter_reading":"...","status":"LOCKED|PROPOSED|UNKNOWN"},
  "decision_chains": [{"id":"D001","character_id":"...","pressure":"...","available_options":[],"chosen_action":"...","immediate_cost":"...","state_change":"...","future_debt":"...","stated_reason":"...","hidden_reason":"...","counterfactual_without_choice":"...","evidence_refs":[],"verdict":"pass|revise|block"}],
  "ending_tournament": [{"id":"CANDIDATE_01","factual_result":"...","final_choice":"...","irreversible_cost":"...","relationship_result":"...","thematic_answer":"...","audience_residue":"...","evidence_refs":[],"tests":{"causal":"pass|revise|block","character":"pass|revise|block","cost":"pass|revise|block","replacement":"pass|revise|block","echo":"pass|revise|block"},"decision":"selected|rejected|open","rejection_reason":"..."}],
  "episode_distinction_matrix": [{"unit":"...","conflict_source":"...","dominant_relationship":"...","protagonist_tactic":"...","reveal_mechanism":"...","emotional_shape":"...","hook_source":"...","ending_load":"...","state_delta":"..."}],
  "peak_aftermath_ledger": [{"id":"PEAK_01","pressure_point":"...","transmission_line":"...","differential_displacement":"...","promise_paid":"...","release":"...","aftermath":"...","evidence_refs":[]}],

  "characters": [], "relationship_shifts": [], "audience_path": [], "breakpoints": [], "unknowns": [], "directions": [],
  "production_packet": {"scope":"...","incoming_state":{},"required_event":"...","character_interpretations":{},"relationship_transmission":[],"audience_knowledge":{},"debts_in":[],"required_irreversible_change":"...","next_unit_interface":"..."},
  "script_audit": {"source_script_version":"...","precision":"SCRIPT_FINE|MIXED","causality_findings":[],"continuity_findings":[],"audience_findings":[],"repair_scope":[],"blueprint_evidence_diff":[{"blueprint_item_id":"...","intent":"...","expected_evidence":"...","observed_evidence":"...","status":"realized|partial|missing|contradicted|unknown","impact":"...","evidence_refs":[]}],"lock_status":"DRAFT|LOCKED"},
  "state_delta": {"new_facts":[],"knowledge_changes":{},"character_changes":{},"relationship_debt_changes":[],"opened_loops":[],"closed_loops":[],"last_irreversible_change":"...","next_unit":"..."},
  "long_form": {"target_chars":0,"unit":"screenplay|prose|planning","quality_route":"STANDARD|SERIES|S-CANDIDATE","volumes":[],"current_scope":"project|volume|chapter|scene_packet","continuation_ledger":{"scope":"...","blueprint_version":"...","knowledge_state":{},"character_state":{},"relationship_debt":[],"open_loops":[],"carried_load":[],"verify_items":[],"last_irreversible_change":"...","next_unit":"...","evidence_refs":[]}},
  "handoff": {"premise":"...","human_question":"...","competing_values":[],"motifs":[],"ending_aftertaste":"...","next_ai_prompt":"..."}
}
~~~

## 阶段判定硬规则

`phase_events` 不按固定幕、分钟、场景、集数或模板切割；尤其禁止固定 A/B/C/D 四阶段或把任何示例阶段名当成通用流程。先完成 `rhythm_causality`，再比较人物与观众的进入/退出状态。认知、目标、关系、处境/选择空间、价值判断、行为策略或不可逆后果发生实质变化时，才建立阶段边界。仅有同一情绪或压力的强弱变化时保持在同一阶段，用 `keyframes` 表达。

## 情绪混合硬规则

- `emotions[].weight` 取 0..1；同一状态建议归一化到 1。
- `emotion` 是开放语义 ID，不再要求必须等于 12 个基础色谱 ID。若不是基础色谱 ID，必须通过 `family` 或 `blend[]` 投影到基础视觉色谱。
- 可选 `semantic_label`、`coordinates`、`confidence`、`evidence_level`；`coordinates` 用于语义空间布局，不能替代剧情证据。
- 一个状态可包含多个细情绪；不要为了“只有一个主色”丢掉矛盾情绪。
- HTML 允许把两个主成分在一个圆点内绘制为渐变比例；不允许 HTML 根据颜色自己推断情绪。
- `motion` 只允许 `cohere|expand|contract|tremor|drift|split|bridge|hold`，由 AUDIT 给出。

## 时间与拓扑硬规则

- `phase_links.family` 只承担通用视觉语义族；`kind` 保持开放 mechanism。
- `phase_links` 是开放阶段图，不要求所有阶段严格单线相邻；允许并行、分支、合流、回返和后续重释。
- v1.1 首选 `audience_lenses`；旧 `audience_segments` 仅作兼容别名。它们表示“模拟观看视角”，不是现实人口分群，也不表达真实观众占比。
- `phase_events[].audience_states[].segment_id` 必须引用已声明的 `audience_lenses[].id`（或兼容字段）。
- `relative_span` 可选，仅控制阶段视觉宽度，不参与阶段判定。

- `story_order` 与 `audience_order` 可以不同。
- `continuity_mode=reset` 时，不得生成虚假的跨单元连续人物成长；项目总谱只总结可被证据支持的重复机制/主题情绪模式。
- `continuity_mode=mixed` 时，每个跨阶段出现的人物状态必须显式填写 `continuity_group`；只有相同 group 的相邻有证据节点才允许连成连续河。某阶段没有该人物状态时必须留空断开，不得跨缺失节点补线。

## 最终 HTML 门槛

Render the final HTML only when `meta.workflow_stage=locked_audit` and `script_audit.lock_status=LOCKED`。此时 `narrative_topology`、`audience_segments`、`phase_events`、`phase_links`、`global_emotional_arc` 为必需字段。`global_emotional_arc` 只保存 summary / throughline / major_turn / ending_residue 等收束语义，情绪河节点由渲染器唯一地从 `phase_events` 聚合，禁止再生成第二套独立情绪节点。`rhythm_causality` 仍是详细剧情因果依据，`phase_events` 只负责语义聚合。

旧 `emotion_field` 在最终 HTML 中**废弃**。它可以作为历史/兼容输入保留在内部数据中，但最终渲染器不再用整张网格波浪代替人物情绪。

Default formal delivery remains 项目名-完整剧本.md；完整捆绑生产仍只正式交付 项目名-完整剧本.md + 情绪图谱-项目名.html，不额外暴露 JSON/账本。


## v1.1 通用化硬规则

1. **开放情绪语义**：基础 12 色只负责视觉，不是完整心理枚举。新出现的内疚、嫉妒、怀旧、释然、悔恨等不得靠改 HTML 新增专用颜色；用开放语义 + family/blend + coordinates 表达。
2. **证据置信度**：情绪可以是 `EXPLICIT|SUPPORTED|INFERRED|UNKNOWN`，并配 `high|medium|low` confidence。HTML 只改变透明度/边缘清晰度，不把低置信度升级为事实。
3. **多驱动阶段**：`drivers[]` 可为 0/1/N；阶段关键帧可用 `driver_ref` 绑定具体剧情驱动。HTML 不再假设一个阶段只有一个 trigger。
4. **叙事层开放**：`narrative_layers` 用少数视觉 family 表达现实、记忆、主观、假设、记录或自定义层；具体标签由作品生成。梦境只是 subjective 的一种，不允许写作品特判。
5. **拓扑双层语义**：`phase_links.family` 为稳定视觉族，`kind` 为开放机制；新剧本出现新 mechanism 时不需要改 CSS。
6. **Global Arc 派生**：所有数值情绪节点只能由 phase state 派生；AI 只能补 throughline / major turn / ending residue 的文字总结。
7. **Semantic Zoom**：超过约 12 个阶段时，优先读取 `phase_clusters[]`；若未提供，只允许 UI 做无语义的技术窗口，不得由 HTML 自行创造“第一幕/第二幕”等聚类。
8. **修订前处理**：DOCX 若包含 Track Changes、删除线、颜色修订或批注，应先运行 `scripts/resolve_revision_docx.py`。颜色不具有全局固定含义，只有用户或文档自身明确图例时才允许传入 color policy。
