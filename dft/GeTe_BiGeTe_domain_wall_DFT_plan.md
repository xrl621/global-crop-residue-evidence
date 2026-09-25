# GeTe / Ge0.92Bi0.08Te 畴壁形成能计算方案
## 基于 Dangic et al., *Physical Review B* 101, 184110 (2020)

> 目标：以文献中最低能的 **180° (1-10) 中性畴壁** 为基准，先复现纯 GeTe 的畴壁能，再在完全相同的畴壁几何框架下比较 Bi 掺杂前后的畴壁形成能。  
> 推荐工作流：**先做纯 GeTe benchmark → 再做 Ge0.92Bi0.08Te → 最后如有需要再做 Bi 偏聚/位点效应。**

---

## 1. 文献中必须复现的核心信息

GeTe 低温为菱方铁电相。文献采用六方表示的 GeTe 晶胞来构造 180° 畴壁。

### 1.1 六方 GeTe 晶胞

文献给出的六方晶格矢量为：

\[
\mathbf h_1=a\left(\frac{\sqrt3 b}{2},-\frac{3b}{2},0\right)
\]

\[
\mathbf h_2=a\left(\frac{\sqrt3 b}{2},\frac{3b}{2},0\right)
\]

\[
\mathbf h_3=a(0,0,3c)
\]

其中 \(a,b,c\) 与菱方原胞定义一致。

六方晶胞中的原子分数坐标：

### Ge
- (0, 0, 0)
- (2/3, 1/3, 1/3)
- (1/3, 2/3, 2/3)

### Te
- (0, 0, 1/2 + τ)
- (2/3, 1/3, 5/6 + τ)
- (1/3, 2/3, 1/6 + τ)

一个六方晶胞共 **6 个原子：3 Ge + 3 Te**。

---

## 2. 选择哪一种畴壁

本文 Table II 中：

| 畴壁 | 类型 | 宽度 | 平均畴壁能 |
|---|---|---:|---:|
| 180° (111) | H-H / T-T，带电 | 19.4 / 22.6 Å | 686 mJ m⁻² |
| **180° (1-10)** | **H-T / T-H，中性** | **9.7 / 8.4 Å** | **25 mJ m⁻²** |

因此本项目主模型固定为：

\[
\boxed{180^\circ(1\bar10)\ \text{neutral domain wall}}
\]

原因：

- 中性畴壁，静电能较小；
- 无孪晶；
- 文献中是所有所比较畴壁中能量最低的一类；
- 适合作为 GeTe 与 Bi-GeTe 的统一 benchmark。

---

## 3. 纯 GeTe 的 benchmark 模型

### 3.1 超胞

文献对 180° (1-10) DW 使用：

\[
\boxed{24\times1\times1}
\]

从六方 GeTe 晶胞扩胞。

因此：

\[
24\times6=144\ \text{atoms}
\]

组成：

\[
\boxed{\mathrm{Ge}_{72}\mathrm{Te}_{72}}
\]

文献对应的 k 点：

\[
\boxed{1\times12\times4}
\]

---

## 4. 180° 畴壁具体怎么构造

### 4.1 单畴状态

先得到完全优化的 \(R3m\) GeTe，并转换为上述六方晶胞。

定义：

- \(+P\)：Te 相对于高对称位置沿三方轴发生 \(+\tau\) 位移；
- \(-P\)：极化反向。

文献没有逐原子给出“反向畴生成脚本”，但根据其六方坐标定义，实际构造时可采用以下等价实现：

\[
\tau \rightarrow -\tau
\]

即在保持晶格和 Ge 子晶格不变的前提下，将 Te 相对于对应高对称参考位置的铁电位移反向。

> 这是对文献坐标定义的实现性推导，不是文中逐字给出的脚本步骤。

### 4.2 双畴超胞

沿 24×1×1 超胞的长轴分成两半：

- cell 1–12：\(+P\)
- cell 13–24：\(-P\)

由于周期性边界条件，一个超胞中实际有 **2 个畴壁**，最终目标是得到 H-T 与 T-H 两个中性 180° (1-10) 畴壁。

---

## 5. GeTe 畴壁形成能

文献公式：

\[
\boxed{
E_{\mathrm{DW}}=
\frac{E_1-E_0}{2S}
}
\]

其中：

- \(E_1\)：弛豫后的含畴壁超胞总能；
- \(E_0\)：与畴壁超胞具有**相同原子数**的 bulk GeTe 总能；
- \(S\)：单个畴壁面积；
- 2：周期超胞中有两个畴壁。

对于本模型：

\[
E_0=72E_{\mathrm{GeTe,f.u.}}
\]

或者直接构建一个完全同尺寸、同原子数的单畴 24×1×1 GeTe 作为 reference。

### 推荐

为了和 VASP 中的数值误差尽量抵消，实际项目中优先使用：

- GeTe-Mono：24×1×1，全部 +P，144 atoms
- GeTe-DW：24×1×1，12 个 +P + 12 个 -P，144 atoms

直接做：

