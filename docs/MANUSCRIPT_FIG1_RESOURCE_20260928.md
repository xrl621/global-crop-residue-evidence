# 正文 Fig 1：OMD 作物残余物总量与三大谷物秸秆的全球分布

**本图唯一问题：** 2020 年 OMD 所含 12 类作物残余物中，重点研究的玉米、水稻、小麦占多大份额；这三种谷物的理论秸秆资源在哪里，洲际与气候构成如何不同？这是论文“全球资源与管理机会空间”的起点，不比较处理效应、焚烧量或政策成效。

## 正文结论

OMD 2020 年所含 12 类作物残余物国家估计合计 **47.93 亿干吨**；其中重点研究的玉米、水稻、小麦合计 **37.06 亿吨，占 77.3%**，另有大豆 **5.00 亿吨，占 10.4%**。三种重点作物分别为玉米 **13.20 亿吨**、水稻 **11.23 亿吨**、小麦 **12.63 亿吨**。三者全球总量处于相近量级，空间构成却明显不同：玉米约 **48.8%** 位于美洲；水稻约 **88.0%** 位于亚洲；小麦约 **45.8%** 位于亚洲、**33.0%** 位于欧洲。按 Köppen 大气候组分层，玉米理论资源约 43% 在寒冷 D 类，水稻约 43%/44% 在热带 A/温带 C 类，小麦约 40%/35%/22% 在温带 C/寒冷 D/干旱 B 类。**因此，重点谷物秸秆的管理环境并不均质；12 作物排序只说明资源范围，不等于所有作物均有同等级处理效应证据。**

## 图面和图注

[整张组图](../figures/manuscript_fig1_20260928/aligned_exports/fig1_resource.png)先排版审查，再拆成四张无编号面板：[三作物地图](../figures/manuscript_fig1_20260928/aligned_exports/resource_map.png)、[12 作物资源排序](../figures/manuscript_fig1_20260928/aligned_exports/crop_scope.png)、[洲际资源份额](../figures/manuscript_fig1_20260928/aligned_exports/continent_mix.png)、[洲际×气候构成](../figures/manuscript_fig1_20260928/aligned_exports/climate_mix.png)。图面无总标题、无 a/b/c/d；采用用户指定色板。图宽 183 mm。可编辑格式另存于 `aligned_exports/`：[整图 PDF](../figures/manuscript_fig1_20260928/aligned_exports/fig1_resource.pdf) / [SVG](../figures/manuscript_fig1_20260928/aligned_exports/fig1_resource.svg)；独立面板为地图 [PDF](../figures/manuscript_fig1_20260928/aligned_exports/resource_map.pdf) / [SVG](../figures/manuscript_fig1_20260928/aligned_exports/resource_map.svg)、作物排序 [PDF](../figures/manuscript_fig1_20260928/aligned_exports/crop_scope.pdf) / [SVG](../figures/manuscript_fig1_20260928/aligned_exports/crop_scope.svg)、洲际图 [PDF](../figures/manuscript_fig1_20260928/aligned_exports/continent_mix.pdf) / [SVG](../figures/manuscript_fig1_20260928/aligned_exports/continent_mix.svg)、气候图 [PDF](../figures/manuscript_fig1_20260928/aligned_exports/climate_mix.pdf) / [SVG](../figures/manuscript_fig1_20260928/aligned_exports/climate_mix.svg)。PDF/SVG 均保留可选中文字与矢量柱图/标注；地图格网和热图色块以图像嵌入。整图另有 TIFF。

