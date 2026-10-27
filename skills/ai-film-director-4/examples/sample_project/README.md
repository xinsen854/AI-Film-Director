# 30秒剧情驱动时长样例

这是一个可复跑的QUICK模式最小样例，用于展示“总时长服从用户、SH时长服从剧情、GU时长服从模型上限”。用户目标总时长为30秒，但两个真实剪辑镜头分别为11.5秒和18.5秒；`30S_BLOCK`只表示当前GU最多30秒。

验证与渲染：

```bash
python scripts/run_pipeline.py --project-root examples/sample_project
```

QUICK模式只验证当前样例成果，不生成或伪装FULL模式八件正式交付。
