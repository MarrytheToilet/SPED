# 数据填充模式 - 精准数值提取

## 🎯 任务目标

根据骨架阶段识别的记录，从当前文本块中**尽可能多地**提取具体数值，填充到12表结构。

> ⚠️ **关键**：仔细阅读每一句话，不要遗漏任何可提取的数据！

---

## 📋 已识别的记录骨架

{SKELETON_INFO}

---

## 📄 当前文本块（第 {CHUNK_INDEX}/{TOTAL_CHUNKS} 块）

{CHUNK_CONTENT}

---

## 🚫 五条铁律

1. **只填原文数据** - 论文没写的不填，找不到就省略该字段
2. **禁止单位转换** - `2.8 cm` 保持原样，不转 `28 mm`
3. **保留原始精度** - `0.16±0.02` 原样保留，不简化
4. **数值字段只填数值** - 不要填 `"见图3"` 这类引用
5. **匹配正确记录** - 根据材料/处理确定属于哪个 record_id

---

## 📊 完整字段提取指南

### 📌 Sheet1_基本信息表

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| 应用部位 | hip joint, knee joint, total hip arthroplasty (THA), total knee replacement (TKR) | `髋关节`、`膝关节` |
| 论文标题 | Title行、首页标题 | 完整英文标题 |
| 论文DOI号 | doi:, DOI:, https://doi.org/ | `10.1016/j.wear.2023.204896` |
| 产品所属专利号或文献 | Patent No., US Patent | `US Patent 8,123,456` |

---

### 📌 Sheet2_内衬基本信息表（聚合物内衬/臼杯内衬）

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| **内衬材料类别** | polymer, ceramic liner | `聚合物`、`陶瓷` |
| **内衬材料名称** | UHMWPE, HXLPE, highly crosslinked PE, PEEK, PEEK-OPTIMA | `UHMWPE`、`HXLPE`、`PEEK` |
| 成型方式 | compression molding, injection molding, ram extrusion | `压缩成型`、`注塑成型` |
| 熔融温度 | melting temperature, Tm, processing temperature | `220°C` |
| 成型压力 | molding pressure, consolidation pressure | `10 MPa` |
| 保温时间 | holding time, consolidation time | `30 min` |
| **碳纤维质量分数** | CF content, carbon fiber wt%, 30% CF | `30 wt%`、`30%` |
| 碳纤维长度 | CF length, fiber length | `3 mm` |
| 碳纤维外径 | CF diameter, fiber diameter | `7 μm` |
| 碳纳米管质量分数 | CNT content, MWCNT wt% | `1 wt%` |
| 碳纳米管长度 | CNT length | `10-30 μm` |
| 碳纳米管外径 | CNT diameter, outer diameter | `10-20 nm` |
| 石墨烯质量分数 | graphene content, GO wt% | `0.5 wt%` |
| 石墨烯厚度 | graphene thickness | `1-2 nm` |
| 石墨烯长度 | graphene lateral size | `5-10 μm` |
| 碳化硅质量分数 | SiC content | `5 wt%` |
| **内衬厚度(mm)** | liner thickness, cup thickness | `6.3 mm` |
| 内衬偏移(mm) | liner offset | `+4 mm` |
| 内衬锁定机制 | locking mechanism, snap-fit | `锁环固定` |
| 内衬加工工艺 | machining, turning | `数控车削` |
| **内衬后处理** | crosslinking, irradiation, gamma, e-beam, annealing, remelting | `γ辐照100kGy`、`电子束辐照75kGy`、`重熔退火` |

**🔍 后处理关键词**：
- γ irradiation / gamma irradiation → γ辐照
- e-beam irradiation / electron beam → 电子束辐照
- annealing / remelting / thermal treatment → 退火/重熔/热处理
- crosslinking dose: 50 kGy, 75 kGy, 100 kGy

---

