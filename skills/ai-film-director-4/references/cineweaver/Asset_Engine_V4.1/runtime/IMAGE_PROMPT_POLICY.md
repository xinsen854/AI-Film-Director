# IMAGE PROMPT POLICY

## General

Image prompts inherit the approved project world, era, materials, palette, and visual style.
The reusable asset should be neutral enough to survive many downstream SHOTs.

## Mandatory character-board contract

人物基础资产 Prompt 必须直接服从 `references/contracts/asset-prompt-contract.md`。当前合同固定包含：

- `画面一：大型3/4面部身份近景`；
- `画面二：正面完整身体参考，从颈部以下至脚部，故意不显示头部`；
- `画面三：背面完整身体参考`；
- 中性灰色背景、平坦均匀照明、真实未经修饰皮肤；
- 不把电影灯光、镜头效果、胶片颗粒、美颜或文字烘焙进基础身份板。

本文件只补充资产类别的 Prompt 约束，不得改写上述合同。

## Character board

Preserve:
- identity;
- silhouette;
- hair;
- base wardrobe;
- stable marks;
- persistent state when the state genuinely needs its own board.

Do not bake in:
- current-shot expression;
- current-shot pose;
- current-shot camera;
- current-shot lighting;
- current Beat acting.

## Location board

Define location identity, view coverage, functional zones, stable geography, and landmarks.
Do not define the current SHOT composition or camera angle.

## Prop board

Define shape, scale, material, function, and persistent state.
Do not define current-shot hand action.

## Project-conditional visual safety

Legacy workflows may specify colored-pencil / weakened-identifiability face treatment. In V4.1 this is **project-conditional**:
- if the Project Creative Bible explicitly locks that treatment, inherit it;
- if the project locks 3D, anime, CG, photorealistic, stylized, or another approved visual treatment, preserve that style instead;
- Asset Engine never imposes colored-pencil face treatment globally.
