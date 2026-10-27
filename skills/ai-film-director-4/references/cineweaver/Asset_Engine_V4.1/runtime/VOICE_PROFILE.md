# V-SERIES TEXT VOICE ASSET｜声音资产

Voice assets are a **separate text-only asset family**. They are not image assets, video assets, or audio-reference files.

## ID

Use three-digit IDs:

```text
V001
V002
V003
...
```

Each speaking A/B character may link to one stable voice asset through `voice_asset_id`.

## Hard media rule

```yaml
asset_family: V
asset_class: TEXT_VOICE_ASSET
media_asset: false
visual_cost_units: 0
seedance_reference_slot_cost: 0
image_file: null
audio_file: null
video_file: null
```

**Current-version hard rule:**
- 不生成音频；
- 不生成图片；
- 不生成视频；
- 不作为 `@图片`、`@视频` 或 `@音频` 参考素材；
- 不占 Seedance 参考素材数量；
- 不占视觉资产预算；
- 只以文字描述进入最终 Prompt 的【声音】部分。

## Voice text fields

```yaml
voice_profile:
  source_status: explicit / inferred / mixed
  confidence:
  perceived_age:
  gender_presentation:
  accent_or_regional_quality:
  register:
  timbre:
  pitch_tendency:
  texture:
  resonance:
  vocal_weight:
  pace:
  rhythm:
  breath_pattern:
  articulation:
  diction_clarity:
  speech_habit:
  sentence_shape:
  emotional_leakage:
  pressure_behavior:
  volume_tendency:
  prohibitions: []
  evidence: []
```

These are stable voice-identity facts, not one-line acting instructions.

当前稳定版至少要求：`perceived_age / gender_presentation / accent_or_regional_quality / register / timbre / texture / resonance / pace / rhythm / volume_tendency / emotional_leakage / pressure_behavior / prohibitions`。缺一项不得通过资产Validator。无法从剧情可靠判断口音时写“普通话，地域口音未指定”，不得臆造。

示例：

```text
A001｜VOICE V001
稳定声线：45岁男性，河北口音，中低音域，低沉、轻微沙哑，胸腔共鸣明显，常态语速偏慢。

本句表演：
人物策略：压住怒气，不愿先暴露恐惧
可听情绪：表面冷静，句尾开始发紧
音量：近距离低声
声源距离：人物相距一臂，近讲收音
语速：前半稳定，后半略加快
重音：“你早就知道”
呼吸：开口前短促吸气
停顿：“你……早就知道？”
对白：“你早就知道？”
```

稳定声线属于V资产；本句表演属于SH/GU对白条目，二者不可混为一段自由描述。

## Evidence policy

Allowed conservative inference sources:
- stated age range;
- physical condition;
- character biography;
- stable personality;
- locked dialogue syntax and rhythm;
- explicitly approved long-term performance identity.

Never invent a specific regional accent or dialect without evidence.
Never invent pathological vocal traits, speech disorders, ethnic markers, or medically specific voice conditions without evidence.

If evidence only supports “older, blunt, economical speaker,” preserve that level of specificity.

## Long-term voice vs current delivery

V-series defines stable identity:
- overall timbre;
- pitch tendency;
- texture / resonance / vocal weight;
- habitual pace and rhythm;
- breath and articulation;
- habitual emotional leakage and pressure behavior.

SHOT / Seedance compiler defines current-line execution:
- current pressure;
- current tone;
- pause / breath;
- interruption;
- current leakage point;
- whether speech is suppressed, clipped, pushed, broken, whispered, or held.

Current delivery may vary, but must not contradict the stable V-series identity without story evidence.
