# 全球秸秆管理数据分析项目章程 v1.0

状态：已确认并冻结（后续方法参照不得改变本章程主线）
日期：2026-09-20
适用范围：本项目后续数据整理、统计建模、全球制图、政策分析和论文写作

原始任务依据及与早期AI扩展内容的边界，见 `ORIGINAL_BRIEF_ALIGNMENT_20260920.md`。本章程以教师最初提出的三类处理、三个评价维度和全球文献数据分析为上位约束。

相关论文的方法仅用于优化数据组织与质量控制，见 `METHOD_REFERENCE_KAIJSER2025.md` 和 `RELATED_METHODS_BENCHMARK_20260920.md`；如需改变本章程中的研究对象、核心路径、一级结局或分析单元，必须另行显式修订版本。

## 1. 项目的一句话主线

> 结合全球田间试验证据、作物空间分布、作物季节、气候与土壤数据，识别不同地区和主要作物的秸秆管理协同、权衡及证据边界，并形成可与国家和区域政策情景衔接的管理分区。

所有新增分析必须至少服务下列问题之一：

1. 什么地方产生什么作物的秸秆？
2. 气候、土壤、水分制度和季节如何改变管理效果？
3. 不同管理路径对产量、SOC和GHG的联合影响是什么？
4. 哪些地区有足够证据支持管理分区，哪些地区仍属证据空白？
5. 科学证据如何与当地主要作物、焚烧负担和政策工具衔接？

不能回答以上问题的分析，原则上不进入主论文。

## 2. 研究对象

### 2.1 “秸秆”的统一定义

本项目中的 crop residue 指主要农作物收获后产生的地上残体，包括茎秆、叶和穗轴等可进入田间管理或离田利用的残体。

不默认包括：

- 畜禽粪便；
- 城市有机废弃物；
- 林业残余物；
- 加工端食品废弃物；
- 地下根系残体，除非原研究明确报告并单独标记。

### 2.2 第一阶段作物

主分析仅冻结三类作物：

- rice；
- maize；
- wheat。

选择理由是全球秸秆量大、空间分布广、政策相关性高，并且现有田间数据库相对更可能提供足够样本。

soybean、barley、sorghum、sugarcane 等进入扩展分析，不与三类核心作物共同决定主结论。

### 2.3 管理路径

核心田间效应路径：

1. `direct_return`：未热解的作物残体直接进入田间；
2. `biochar_return`：作物残体经热解形成生物炭后施入田间。

政策和资源背景路径：

3. `open_burning`：露天焚烧，作为政策压力和排放基线；
4. `removal`：离田，作为资源竞争和替代情景。

由于现有 burning/removal 田间效应样本稀少，两者暂不与 direct return 和 biochar 做同等强度的全球效应排名。若后续数据量通过预设门槛，再升级为正式比较路径。

其中 `open_burning` 是教师原始任务明确要求的第三类处理，因此必须保留为目标路径。第一阶段增加专项文献补库，并区分露天焚烧排放与焚烧灰还田的田间效应；在补库完成前，不使用现有少量记录进行全球优劣排名。

## 3. 唯一中心科学问题

> 在全球主要作物系统中，秸秆管理路径与作物类型、水分制度、季节性气候和土壤背景如何共同影响产量、SOC和GHG的联合结果；这些规律在哪些地区具有证据支持和可迁移性？

政策分析从属于这一科学问题，不另起一条与田间证据脱节的政策主线。

## 4. 预先固定的科学假设

- **H1 路径异质性**：direct return 与 biochar return 在 yield、SOC和GHG上呈现不同的联合响应，但观测差异同时受到证据组成影响。
- **H2 水分调节**：paddy/flooded 与 upland/rainfed 条件会显著改变路径的GHG响应，特别是CH4。
- **H3 季节窗口**：收获后0–30天和30–90天的温度、降水与土壤湿度比年均气候更能解释残体分解和GHG差异。
- **H4 作物差异**：rice、maize和wheat具有不同的路径响应和气候敏感性，不应仅作为普通分类变量合并解释。
- **H5 联合结果依赖阈值**：三目标协同概率和主要瓶颈会随具有实际意义的阈值改变。
- **H6 可迁移性受限**：模型在跨国家、跨气候区和跨作物系统验证中的表现低于普通随机或论文分组验证。

