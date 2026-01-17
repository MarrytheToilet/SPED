-- ================================================================================
-- 人工关节材料数据库 Schema v2.0
-- 规范化多表结构
-- 生成日期: 2026-01-17
-- ================================================================================

-- ============================================================
-- 表1: 基本信息表 (主表)
-- 用途: 记录的基本标识信息和文献来源
-- ============================================================
CREATE TABLE IF NOT EXISTS basic_info (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 数据ID，唯一标识符
    application_site TEXT,               -- 应用部位（髋关节、膝关节等）
    patent_or_literature TEXT,           -- 产品所属专利号或文献
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_basic_info_site ON basic_info(application_site);

-- ============================================================
-- 表2: 内衬基本信息表
-- 用途: 内衬材料的基本属性和加工工艺
-- ============================================================
CREATE TABLE IF NOT EXISTS liner_basic (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 外键，关联basic_info
    material_category TEXT,              -- 内衬材料类别
    material_name TEXT,                  -- 内衬材料名称
    thickness_mm TEXT,                   -- 内衬厚度(mm)
    offset_mm TEXT,                      -- 内衬偏移(mm)
    locking_mechanism TEXT,              -- 内衬锁定机制
    processing_technology TEXT,          -- 内衬加工工艺
    post_treatment TEXT,                 -- 内衬后处理
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id) ON DELETE CASCADE
);

-- ============================================================
-- 表3: 球头基本信息表
-- 用途: 球头材料的基本属性和加工工艺
-- ============================================================
CREATE TABLE IF NOT EXISTS head_basic (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 外键，关联basic_info
    material_category TEXT,              -- 球头材料类别
    material_name TEXT,                  -- 球头材料名称
    diameter_mm TEXT,                    -- 球头直径(mm)
    texture TEXT,                        -- 球头纹理
    processing_technology TEXT,          -- 球头加工工艺
    post_treatment TEXT,                 -- 球头后处理
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id) ON DELETE CASCADE
);

-- ============================================================
-- 表4: 配合信息表
-- 用途: 内衬与球头的配合参数
-- ============================================================
CREATE TABLE IF NOT EXISTS fitting_info (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 外键，关联basic_info
    radial_clearance_mm TEXT,            -- 内衬-球头径向间隙(mm)
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id) ON DELETE CASCADE
);

-- ============================================================
-- 表5: 股骨柄基本信息表
-- 用途: 股骨柄的几何参数和材料信息
-- ============================================================
CREATE TABLE IF NOT EXISTS stem_basic (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 外键，关联basic_info
    material_category TEXT,              -- 股骨柄材料类别
    material_name TEXT,                  -- 股骨柄材料名称
    taper_degree TEXT,                   -- 锥度(°)
    taper_size TEXT,                     -- 锥颈尺寸
    neck_length_mm TEXT,                 -- 颈长(mm)
    sleeve_design TEXT,                  -- 锥套设计
    taper_clearance_degree TEXT,         -- 锥度间隙(°)
    neck_shaft_angle_degree TEXT,        -- 股骨柄颈干角(°)
    offset_mm TEXT,                      -- 股骨柄偏心距(mm)
    topology_structure TEXT,             -- 股骨柄拓扑结构
    porosity_percent TEXT,               -- 股骨柄孔隙率(%)
    cross_section TEXT,                  -- 股骨柄横截面
    body_length_mm TEXT,                 -- 柄体长度H(mm)
    processing_technology TEXT,          -- 股骨柄加工工艺
    post_treatment TEXT,                 -- 股骨柄后处理
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id) ON DELETE CASCADE
);

-- ============================================================
-- 表6: 内衬物理性能表
-- 用途: 内衬材料的力学和物理性能参数
-- ============================================================
CREATE TABLE IF NOT EXISTS liner_properties (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 外键，关联basic_info
    hardness_hv TEXT,                    -- 内衬硬度(HV)
    surface_roughness_um TEXT,           -- 内衬表面粗糙度(μm)
    elastic_modulus_gpa TEXT,            -- 内衬弹性模量(GPa)
    compressive_strength_mpa TEXT,       -- 内衬抗压强度(MPa)
    yield_strength_mpa TEXT,             -- 内衬屈服强度(MPa)
    density_g_cm3 TEXT,                  -- 内衬密度(g/cm³)
    poisson_ratio TEXT,                  -- 内衬泊松比
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id) ON DELETE CASCADE
);