\[
\boxed{
\gamma_{\mathrm{GeTe}}
=
\frac{E_{\mathrm{GeTe-DW}}-E_{\mathrm{GeTe-Mono}}}{2S}
}
\]

### benchmark

文献目标值：

\[
\boxed{\gamma_{\mathrm{GeTe}}\approx25\ \mathrm{mJ\,m^{-2}}}
\]

不要要求完全等于 25，因为：

- 文献使用 ABINIT；
- PBE；
- HGH pseudopotential；
- 16 Ha cutoff；
- 无 SOC；
- 我们若改用 VASP + PAW，绝对值会有一定差异。

但数量级和相对趋势应合理。

---

## 6. VASP 中建议的纯 GeTe 计算流程

### Step 1：优化 bulk GeTe

输入：R3m GeTe。

建议：

```text
ISIF = 3
ISYM = 0
EDIFF = 1E-7
EDIFFG = -0.005 ~ -0.01
PREC = Accurate
```

先获得稳定晶格常数与内部位移。

### Step 2：转换成六方 6 原子晶胞

确保：

- 极化沿六方 c 轴；
- 结构与文献的 hexagonal setting 一致；
- Ge / Te 坐标顺序固定，便于后续自动生成反向畴。

### Step 3：生成 24×1×1 单畴 reference

```text
GeTe_Mono/
POSCAR
INCAR
KPOINTS
POTCAR
```

144 atoms。

### Step 4：生成 24×1×1 双畴结构

```text
GeTe_DW/
```

前 12 个 hex cells 为 +P，后 12 个为 -P。

初始不需要人为插入平滑过渡层，让结构优化自己形成畴壁宽度。

### Step 5：结构优化

为了 benchmark 稳定，建议先：

```text
ISIF = 2
ISYM = 0
```

固定超胞晶格，放松所有原子。

如果需要更严格复现论文的“局域结构 + 超胞晶格共同弛豫”，再补一轮允许晶格响应的计算。

> 文献本身采用两步弛豫：先仅弛豫 Te，固定 Ge 与全局晶格；随后弛豫 Ge、Te 和超胞晶格。VASP 实施时可按项目计算成本决定是否完全照搬。

---

## 7. Bi 掺杂模型

实验目标组成：

\[
\mathrm{Ge}_{0.92}\mathrm{Bi}_{0.08}\mathrm{Te}
\]

24×1×1 GeTe 超胞中有：

\[
72\ \text{个 Ge 位}
\]

8% 对应：

\[
72\times0.08=5.76
\]

因此替换：

\[
\boxed{6\ \mathrm{Ge}\rightarrow6\ \mathrm{Bi}}
\]

模型组成：

\[
\mathrm{Ge}_{66}\mathrm{Bi}_{6}\mathrm{Te}_{72}
\]

对应实际 Bi 含量：

\[
x_{\mathrm{Bi}}=\frac{6}{72}=0.08333
\]

即：

\[
\boxed{\mathrm{Ge}_{0.9167}\mathrm{Bi}_{0.0833}\mathrm{Te}}
\]

与目标 Ge0.92Bi0.08Te 足够接近。

---

## 8. Bi 应该怎么放

为了让比较主要反映“8% Bi 掺杂对畴壁形成能的影响”，第一版采用**近似均匀、对称的 Bi 分布**：

- Domain A 放 3 个 Bi；
- Domain B 放 3 个 Bi；
- 两侧尽量镜像；
- 两个畴壁附近的局域化学环境尽量对称；
- Bi-Bi 尽量拉开；
- 不要 6 个全部堆在畴壁附近。

需要生成两个严格对应的模型：

### BiGeTe-Mono
- 24×1×1
- 6 Bi
- 全部 +P

### BiGeTe-DW
- 24×1×1
- 完全相同的 6 个 Bi 相对占位
- 12 个 +P + 12 个 -P

只有极化构型不同。

---

## 9. Bi-GeTe 畴壁形成能

定义：

\[
\boxed{
\gamma_{\mathrm{Bi-GeTe}}
=
\frac{
E_{\mathrm{BiGeTe-DW}}
-
E_{\mathrm{BiGeTe-Mono}}
}
{2S}
}
\]

然后比较：

\[
\boxed{
\Delta\gamma=
\gamma_{\mathrm{Bi-GeTe}}
-
\gamma_{\mathrm{GeTe}}
}
\]

解释：

- 若 \(\Delta\gamma<0\)：在当前 Bi 分布与计算条件下，Bi 掺杂降低该 180° (1-10) 中性畴壁形成能。
- 若 \(\Delta\gamma>0\)：在当前 Bi 分布与计算条件下，Bi 掺杂提高该畴壁形成能。

不要扩展成“Bi 一定促进/抑制所有畴结构”，因为这里只计算了这一种具体畴壁。

---

## 10. 第二阶段可选：Bi 偏聚到畴壁

若第一阶段发现 Bi 对 DW 能影响明显，可继续比较：

- Bi-bulk-like：Bi 远离 DW
- Bi@DW：Bi 位于 DW 邻近 Ge 位

定义偏聚能：

