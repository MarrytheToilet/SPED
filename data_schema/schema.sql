-- 人工关节材料数据库 Schema
-- 生成时间: 2026-02-06
-- Schema版本: 3.0

-- Sheet1_基本信息表
CREATE TABLE IF NOT EXISTS basic_info (
    '数据ID' TEXT PRIMARY KEY NOT NULL,
    '应用部位' TEXT,
    '产品所属专利号或文献' TEXT,
    '来源文件' TEXT,
    '论文标题' TEXT,
    '论文DOI号' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_basic_info_application ON basic_info(应用部位);
CREATE INDEX IF NOT EXISTS idx_basic_info_dataid ON basic_info(数据ID);

-- Sheet2_内衬基本信息表
CREATE TABLE IF NOT EXISTS liner_basic (
    '数据ID' TEXT NOT NULL,
    '内衬材料类别' TEXT,
    '内衬材料名称' TEXT,
    '成型方式' TEXT,
    '熔融温度' TEXT,
    '成型压力' TEXT,
    '保温时间' TEXT,
    '碳纤维质量分数' TEXT,
    '碳纤维长度' TEXT,
    '碳纤维外径' TEXT,
    '碳纳米管质量分数' TEXT,
    '碳纳米管长度' TEXT,
    '碳纳米管外径' TEXT,
    '石墨烯质量分数' TEXT,
    '石墨烯厚度' TEXT,
    '石墨烯长度' TEXT,
    '碳化硅质量分数' TEXT,
    '内衬厚度(mm)' TEXT,
    '内衬偏移(mm)' TEXT,
    '内衬锁定机制' TEXT,
    '内衬加工工艺' TEXT,
    '内衬后处理' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_liner_basic_dataid ON liner_basic(数据ID);

-- Sheet3_球头基本信息表
CREATE TABLE IF NOT EXISTS head_basic (
    '数据ID' TEXT NOT NULL,
    '球头材料类别' TEXT,
    '球头材料名称' TEXT,
    '球头合金成分' TEXT,
    '球头直径(mm)' TEXT,
    '球头纹理' TEXT,
    '球头加工工艺' TEXT,
    '球头后处理' TEXT,
    '球头晶粒尺寸' TEXT,
    '球头晶粒取向' TEXT,
    '球头相组成' TEXT,
    '碳化物尺寸' TEXT,
    '碳化物分布位置' TEXT,
    '碳化物连续性' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_head_basic_dataid ON head_basic(数据ID);

-- Sheet4_配合信息表
CREATE TABLE IF NOT EXISTS fitting_info (
    '数据ID' TEXT NOT NULL,
    '内衬-球头径向间隙(mm)' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_fitting_info_dataid ON fitting_info(数据ID);

-- Sheet5_股骨柄基本信息表
CREATE TABLE IF NOT EXISTS stem_basic (
    '数据ID' TEXT NOT NULL,
    '股骨柄材料类别' TEXT,
    '股骨柄材料名称' TEXT,
    '锥度(°)' TEXT,
    '锥颈尺寸' TEXT,
    '颈长(mm)' TEXT,
    '锥套设计' TEXT,
    '锥度间隙(°)' TEXT,
    '股骨柄颈干角(°)' TEXT,
    '股骨柄偏心距(mm)' TEXT,
    '股骨柄拓扑结构' TEXT,
    '股骨柄孔隙率(%)' TEXT,
    '股骨柄横截面' TEXT,
    '柄体长度H(mm)' TEXT,
    '股骨柄加工工艺' TEXT,
    '股骨柄后处理' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_stem_basic_dataid ON stem_basic(数据ID);

-- Sheet6_内衬物理性能表
CREATE TABLE IF NOT EXISTS liner_properties (
    '数据ID' TEXT NOT NULL,
    '内衬硬度(HV)' TEXT,
    '内衬表面粗糙度(μm)' TEXT,
    '内衬弹性模量(GPa)' TEXT,
    '内衬杨氏模量' TEXT,
    '内衬极限拉伸强度' TEXT,
    '内衬弯曲强度' TEXT,
    '内衬剪切强度' TEXT,
    '内衬断裂韧性' TEXT,
    '内衬抗压强度(MPa)' TEXT,
    '内衬屈服强度(MPa)' TEXT,
    '内衬密度(g/cm³)' TEXT,
    '内衬泊松比' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_liner_properties_dataid ON liner_properties(数据ID);

-- Sheet7_球头物理性能表
CREATE TABLE IF NOT EXISTS head_properties (
    '数据ID' TEXT NOT NULL,
    '球头硬度(HV)' TEXT,
    '球头表面粗糙度(nm)' TEXT,
    '弹性模量(GPa)' TEXT,
    '球头抗压强度(MPa)' TEXT,
    '球头屈服强度(MPa)' TEXT,
    '球头断裂伸长率' TEXT,
    '球头密度(g/cm³)' TEXT,
    '球头泊松比' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_head_properties_dataid ON head_properties(数据ID);

-- Sheet8_股骨柄物理性能表
CREATE TABLE IF NOT EXISTS stem_properties (
    '数据ID' TEXT NOT NULL,
    '股骨柄硬度(HV)' TEXT,
    '股骨柄表面粗糙度(μm)' TEXT,
    '股骨柄弹性模量(GPa)' TEXT,
    '股骨柄抗压强度(MPa)' TEXT,
    '股骨柄屈服强度(MPa)' TEXT,
    '股骨柄密度(g/cm³)' TEXT,
    '股骨柄泊松比' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_stem_properties_dataid ON stem_properties(数据ID);

-- Sheet9_实验参数
CREATE TABLE IF NOT EXISTS experiment_params (
    '数据ID' TEXT NOT NULL,
    '实验器材' TEXT,
    '滑动距离' TEXT,
    '频率' TEXT,
    '摩擦时间' TEXT,
    '载荷' TEXT,
    '实验温度' TEXT,
    '润滑液类型' TEXT,
    '蛋白质浓度' TEXT,
    '润滑液pH' TEXT,
    '接触载荷' TEXT,
    '运动模式' TEXT,
    '速率' TEXT,
    '接触方式' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_experiment_params_dataid ON experiment_params(数据ID);

-- Sheet10_性能测试结果表
CREATE TABLE IF NOT EXISTS test_results (
    '数据ID' TEXT NOT NULL,
    '内衬相含量变化' TEXT,
    '累计磨损量' TEXT,
    '磨损率' TEXT,
    '摩擦系数' TEXT,
    '腐蚀速率' TEXT,
    '离子释放量' TEXT,
    '磨损颗粒大小' TEXT,
    '磨损颗粒形貌' TEXT,
    '摩擦膜组成' TEXT,
    '摩擦膜厚度' TEXT,
    '抗疲劳性' TEXT,
    '接触应力' TEXT,
    'Von Mises应力' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_test_results_dataid ON test_results(数据ID);

-- Sheet11_计算模拟参数表
CREATE TABLE IF NOT EXISTS simulation_params (
    '数据ID' TEXT NOT NULL,
    '计算建模软件' TEXT,
    '计算建模输入参数' TEXT,
    '计算建模输出参数' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_simulation_params_dataid ON simulation_params(数据ID);

-- Sheet12_计算模拟图像表
CREATE TABLE IF NOT EXISTS simulation_images (
    '数据ID' TEXT NOT NULL,
    '计算建模模拟结构图' TEXT,
    '计算建模模拟结构图说明' TEXT,
    '来源文件' TEXT,
    '论文ID' TEXT,
    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 外键约束
-- FOREIGN KEY (数据ID) REFERENCES basic_info(数据ID);

CREATE INDEX IF NOT EXISTS idx_simulation_images_dataid ON simulation_images(数据ID);
