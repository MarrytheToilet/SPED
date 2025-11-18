-- Table for sheet '目录'
CREATE TABLE sheet_目录 (
  "dataid" TEXT NOT NULL /* 数据ID */,
  "工作表名" BIGINT NULL /* 工作表名 */,
  "内容" TEXT NULL /* 内容 */
);
ALTER TABLE sheet_目录 ADD CONSTRAINT fk_sheet_目录_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '元数据'
CREATE TABLE sheet_元数据 (
  "dataid" TEXT NULL /* 数据ID */,
  "北京科技大学_001_高精尖学院_0010" TEXT NULL /* 北京科技大学（001）/高精尖学院（0010） */
);
ALTER TABLE sheet_元数据 ADD CONSTRAINT fk_sheet_元数据_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '1'
CREATE TABLE sheet_1 (
  "dataid" TEXT NOT NULL /* 数据ID */,
  "数据标识" TEXT NULL /* 数据标识 */,
  "应用部位" TEXT NULL /* 应用部位 */,
  "产品所属专利号或文献" TEXT NULL /* 产品所属专利号或文献 */,
  "球头信息_球头基本信息" TEXT NULL /* 球头信息.球头基本信息 */,
  "球头信息_球头_成分组成" TEXT NULL /* 球头信息.球头-成分组成 */,
  "球头信息_球头_物理性能" TEXT NULL /* 球头信息.球头-物理性能 */,
  "球头信息_球头_微观组织" TEXT NULL /* 球头信息.球头-微观组织 */,
  "股骨柄信息_股骨柄基本信息" TEXT NULL /* 股骨柄信息.股骨柄基本信息 */,
  "股骨柄信息_股骨柄_成分组成" TEXT NULL /* 股骨柄信息.股骨柄-成分组成 */,
  "股骨柄信息_股骨柄_物理性能" TEXT NULL /* 股骨柄信息.股骨柄-物理性能 */,
  "股骨柄信息_股骨柄_微观组织" TEXT NULL /* 股骨柄信息.股骨柄-微观组织 */,
  "内衬信息_内衬_基本信息" TEXT NULL /* 内衬信息.内衬-基本信息 */,
  "内衬信息_内衬_改性填料" TEXT NULL /* 内衬信息.内衬-改性填料 */,
  "内衬信息_内衬_成分组成" TEXT NULL /* 内衬信息.内衬-成分组成 */,
  "内衬信息_内衬_物理性能" TEXT NULL /* 内衬信息.内衬-物理性能 */,
  "内衬信息_复合材料性能" TEXT NULL /* 内衬信息.复合材料性能 */,
  "内衬信息_内衬_材料表征" TEXT NULL /* 内衬信息.内衬-材料表征 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置 */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验环境_润滑液组成" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验环境-润滑液组成 */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果 */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头表面成分分析" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头表面成分分析 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_锥颈与球头_实验环境_润滑液组成" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.锥颈与球头-实验环境-润滑液组成 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.腐蚀与磨损实验结果 */,
  PRIMARY KEY ("dataid")
);

