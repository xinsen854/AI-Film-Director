# CURRENT_GU_ONLY 防污染合同

本合同只做工程隔离，不改变导演创作与Prompt格式。

每个GU最终执行数据只允许包含当前Member SH真正需要的事实。校验器从结构化Storyboard本身反向推导当前与未来范围，不相信模型自行声明白名单。

阻断范围仅包括：
- 当前GU提前包含后续SH的剧情执行事实；
- 当前GU提前包含后续SH独有对白；
- 当前GU提前包含后续SH独有声音；
- 当前GU提前激活后续SH才出现的 `-ST` 持续状态资产；
- 当前GU出现 Information Ledger 中仍受保护的 `protected_literals`，包括把秘密写进“不要出现……”等负面限制；
- 当前Member SH实际调用的资产参考图Prompt本身提前包含仍受保护的Reveal内容；
- 当前调用的 MASTER / STATE 参考图Prompt提前混入同一资产族未来 STATE 的 `visible_change`；
- 当前调用的 STATE 若其 `state_start` 尚未到达，直接阻断。

防过度限制：
- 当前Member SH自身已经使用的对白、声音、状态允许进入Prompt；
- 后续再次重复但当前已存在的事实，不因“后续也出现”而误判；
- 未在当前GU出现、且未被当前Member SH调用的资产不造成错误；
- 当前STATE自身已经生效的 `visible_change` 允许进入参考图Prompt，不因同资产族后续还有状态而误判；
- 不扫描泛化情绪词、导演方法或普通公共词，不据此限制创作。
