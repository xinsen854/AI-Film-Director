# Quality & Delivery｜融合版

## 职责

CineWeaver Final QC负责Shot/Prompt/Asset等内容硬检查；AFD Quality & Delivery负责项目级自审、Owner Layer最小返工、Production Ledger Checkpoint和FULL模式最终八件文件交付。QC过程保留在内部，不交付用户。

## 一、Director Self Review

只检查真实创作问题，不用形式主义替导演决策：

- 场景是否发生有效变化；
- 人物目标、阻力、策略变化和接收者反应是否存在；
- 微表演是否由刺激引起而非随机堆叠；
- Blocking、轴线、屏幕方向、动作因果是否可理解；
- 镜头是否只会机械正反打；
- 声音是否属于当前空间/动作；
- 当前情绪目标是否有故事承载；
- 人物、道具、场景与信息是否出现无解释重置。

发现问题只修最小负责层。

## 二、CineWeaver Hard QC

正式分镜完成后必须运行 `references/cineweaver/Final_QC_Engine_V1.3/` 的现有检查，并至少覆盖：

1. `ASSET_LIBRARY.json` 与 `ASSET_LIBRARY.md` 存在且为唯一资产权威；
2. V系列没有媒体泄漏，没有图片/音频/视频文件，没有占参考槽；
3. GENERATED视觉资产的 `image_file` 真实存在；未生成媒体没有伪造成真实引用；
4. Spatial Narrative只有Router判定ACTIVE时才要求存在；简单场景不得因缺Spatial Plan失败；
5. `storyboard/<unit>_STORYBOARD.json` 真实存在；
6. 必须执行 `python scripts/validate_cineweaver_storyboard.py --input ...` 并PASS；
7. 必须执行 `python scripts/render_storyboard.py --input ... --output ...`，最终Markdown由Renderer生成；
8. 每个SH保留完整V4.8-derived固定栏目且内容为当前镜头具体事实；
9. `FIELD_BOILERPLATE`、`SUMMARY_COLLAPSE`、`GLOBAL_PROMPT_POLLUTION`、`REFERENCE_BINDING_FAILURE`、`VOICE_MEDIA_LEAK` 均不存在；
10. SH/GU/PH编号结构正确，PH中不存在隐藏剪辑；MULTI_SHOT必须显式CUT；
11. Seedance 2.5单GU≤30秒、Seedance 2.0单GU≤15秒、OTHER有明确Adapter；
11.1 `15S / 30S_BLOCK`只作为最大窗口；连续SH机械填满同一模型上限且没有逐镜`duration_basis`时触发`MECHANICAL_DURATION_QUANTIZATION`；
12. 每个EDIT SHOT只调用当前镜头必要的视觉图片资产，V系列不计入；不设置全局固定数量上限，若目标模型/项目Profile声明媒体容量则按其验证；
13. 锁定对白逐字进入对应执行段，不得改写；
14. Prompt固定结构完整：生成目标/参考素材职责/初始状态/阶段推进/声音/保持一致/局部限制；
15. Prompt执行 `CURRENT_GU_ONLY`，不得批量写入未来事件、无关资产、无关声音或全局连续性；
16. `同上 / 继承上一镜 / same as before / as above / 保持克制 / 按资产库执行` 不得替代可观察事实；
17. 首尾帧、轴线、站位、道具、人物状态和下一镜handoff没有无法解释的冲突。

**不以固定字符下限/上限替代内容质量判断。** CineWeaver V1.5的Final QC以执行事实覆盖和是否摘要塌缩为准；长GU可以很长，短GU也不为凑字数重复灌水。

## 三、Owner Layer + Rerun Matrix｜最小返工

每个FAIL/WARNING必须记录：

```text
issue_id
severity
error_code
owner_layer
affected_ids
reason
rerun_path
do_not_rerun
```

`owner_layer` 必须优先由明确 `error_code` 查固定映射；不得依赖中文/英文错误文案关键词猜负责层。未知错误码安全兜底到 `DELIVERY`，避免误重跑创作上游。结构合同见 `schemas/qc_issue.schema.json`。

允许的 `owner_layer`：