-- ============================================================
-- 表7: 球头物理性能表
-- 用途: 球头材料的力学和物理性能参数
-- ============================================================
CREATE TABLE IF NOT EXISTS head_properties (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 外键，关联basic_info
    hardness_hv TEXT,                    -- 球头硬度(HV)
    surface_roughness_nm TEXT,           -- 球头表面粗糙度(nm)
    elastic_modulus_gpa TEXT,            -- 弹性模量(GPa)
    compressive_strength_mpa TEXT,       -- 球头抗压强度(MPa)
    yield_strength_mpa TEXT,             -- 球头屈服强度(MPa)
    density_g_cm3 TEXT,                  -- 球头密度(g/cm³)
    poisson_ratio TEXT,                  -- 球头泊松比
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id) ON DELETE CASCADE
);

-- ============================================================
-- 表8: 股骨柄物理性能表
-- 用途: 股骨柄材料的力学和物理性能参数
-- ============================================================
CREATE TABLE IF NOT EXISTS stem_properties (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 外键，关联basic_info
    hardness_hv TEXT,                    -- 股骨柄硬度(HV)
    surface_roughness_um TEXT,           -- 股骨柄表面粗糙度(μm)
    elastic_modulus_gpa TEXT,            -- 股骨柄弹性模量(GPa)
    compressive_strength_mpa TEXT,       -- 股骨柄抗压强度(MPa)
    yield_strength_mpa TEXT,             -- 股骨柄屈服强度(MPa)
    density_g_cm3 TEXT,                  -- 股骨柄密度(g/cm³)
    poisson_ratio TEXT,                  -- 股骨柄泊松比
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id) ON DELETE CASCADE
);

-- ============================================================
-- 表9: 性能测试结果表
-- 用途: 摩擦磨损和力学性能测试结果
-- ============================================================
CREATE TABLE IF NOT EXISTS test_results (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 外键，关联basic_info
    phase_content_change TEXT,           -- 内衬相含量变化
    cumulative_wear TEXT,                -- 累计磨损量
    wear_rate TEXT,                      -- 磨损率
    fatigue_resistance TEXT,             -- 抗疲劳性
    contact_stress TEXT,                 -- 接触应力
    von_mises_stress TEXT,               -- Von Mises应力
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id) ON DELETE CASCADE
);

-- ============================================================
-- 表10: 计算模拟参数表
-- 用途: 计算模拟的软件和参数设置
-- ============================================================
CREATE TABLE IF NOT EXISTS simulation_params (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 外键，关联basic_info
    software TEXT,                       -- 计算建模软件
    input_params TEXT,                   -- 计算建模输入参数(JSON)
    output_params TEXT,                  -- 计算建模输出参数(JSON)
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id) ON DELETE CASCADE
);

-- ============================================================
-- 表11: 计算模拟图像表
-- 用途: 计算模拟的结构图和说明
-- ============================================================
CREATE TABLE IF NOT EXISTS simulation_images (
    data_id TEXT PRIMARY KEY NOT NULL,  -- 外键，关联basic_info
    structure_diagram TEXT,              -- 计算建模模拟结构图
    diagram_description TEXT,            -- 计算建模模拟结构图说明
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id) ON DELETE CASCADE
);