- 地图：三作物**合计**理论干重在 0.5° 格网的模型化分配；共享对数色标，白色为零/未分配。OMD 国家×作物估计按同国家、同作物 MapSPAM 2020 粮食生产量权重分配，**格网吨数不是观测值**。地图不区分田间焚烧、留田或实际可收集量。
- 作物排序：OMD 原表 2020 年 **12 类作物残余物**的国家估计理论干重合计，着色突出三种重点谷物；此面板是 OMD 的作物范围，不是所有世界农作物的普查。大豆、花生、马铃薯等属于非谷物残余物，不能笼统称为“秸秆”；它们只用于资源背景，不自动进入后续三路径处理效应模型。原表 2020 年有 1,269 行国家×作物记录，其中 9 行未提供残余物吨数，排序只汇总已报告数值，未用零或均值填补。
- 洲际图：15 行对应三作物×五大洲，每个条形表示该大洲占**该作物全球**理论秸秆量的百分比，同作物五行合计为 100%。玉米、水稻、小麦的全球总量分别为 13.20、11.23、12.63 亿干吨。
- 气候图：与洲际图逐行对齐，展示各作物×大洲内部在 Köppen 1991–2020 五大气候组的份额，共 75 个分层单元；每行分母是**该作物在该大洲**的已分配理论吨数，而非该作物全球总量。数字按整数四舍五入，“·”为 <1%；行内数字可能不恰好加至 100%。大洋洲玉米/水稻等低总量行应连同左侧份额一起读，不能将高气候百分比误认为高全球资源量。这描述地理环境，不说明气候**导致**处理效应差异。

**自行组版：** 请用 `aligned_exports/` 中四张 PDF 或四张 SVG，按“地图｜作物排序；洲际图｜气候图”排成两行两列，保持原始尺寸、不要分别裁掉留白。左列两张均宽 **111.49 mm**，右列两张均宽 **71.51 mm**；上排均高 **61.87 mm**，下排均高 **111.13 mm**，拼合后恰为 **183 × 173 mm**。这些位置由最终整图画布一次切分，而非四张图各自紧裁；[切分几何记录](../figures/manuscript_fig1_20260928/aligned_exports/panel_slots.json)中上排内容边缘差异 <1 pt。上排地图与排序的内容类型不同，不要求两者内部坐标轴同宽。

作物排序界定数据库覆盖与焦点，地图定位三种重点谷物，洲际图定量拆解，气候图显示环境分层；旧稿的试验论文地理分布、仅玉米可可靠分配的成熟季和谷物合计的 Smerald 管理去向暂不进入 Fig 1，分别留给来源审计/补充材料及后续管理—政策图。这样 Fig 2 才能从“资源在哪里”转向“三条路径对产量、SOC 和 GHG 的影响”。

## 数据、验证与边界

来源：[OMD 2025 论文](https://doi.org/10.5194/essd-17-369-2025)、[OMD 数据 v2](https://doi.org/10.5281/zenodo.10450921)、[MapSPAM 2020 v2r2](https://doi.org/10.7910/DVN/SWPENT)、项目已接入的 Köppen–Geiger 1991–2020 栅格。格网分配覆盖 **99.9969%** 的 OMD 三作物国家吨数；未联结的国家×作物组合保留为空，未跨国填补。地图采用最近邻像元显示，不做空间平滑；Natural Earth 国界只作底图。

重算入口：`python scripts/integrate_omd_residue_geography.py`（需本地原始文件）和 `python scripts/plot_manuscript_fig1.py --qa-scripts <nature-figure scripts 目录>`。完整格网源文件保留本地；公开的[12 行作物排序源表](../figures/manuscript_fig1_20260928/omd_all_12_crop_residue_2020.csv)与[75 行气候分层源表](../figures/manuscript_fig1_20260928/crop_continent_climate_source.csv)可逐格复核。图脚本核对 OMD 原始文件哈希、三重点作物的国家吨数以及格网、洲际、气候和三维分层吨数守恒；75 格中 65 格理论吨数大于零。这是**同一批格网数据的交叉汇总，不是新收集的 75 项独立试验**。76 项测试通过；最终 PDF 文字最小 6.1 pt，渲染碰撞 0 失败/0 警告；底部两张可比较面板对齐审查通过。上排地图与 12 作物排序承担不同角色、几何比例不同，已在整图和单独面板作视觉审查。此图是正文 Fig 1 的工作定稿，不等于已完成投稿前的所有授权和期刊格式核查。
