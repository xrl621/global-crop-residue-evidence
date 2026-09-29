# Fig. 2 独立试验晋级矩阵与定向补证前沿（2026-09-29）

**状态：执行层已建立；本页不新增正式主库效应。** 当前全文核验主库仍为 **607 条效应 / 34 个试验键**，严格描述层 **485 / 27**，三作物核心逐指标层 **472 / 25**。本页把现有 Fig. 2 的证据缺口固定成可复算的晋级表，并建立外部原始研究候选前沿；任何候选在逐臂均值、误差、重复数、对照、系统边界与独立试验身份核验前都不得并入主库。

## 1. 12 个核心格子的独立试验缺口

上游数据使用[三路径×四终点完整阶段统计](MANUSCRIPT_FIG2_THREE_PATHWAY_STATISTICS_20260929.md)的
[`pathway_endpoint_summary.csv`](../data/processed/fig2_three_pathway_stats_20260929/pathway_endpoint_summary.csv)。
自动输出见[`pathway_endpoint_promotion.csv`](../data/processed/fig2_promotion_20260929/pathway_endpoint_promotion.csv)；
运行 `python scripts/build_fig2_promotion_matrix.py --check` 可检查是否与上游统计一致。

| 路径 | Yield | SOC concentration | CH₄ | N₂O |
| --- | ---: | ---: | ---: | ---: |
| Direct return | 11 (gap 0) | 5 (gap 5) | 3 (gap 7) | 3 (gap 7) |
| Biochar return | 8 (gap 2) | 4 (gap 6) | 4 (gap 6) | 4 (gap 6) |
| Open burning | 9 (gap 1) | 5 (gap 5) | 2 (gap 8) | 2 (gap 8) |

这里的 **gap** 只表示到项目预设“10 个独立试验计数门”的数量差，不是“补够就能做 Meta”的承诺。达到 10 后仍要检查共同对照、方差来源、共享对照/重复年份依赖、SOC 指标、气体时间边界、地区支持域和系统边界。

**当前最明确的瓶颈在 CH₄/N₂O，而不是产量。** 产量已为 11/8/9 个独立试验；SOC 为 5/4/5；气体仅 3/4/2 或 3/4/2。补证应优先寻找同一试验同时报告产量或 SOC 与 CH₄/N₂O 的研究，以提高真正多目标权衡的配对覆盖。

## 2. 第一轮非亚洲定向候选

候选明细见 [`fig2_targeted_candidates_20260929.csv`](../literature/fig2_targeted_candidates_20260929.csv)。10 个 DOI 已与当前公开 607 行主库做字符串核对，均未命中；这只说明“主库未命中”，不等于它们彼此独立或一定符合准入。

### 美国：补 direct return 的 N₂O 与 SOC

- **Yuan et al. 2018, Illinois**：长期连续玉米，秸秆保留/移除 × 耕作，三年测 N₂O 和产量。重点核相同耕作背景下的保留—移除逐臂均值和方差。
- **Li et al. 2023, Nebraska**：免耕灌溉玉米的秸秆保留/机械移除，含产量与土壤 N₂O。需拆开灌溉/覆盖作物因子，并与 Nebraska ARS 系列做 trial identity 去重。
- **Jha et al. 2017, Ohio**：9 年免耕玉米，0–200% 秸秆保留梯度，提供 SOC 浓度候选。
- **Schmer et al. 2024, Nebraska**：20 年灌溉连续玉米，产量和 SOC 储量；SOC stock 不直接进入当前 `SOC_concentration` 格子。

### California：焚烧—还田的同试验多结局线索

- **Bossio et al. 1999**：1993 年起的稻草焚烧/翻埋 × 冬季淹水田间试验，1997 年测 CH₄，并记录生长/产量。
- **Cintas & Webster 2001**：同样从 1993 年开始的 Colusa County 稻草管理试验，包含翻埋、碾压、打捆移除和秋季焚烧，报告多年产量。

两篇在地区、起始年份和处理结构上高度相似，标记为 **possible shared trial**。在原文地点和布局完全核对前，不能当作两项独立试验。价值在于可能把 yield 与 CH₄ 放回同一个 trial identity，而不是增加论文计数。

### 澳大利亚：补 open burning 的 yield/SOC 与地域支持

- **Chan & Heenan 2005**：两个田间试验（19 年和 5 年）研究秸秆焚烧、耕作、土壤碳和作物生产；先核每个试验的核心作物身份、逐臂数值和方差。
- **Haines & Uren 1990**：东北 Victoria 连续小麦，直接播种条件下秸秆保留 vs 焚烧；可补 SOC，但要恢复共同深度的逐臂误差并与后续 Victoria 系列去重。
- **Roper et al. 2021**：重点是历史焚烧停止后的恢复/遗留效应，先留 **separate-boundary candidate**，不能把遗留效应当当前焚烧效应。

### 埃塞俄比亚：补 biochar 的非亚洲核心作物证据

- **Raji et al. 2026**：南部埃塞俄比亚玉米田间试验，明确含 **maize-straw biochar**，报告产量与土壤性质。只考虑玉米秸秆炭处理臂；需核等肥背景、土壤 C 指标/深度和逐臂误差。

## 3. 下一轮执行顺序

1. **Yuan 2018 + Li 2023：** 逐臂提取 N₂O + yield，判断能否进入 `direct_return × N2O`。
2. **Bossio 1999 + Cintas 2001：** 先做 California trial identity 去重，再恢复可用 burning/removal/incorporation 比较。
3. **Chan 2005 + Haines 1990：** 目标是非亚洲 open-burning 的 yield/SOC 独立试验，而不是摘要方向入库。
4. **Raji 2026：** 提取 maize-straw biochar 臂；SOC 指标按 schema 原样分类，不为凑 `SOC_concentration` 强制转换。
5. 每晋级一个来源，先更新 trial identity / quality audit，再重跑严格层、三路径统计和本晋级矩阵。

## 4. 不变的推断边界

- 候选表不是正式证据层；当前 607/34、485/27、472/25 **均不变**。
- 非配对路径间的中位数不能解释为技术优劣或因果排名。
- CH₄/N₂O 是田间通量终点；open burning 的燃烧瞬时排放单独编码。
- SOC concentration、SOC stock 与 SOM proxy 分开。
- 同一长期试验的多年份、多剂量、多论文仍以独立 trial identity 聚类。
