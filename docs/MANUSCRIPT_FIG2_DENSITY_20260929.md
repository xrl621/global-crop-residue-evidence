# 旧正文 Fig 2 候选：直接还田的产量–SOC 联合响应分布

**历史单图版：** 其后曾扩为[总体＋三作物组图](MANUSCRIPT_FIG2_MULTIPANEL_20260929.md)；两版均已从正文 Fig. 2 定稿位置撤下，现行问题见[三路径重设契约](MANUSCRIPT_FIG2_REDESIGN_20260929.md)。本页保留单图与拆分边缘分布文件，供版式回退和溯源。

**当前版式：** 一张连续的联合分布图，不再把总体、作物、气候、地区和样本数排成多个清单式面板。图面只保留坐标、零效应参考线、标题层散点、视觉密度线以及两个边缘分布；统计口径和例外点处理移入图注。旧三面板分层图保留在[上一版说明](MANUSCRIPT_FIG2_JOINT_20260929.md)，其作物与气候结果可作为后续独立结果图的素材，不再占正文 Fig 2。

[整图 PNG](../figures/manuscript_fig2_joint_density_20260929/fig2_joint_density.png) · [可编辑 SVG](../figures/manuscript_fig2_joint_density_20260929/fig2_joint_density.svg) · [PDF](../figures/manuscript_fig2_joint_density_20260929/fig2_joint_density.pdf)。先在同一画布组好整图，再按[固定槽位](../figures/manuscript_fig2_joint_density_20260929/panel_slots.json)拆出[中央散点](../figures/manuscript_fig2_joint_density_20260929/paired_scatter.svg)、[上缘产量分布](../figures/manuscript_fig2_joint_density_20260929/yield_marginal.svg)和[右缘 SOC 分布](../figures/manuscript_fig2_joint_density_20260929/soc_marginal.svg)，均有 SVG/PDF/PNG；拆件需要按槽位尺寸保留白边拼合。图面无总标题、a/b/c 编号、样本数字贴标或重复图例。粉色上缘曲线对应产量变化分布，蓝色右缘曲线对应表层 SOC 储量变化分布；虚线标出全部标题的中位响应。紫色等密度线只用于显示散点集中位置，**不是置信区间**。浅粉色右上象限标识两终点均高于移除对照。

## 可用于正文的结果句

在公开二次汇编的三种谷物直接还田—移除比较中，产量和表层 SOC 储量的论文标题层中位响应分别为 **+7.58%** 和 **+9.27%**；215 个来源标题中，172 个（80%）在两终点上均呈正方向。联合分布显示响应有较大离散度，因此这里可以说“多数来源同向改善”，不能说“所有地区必然协同”或推断两个终点之间存在因果促进。

## 图注草案

**Fig. 2 | 直接还田相对秸秆移除的产量与表层土壤有机碳联合响应。** 每个紫色点为一个来源标题内配对比较的产量和表层 SOC 储量 log 比率中位数，经 `100 × [exp(lnRR) − 1]` 转换为百分比。共从 1,151 条配对比较聚合出 215 个唯一来源标题；图窗内显示 213 个，另 2 个极端标题未显示但保留在方向计数和总体中位数中，完整值见[图源数据](../figures/manuscript_fig2_joint_density_20260929/fig2_joint_density_source.csv)。上方粉色、右侧蓝色曲线为显示点的核密度估计；对应虚线为全部 215 个标题的中位数。水平和垂直灰线表示零变化，浅粉背景表示两个结局均高于移除对照。紫色等密度线仅描述点的集中区域。标题是平衡汇总单位而非独立田间试验；本图来自[公开二次数据源](https://github.com/davidencarnation/sustainable_ag_SOC_yield_meta_analysis)，未做逐篇原文核验或逆方差 Meta 合并，不报告路径间因果差异。Source data are provided as a Source Data file.

## 统计和图形边界

- 作图范围为产量 −45% 至 +90%、SOC −20% 至 +65%；仅影响可见点，不影响中位响应、四象限数或其他源表。超出范围的两标题在 `visible` 字段标记为 `False`，不被静默删除。
- 边缘分布和等密度线只在 213 个可见标题上做核平滑；其形状受带宽影响，不能读作后验概率或不确定性区间。四象限计数 172/7/27/9 基于全部 215 标题。探索性 Spearman ρ = 0.20，但未调节作物、地区、管理细节与研究依赖，因此不据此作机制解释。
- 原数据是已发表资料的二次整理，亚洲来源占 187/215；该图不是全球代表性处理效应，也不覆盖生物炭、露天焚烧、N₂O、CH₄ 或政策效果。跨作物、气候和地区的分层将在后续结果图中单独回答，不挤在这张图内。
- 图尺寸 183 × 140 mm；SVG/PDF 保留可编辑文字。边缘分布与主散点共享精确数据边界，[几何记录](../figures/manuscript_fig2_joint_density_20260929/marginal_geometry.json)可核；整图 PDF 字体最低 7 pt、文本碰撞审查为 0 失败／0 警告。复算：`python scripts/plot_manuscript_fig2_joint_density.py --qa-scripts <nature-figure脚本目录>`。
