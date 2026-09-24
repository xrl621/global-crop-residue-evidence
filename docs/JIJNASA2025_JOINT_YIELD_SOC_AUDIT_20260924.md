# 同一试验的三路径产量—SOC 联合提取（2026-09-24）

## 来源与独立性

Jijnasa 等在同一个印度 Odisha、OUAT Bhubaneswar 稻—稻裂区试验上发表了[逐季产量论文](https://doi.org/10.14719/pst.9983)和[逐年土壤性质论文](https://doi.org/10.14719/pst.10362)。两文均采用四种水稻建立方式主区、五种残体管理副区；配套土壤论文明确写 20 个处理组合、3 次重复、随机分配，以及 2022–2024 年同一地点和处理。故两个 DOI 是**同一独立试验**，公开表统一为 `jijnasa_bhubaneswar_2022_2024`，不能按两篇论文或四季算多项独立研究。这与同校 2020–2021 年 Nayak 试验的年份、设计和处理组不同，暂按另一项试验记录；后续全模型仍应检验同站点聚类的敏感性。

从[产量文 Table 2](https://www.researchgate.net/publication/396287103_Comparative_assessment_of_establishment_methods_and_residue_management_on_yield_and_profitability_in_rice-rice_cropping_system)按 Kharif 2022、Kharif 2023、Rabi 2023、Rabi 2024 四季提取 S2 焚烧、S3 原位翻埋和 S4 场外制备稻草生物炭后还田，相对 S1 稻草完全移除的边际均值及每季残体副区 `SEm`，得 **12 条产量效应**。从[土壤文 Table 3a](https://www.researchgate.net/publication/398042150_Physicochemical_transformations_of_soil_under_different_rice_establishment_methods_and_residue_management_practices_in_rice-rice_system)按 2022–23、2023–24 两个年度同样三路径提取 S1–S4 SOC 浓度与 `SEm`，得 **6 条 SOC 效应**。原始逐臂转录为 [`literature/primary_extractions/jijnasa2025_yield_soc.csv`](../literature/primary_extractions/jijnasa2025_yield_soc.csv)。两篇论文共用 S1、试验设计和区组，效应必须在 `study_id` 内聚类。

| 路径 / 移除 | 四季产量增幅范围 | 两年度 SOC 浓度增幅范围 | 注意 |
| --- | ---: | ---: | --- |
| 焚烧 | +2.7% 至 +4.8% | +4.9% 至 +4.9% | 不含燃烧烟气/颗粒物 |
| 直接翻埋 | +12.2% 至 +18.7% | +23.9% 至 +24.3% | 同一试验内的方向，非全球效应 |
| 稻草生物炭 | +8.3% 至 +15.0% | +13.9% 至 +17.0% | 原文未报清热解工艺，不能做剂量/工艺调节 |

表中是原始边际处理均值计算的**同一试验描述性变化**，不是统计显著性、Meta 合并效应或三路径全球排名。产量原文说 Kharif 年份“建立方式 × 残体”交互不显著，但边际结果仍平均了四种建立方式；Rabi 结果也按原文边际表提取，没有创造四个独立地点。SOC 是百分比浓度，原文未明确采样深度；公开表留空并标 `soil_depth_unreported`，不能换算成 SOC 储量或年固碳量。生物炭热解工艺未报清，标 `biochar_pyrolysis_process_unreported`。两文分别给出主效应 `SEm`；以三个区组的均值 SE 代表处理不确定性，`SD=SEm×√3` 只是公开表的表示方式，`lnRR` 方差暂按两臂协方差为零；正式模型要测试该假设，并处理年度、季节、结局和共享对照相关性。

## 对整个数据库的影响

公开快照 **492 条/31 项 → 510 条配对效应/32 项独立田间试验**。最初只按前一轮旗标筛查时，焚烧×产量出现 22 条/10 项，似乎恰达计数门槛。**随后逐研究复核推翻了这个判断：**[Shittu & Fasina 2006 原文](https://www.researchgate.net/publication/233322391_Comparative_Effect_of_Different_Residue_Management_on_Maize_Yield_at_Ado-Ekiti_Nigeria)的 Methods 写明试验地在 2001 年清理，待处理残体来自前茬可可、柯拉、山药、玉米等混合植被，而非明确的收获后秸秆。其 2 条玉米产量效应仍保留供追溯，新增 `land_clearing_residue_not_harvest_straw` 后退出核心原料筛查。当前焚烧×产量**20 条/9 项**，再次低于 ≥10 项门槛；直接还田×产量 **41 条/9 项**，生物炭×产量 **48 条/7 项**。这是严格口径起作用而非“丢失数据”。

本轮不运行或宣布全球随机效应估计；旧 +8.6% 结果仍已撤回。当前研究等权的探索性方向为 9 项中 7 项正、2 项负，试验级增幅 −5.42% 至 +15.38%，仅用于决定后续研究级异质性审计。除样本量外，后续还须逐研究复核处理共变、方差近似、同站点/年度依赖、燃烧与移除的可比性、出版质量及地理代表性，再冻结分析集。

检查：`python scripts/export_evidence_database.py --check`；`python scripts/describe_evidence.py`；`python -m unittest discover -s tests -p 'test_*.py'`。