假设检验不预设“biochar一定更好”或“direct return一定更差”。

## 5. 统一分析单元

### 5.1 田间证据单元

最低层级：

`paper → experiment → site → crop season/year → treatment arm → control arm → outcome`

任何效应量必须能够追溯到上述层级。记录数不等同于独立试验数。

### 5.2 全球空间单元

主分析单元固定为：

`0.5° grid × crop × production system × crop season`

其中 production system 至少区分：

- irrigated / rainfed；
- flooded / non-flooded，在数据允许时使用。

MapSPAM、SoilGrids等高分辨率数据可以聚合进入0.5°网格，但不发布超出田间模型支持能力的伪高精度推荐图。

### 5.3 时间口径

历史基线期暂定：`2001–2020`。

理由：

- 与MapSPAM 2020基准年份相对协调；
- 能提供20年气候正常值与年际变率；
- 避免用单一年份气候代表长期农业环境。

政策文本使用最新可核实版本，并记录访问日期和生效状态。未来气候情景不进入第一阶段主分析。

## 6. 作物季节口径

不采用简单的春、夏、秋、冬分类。每个 grid-crop 使用作物日历定义：

1. `growing_window`：播种至成熟/收获；
2. `postharvest_0_30d`：收获后0–30天；
3. `postharvest_31_90d`：收获后31–90天；
4. `interseason_window`：90天后至下一季播种前。

水稻和小麦若存在双季或冬/春类型，分别保留独立作物季，不取简单平均。

## 7. 结局变量与优先级

### 7.1 三个一级结局

1. crop yield response；
2. soil organic carbon response；
3. field GHG response。

### 7.2 二级结局

- CH4；
- N2O；
- CO2；
- reported or consistently reconstructed net GHG；
- yield-scaled GHG，仅在分子和分母边界一致时使用。

### 7.3 不允许混合的口径

- SOC concentration 与 SOC stock 分开；
- annual flux 与 cumulative flux 分开；
- reported net GHG 与项目重算 net GHG 分开；
- 不同GWP版本分开记录，统一转换时保存原始值；
- 田间GHG不等同完整生命周期GHG；
- 短期SOC增加不等同永久碳汇。

## 8. 联合收益定义

不再把单一正负号分类作为唯一主结果。联合收益统一表示为：

`P(yield > δY, SOC > δSOC, GHG < −δGHG)`

主文至少报告三套阈值：

- `δ = 0%`：方向性分析；
- `δ = 5%`：中等实际效应；
- `δ = 10%`：较强实际效应。

阈值敏感性属于主要结果，不放入补充材料隐藏。

## 9. 气候变量的冻结清单

为避免无目的筛选大量气候变量，第一阶段固定为：

### 生长季

- mean temperature；
- total precipitation；
- climatic water balance或干旱指标；
- extreme heat days，在作物阈值可定义时使用。

### 收获后0–30天和31–90天

- mean temperature；
- total precipitation；
- mean soil moisture；
- heavy precipitation days；
- freeze days；
- flooded/irrigated/rainfed status。

年均温和年降水仅作为背景变量，不替代作物季节变量。

## 10. 土壤变量的冻结清单

第一阶段只使用具有明确机制意义并能全球匹配的变量：

- initial SOC；
- pH；
- clay fraction；
- bulk density，在SOC stock换算中使用；
- total N或C:N，在覆盖度允许时使用。

不得因为SoilGrids提供大量变量就全部加入模型。全球栅格预测值与原试验实测值需分别标记。

## 11. 统计与预测口径

### 11.1 主效应

- paper-balanced结果；
- paper/experiment/site多层模型；
- cluster-robust uncertainty；
- 方差完整子集的inverse-variance敏感性；
- prediction interval与影响诊断。

### 11.2 情景模型

优先使用可解释的hierarchical meta-regression或GAM。RF/XGBoost作为非线性敏感性模型。

### 11.3 验证

必须包括：