\[
\boxed{
E_{\mathrm{seg}}
=
E_{\mathrm{Bi@DW}}
-
E_{\mathrm{Bi@bulk-like}}
}
\]

若：

\[
E_{\mathrm{seg}}<0
\]

说明 Bi 更倾向位于畴壁附近。

这一部分是**本项目扩展**，不是 Dangic et al. 论文已经做过的内容。

---

# 11. 需要提交的最小模型集合

## A. 纯 GeTe

### M1 — GeTe-Mono
- R3m-derived hexagonal GeTe
- 24×1×1
- 144 atoms
- 单畴

### M2 — GeTe-DW
- 同 M1 晶格与原子数
- 180° (1-10)
- H-T / T-H
- 两个周期畴壁

计算 \(\gamma_{\mathrm{GeTe}}\)，并与文献 25 mJ m⁻² benchmark 比较。

## B. Bi 掺杂

### M3 — BiGeTe-Mono
- Ge66Bi6Te72
- 144 atoms
- 6 Bi 均匀/近似对称分布
- 单畴

### M4 — BiGeTe-DW
- Ge66Bi6Te72
- 与 M3 相同 Bi 位点
- 180° (1-10) 双畴

计算 \(\gamma_{\mathrm{Bi-GeTe}}\) 和 \(\Delta\gamma\)。

---

# 12. 计算一致性要求

四个主模型必须保持：

- 相同 XC functional；
- 相同 PAW/POTCAR；
- 相同 ENCUT；
- 相同电子收敛标准；
- 相同离子收敛标准；
- 相同 smearing 方法；
- 相同 SOC 选择；
- 相同类型的 k 点密度；
- 同一种晶格约束策略。

### SOC

原文所有 DW 计算均 **不含 SOC**。

因此建议：

- benchmark 阶段先不加 SOC；
- 若最终文章必须考虑 Bi/GeTe 重元素 SOC，再对最终 M1–M4 做统一的 SOC 单点或结构验证；
- 不允许 GeTe 不加 SOC 而 Bi-GeTe 加 SOC 后直接比较畴壁能。

---

# 13. 单位换算

若 VASP 得到：

\[
\Delta E=E_{\mathrm{DW}}-E_{\mathrm{Mono}}
\]

单位为 eV，面积 \(S\) 单位为 Å²：

\[
\gamma(\mathrm{eV/\AA^2})
=
\frac{\Delta E}{2S}
\]

转换：

\[
1\ \mathrm{eV/\AA^2}
=
16021.766\ \mathrm{mJ/m^2}
\]

因此：

\[
\boxed{
\gamma(\mathrm{mJ/m^2})
=
\frac{\Delta E}{2S}
\times16021.766
}
\]

---

# 14. 最终建议输出结果

至少整理：

| Model | Composition | DW | Total energy | S | γ |
|---|---|---|---:|---:|---:|
| GeTe-Mono | Ge72Te72 | none |  | — | — |
| GeTe-DW | Ge72Te72 | 180° (1-10) |  |  |  |
| BiGeTe-Mono | Ge66Bi6Te72 | none |  | — | — |
| BiGeTe-DW | Ge66Bi6Te72 | 180° (1-10) |  |  |  |

另外建议输出：

1. 优化后畴壁结构图；
2. 沿超胞长轴的局域极化/Te 位移曲线；
3. GeTe 与 Bi-GeTe 的畴壁宽度；
4. GeTe 与 Bi-GeTe 的畴壁能；
5. Bi 在畴壁附近的局域结构变化（若明显）。

---

# 15. 执行顺序

```text
01_bulk_GeTe_opt
        ↓
02_hex_GeTe
        ↓
03_GeTe_Mono_24x1x1
        ↓
04_GeTe_DW_24x1x1
        ↓
计算 γGeTe
        ↓
确认是否接近文献 25 mJ/m² 的合理数量级
        ↓
05_BiGeTe_Mono
        ↓
06_BiGeTe_DW
        ↓
计算 γBi-GeTe 和 Δγ
        ↓
若有必要
        ↓
07_Bi_site_or_segregation
```

---

# 16. 文献依据

Dangic, Đ.; Murray, É. D.; Fahy, S.; Savic, I.  
**Structural and thermal transport properties of ferroelectric domain walls in GeTe from first principles.**  
*Physical Review B* **101**, 184110 (2020).  
DOI: 10.1103/PhysRevB.101.184110

文献中直接支持的关键内容：

- GeTe 畴壁构建方法；
- 六方晶胞晶格与原子坐标；
- 180° (1-10) DW 使用 24×1×1 六方超胞；
- 共 144 atoms；
- 该模型采用 1×12×4 k-point grid；
- 180° (1-10) 为 H-T/T-H 中性 DW；
- Table II 中平均 DW energy = 25 mJ m⁻²；
- DW energy 公式：\(E_{\mathrm{DW}}=(E_1-E_0)/(2S)\)；
- 原文 DFT 采用 PBE，且所有计算不包含 SOC。

Bi 掺杂模型、6 Bi/72 Ge、对称分布以及 Bi 偏聚分析属于**本项目在该文献基础上的扩展方案**。
