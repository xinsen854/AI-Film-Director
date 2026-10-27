# Final Hard QC｜仅最终交付硬错误

本层只阻断会让最终成片/交付客观错误的情况，不规定导演怎样表达。

## 已由既有链路负责（不重复实现）
- 总集数不对：Production Ledger / Final Delivery Gate。
- 漏剧情、漏场、漏重要对白、提前Reveal：Story Coverage Ledger。
- 最终交付与账本不一致：Production Ledger / Final Delivery Gate。

## 本项新增的最小硬检查
- 用户明确提供时长上下限时，实际时长越界；没有明确上下限时不自行发明容差。
- `15S / 30S_BLOCK`只作为GU最大窗口；连续SH机械填满同一模型上限且没有逐镜`duration_basis`时阻断。明确说明不同戏剧依据的有意等长长镜头不误杀。
- 已完成单元缺SH、GU、PH或最终视频Prompt结构。
- 资产模式要求实际生成时，必要资产仍为PROMPT_ONLY / FAILED / MISSING。
- 只阻断“同一轴线、摄影机侧明确跳边且未声明允许越轴”的显性严重连续性错误；完整连续性检查留给后续专项。
- 剧集连续三个单元机械复用同一Scene Intelligence结构，且后两单元没有关系/权力/信息/节拍推进；有明确“有意重复理由”时不阻断。电影不做此自动模板判定。

## 禁止扩张
- 不检查镜头美不美、是否足够电影化。
- 不固定镜头数量、镜头时长、Prompt字数、资产数量、微表情数量。
- 不因为没有Scene Intelligence证据就凭空判断重复剧情。
- 不把普通相似、伏笔回收、平行结构自动判为硬错误。

- GU对白身份完整性：Member SH中的逐字对白必须在最终GU按原顺序保留说话人；已有V-series时保留对应V-ID；不得丢speaker、串错人或压平成匿名字符串。


## 模型表面预检
若当前GU绑定了 `references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json` 中的 profile，模型参数合法性由 `scripts/model_preflight.py` 做机械检查；Final Hard QC只消费其FAIL结果，不重新猜模型能力。
