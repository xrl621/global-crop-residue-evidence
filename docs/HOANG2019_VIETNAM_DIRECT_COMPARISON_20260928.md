# 越南水稻还田—焚烧原文直接比较：均值层审核（2026-09-28）

## 为什么单列

[Hoang 等，*Archives of Agronomy and Soil Science*，doi:10.1080/03650340.2018.1487553](https://doi.org/10.1080/03650340.2018.1487553) 的[原文 PDF（顺化大学托管）](https://csdlkhoahoc.hueuni.edu.vn/data/2018/11/Incorporation_of_rice_straw_mitigates_CH4_and_N2O_emissions_in_water_saving_paddy_fields_of_Central_Vietnam.pdf)报告越南承天顺化省 Huong An 村的同一项三重复裂区田间试验。两季（夏稻 2014、春稻 2015）× 四个**相同水分制度内**的秸秆翻埋与田间焚烧比较，Table 3 给 CH₄/N₂O 季节累计排放，Table 4 给稻谷产量。两种管理都使用 **5 t/ha 稻草**；同一水分层内肥料、作物和季节相同。Table 1 的季节标题与 Table 2–4 的年份标签不完全一致，提取采用结局所在的 Table 3–4 标签，并保留这个来源内部疑点。

已从原文逐臂录入 **24 条均值比较 = 2 季 × 4 水分层 × 3 结局**，但它们只属于 **1 项独立试验**，不是 24 项新研究。本地原文 PDF SHA-256 为 `55d404ad9815469654874e392f696a904d19327b062ea1a7345536cdc2800748`；PDF 放在忽略上传的 `data/raw/hoang2019_vietnam_primary.pdf`。原文数字与换算在[均值比较表](../literature/primary_extractions/hoang2019_vietnam_direct_vs_burning_MEAN_ONLY_NOT_MAIN.csv)及[生成脚本](../scripts/extract_hoang2019_vietnam_mean_only.py)中。运行 `python scripts/extract_hoang2019_vietnam_mean_only.py --check` 可检查表；本地 PDF 存在时可加 `--pdf data/raw/hoang2019_vietnam_primary.pdf` 校验来源哈希。

## 观察信号与不能跨过的边界

同水分层内，还田相对焚烧的 8 个季节/水分单元，**产量、土壤季节 CH₄ 与 N₂O 均为 8/8 正向**。未经独立性加权的单元中位百分比仅供核数：产量约 +8.7%，CH₄ 约 +21.2%，N₂O 约 +37.2%。它们是一个试验内部反复观测的描述，不是越南或全球的合并效果，更没有因重复水分层而增加独立试验数。

原文 Methods 说收集数据以均值 ± SE、n=3 处理，但 **Table 3/4 的季节累计指标只列均值和显著性字母，未列各处理臂的具体 SE/SD**。不能用字母或二次数据库的插补方差生成精确置信区间。因此 CSV 的 `treatment_sd`、`control_sd`、`variance_lnrr` 均为空，状态为 `PRIMARY_MEAN_ONLY_DIRECT_PATHWAY_COMPARISON_NOT_MAIN`；**不进入 607 条移除参照主库，也不进入 485 条严格描述层或逆方差 Meta 分析**。

本研究的对照是**焚烧**，不是移除；它直接回答“翻埋相对于焚烧”的问题，不能分别当作“翻埋对移除”和“焚烧对移除”的两项效应。Table 3 测量的是后续稻季田间土壤气体，不包括秸秆燃烧瞬时排放、上游投入或 SOC 变化；**不能据这两个土壤气体端点判断全路径哪种技术净减排**。N₂O Table 3 单位为 `kg N2O ha-1`，与 Xiong Table 2 的 `kg N2O-N ha-1` 不能直接合并绝对量。

## 决策与后续

这项越南试验为跨技术头对头比较提供地区和水分分层信息，现阶段只作为**原文已核均值层**。下一步查补充数据或联系作者获取 Table 3/4 各臂 SE/SD（联系作者需另行确认），同时核对二次库 StudyID 213 的处理层遗漏；获取真实方差并核定结局边界后，才能考虑纳入正式头对头模型。来源单页或摘要中宣称的减排百分比不能替代同水分层对照计算。
