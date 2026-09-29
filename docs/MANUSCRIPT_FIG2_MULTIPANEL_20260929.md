# 正文 Fig. 2 组图：还田／地表保留的产量–SOC 联合响应

**当前版（2026-09-29）。** 从单一总体联合分布扩为一张完整组图：总体为主视觉，玉米、水稻、小麦为同尺度的作物分层小图。图中无总标题、无 a/b/c 编号；[整版 PNG](../figures/manuscript_fig2_multipanel_20260929/fig2_multipanel.png)、[SVG](../figures/manuscript_fig2_multipanel_20260929/fig2_multipanel.svg)、[PDF](../figures/manuscript_fig2_multipanel_20260929/fig2_multipanel.pdf)。整版 183 × 155 mm，另有 600 dpi TIFF。

四块内容先在同一画布排版，再按[固定槽位](../figures/manuscript_fig2_multipanel_20260929/panel_slots.json)拆出无编号可编辑文件：[总体](../figures/manuscript_fig2_multipanel_20260929/global_joint.svg)、[玉米](../figures/manuscript_fig2_multipanel_20260929/maize_joint.svg)、[水稻](../figures/manuscript_fig2_multipanel_20260929/rice_joint.svg)、[小麦](../figures/manuscript_fig2_multipanel_20260929/wheat_joint.svg)；每块同时有 PDF 和 PNG。拼接时保留槽位白边，不要自动紧裁。

## 图要回答的问题

公开二次汇编中的秸秆还田／地表保留相对移除，是否在产量与表层 SOC 储量上呈共同正向响应；这一方向是否只由一种主要谷物造成？左侧每点是一个来源标题的两结局配对中位响应；上缘与右缘分别显示产量、SOC 的单变量密度。右侧三图是在作物×标题内汇总后的相同两个终点，所有小图与左侧共用坐标范围；菱形是该作物的两个边际中位值构成的描述性位置，**不代表某个真实试验或联合置信区间**。浅粉区域是双正向象限；等密度线只显示点集中在哪里，不是置信区间。

**可报告的描述性结果：** 总体 215 个来源标题中有 172 个双正向（80%），标题层产量、表层 SOC 储量的中位响应分别为 +7.58% 和 +9.27%。按作物×标题单元，玉米 91/109、水稻 56/71、小麦 82/107 双正向，对应约 83%、79%、77%。三个作物的分布都集中在双正向象限；不据此宣称作物间效应差异显著、所有产区均成立或气候因果调节。

## 数据口径与图注要点

来源为 [Encarnation 等公开的二次数据整理](https://github.com/davidencarnation/sustainable_ag_SOC_yield_meta_analysis)。从其中可辨认的 `Incorporated vs removed` 与 `Surface-retained vs removed` 比较提取同时报告产量与表层 SOC 储量的三谷物记录，共 1,151 条配对比较。左图先在来源标题内取每个终点 log 比率中位数，得到 215 个唯一标题。作物图先在作物×标题内取中位数，得到 287 个作物×标题单元；同一标题可能贡献多个作物，**287 不是独立论文数**。原始 log 比率转换为 `100 × [exp(lnRR) − 1]`。

所有图使用相同显示范围：产量 −45% 至 +90%、SOC −20% 至 +65%。总体图可见 213/215 标题；玉米 107/109、水稻 70/71、小麦 107/107 作物×标题单元可见。超窗记录保留在[总体衍生数据](../data/processed/manuscript_fig2_joint_20260929/paper_global.csv)和[作物衍生数据](../data/processed/manuscript_fig2_joint_20260929/paper_crop.csv)及全部方向、中位数计算中，没有被分析删除。核密度仅由可见点生成，受带宽和显示窗影响。精确计数、源文件哈希、分组中位值见[渲染清单](../figures/manuscript_fig2_multipanel_20260929/render_manifest.json)。脚本另在本地输出逐点绘图源 CSV，遵循仓库对第三方逐记录衍生表的上传限制。

这仍是**标题平衡的二次数据描述**，不是逐篇核实处理臂和方差后的田间试验 Meta 分析，也不是全球代表性管理效应。现有亚洲来源集中，Fig. 2 不承载生物炭、露天焚烧、N₂O/CH₄、政策效果或气候因果结论。下一结果图再分析不同管理路径，而不是把三路径虚构到这张图中。

## 图形质量与复算

脚本：[plot_manuscript_fig2_multipanel.py](../scripts/plot_manuscript_fig2_multipanel.py)。运行：`python scripts/plot_manuscript_fig2_multipanel.py --qa-scripts <nature-figure脚本目录>`。右列三个作物绘图区的宽、高、左缘和间距通过 1.5 pt 对齐门槛；总体图的两条边缘分布与散点绘图区严格共边。[对齐报告](../figures/manuscript_fig2_multipanel_20260929/fig2_multipanel.alignment.json)可核。整图与四张拆分 PDF 的可编辑文字最低 6.7 pt，最终 PDF 文字碰撞审查均为 0 失败／0 警告；SVG 保留文字元素。脚本静态检查 21 项通过、0 警告。
