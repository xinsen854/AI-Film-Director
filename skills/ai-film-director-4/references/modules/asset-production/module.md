# Asset Production｜融合版执行层

## 职责

本模块只负责**执行** CineWeaver **Asset Engine V4.1** 已经确定的资产Prompt与媒体生成，不再承担资产定义权。

唯一资产事实源是：

```text
assets/ASSET_LIBRARY.json
```

用户可读资产文件由：

```bash
python scripts/render_asset_library.py --input assets/ASSET_LIBRARY.json --output assets/ASSET_LIBRARY.md
```

固定渲染。不得建立第二个 `asset_registry.json` 或第二套平行资产库。

## 一、绝对禁止越权

Asset Engine V4.1 已经确定的以下内容，本模块不得重新设计：

- `asset_id / state_id`；
- A/B/G/S/P/V分类；
- 人物故事身份、稳定外貌身份和母资产关系；
- 场景稳定几何与功能区；
- 道具结构与世界规则；
- MASTER → STATE谱系；
- V系列文字声线身份；
- `image_prompt` 的故事与资产事实。

**不得重新创建或改写 asset_id。** 如果上游资产缺失或Prompt本身错误，返回Asset Engine V4.1修正，不在生成阶段临时造一个新资产。

## 二、输入

读取当前 `assets/ASSET_LIBRARY.json` 中需要执行的视觉资产记录：

- `character_assets`；
- `persistent_states`；
- `location_assets`；
- `prop_assets`；
- `g_assets`。

每条视觉资产至少使用上游已有：`asset_id/name/image_prompt/image_status/image_file` 及身份/结构/状态事实。

V系列 `voice_assets` 是纯文字资产：不调用图片、视频或音频生成，不创建伪媒体文件，不占媒体参考槽。

## 人物基础资产合同不可降级

执行人物基础资产前必须读取 `references/contracts/asset-prompt-contract.md`。宿主调用所需的**技术转换**只能改外层格式，**不得删除、移除、反转或弱化**合同中的身份板结构，尤其不得删除：`大型3/4面部身份近景`、`正面颈部以下至脚部并故意不显示头部`、`背面完整身体参考`以及中性灰背景/平坦照明要求。

如果宿主接口无法表达该合同，保持 `PROMPT_ONLY` 或返回上游，不得擅自改成普通全身人物图。

## 三、资产生产方式

根据用户确认的资产生产方式：

- `prompts_only`：不调用生图，保持 `image_status=PROMPT_ONLY`；
- `core_assets`：只生成核心人物、主要重复场景、关键道具和当前必要持续状态；
- `all_required`：生成当前生产范围全部必要视觉资产；
- `mixed`：先绑定用户真实媒体，再补缺失资产；用户真实媒体在写入GENERATED前先复制为项目内Canonical文件到 `assets/generated/`，不长期引用项目外路径。

宿主没有图像生成能力时必须保持 `PROMPT_ONLY`，不能写成GENERATED。

## 四、实际生成

对每条需生成视觉资产：

1. 原样读取 Asset Engine V4.1 的 `image_prompt`；
2. 仅把宿主调用所需格式做技术转换，不改变身份、结构和状态意义；
3. 调用宿主图像生成能力；
4. 检查生成物是否满足当前资产事实；
5. 成功：真实图片必须落入 `assets/generated/`，写 `image_status=GENERATED` 与 `image_file`，并记录实际 `file_size / width / height / mime_type / sha256`；
6. 标记GENERATED前必须运行真实媒体校验；文件不能解码、路径逃逸、元数据不一致时不得写GENERATED；
7. 失败：写 `image_status=FAILED`，保留Prompt，并记录失败原因；
8. 未生成：保持 `PROMPT_ONLY` 或 `MISSING`；
9. 每次状态回写后重新运行 `render_asset_library.py`，保证 `ASSET_LIBRARY.md` 与JSON一致。

## 五、接受检查

### 人物
- 同一人物多视图是否仍是同一个人；
- 脸型、发型、体型、基础服装和稳定识别点是否一致；
- 是否错误继承了当前镜头Pose、夸张表情或分镜构图。

### 持续状态
- 是否真正继承母资产；
- 只改变 `visible_change` 明确允许改变的部分；
- `unchanged_facts` 是否保持；
- 是否把轻微状态夸张成另一种状态。

### 场景
- 多视图是否能验证同一稳定几何；
- 门、窗、柜台、功能区、landmark相互关系是否一致；
- 是否错误把人物或多视图排版变成场景固定元素。

### 道具/G资产
- 几何、尺度、材质、功能边界是否正确；
- 是否出现资产库未允许的新结构、文字或能力。

## 六、Canonical文件

真实生成文件必须使用稳定工程名，例如：