-- Table for sheet '2'
CREATE TABLE sheet_2 (
  "dataid" TEXT NULL /* 数据ID */,
  "球头信息_球头基本信息_材料编号" TEXT NULL /* 球头信息.球头基本信息.材料编号 */,
  "球头信息_球头基本信息_材料类别" TEXT NULL /* 球头信息.球头基本信息.材料类别 */,
  "球头信息_球头基本信息_加工工艺" TEXT NULL /* 球头信息.球头基本信息.加工工艺 */,
  "球头信息_球头基本信息_表面处理" TEXT NULL /* 球头信息.球头基本信息.表面处理 */
);
ALTER TABLE sheet_2 ADD CONSTRAINT fk_sheet_2_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '3'
CREATE TABLE sheet_3 (
  "dataid" TEXT NULL /* 数据ID */,
  "球头信息_球头_成分组成_成分" TEXT NULL /* 球头信息.球头-成分组成.成分 */,
  "球头信息_球头_成分组成_成分_2" DOUBLE PRECISION NULL /* 球头信息.球头-成分组成.成分(%) */,
  "球头信息_球头_成分组成_碳含量" DOUBLE PRECISION NULL /* 球头信息.球头-成分组成.碳含量(%) */
);
ALTER TABLE sheet_3 ADD CONSTRAINT fk_sheet_3_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '4'
CREATE TABLE sheet_4 (
  "dataid" TEXT NULL /* 数据ID */,
  "球头信息_球头_物理性能_硬度_hv" TEXT NULL /* 球头信息.球头-物理性能.硬度(HV) */,
  "球头信息_球头_物理性能_接触应力_mpa" TEXT NULL /* 球头信息.球头-物理性能.接触应力(MPa) */,
  "球头信息_球头_物理性能_表面粗糙度_μm" TEXT NULL /* 球头信息.球头-物理性能.表面粗糙度(μm) */,
  "球头信息_球头_物理性能_弹性模量_gpa" TEXT NULL /* 球头信息.球头-物理性能.弹性模量(GPa) */,
  "球头信息_球头_物理性能_抗压强度_mpa" TEXT NULL /* 球头信息.球头-物理性能.抗压强度(MPa) */,
  "球头信息_球头_物理性能_抗拉强度_mpa" TEXT NULL /* 球头信息.球头-物理性能.抗拉强度(MPa) */,
  "球头信息_球头_物理性能_屈服强度_mpa" TEXT NULL /* 球头信息.球头-物理性能.屈服强度(MPa) */,
  "球头信息_球头_物理性能_屈服应力_mpa" TEXT NULL /* 球头信息.球头-物理性能.屈服应力(MPa) */,
  "球头信息_球头_物理性能_密度_kg_m³" TEXT NULL /* 球头信息.球头-物理性能.密度(Kg/m³) */,
  "球头信息_球头_物理性能_剪切模量_pa" TEXT NULL /* 球头信息.球头-物理性能.剪切模量(Pa) */,
  "球头信息_球头_物理性能_极限拉伸强度_mpa" TEXT NULL /* 球头信息.球头-物理性能.极限拉伸强度(MPa) */,
  "球头信息_球头_物理性能_泊松比" TEXT NULL /* 球头信息.球头-物理性能.泊松比 */,
  "球头信息_球头_物理性能_疲劳强度_mpa" TEXT NULL /* 球头信息.球头-物理性能.疲劳强度(MPa) */,
  "球头信息_球头_物理性能_断裂韧性_mpa_m1_2" TEXT NULL /* 球头信息.球头-物理性能.断裂韧性(MPa·m1/2) */,
  "球头信息_球头_物理性能_亲疏水性" TEXT NULL /* 球头信息.球头-物理性能.亲疏水性 */,
  "球头信息_球头_物理性能_表面电荷_势_mv" TEXT NULL /* 球头信息.球头-物理性能.表面电荷/势(mV) */,
  "球头信息_球头_物理性能_蠕变常数" TEXT NULL /* 球头信息.球头-物理性能.蠕变常数 */,
  "球头信息_球头_物理性能_孔隙率" DOUBLE PRECISION NULL /* 球头信息.球头-物理性能.孔隙率(%) */,
  "球头信息_球头_物理性能_孔径大小_μm" TEXT NULL /* 球头信息.球头-物理性能.孔径大小(μm) */,
  "球头信息_球头_物理性能_杨氏模量_gpa" TEXT NULL /* 球头信息.球头-物理性能.杨氏模量(GPa) */
);
ALTER TABLE sheet_4 ADD CONSTRAINT fk_sheet_4_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '5'
CREATE TABLE sheet_5 (
  "dataid" TEXT NULL /* 数据ID */,
  "球头信息_球头_微观组织_晶粒大小_μm" TEXT NULL /* 球头信息.球头-微观组织.晶粒大小(μm) */,
  "球头信息_球头_微观组织_晶粒取向" TEXT NULL /* 球头信息.球头-微观组织.晶粒取向 */,
  "球头信息_球头_微观组织_晶粒形貌" TEXT NULL /* 球头信息.球头-微观组织.晶粒形貌 */,
  "球头信息_球头_微观组织_晶粒形貌描述" TEXT NULL /* 球头信息.球头-微观组织.晶粒形貌描述 */,
  "球头信息_球头_微观组织_碳化物的分布情况" TEXT NULL /* 球头信息.球头-微观组织.碳化物的分布情况 */,
  "球头信息_球头_微观组织_碳化物的分布情况描述" TEXT NULL /* 球头信息.球头-微观组织.碳化物的分布情况描述 */
);
ALTER TABLE sheet_5 ADD CONSTRAINT fk_sheet_5_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '6'
CREATE TABLE sheet_6 (
  "dataid" TEXT NULL /* 数据ID */,
  "股骨柄信息_股骨柄基本信息_材料编号" TEXT NULL /* 股骨柄信息.股骨柄基本信息.材料编号 */,
  "股骨柄信息_股骨柄基本信息_材料类别" TEXT NULL /* 股骨柄信息.股骨柄基本信息.材料类别 */,
  "股骨柄信息_股骨柄基本信息_加工工艺" TEXT NULL /* 股骨柄信息.股骨柄基本信息.加工工艺 */,
  "股骨柄信息_股骨柄基本信息_表面处理" TEXT NULL /* 股骨柄信息.股骨柄基本信息.表面处理 */
);
ALTER TABLE sheet_6 ADD CONSTRAINT fk_sheet_6_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '7'
CREATE TABLE sheet_7 (
  "dataid" TEXT NULL /* 数据ID */,
  "股骨柄信息_股骨柄_成分组成_成分" TEXT NULL /* 股骨柄信息.股骨柄-成分组成.成分 */,
  "股骨柄信息_股骨柄_成分组成_成分_2" DOUBLE PRECISION NULL /* 股骨柄信息.股骨柄-成分组成.成分(%) */,
  "股骨柄信息_股骨柄_成分组成_碳含量" DOUBLE PRECISION NULL /* 股骨柄信息.股骨柄-成分组成.碳含量(%) */
);
ALTER TABLE sheet_7 ADD CONSTRAINT fk_sheet_7_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '8'
CREATE TABLE sheet_8 (
  "dataid" TEXT NULL /* 数据ID */,
  "股骨柄信息_股骨柄_物理性能_硬度_hv" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.硬度(HV) */,
  "股骨柄信息_股骨柄_物理性能_接触应力_mpa" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.接触应力(MPa) */,
  "股骨柄信息_股骨柄_物理性能_表面粗糙度_μm" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.表面粗糙度(μm) */,
  "股骨柄信息_股骨柄_物理性能_弹性模量_gpa" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.弹性模量(GPa) */,
  "股骨柄信息_股骨柄_物理性能_抗压强度_mpa" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.抗压强度(MPa) */,
  "股骨柄信息_股骨柄_物理性能_抗拉强度_mpa" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.抗拉强度(MPa) */,
  "股骨柄信息_股骨柄_物理性能_屈服强度_mpa" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.屈服强度(MPa) */,
  "股骨柄信息_股骨柄_物理性能_屈服应力_mpa" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.屈服应力(MPa) */,
  "股骨柄信息_股骨柄_物理性能_疲劳强度_mpa" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.疲劳强度(MPa) */,
  "股骨柄信息_股骨柄_物理性能_断裂韧性_mpa_m1_2" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.断裂韧性(MPa·m1/2) */,
  "股骨柄信息_股骨柄_物理性能_亲疏水性" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.亲疏水性 */,
  "股骨柄信息_股骨柄_物理性能_表面电荷_势_mv" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.表面电荷/势(mV) */,
  "股骨柄信息_股骨柄_物理性能_蠕变常数" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.蠕变常数 */,
  "股骨柄信息_股骨柄_物理性能_孔隙率" DOUBLE PRECISION NULL /* 股骨柄信息.股骨柄-物理性能.孔隙率(%) */,
  "股骨柄信息_股骨柄_物理性能_孔径大小_μm" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.孔径大小(μm) */,
  "股骨柄信息_股骨柄_物理性能_杨氏模量_gpa" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.杨氏模量(GPa) */,
  "股骨柄信息_股骨柄_物理性能_密度_kg_m³" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.密度(Kg/m³) */,
  "股骨柄信息_股骨柄_物理性能_剪切模量_pa" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.剪切模量(Pa) */,
  "股骨柄信息_股骨柄_物理性能_极限拉伸强度_mpa" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.极限拉伸强度(MPa) */,
  "股骨柄信息_股骨柄_物理性能_泊松比" TEXT NULL /* 股骨柄信息.股骨柄-物理性能.泊松比 */
);
ALTER TABLE sheet_8 ADD CONSTRAINT fk_sheet_8_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '9'
CREATE TABLE sheet_9 (
  "dataid" TEXT NULL /* 数据ID */,
  "股骨柄信息_股骨柄_微观组织_晶粒大小_μm" TEXT NULL /* 股骨柄信息.股骨柄-微观组织.晶粒大小(μm) */,
  "股骨柄信息_股骨柄_微观组织_晶粒取向" TEXT NULL /* 股骨柄信息.股骨柄-微观组织.晶粒取向 */,
  "股骨柄信息_股骨柄_微观组织_晶粒形貌" TEXT NULL /* 股骨柄信息.股骨柄-微观组织.晶粒形貌 */,
  "股骨柄信息_股骨柄_微观组织_晶粒形貌描述" TEXT NULL /* 股骨柄信息.股骨柄-微观组织.晶粒形貌描述 */,
  "股骨柄信息_股骨柄_微观组织_碳化物的分布情况" TEXT NULL /* 股骨柄信息.股骨柄-微观组织.碳化物的分布情况 */,
  "股骨柄信息_股骨柄_微观组织_碳化物的分布情况描述" TEXT NULL /* 股骨柄信息.股骨柄-微观组织.碳化物的分布情况描述 */
);
ALTER TABLE sheet_9 ADD CONSTRAINT fk_sheet_9_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '10'
CREATE TABLE sheet_10 (
  "dataid" TEXT NULL /* 数据ID */,
  "内衬信息_内衬_基本信息_材料编号" TEXT NULL /* 内衬信息.内衬-基本信息.材料编号 */,
  "内衬信息_内衬_基本信息_材料类别" TEXT NULL /* 内衬信息.内衬-基本信息.材料类别 */,
  "内衬信息_内衬_基本信息_分子量" TEXT NULL /* 内衬信息.内衬-基本信息.分子量 */,
  "内衬信息_内衬_基本信息_结晶度" TEXT NULL /* 内衬信息.内衬-基本信息.结晶度 */,
  "内衬信息_内衬_基本信息_改性填料" TEXT NULL /* 内衬信息.内衬-基本信息.改性填料 */,
  "内衬信息_内衬_基本信息_加工工艺" TEXT NULL /* 内衬信息.内衬-基本信息.加工工艺 */,
  "内衬信息_内衬_基本信息_表面处理" TEXT NULL /* 内衬信息.内衬-基本信息.表面处理 */
);
ALTER TABLE sheet_10 ADD CONSTRAINT fk_sheet_10_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '11'
CREATE TABLE sheet_11 (
  "dataid" TEXT NULL /* 数据ID */,
  "内衬信息_内衬_改性填料_改性填料的种类" TEXT NULL /* 内衬信息.内衬-改性填料.改性填料的种类 */,
  "内衬信息_内衬_改性填料_改性填料的添加量_wt" DOUBLE PRECISION NULL /* 内衬信息.内衬-改性填料.改性填料的添加量(wt%) */
);
ALTER TABLE sheet_11 ADD CONSTRAINT fk_sheet_11_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '12'
CREATE TABLE sheet_12 (
  "dataid" TEXT NULL /* 数据ID */,
  "内衬信息_内衬_成分组成_材料名称" TEXT NULL /* 内衬信息.内衬-成分组成.材料名称 */,
  "内衬信息_内衬_成分组成_成分" TEXT NULL /* 内衬信息.内衬-成分组成.成分 */,
  "内衬信息_内衬_成分组成_组成" DOUBLE PRECISION NULL /* 内衬信息.内衬-成分组成.组成(%) */
);
ALTER TABLE sheet_12 ADD CONSTRAINT fk_sheet_12_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '13'
CREATE TABLE sheet_13 (
  "dataid" TEXT NULL /* 数据ID */,
  "内衬信息_内衬_物理性能_硬度_hv" TEXT NULL /* 内衬信息.内衬-物理性能.硬度(HV) */,
  "内衬信息_内衬_物理性能_接触应力_mpa" TEXT NULL /* 内衬信息.内衬-物理性能.接触应力(MPa) */,
  "内衬信息_内衬_物理性能_表面粗糙度_μm" TEXT NULL /* 内衬信息.内衬-物理性能.表面粗糙度(μm) */,
  "内衬信息_内衬_物理性能_弹性模量_gpa" TEXT NULL /* 内衬信息.内衬-物理性能.弹性模量(GPa) */,
  "内衬信息_内衬_物理性能_抗压强度_mpa" TEXT NULL /* 内衬信息.内衬-物理性能.抗压强度(MPa) */,
  "内衬信息_内衬_物理性能_抗拉强度_mpa" TEXT NULL /* 内衬信息.内衬-物理性能.抗拉强度(MPa) */,
  "内衬信息_内衬_物理性能_屈服强度_mpa" TEXT NULL /* 内衬信息.内衬-物理性能.屈服强度(MPa) */,
  "内衬信息_内衬_物理性能_屈服应力_mpa" TEXT NULL /* 内衬信息.内衬-物理性能.屈服应力(MPa) */,
  "内衬信息_内衬_物理性能_疲劳强度_mpa" TEXT NULL /* 内衬信息.内衬-物理性能.疲劳强度(MPa) */,
  "内衬信息_内衬_物理性能_断裂韧性_mpa_m1_2" TEXT NULL /* 内衬信息.内衬-物理性能.断裂韧性(MPa·m1/2) */,
  "内衬信息_内衬_物理性能_亲疏水性" TEXT NULL /* 内衬信息.内衬-物理性能.亲疏水性 */,
  "内衬信息_内衬_物理性能_表面电荷_势_mv" TEXT NULL /* 内衬信息.内衬-物理性能.表面电荷/势(mV) */,
  "内衬信息_内衬_物理性能_蠕变常数" TEXT NULL /* 内衬信息.内衬-物理性能.蠕变常数 */,
  "内衬信息_内衬_物理性能_密度_kg_m³" TEXT NULL /* 内衬信息.内衬-物理性能.密度(Kg/m³) */,
  "内衬信息_内衬_物理性能_剪切模量_pa" TEXT NULL /* 内衬信息.内衬-物理性能.剪切模量(Pa) */,
  "内衬信息_内衬_物理性能_极限拉伸强度_mpa" TEXT NULL /* 内衬信息.内衬-物理性能.极限拉伸强度(MPa) */,
  "内衬信息_内衬_物理性能_泊松比" TEXT NULL /* 内衬信息.内衬-物理性能.泊松比 */
);
ALTER TABLE sheet_13 ADD CONSTRAINT fk_sheet_13_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '14'
CREATE TABLE sheet_14 (
  "dataid" TEXT NULL /* 数据ID */,
  "内衬信息_复合材料性能_直径_nm" TEXT NULL /* 内衬信息.复合材料性能.直径(nm) */,
  "内衬信息_复合材料性能_长度_μm" TEXT NULL /* 内衬信息.复合材料性能.长度(μm) */,
  "内衬信息_复合材料性能_比表面积_m²_g" TEXT NULL /* 内衬信息.复合材料性能.比表面积(m²/g) */,
  "内衬信息_复合材料性能_粒径范围_μm" TEXT NULL /* 内衬信息.复合材料性能.粒径范围(μm) */,
  "内衬信息_复合材料性能_复合薄膜厚度_mm" TEXT NULL /* 内衬信息.复合材料性能.复合薄膜厚度(mm) */,
  "内衬信息_复合材料性能_相对结晶度" DOUBLE PRECISION NULL /* 内衬信息.复合材料性能.相对结晶度(%) */,
  "内衬信息_复合材料性能_拉伸强度_mpa" TEXT NULL /* 内衬信息.复合材料性能.拉伸强度(MPa) */,
  "内衬信息_复合材料性能_弹性模量_mpa" TEXT NULL /* 内衬信息.复合材料性能.弹性模量​​(MPa) */,
  "内衬信息_复合材料性能_平均孔径_nm" TEXT NULL /* 内衬信息.复合材料性能.平均孔径(nm) */,
  "内衬信息_复合材料性能_界面吸附能_kcal_mol" TEXT NULL /* 内衬信息.复合材料性能.界面吸附能(Kcal/mol) */,
  "内衬信息_复合材料性能_内聚力能密度_j_cm³" TEXT NULL /* 内衬信息.复合材料性能.内聚力能密度​​(J/cm³) */
);
ALTER TABLE sheet_14 ADD CONSTRAINT fk_sheet_14_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '15'
CREATE TABLE sheet_15 (
  "dataid" TEXT NULL /* 数据ID */,
  "内衬信息_内衬_材料表征_表征方法" TEXT NULL /* 内衬信息.内衬-材料表征.表征方法 */,
  "内衬信息_内衬_材料表征_表征图片" TEXT NULL /* 内衬信息.内衬-材料表征.表征图片 */,
  "内衬信息_内衬_材料表征_分析结果" TEXT NULL /* 内衬信息.内衬-材料表征.分析结果 */
);
ALTER TABLE sheet_15 ADD CONSTRAINT fk_sheet_15_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '16'
CREATE TABLE sheet_16 (
  "dataid" TEXT NULL /* 数据ID */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置_测试设备" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置.测试设备 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置_测试设备图片" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置.测试设备图片 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置_摩擦测试条件" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置.摩擦测试条件 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置_负载_n" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置.负载(N) */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置_滑动距离_mm" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置.滑动距离(mm) */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置_润滑液类型" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置.润滑液类型 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置_蛋白质浓度_g_l" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置.蛋白质浓度(g/L) */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置_测试周期" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置.测试周期 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置_测试温度" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置.测试温度(℃) */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置_测试时间_h" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置.测试时间(h) */
);
ALTER TABLE sheet_16 ADD CONSTRAINT fk_sheet_16_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '17'
CREATE TABLE sheet_17 (
  "dataid" TEXT NULL /* 数据ID */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果_腐蚀速率_mm³_year" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果.腐蚀速率（mm³/year） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果_腐蚀电流_a" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果.腐蚀电流（A） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果_测试时间_h" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果.测试时间（h） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果_开路电位_v" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果.开路电位（V） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果_零电流电位_v" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果.零电流电位（V） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果_离子释放量_μg_l" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果.离子释放量（μg/L） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果_钝化膜电阻_ω_cm²" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果.钝化膜电阻（Ω·cm²） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果_腐蚀形貌" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果.腐蚀形貌 */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果_腐蚀形貌描述" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果.腐蚀形貌描述 */
);
ALTER TABLE sheet_17 ADD CONSTRAINT fk_sheet_17_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '18'
CREATE TABLE sheet_18 (
  "dataid" TEXT NULL /* 数据ID */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果_腐蚀速率_mm³_year" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果.腐蚀速率（mm³/year） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果_腐蚀电流_a" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果.腐蚀电流（A） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果_测试时间_h" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果.测试时间（h） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果_开路电位_v" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果.开路电位（V） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果_零电流电位_v" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果.零电流电位（V） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果_离子释放量_μg_l" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果.离子释放量（μg/L） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果_钝化膜电阻_ω_cm²" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果.钝化膜电阻（Ω·cm²） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果_腐蚀形貌" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果.腐蚀形貌 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果_腐蚀形貌描述" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果.腐蚀形貌描述 */
);
ALTER TABLE sheet_18 ADD CONSTRAINT fk_sheet_18_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '19'
CREATE TABLE sheet_19 (
  "dataid" TEXT NULL /* 数据ID */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验环境_润滑液组成_环境名称" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验环境-润滑液组成.环境名称 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验环境_润滑液组成_成分" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验环境-润滑液组成.成分 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验环境_润滑液组成_浓度或组成" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验环境-润滑液组成.浓度或组成 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验环境_润滑液组成_单位" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验环境-润滑液组成.单位 */
);
ALTER TABLE sheet_19 ADD CONSTRAINT fk_sheet_19_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '20'
CREATE TABLE sheet_20 (
  "dataid" TEXT NULL /* 数据ID */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果_磨损率_mg_mc" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果.磨损率（mg/Mc） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果_磨损因子_mm³_nm" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果.磨损因子（mm³/Nm） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果_总重量损失_mg" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果.总重量损失（mg） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果_磨损形貌" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果.磨损形貌 */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果_磨损颗粒大小_nm" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果.磨损颗粒大小（nm） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果_磨损颗粒形貌" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果.磨损颗粒形貌 */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果_摩擦膜厚度_nm" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果.摩擦膜厚度（nm） */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果_摩擦膜成分" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果.摩擦膜成分 */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果_摩擦膜硬度_hv" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果.摩擦膜硬度（HV） */
);
ALTER TABLE sheet_20 ADD CONSTRAINT fk_sheet_20_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '21'
CREATE TABLE sheet_21 (
  "dataid" TEXT NULL /* 数据ID */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果_磨损率_mg_mc" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果.磨损率（mg/Mc） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果_磨损因子_mm³_nm" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果.磨损因子（mm³/Nm） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果_总重量损失_mg" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果.总重量损失（mg） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果_磨损形貌" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果.磨损形貌 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果_磨损颗粒大小_nm" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果.磨损颗粒大小（nm） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果_磨损颗粒形貌" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果.磨损颗粒形貌 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果_摩擦膜厚度_nm" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果.摩擦膜厚度（nm） */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果_摩擦膜成分" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果.摩擦膜成分 */,
  "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果_摩擦膜硬度_hv" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果.摩擦膜硬度（HV） */
);
ALTER TABLE sheet_21 ADD CONSTRAINT fk_sheet_21_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '22'
CREATE TABLE sheet_22 (
  "dataid" TEXT NULL /* 数据ID */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头表面成分分析_分析方法" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头表面成分分析.分析方法 */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头表面成分分析_测试环境" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头表面成分分析.测试环境 */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头表面成分分析_成分" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头表面成分分析.成分 */,
  "体外实验_内衬与球头摩擦腐蚀实验_球头表面成分分析_成分组成" TEXT NULL /* 体外实验-内衬与球头摩擦腐蚀实验.球头表面成分分析.成分组成 */
);
ALTER TABLE sheet_22 ADD CONSTRAINT fk_sheet_22_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '23'
CREATE TABLE sheet_23 (
  "dataid" TEXT NULL /* 数据ID */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_测试设备" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.测试设备 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_测试设备图片" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.测试设备图片 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_摩擦测试条件" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.摩擦测试条件 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_负载_n" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.负载(N) */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_滑动距离_mm" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.滑动距离(mm) */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_润滑液类型" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.润滑液类型 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_蛋白质浓度_g_l" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.蛋白质浓度(g/L) */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_测试周期" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.测试周期 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_测试温度" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.测试温度(℃) */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_测试时间_h" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.测试时间(h) */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_装配扭矩_n_m" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.装配扭矩（N·m） */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_接触应力_mpa" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.接触应力（MPa） */,
  "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置_微动频率_hz" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置.微动频率（Hz） */
);
ALTER TABLE sheet_23 ADD CONSTRAINT fk_sheet_23_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '24'
CREATE TABLE sheet_24 (
  "dataid" TEXT NULL /* 数据ID */,
  "体外实验_球头与锥颈界面微动腐蚀实验_锥颈与球头_实验环境_润滑液组成_环境名称" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.锥颈与球头-实验环境-润滑液组成.环境名称 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_锥颈与球头_实验环境_润滑液组成_成分" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.锥颈与球头-实验环境-润滑液组成.成分 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_锥颈与球头_实验环境_润滑液组成_浓度或组成" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.锥颈与球头-实验环境-润滑液组成.浓度或组成 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_锥颈与球头_实验环境_润滑液组成_单位" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.锥颈与球头-实验环境-润滑液组成.单位 */
);
ALTER TABLE sheet_24 ADD CONSTRAINT fk_sheet_24_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");

-- Table for sheet '25'
CREATE TABLE sheet_25 (
  "dataid" TEXT NULL /* 数据ID */,
  "体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果_微动摩擦系数" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.腐蚀与磨损实验结果.微动摩擦系数 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果_微动磨损体积_mm³" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.腐蚀与磨损实验结果.微动磨损体积(mm³) */,
  "体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果_微动腐蚀速率_μm_年" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.腐蚀与磨损实验结果.微动腐蚀速率(μm/年) */,
  "体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果_磨损颗粒形貌" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.腐蚀与磨损实验结果.磨损颗粒形貌 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果_磨损颗粒形貌描述" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.腐蚀与磨损实验结果.磨损颗粒形貌描述 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果_腐蚀产物" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.腐蚀与磨损实验结果.腐蚀产物 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果_离子释放量" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.腐蚀与磨损实验结果.离子释放量 */,
  "体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果_界面失效模式" TEXT NULL /* 体外实验-球头与锥颈界面微动腐蚀实验.腐蚀与磨损实验结果.界面失效模式 */
);
ALTER TABLE sheet_25 ADD CONSTRAINT fk_sheet_25_dataid FOREIGN KEY ("dataid") REFERENCES sheet_1("dataid");