- leave-one-paper-out或按paper分组；
- leave-one-country-out；
- leave-one-climate-zone-out；
- leave-one-crop-system-out；
- China/paddy versus remaining evidence sensitivity。

### 11.4 空间外推

每个栅格必须同时输出：

- expected response；
- uncertainty interval；
- environmental novelty；
- evidence density；
- applicability flag。

不在适用域内的像元标为 `evidence gap`，不强制给出管理推荐。

## 12. 全球秸秆资源口径

理论秸秆量：

`crop production × residue-to-product ratio`

可管理秸秆量还需要扣除：

- 维持土壤覆盖的最低保留量；
- 牲畜饲料；
- 燃料；
- 垫料和其他既有用途；
- 收集损失和经济不可达部分。

在缺少可靠竞争用途数据时，只发布 theoretical residue production 或 scenario-based recoverable residue，不称实际可利用量。

## 13. 政策分析口径

政策单位为 `country`，有可靠资料时下沉到一级行政区。

每项政策分别编码：

- policy text mentions residue/agricultural burning/soil carbon/biochar；
- policy instrument，例如禁令、补贴、标准、碳项目；
- legal status与生效时间；
- implementation evidence；
- geographic coverage；
- target crop或农业系统。

政策文本存在不等于有效实施。NDC、法规和实施证据不得合并成单一0/1变量。

## 14. 最终空间分区

所有区域统一划为四类：

1. `supported_opportunity`：联合收益概率较高，且位于证据支持域；
2. `conditional_option`：效果取决于水分、季节、成本或其他条件；
3. `tradeoff_hotspot`：至少一个一级目标存在明显损失风险；
4. `evidence_gap`：缺乏相似田间证据或预测不确定性过高。

政策输出必须基于这四类分区，不生成没有证据等级的“全球最优路径图”。

## 15. 第一阶段核心成果

1. 全球rice/maize/wheat秸秆产生与田间证据分布图；
2. crop-specific climate response surfaces；
3. 收获后季节气候风险图；
4. 三目标联合收益概率图；
5. 证据密度、适用域与不确定性图；
6. 国家/农业生态区政策分型表；
7. 全球田间试验缺口和新增试验优先区。

## 16. 明确禁止的主张

在未补充相应数据和验证前，禁止：

- 宣称biochar在全球普遍优于direct return；
- 把跨研究比较写成因果替代效应；
- 把田间GHG写成完整生命周期减排；
- 计算全球净碳汇或MtCO2e减排潜力；
- 在模型适用域外给出确定性政策推荐；
- 将NDC或政策文本视为实施成效；
- 使用高分辨率输入数据制造高分辨率结论；
- 把非显著趋势写成确定性增加或降低。

## 17. Go/no-go决策点

### Gate 1：数据来源

若记录不能追溯至原始论文和独立试验层级，暂停建模，先完成provenance。

### Gate 2：作物样本量

若某作物在关键pathway × water × climate单元中的独立论文数不足，则该单元只做证据缺口展示，不做全球预测。

### Gate 3：路径可比性

若biochar与direct return共同支持域过小，则不发布调整后的路径排名，只分别绘制路径响应和适用域。

### Gate 4：外部块验证

若leave-country/climate/crop-out性能或校准明显失效，则停止全球推荐，只发布证据分布和区域性结果。

### Gate 5：政策解释

若某国只有政策文本、没有执行信息，则仅标记policy intent，不评价政策成效。

## 18. 变更控制

本章程确认后冻结为v1.0。后续任何新增：

- 作物；
- 管理路径；
- 一级结局；
- 气候变量；
- 空间分辨率；
- 时间基线；
- 全球定量主张；

必须记录变更原因、数据依据、对原假设的影响和版本号。探索性分析不得在结果出现后升级为未预设的主假设。

## 19. 当前待确认的三个口径

1. 第一阶段是否正式冻结为rice、maize、wheat三类作物；
2. 历史气候基线是否采用2001–2020；
3. 全球主网格是否采用0.5°，高分辨率数据仅用于聚合和区域补充。

除这三个选择外，其余条款可先作为默认执行口径。