`STORY / AUTHORITY / EMOTION / SCENE_INTELLIGENCE / ROUTER / DIRECTOR / ASSET / SPATIAL / SHOT_SEGMENT / DELIVERY`

| owner_layer | 从哪里修 | 只向下重跑 |
|---|---|---|
| STORY | Story Development | 受影响Authority→情绪→导演链→资产→SH/GU→QC |
| AUTHORITY | Screenplay Authority | 受影响情绪/导演链→资产→SH/GU→QC |
| EMOTION | Audience Emotion | 受影响导演链→SH/GU→QC，不改锁定剧情 |
| SCENE_INTELLIGENCE | Scene Intelligence | 受影响Router→Director Craft→Scene Direction→SH/GU→QC |
| ROUTER | Capability Router | 受影响Director Craft→Scene Direction→必要Spatial→SH/GU→QC |
| DIRECTOR | Director Craft / AFD Scene Direction | 受影响资产状态→必要Spatial→SH/GU→QC |
| ASSET | Asset Engine V4.1 / Asset Production | 受影响资产→相关SH/GU→QC |
| SPATIAL | Spatial Narrative | 只重跑受影响空间结果→相关SH/GU→QC |
| SHOT_SEGMENT | Shot/Segment Engine V1.3 | **只重做受影响SH/GU→Validator→Renderer→QC** |
| DELIVERY | Export | 只重建交付包 |

`do_not_rerun` 必须保护无关已完成单元。单镜格式或GU Prompt问题禁止从剧本重新跑。

`affected_ids` 只用于定位最小受影响范围，必须识别：`EP / PU / SC / ST / DB / I / SH / GU / Asset(A/B/G/S/P/V及其-ST状态)`；它不改变owner判定，也不扩大返工路径。

## 四、Production Ledger与Checkpoint

每个生产单元在Checkpoint前必须确认：

- 正式编剧剧本已落盘；
- Scene Intelligence / Router / Director Craft / Scene Direction当前需要的状态已落盘；
- `assets/ASSET_LIBRARY.json` 可用且已渲染；
- 结构化SH/GU/PH JSON通过Validator；
- 正式分镜Markdown由Renderer生成；
- Final QC无BLOCKER。

电影用真实自然生产单元起止秒数写 `PRODUCTION_LEDGER.json`；剧集登记完成集号。账本只负责覆盖，不机械规定镜头时长。

`pipeline_state.json` 使用 `story_authority_ready / asset_library_ready / scene_intelligence_ready / director_craft_ready / completed_units` 与真实文件保持一致。

## 五、内部文件与用户交付

以下全部内部保留但不交付：Project Brief、Creative Bible、Scene Intelligence、Router、Director Craft状态、Spatial结果、Asset JSON、Storyboard JSON、Final QC、Production Ledger/Index、Tail State。

FULL模式用户交付必须由：

```bash
python scripts/build_exports.py --project-root <project_root>
```

生成，且只能出现：

- `01_项目需求确认单.md`
- `02_剧本审查与修改结论.md`
- `03_正式编剧剧本.md`
- `04_整合导演剧本.md`
- `05_双层情绪规划图.html`
- `06_资产总表与详细生成提示词.md`
- `07_正式分镜与视频模型最终Prompt.md`
- `08_Story_Coverage_Ledger.html`
- `assets/`（仅存在真实生成视觉资产时创建）

缺源成果必须FAIL，不得写“暂无”伪装完成。

QUICK模式使用`python scripts/run_pipeline.py --project-root <project_root>`验证当前已有成果，但不调用`build_exports.py`，不生成或伪装正式八件交付。

## 六、完成声明

只有当前请求范围真实文件存在、Validator/Renderer成功、Final QC无BLOCKER、Production Ledger与实际覆盖一致时才能说“本单元完成”。整个项目只有覆盖用户确认的全部时长/集数时才能说“项目完成”。


## Final Hard QC（最终交付硬门）

最终交付除既有Production Ledger与Story Coverage外，运行`scripts/hard_delivery_qc.py`。只检查`references/contracts/final-hard-qc.md`列出的硬错误，不把导演偏好、镜头美学或固定模板升级为交付硬门。