### 📌 Sheet3_球头基本信息表（股骨头）

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| **球头材料类别** | metal, ceramic, CoCr head, alumina head | `金属`、`陶瓷` |
| **球头材料名称** | CoCrMo, Co-Cr-Mo, cobalt chrome, alumina, Al2O3, zirconia, ZrO2, BIOLOX | `CoCrMo合金`、`Al₂O₃陶瓷`、`ZrO₂陶瓷` |
| **球头合金成分** | Co-28Cr-6Mo, composition (wt%) | `Co-28Cr-6Mo`、`Co 64%, Cr 28%, Mo 6%` |
| **球头直径(mm)** | femoral head diameter, head size, 28mm/32mm/36mm head | `28 mm`、`32 mm`、`36 mm` |
| 球头纹理 | surface texture, dimpled, grooved | `凹坑纹理`、`沟槽纹理` |
| 球头加工工艺 | machining, polishing, grinding | `精密研磨` |
| **球头后处理** | coating, TiN, DLC, CrN, nitriding, PVD | `TiN涂层`、`DLC涂层`、`等离子氮化` |
| 球头晶粒尺寸 | grain size | `5-10 μm` |
| 球头晶粒取向 | grain orientation | `随机取向` |
| 球头相组成 | phase composition, FCC, HCP | `FCC相为主` |
| 碳化物尺寸 | carbide size | `1-3 μm` |
| 碳化物分布位置 | carbide distribution | `晶界分布` |
| 碳化物连续性 | carbide continuity | `连续分布` |

**🔍 材料名称对照**：
- CoCrMo / Co-Cr-Mo / cobalt-chromium-molybdenum → CoCrMo合金
- Ti6Al4V / Ti-6Al-4V / titanium alloy → Ti6Al4V
- 316L / 316L stainless steel → 316L不锈钢
- Alumina / Al2O3 / aluminum oxide → Al₂O₃陶瓷
- Zirconia / ZrO2 / Y-TZP → ZrO₂陶瓷
- BIOLOX delta / BIOLOX forte → 对应陶瓷名

---

### 📌 Sheet4_配合信息表

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| **内衬-球头径向间隙(mm)** | radial clearance, diametral clearance, gap | `0.1 mm`、`100 μm` |

---