```text
A001_许程_人物母板_V01.png
A002-ST001_许国安_右手震颤状态_V01.png
S001_老街钟表店_场景母板_V01.png
P001_营业木牌_道具母板_V01.png
```

不得用随机UUID作为最终Canonical文件名。

`image_status=GENERATED` 时 `image_file` 必须真实存在于 `assets/generated/`，且能被图像解码器验证；记录的MIME、宽高、文件大小和SHA256必须与真实文件一致。文件不存在、伪图片、扩展名与真实格式不一致或校验字段不一致时不得交给Shot/Segment当媒体参考。

校验命令：

```bash
python scripts/validate_asset_files.py --project-root <project_root>
```

## 七、资产板防污染

多视图资产板只负责资产身份/空间/结构。下游视频Prompt必须明确：

- 不继承多宫格、拼贴、边框、标签；
- 同一人物的多视图不得生成为多人；
- 场景板鸟瞰/结构图不得直接变成电影构图；
- 素材只负责它在Asset Library定义的职责。

## 输出

本模块不新增资产文件体系，只更新：

- `assets/ASSET_LIBRARY.json` 中的 `image_status / image_file / generation_error / file_size / width / height / mime_type / sha256`；
- 真实生成的视觉资产文件；
- 经Renderer同步后的 `assets/ASSET_LIBRARY.md`。

## 比例参考执行（可选）

若现有主资产的 `downstream_metadata.scale_reference` 通过 Size-ref necessity gate，则它作为**辅助参考媒体**沿用同一资产生产链：读取自己的 `image_prompt`，生成结果仍落入 `assets/generated/`，`GENERATED` 时必须记录并校验真实文件元数据。它使用 `SCALE-...` reference ID，不建立新的 A/B/G/S/P/V 主资产家族。未满足必要性、宿主无生图能力或尚未生成时保持 `PROMPT_ONLY`；不得为了“尺寸一致”给普通道具批量新增比例板。

## 八、VFX Location 光线 QA（按需）

仅当当前生产任务明确进入 VFX / plate integration 工作流时，对 location still 增加一层 light-selection QA：检查主光方向、软硬、曝光、关键区域可读性，以及是否与 source plate 的环境光逻辑冲突。已有合格场景资产直接复用；不得为了套流程强制重做。

公开 FIELD 工作流中“多生成、按光线选”是生产经验，不是 AFD 的固定批次要求，也**不要求必须使用 Soul Cinema 或任何固定图像模型**。模型选择仍服从当时已验证的 Image Model Surface / 用户已有工具；当前 AFD 没有图像 API 时保持现有 `PROMPT_ONLY / 宿主生成` 边界。

## 九、Project Asset Baseline（4.7 项目范围合同）

当 `state/PROJECT_SCOPE.json` 存在时，唯一 `assets/ASSET_LIBRARY.json` 必须先作为**全项目资产基线**建立，再进入逐 PU 的 Asset Delta。不得用当前 PU 的局部资产切片覆盖项目唯一资产库。

项目级资产需求 Expected Set 写入 `state/project_asset_requirements.json`。它只记录锁稿证据、需求类型、场景范围与需求 ID；**不得包含 image_prompt、媒体文件、Canonical asset_id 或第二套资产定义**。实际资产定义与 Prompt 仍只属于 `ASSET_LIBRARY.json`。

项目基线要求：

- `ASSET_LIBRARY.contract_version` 必填且严格等于 `4.3`；缺失或其它版本直接 FAIL，不允许降级到宽松验证；
- `ASSET_LIBRARY.source.production_range = PROJECT`；
- `ASSET_LIBRARY.project_baseline.requirement_bindings` 必须覆盖全部 Project Asset Requirements；
- 人物基础、人物状态、地点、道具、实体、声音需求必须绑定到对应资产家族；人物状态不能拿人物母资产冒充；
- 每个绑定资产的 `use_scope` 必须覆盖该需求实际出现的 Scene；
- `existing_media` 每一项必须显式记账：属于资产的媒体复制到项目内 canonical 文件并绑定到 `reference_media`；非资产素材允许 `NON_ASSET_MEDIA`，但必须写明理由；
- 基线锁定后写 `state/project_asset_baseline.json`。逐 PU Asset Delta 允许新增资产、更新 Prompt/生成状态/真实文件，但不得删除基线资产、改写既有需求绑定或缩窄已锁需求的 Scene 覆盖。

校验/锁定：

```bash
python scripts/project_asset_baseline.py --project-root <project_root> validate-requirements
python scripts/project_asset_baseline.py --project-root <project_root> validate-library
python scripts/project_asset_baseline.py --project-root <project_root> lock
python scripts/project_asset_baseline.py --project-root <project_root> validate-lock
```
