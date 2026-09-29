# Yuan 2018 Illinois 原文核查：direct return × N₂O / yield（2026-09-29）

**DOI:** 10.1111/gcbb.12564  
**当前处置:** `held_numeric_arm_data_after_primary_audit`  
**正式主库新增:** 0 effects / 0 independent trials

## 1. 为什么值得继续追

该研究是美国 Illinois 的长期连续玉米田间试验。主文能够确认：

- 长期秸秆处理在 2005 年秋季建立，本研究分析 2015–2017 年；
- 处理包含 **full residue removal (RR−)** 与 **residue retained (R+)**；
- 同时设置 **chisel tillage (CT)** 与 **no-till (NT)**，因此是 residue × tillage 的析因设计；
- 采用区组设计并有 4 次重复；
- 连续观测土壤 N₂O 通量并报告玉米产量。

这使它在科学上很适合当前 Fig. 2 的两个目标：补充非亚洲 `direct_return × N2O`，并让 N₂O 与 yield 落在同一个试验身份中。

## 2. 为什么这次没有直接入库

当前可访问主文可以核实实验设计、重复数、总体统计检验及若干按年份/耕作汇总，但**不能仅凭主文恢复一个可审计的 R+ vs RR− 效应量及采样方差**：

1. 累计 N₂O 的主文表格没有给出每个 residue × tillage 处理组合可直接使用的逐臂均值与不确定性；
2. 主文的统计检验/P 值不能替代处理臂 mean + SD/SE + n；
3. 产量处理组合主要以图形展示，当前没有可靠的逐臂数值表可直接复算；
4. 出版页面明确存在 Supporting Tables S1–S2，处理组合数值需要回到补充表核对后才能正式提取。

因此本轮**不**从 P 值倒推方差，不按图形柱高目测均值，也不把“论文存在”当成一项已晋级独立试验。

## 3. 对当前 Fig. 2 计数的影响

没有变化：

- 主库：607 effects / 34 trial keys；
- 严格描述层：485 / 27；
- 核心逐指标层：472 / 25；
- `direct_return × N2O`：仍为 **3** 个独立试验；
- `direct_return × yield`：仍为 **11** 个独立试验。

这项核查的价值是把一个“看起来能直接补数据”的候选，转换成了一个明确的 **numeric-data hold**，避免为了达到 10 项计数门而制造伪精度。

## 4. 正式晋级所需数据

下一次只要恢复以下信息，就可以重新判断是否可入库：

- CT 条件下 R+ 与 RR− 的累计 N₂O mean、SD/SE、n；
- NT 条件下 R+ 与 RR− 的累计 N₂O mean、SD/SE、n；
- 对应年份/积分期；
- R+ 与 RR− 的产量逐臂 mean、SD/SE、n；
- Supporting Table S2 对误差类型和统计单位的说明。

若 CT 和 NT 的其他管理背景一致，可作为同一独立试验中的两个 residue contrast 保留层级关系，而不是记为两项独立试验。

## 5. 来源定位

- Yuan et al. (2018), *Global Change Biology Bioenergy*, DOI 10.1111/gcbb.12564.
- Publisher main text: experimental design, residue/tillage treatment structure, replication, N₂O measurement and yield analysis.
- Publisher supporting information: `gcbb12564-sup-0001-TableS1-S2.docx`;正式数值提取需以该补充表为准。

本记录只描述来源核查与准入状态，不把论文中的显著性解释成独立效应，也不改变当前三路径统计结果。