### 📌 Sheet5_股骨柄基本信息表

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| 股骨柄材料类别 | metal stem, titanium stem | `金属` |
| **股骨柄材料名称** | Ti6Al4V, CoCrMo stem | `Ti6Al4V` |
| **锥度(°)** | taper angle, Morse taper, 5°42', 12/14 taper | `5°42'`、`5.6°` |
| 锥颈尺寸 | taper size, 12/14, V40 | `12/14` |
| **颈长(mm)** | neck length, +0, +3.5, +7 | `12 mm`、`+3.5 mm` |
| 锥套设计 | taper sleeve, adapter | `钛合金锥套` |
| 锥度间隙(°) | taper mismatch, angular mismatch | `0.02°` |
| 股骨柄颈干角(°) | neck-shaft angle, CCD angle | `135°` |
| 股骨柄偏心距(mm) | offset | `42 mm` |
| 股骨柄拓扑结构 | porous structure, trabecular, lattice | `多孔结构`、`蜂窝结构` |
| **股骨柄孔隙率(%)** | porosity, pore volume fraction | `65%`、`60-70%` |
| 股骨柄横截面 | cross-section, rectangular, trapezoidal | `矩形`、`梯形` |
| 柄体长度H(mm) | stem length | `150 mm` |
| 股骨柄加工工艺 | manufacturing, 3D printing, SLM, EBM | `选择性激光熔化(SLM)` |
| 股骨柄后处理 | surface treatment, HA coating, grit blasting | `HA涂层`、`喷砂处理` |

---

### 📌 Sheet6_内衬物理性能表

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| 内衬硬度(HV) | hardness, Shore D | `20 HV`、`65 Shore D` |
| **内衬表面粗糙度(μm)** | surface roughness, Ra | `0.5 μm`、`Ra = 0.5 μm` |
| **内衬弹性模量(GPa)** | elastic modulus, Young's modulus, E | `1.0 GPa`、`1000 MPa` |
| 内衬杨氏模量 | Young's modulus | `1.0 GPa` |
| 内衬极限拉伸强度 | ultimate tensile strength, UTS | `40 MPa` |
| 内衬弯曲强度 | flexural strength | `35 MPa` |
| 内衬剪切强度 | shear strength | `25 MPa` |
| 内衬断裂韧性 | fracture toughness, KIC | `2.5 MPa·m^0.5` |
| 内衬抗压强度(MPa) | compressive strength | `25 MPa` |
| 内衬屈服强度(MPa) | yield strength | `20 MPa` |
| 内衬密度(g/cm³) | density | `0.93 g/cm³` |
| 内衬泊松比 | Poisson's ratio | `0.46` |

---

### 📌 Sheet7_球头物理性能表

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| **球头硬度(HV)** | hardness, Vickers hardness, HV, HRC | `450 HV`、`45 HRC` |
| **球头表面粗糙度(nm)** | surface roughness, Ra, surface finish | `5 nm`、`Ra < 10 nm` |
| **弹性模量(GPa)** | elastic modulus, Young's modulus | `210 GPa` |
| 球头抗压强度(MPa) | compressive strength | `2000 MPa` |
| 球头屈服强度(MPa) | yield strength | `450 MPa` |
| 球头断裂伸长率 | elongation at break | `12%` |
| 球头密度(g/cm³) | density | `8.3 g/cm³` |
| 球头泊松比 | Poisson's ratio | `0.30` |

---

### 📌 Sheet8_股骨柄物理性能表

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| 股骨柄硬度(HV) | hardness | `350 HV` |
| 股骨柄表面粗糙度(μm) | surface roughness, Ra | `2.5 μm` |
| 股骨柄弹性模量(GPa) | elastic modulus | `110 GPa` |
| 股骨柄抗压强度(MPa) | compressive strength | `1000 MPa` |
| 股骨柄屈服强度(MPa) | yield strength | `850 MPa` |
| 股骨柄密度(g/cm³) | density | `4.43 g/cm³` |
| 股骨柄泊松比 | Poisson's ratio | `0.34` |

---

### 📌 Sheet9_实验参数（摩擦磨损实验）

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| **实验器材** | tribometer, wear simulator, pin-on-disk, ball-on-disk, hip simulator | `Pin-on-Disc`、`髋关节模拟器`、`Ball-on-Flat` |
| **滑动距离** | sliding distance, total distance | `1000 m`、`5 km` |
| **频率** | frequency, oscillation frequency | `1 Hz`、`2 Hz` |
| **摩擦时间** | test duration, wear duration | `2 h`、`5 million cycles` |
| **载荷** | load, normal load, applied load, contact force | `5 N`、`2000 N`、`3 kN` |
| **实验温度** | temperature, test temperature | `37°C`、`室温` |
| **润滑液类型** | lubricant, bovine serum, PBS, saline, synovial fluid | `25% bovine serum`、`PBS缓冲液`、`生理盐水` |
| **蛋白质浓度** | protein concentration, albumin concentration | `25 g/L`、`20 mg/mL` |
| 润滑液pH | pH value | `7.4` |
| 接触载荷 | contact load, Hertzian contact | `2000 N` |
| **运动模式** | motion, reciprocating, unidirectional, multidirectional | `往复运动`、`单向滑动`、`多向运动` |
| **速率** | speed, sliding speed, velocity | `50 mm/s`、`0.1 m/s` |
| **接触方式** | contact type, point contact, line contact | `点接触`、`面接触` |

**🔍 实验设备对照**：
- Pin-on-disc / Pin-on-disk → Pin-on-Disc摩擦试验机
- Ball-on-disc / Ball-on-flat → Ball-on-Disc/Flat试验机
- Hip simulator / Hip joint simulator → 髋关节模拟器
- Knee simulator → 膝关节模拟器
- Reciprocating tribometer → 往复式摩擦试验机

---

### 📌 Sheet10_性能测试结果表

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| 内衬相含量变化 | crystallinity change, phase transformation | `结晶度从45%增至52%` |
| **累计磨损量** | total wear, cumulative wear, wear volume, wear mass | `15.6 mg`、`2.3 mm³` |
| **磨损率** | wear rate, specific wear rate, k | `3.2 mg/Mc`、`1.5×10⁻⁶ mm³/Nm` |
| **摩擦系数** | coefficient of friction, COF, friction coefficient, μ | `0.12`、`0.12±0.02` |
| **腐蚀速率** | corrosion rate | `0.05 mm/year`、`2.5 μA/cm²` |
| **离子释放量** | ion release, metal ion concentration | `Cr: 2.5 μg/L, Co: 1.8 μg/L` |
| 磨损颗粒大小 | particle size, debris size | `0.1-1 μm` |
| 磨损颗粒形貌 | particle morphology, debris shape | `片状`、`球状`、`不规则形` |
| 摩擦膜组成 | tribofilm composition, transfer film | `氧化物膜`、`蛋白质吸附层` |
| 摩擦膜厚度 | tribofilm thickness | `50 nm` |
| 抗疲劳性 | fatigue resistance, fatigue life | `10^7 cycles` |
| **接触应力** | contact stress, contact pressure, Hertzian stress | `25 MPa`、`1.2 GPa` |
| **Von Mises应力** | Von Mises stress, equivalent stress | `150 MPa` |

**🔍 磨损率单位**：
- mg/Mc (毫克/百万次循环)
- mm³/Nm (立方毫米/牛顿·米)
- mm³/m (立方毫米/米)
- μm/year (微米/年)

---

### 📌 Sheet11_计算模拟参数表

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| **计算建模软件** | ABAQUS, ANSYS, COMSOL, Fluent, Matlab | `ABAQUS`、`ANSYS Workbench` |
| **计算建模输入参数** | boundary conditions, material properties, mesh size | `载荷2000N，摩擦系数0.1，网格尺寸0.5mm` |
| **计算建模输出参数** | maximum stress, deformation, contact pressure | `最大Von Mises应力150MPa，最大变形0.1mm` |

---

### 📌 Sheet12_计算模拟图像表

| 字段 | 论文中常见表达 | 提取示例 |
|------|---------------|----------|
| 计算建模模拟结构图 | FEA model, mesh model, stress distribution | `应力分布云图` |
| 计算建模模拟结构图说明 | showing stress distribution, deformation contour | `Von Mises应力分布，最大值位于接触区` |

---

## 📤 输出格式

```json
{
  "chunk_id": 1,
  "extractions": [
    {
      "record_id": 0,
      "record_name": "CoCrMo-抛光",
      "fields": {
        "Sheet1_基本信息表": {
          "应用部位": "髋关节",
          "论文DOI号": "10.1016/j.wear.2023.204896"
        },
        "Sheet3_球头基本信息表": {
          "球头材料类别": "金属",
          "球头材料名称": "CoCrMo合金",
          "球头合金成分": "Co-28Cr-6Mo",
          "球头直径(mm)": "28 mm",
          "球头后处理": "镜面抛光"
        },
        "Sheet7_球头物理性能表": {
          "球头硬度(HV)": "450±20 HV",
          "球头表面粗糙度(nm)": "5±2 nm",
          "弹性模量(GPa)": "210 GPa"
        },
        "Sheet9_实验参数": {
          "实验器材": "Pin-on-Disc摩擦试验机",
          "载荷": "5 N",
          "频率": "1 Hz",
          "滑动距离": "1000 m",
          "润滑液类型": "25% bovine serum",
          "蛋白质浓度": "25 g/L",
          "实验温度": "37°C",
          "运动模式": "往复滑动"
        },
        "Sheet10_性能测试结果表": {
          "摩擦系数": "0.12±0.02",
          "磨损率": "3.2±0.5 mg/Mc",
          "累计磨损量": "15.6 mg"
        }
      }
    }
  ],
  "no_relevant_data": false
}
```

---

## ⚠️ 重要提醒

### 不要遗漏这些常见数据：
1. **尺寸数据**：球头直径、内衬厚度、颈长、间隙
2. **材料成分**：合金成分比例、添加剂含量
3. **表面参数**：粗糙度Ra、硬度HV
4. **实验条件**：载荷、温度、频率、润滑液
5. **性能结果**：摩擦系数、磨损率、磨损量

### 表名必须准确
使用标准表名：Sheet1_基本信息表、Sheet2_内衬基本信息表、Sheet3_球头基本信息表、Sheet4_配合信息表、Sheet5_股骨柄基本信息表、Sheet6_内衬物理性能表、Sheet7_球头物理性能表、Sheet8_股骨柄物理性能表、Sheet9_实验参数、Sheet10_性能测试结果表、Sheet11_计算模拟参数表、Sheet12_计算模拟图像表

### 无相关数据时
```json
{"chunk_id": 3, "extractions": [], "no_relevant_data": true}
```

**直接输出JSON，不要markdown代码块：**
