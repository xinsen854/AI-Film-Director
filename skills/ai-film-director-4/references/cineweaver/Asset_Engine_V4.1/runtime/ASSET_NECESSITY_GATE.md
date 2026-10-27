# ASSET NECESSITY GATE

Create a formal visual asset only when at least one is true:
- it will be reused across SHOTs / scenes;
- identity drift would break the story;
- visual continuity is important;
- it is a key character, location, prop, creature, entity, or crowd definition;
- a visible state persists across multiple SHOTs;
- the target model is known to be unstable for this object without a reference;
- downstream repeatedly needs the same visual reference.

Default to text-only description for:
- ordinary cups, chairs, generic phones, background cars;
- one-use background objects;
- single-shot expression;
- temporary pose;
- current Beat reaction;
- ordinary lighting fluctuation;
- minor wrinkles or momentary dirt that does not affect recognition.

The gate asks: **Would failure to formalize this asset materially threaten identity, continuity, reuse, or generation stability?**
If no, do not create a formal asset.

## Size-ref necessity gate

Size-ref 只在极端跨主体尺度本身是当前生产稳定性风险时启用。若普通物体可由可靠尺寸 + 经计算的人体地标说明，或当前镜头并不需要同时证明两个主体的比例，则不创建 Size-ref。Size-ref 是已有资产的 supporting reference，不建立新资产家族。
