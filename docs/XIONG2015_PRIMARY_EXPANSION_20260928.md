# 原文扩库审计：Xiong 等水稻三年田间试验（2026-09-28）

## 来源和实际新增

原文：[Xiong 等，*Scientific Reports*，doi:10.1038/srep17774](https://www.nature.com/articles/srep17774)，原文 Table 2；[补充材料 Tables S1–S2](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fsrep17774/MediaObjects/41598_2015_BFsrep17774_MOESM1_ESM.pdf)。原文在线发表于 2015 年，期刊卷号引用可能显示 2016 年；公开表的 `publication_year=2015` 指在线发表年。

原文公开 JATS XML：[Europe PMC PMC4667221](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4667221/fullTextXML)，提取时 SHA-256 为 `6b4ae3f91ed840809b04a4c48efadc0efad21b33dcfbceb827ed9b9fa82e9678`。脚本锁定该哈希，源文件变化时停止，不静默改变数值。XML 不在仓库重复分发。

原文在江苏南京 Mo ling 镇的同一固定试验点，以 3 个随机区组比较同一轮作系统中的 S0（不还田）与 S1/S2（每公顷 3/6 吨秸秆翻埋）。本次只在同一年、同一轮作系统、同一稻季、相同施氮安排下构造 S1/S2 对 S0；单季稻与早/晚稻不互为对照。2008–2009 至 2010–2011 三年度 × 单季稻/早稻/晚稻 × 两剂量 × 产量/CH₄/N₂O，形成 **54 条处理—对照效应，但只新增 1 项独立试验**。一个 S0 可能供两个剂量共用；所有年份、稻季、剂量、结局在 `study_id=xiong_moling_2008_2011` 下聚类。来源 Table 2 明确标示均值 ± **SD**，区组重复数为 3；没有把 SD 当 SE 或自造误差。

产量单位是 `t rice grain ha-1`，CH₄ 为 `kg CH4 ha-1 rice-season-1`，N₂O 为 `kg N2O-N ha-1 rice-season-1`。后者是**以 N 计**，不能与 `kg N2O` 直接拼接绝对排放量；同单位同源处理—对照的 lnRR 可以单独描述。没有把非水稻季节、小麦/油菜产量、年度均值重复录入，也没有把 Table 3 含 SOC 封存项的年度净 GWP 当作土壤 CH₄+N₂O GWP。原文没有明确指出各稻季投入秸秆的物种；所有行标注 `straw_feedstock_species_unreported`，不能称为“稻草还田”的特异证据，后续要做排除该试验的原料敏感性分析。

## 二次数据库逐值交叉核对

本地已有 Figshare 水稻温室气体候选库 StudyID 96 的 27 条处理臂。以原文 Table 2 为标准，对 54 条效应的处理/对照均值和 SD 共核 216 个单元，213 个一致、3 个核对行冲突；后两行重复引用同一个共享对照，因此实际是 **2 个不同原始单元**有冲突：

| 原文 Table 2 原始单元 | 原文 | 候选库 | 处理 |
| --- | ---: | ---: | --- |
| 2008–2009 单季稻 UR-S1，CH₄ SD | 57.7 | 45.77 | 用原文 SD |
| 2010–2011 晚稻 DR-S0，产量均值（t/ha） | 9.93 | 9.33 | 用原文均值；该 S0 为 S1/S2 共用 |

逐单元本地核对表 `data/processed/xiong2015_review_20260928/source_numeric_audit.csv` 不上传完整第三方候选数据；公开的[原文提取表](../literature/primary_extractions/xiong2015_rice_season_table2.csv)只含从许可原文提取的处理—对照数字。[提取脚本](../scripts/extract_xiong2015_table2.py)在 `--audit-secondary` 指向本地候选 CSV 时可重建核对表；不提供该参数也能独立从原文 XML 重建提取表。

## 入库、筛选与结果解释

主库从 **553 条/33 试验键**到 **607 条/34 试验键**。原 553 条效应 ID 和均值、SD、lnRR、方差保持不变。[新阶段清单](../data/processed/stage_20260928/manifest.json)的严格描述层由 437 条/26 键变为 **485 条/27 键**：新增 18 条产量、18 条 CH₄、12 条 N₂O；另外 6 条 N₂O 因相对 SE 大于既定 0.5 门槛保留在主库、不进入严格描述层。三作物/六指标的核心矩阵由 424 条/24 键变为 **472 条/25 键**；另列的 13 条边界记录未改变。[逐技术矩阵 v2](../data/processed/pathway_endpoint_v2_20260928/pathway_outcome.csv)因此是更新后的描述性快照，前一版保留为历史版本。

在**这一个田间试验**内，18/18 条 CH₄ 效应高于相应 S0；严格层的 12 条 N₂O 中 11 条较低、1 条较高；18 条产量有 9 条较高、8 条较低、1 条相同。把同试验的各年/季/剂量 lnRR 等权平均，产量约 +0.23%、CH₄ 约 +223%、N₂O 约 −16%；这些只是**单试验描述量**，并非三个独立结论、更非全球合并效应。CH₄/N₂O 的不同计量和系统边界不允许仅凭这些百分比宣布净气候收益；产量在此试验也无稳定同向响应。部分 N₂O 高不确定度效应被筛掉，不能把筛后方向当成无偏总体方向。

当前逐技术—指标主分析允许一篇原文只贡献它实际报告的合格结局；SOC 缺席并不妨碍该试验贡献产量和气体，但它**不能**被当成产量—SOC—GHG 三结局协同证据。核心数据仍高度偏向亚洲；本次增加的是中国水稻单站点，不改善全球地区代表性，也不足以启动全球空间外推、气候归因或路径政策排名。

## 复现与下一步

运行：`python scripts/extract_xiong2015_table2.py`、`python scripts/export_evidence_database.py --check`、`python scripts/analyze_stage_evidence.py`、`python scripts/analyze_pathways_separately.py`、`python -m unittest discover -s tests -q`。两个分析脚本默认输出已更新到 2026-09-28 新目录，不覆盖历史目录。

下一批优先从待审来源中核入**其他国家/气候区的独立田间试验**，并补生物炭与焚烧路径的产量/SOC/GHG 空格；同一试验再拆年份或剂量会增加效应行数，但不会解决全球代表性。先核原料物种、施氮/水分匹配、SD/SE 和完整燃烧边界，再进行分层 Meta 模型及敏感性分析。