-- ============================================================
-- 创建视图：完整数据视图
-- ============================================================
CREATE VIEW IF NOT EXISTS full_data_view AS
SELECT 
    bi.data_id,
    bi.application_site,
    bi.patent_or_literature,
    
    -- 内衬基本信息
    lb.material_category as liner_material_category,
    lb.material_name as liner_material_name,
    lb.thickness_mm as liner_thickness_mm,
    lb.offset_mm as liner_offset_mm,
    lb.locking_mechanism as liner_locking_mechanism,
    lb.processing_technology as liner_processing_technology,
    lb.post_treatment as liner_post_treatment,
    
    -- 球头基本信息
    hb.material_category as head_material_category,
    hb.material_name as head_material_name,
    hb.diameter_mm as head_diameter_mm,
    hb.texture as head_texture,
    hb.processing_technology as head_processing_technology,
    hb.post_treatment as head_post_treatment,
    
    -- 配合信息
    fi.radial_clearance_mm,
    
    -- 股骨柄基本信息
    sb.material_category as stem_material_category,
    sb.material_name as stem_material_name,
    sb.taper_degree,
    sb.taper_size,
    sb.neck_length_mm,
    sb.sleeve_design,
    sb.taper_clearance_degree,
    sb.neck_shaft_angle_degree,
    sb.offset_mm as stem_offset_mm,
    sb.topology_structure,
    sb.porosity_percent,
    sb.cross_section,
    sb.body_length_mm,
    sb.processing_technology as stem_processing_technology,
    sb.post_treatment as stem_post_treatment,
    
    -- 内衬物理性能
    lp.hardness_hv as liner_hardness_hv,
    lp.surface_roughness_um as liner_surface_roughness_um,
    lp.elastic_modulus_gpa as liner_elastic_modulus_gpa,
    lp.compressive_strength_mpa as liner_compressive_strength_mpa,
    lp.yield_strength_mpa as liner_yield_strength_mpa,
    lp.density_g_cm3 as liner_density_g_cm3,
    lp.poisson_ratio as liner_poisson_ratio,
    
    -- 球头物理性能
    hp.hardness_hv as head_hardness_hv,
    hp.surface_roughness_nm as head_surface_roughness_nm,
    hp.elastic_modulus_gpa as head_elastic_modulus_gpa,
    hp.compressive_strength_mpa as head_compressive_strength_mpa,
    hp.yield_strength_mpa as head_yield_strength_mpa,
    hp.density_g_cm3 as head_density_g_cm3,
    hp.poisson_ratio as head_poisson_ratio,
    
    -- 股骨柄物理性能
    sp.hardness_hv as stem_hardness_hv,
    sp.surface_roughness_um as stem_surface_roughness_um,
    sp.elastic_modulus_gpa as stem_elastic_modulus_gpa,
    sp.compressive_strength_mpa as stem_compressive_strength_mpa,
    sp.yield_strength_mpa as stem_yield_strength_mpa,
    sp.density_g_cm3 as stem_density_g_cm3,
    sp.poisson_ratio as stem_poisson_ratio,
    
    -- 测试结果
    tr.phase_content_change,
    tr.cumulative_wear,
    tr.wear_rate,
    tr.fatigue_resistance,
    tr.contact_stress,
    tr.von_mises_stress,
    
    -- 计算模拟
    sim.software as simulation_software,
    sim.input_params as simulation_input_params,
    sim.output_params as simulation_output_params,
    simg.structure_diagram,
    simg.diagram_description,
    
    bi.created_at,
    bi.updated_at
FROM basic_info bi
LEFT JOIN liner_basic lb ON bi.data_id = lb.data_id
LEFT JOIN head_basic hb ON bi.data_id = hb.data_id
LEFT JOIN fitting_info fi ON bi.data_id = fi.data_id
LEFT JOIN stem_basic sb ON bi.data_id = sb.data_id
LEFT JOIN liner_properties lp ON bi.data_id = lp.data_id
LEFT JOIN head_properties hp ON bi.data_id = hp.data_id
LEFT JOIN stem_properties sp ON bi.data_id = sp.data_id
LEFT JOIN test_results tr ON bi.data_id = tr.data_id
LEFT JOIN simulation_params sim ON bi.data_id = sim.data_id
LEFT JOIN simulation_images simg ON bi.data_id = simg.data_id;

-- ============================================================
-- 索引优化
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_liner_basic_material ON liner_basic(material_name);
CREATE INDEX IF NOT EXISTS idx_head_basic_material ON head_basic(material_name);
CREATE INDEX IF NOT EXISTS idx_stem_basic_material ON stem_basic(material_name);

-- ============================================================
-- 触发器：自动更新时间戳
-- ============================================================
CREATE TRIGGER IF NOT EXISTS update_basic_info_timestamp 
AFTER UPDATE ON basic_info
BEGIN
    UPDATE basic_info SET updated_at = CURRENT_TIMESTAMP WHERE data_id = NEW.data_id;
END;

-- ================================================================================
-- Schema 信息
-- ================================================================================
-- 版本: 2.0
-- 表数量: 11个表 + 1个视图
-- 主键: data_id (TEXT)
-- 外键关系: 所有从表通过data_id关联basic_info主表
-- 级联删除: 启用 (删除主表记录时自动删除所有关联记录)
-- ================================================================================
