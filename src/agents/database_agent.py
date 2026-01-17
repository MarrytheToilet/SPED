"""
数据库插入Agent - 将提取的数据写入数据库
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import sqlite3
import json
from datetime import datetime
from pathlib import Path

from .base_agent import BaseAgent
from settings import DB_PATH


class DatabaseInsertionAgent(BaseAgent):
    """数据库插入Agent"""
    
    def __init__(self):
        super().__init__(
            name="数据库插入Agent",
            description="将提取的结构化数据插入到SQLite数据库"
        )
        self.conn = None
        self.cursor = None
        self._connect()
    
    def _connect(self):
        """连接数据库"""
        try:
            # 确保数据库目录存在
            db_path = Path(DB_PATH)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.conn = sqlite3.connect(DB_PATH)
            self.cursor = self.conn.cursor()
            self.log_info(f"数据库连接成功: {DB_PATH}")
        except Exception as e:
            self.log_error(f"数据库连接失败: {str(e)}")
            raise
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理并插入数据 - 支持多组实验数据
        
        Args:
            input_data: 从LLM Agent提取的结构化数据
        
        Returns:
            插入结果
        """
        paper_id = input_data.get("paper_id", "unknown")
        extraction_type = input_data.get("extraction_type", "unknown")
        
        self.log_info(f"开始插入数据 - Paper: {paper_id}, Type: {extraction_type}")
        
        try:
            # 检查是否是多组实验数据
            if extraction_type == "multi_experiment" and "experiments" in input_data:
                # 多组实验，逐组插入
                total = input_data.get("total_experiments", 0)
                experiments = input_data.get("experiments", [])
                
                self.log_info(f"检测到多组实验数据，共 {total} 组")
                
                results = []
                for idx, exp_data in enumerate(experiments, 1):
                    dataid = exp_data.get("dataid")
                    exp_id = exp_data.get("exp_id", f"EXP{idx:03d}")
                    
                    self.log_info(f"插入实验组 {idx}/{total}: {exp_id}, dataid={dataid}")
                    
                    try:
                        result = self._insert_single_experiment(exp_data, dataid)
                        results.append({
                            "exp_id": exp_id,
                            "dataid": dataid,
                            "success": True,
                            "result": result
                        })
                        self.log_info(f"✓ 实验组 {exp_id} 插入成功")
                    except Exception as e:
                        self.log_error(f"✗ 实验组 {exp_id} 插入失败: {str(e)}")
                        results.append({
                            "exp_id": exp_id,
                            "dataid": dataid,
                            "success": False,
                            "error": str(e)
                        })
                
                self.conn.commit()
                success_count = sum(1 for r in results if r["success"])
                self.log_info(f"多组实验插入完成：{success_count}/{total} 成功")
                
                return {
                    "success": success_count > 0,
                    "total_experiments": total,
                    "success_count": success_count,
                    "results": results
                }
            
            else:
                # 单组实验（向后兼容）
                dataid = input_data.get("dataid")
                
                if not dataid:
                    self.log_error(f"缺少dataid: {paper_id}")
                    return {"success": False, "error": "缺少dataid"}
                
                # 对于single_experiment类型，使用简化的sheet_1插入
                if extraction_type in ["single_experiment", "basic_info", "multi_section", "experimental_data"]:
                    self.log_info(f"使用简化插入方法处理 {extraction_type}")
                    result = self._insert_single_experiment(input_data, dataid)
                else:
                    # 其他未知类型
                    self.log_warning(f"未知的提取类型: {extraction_type}，尝试通用插入")
                    result = self._insert_single_experiment(input_data, dataid)
                
                self.conn.commit()
                self.log_info(f"数据插入成功: {result}")
                return {
                    "success": True, 
                    "inserted": result, 
                    "dataid": dataid,
                    "extraction_type": extraction_type
                }
            
        except Exception as e:
            self.conn.rollback()
            self.log_error(f"数据插入失败: {str(e)}")
            import traceback
            self.log_error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def _insert_single_experiment(self, exp_data: Dict[str, Any], dataid: str) -> Dict[str, int]:
        """
        插入单个实验组的数据到sheet_1主表
        所有复杂结构以TEXT/JSON字符串格式存储
        
        Args:
            exp_data: 实验数据（已清理，只包含schema字段）
            dataid: 数据ID
            
        Returns:
            插入的记录数
        """
        inserted_counts = {}
        
        # 准备sheet_1的数据（主表）
        sheet1_data = self._prepare_sheet1_simplified(exp_data, dataid)
        
        # 插入到sheet_1
        try:
            count = self._insert_into_sheet1_simplified(sheet1_data)
            inserted_counts["sheet_1"] = count
            self.log_info(f"✓ Sheet_1 插入成功: dataid={dataid}")
        except Exception as e:
            self.log_error(f"✗ Sheet_1 插入失败: {str(e)}")
            raise
        
        return inserted_counts
    
    def _insert_multi_section_data(self, data: Dict[str, Any], dataid: str) -> Dict[str, int]:
        """插入多section处理的数据"""
        inserted_counts = {}
        
        # 插入基本信息
        if "球头信息" in data or "内衬信息" in data or "应用部位" in data:
            basic_counts = self._insert_basic_info(data, dataid)
            inserted_counts.update(basic_counts)
        
        # 插入实验设置
        if "实验设置" in data:
            exp_counts = self._insert_experimental_setup(data["实验设置"], dataid)
            inserted_counts["experimental_setup"] = exp_counts
        
        # 插入实验结果
        if "实验结果" in data:
            result_counts = self._insert_experimental_results_data(data["实验结果"], dataid)
            inserted_counts["experimental_results"] = result_counts
        
        return inserted_counts
    
    def _insert_experimental_setup(self, setup_data: Dict, dataid: str) -> int:
        """插入实验设置数据"""
        # 这里可以插入到相应的实验设置表
        # 根据你的schema调整
        count = 0
        self.log_info(f"实验设置数据待插入（需要根据schema调整）")
        return count
    
    def _insert_experimental_results_data(self, results_data: Dict, dataid: str) -> int:
        """插入实验结果数据"""
        # 这里可以插入到相应的结果表
        count = 0
        self.log_info(f"实验结果数据待插入（需要根据schema调整）")
        return count
    
    def _insert_basic_info(self, data: Dict[str, Any], dataid: str) -> Dict[str, int]:
        """插入基本信息"""
        paper_id = data.get("paper_id")
        
        inserted_counts = {}
        
        # 插入到sheet_1主表
        sheet1_data = self._prepare_sheet1_data(data, dataid)
        count = self._insert_into_sheet1(sheet1_data)
        inserted_counts["sheet_1"] = count
        
        # 插入球头基本信息到sheet_2
        if "球头信息" in data:
            ball_info = data["球头信息"]
            if isinstance(ball_info, dict) and ("材料类别" in ball_info or "材料编号" in ball_info):
                sheet2_data = self._prepare_sheet2_data(ball_info, dataid)
                count = self._insert_into_sheet2(sheet2_data)
                inserted_counts["sheet_2"] = count
            
            # 插入成分组成到sheet_3
            if "成分组成" in ball_info and isinstance(ball_info["成分组成"], list):
                for component in ball_info["成分组成"]:
                    if isinstance(component, dict):
                        sheet3_data = self._prepare_sheet3_data(component, dataid)
                        count = self._insert_into_sheet3(sheet3_data)
                        inserted_counts["sheet_3"] = inserted_counts.get("sheet_3", 0) + count
            
            # 插入物理性能到sheet_4
            if "物理性能" in ball_info and isinstance(ball_info["物理性能"], dict):
                sheet4_data = self._prepare_sheet4_data(ball_info["物理性能"], dataid)
                count = self._insert_into_sheet4(sheet4_data)
                inserted_counts["sheet_4"] = count
        
        # 插入内衬信息（类似处理）
        # ...
        
        return inserted_counts
    
    def _prepare_sheet1_simplified(self, data: Dict, dataid: str) -> Dict:
        """
        准备sheet_1数据（简化版，TEXT字段存储JSON字符串）
        严格按照 schema.json 的 sheet_1 列定义
        """
        import json
        
        # 将复杂对象转为JSON字符串（如果还不是字符串）
        def to_text(value):
            if value is None:
                return None
            if isinstance(value, str):
                return value
            return json.dumps(value, ensure_ascii=False)
        
        sheet1_data = {
            "数据id": dataid,  # 对应 schema.json 的 name: "数据id"
            "数据标识": data.get("数据标识"),
            "应用部位": data.get("应用部位"),
            "产品所属专利号或文献": data.get("产品所属专利号或文献"),
            
            # 球头信息
            "球头信息_球头基本信息": to_text(data.get("球头信息_球头基本信息")),
            "球头信息_球头_成分组成": to_text(data.get("球头信息_球头_成分组成")),
            "球头信息_球头_物理性能": to_text(data.get("球头信息_球头_物理性能")),
            "球头信息_球头_微观组织": to_text(data.get("球头信息_球头_微观组织")),
            
            # 股骨柄信息
            "股骨柄信息_股骨柄基本信息": to_text(data.get("股骨柄信息_股骨柄基本信息")),
            "股骨柄信息_股骨柄_成分组成": to_text(data.get("股骨柄信息_股骨柄_成分组成")),
            "股骨柄信息_股骨柄_物理性能": to_text(data.get("股骨柄信息_股骨柄_物理性能")),
            "股骨柄信息_股骨柄_微观组织": to_text(data.get("股骨柄信息_股骨柄_微观组织")),
            
            # 内衬信息
            "内衬信息_内衬_基本信息": to_text(data.get("内衬信息_内衬_基本信息")),
            "内衬信息_内衬_改性填料": to_text(data.get("内衬信息_内衬_改性填料")),
            "内衬信息_内衬_成分组成": to_text(data.get("内衬信息_内衬_成分组成")),
            "内衬信息_内衬_物理性能": to_text(data.get("内衬信息_内衬_物理性能")),
            "内衬信息_复合材料性能": to_text(data.get("内衬信息_复合材料性能")),
            "内衬信息_内衬_材料表征": to_text(data.get("内衬信息_内衬_材料表征")),
            
            # 体外实验 - 内衬与球头
            "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置": to_text(data.get("体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置")),
            "体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果": to_text(data.get("体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果")),
            "体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果": to_text(data.get("体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果")),
            "体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验环境_润滑液组成": to_text(data.get("体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验环境_润滑液组成")),
            "体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果": to_text(data.get("体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果")),
            "体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果": to_text(data.get("体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果")),
            "体外实验_内衬与球头摩擦腐蚀实验_球头表面成分分析": to_text(data.get("体外实验_内衬与球头摩擦腐蚀实验_球头表面成分分析")),
            
            # 体外实验 - 球头与锥颈
            "体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置": to_text(data.get("体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置")),
            "体外实验_球头与锥颈界面微动腐蚀实验_锥颈与球头_实验环境_润滑液组成": to_text(data.get("体外实验_球头与锥颈界面微动腐蚀实验_锥颈与球头_实验环境_润滑液组成")),
            "体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果": to_text(data.get("体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果"))
        }
        
        return sheet1_data
    
    def _insert_into_sheet1_simplified(self, data: Dict) -> int:
        """插入到sheet_1（简化版）"""
        # 只插入非None的字段
        columns = [k for k, v in data.items() if v is not None]
        values = [data[k] for k in columns]
        
        if not columns:
            self.log_warning("没有数据可插入")
            return 0
        
        placeholders = ','.join(['?'] * len(columns))
        
        # 使用 REPLACE INTO (SQLite的 UPSERT)
        sql = f"""
        INSERT OR REPLACE INTO sheet_1 ({','.join([f'"{c}"' for c in columns])})
        VALUES ({placeholders})
        """
        
        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
            self.log_info(f"SQL执行成功，影响行数: {self.cursor.rowcount}")
            return 1
        except Exception as e:
            self.log_error(f"SQL执行失败: {str(e)}")
            self.log_error(f"SQL: {sql}")
            self.log_error(f"Values: {values[:3]}...")  # 只显示前几个值
            raise
    
    def _prepare_sheet2_data(self, ball_info: Dict, dataid: str) -> Dict:
        """准备sheet_2数据（球头基本信息）"""
        return {
            "dataid": dataid,
            "球头信息_球头基本信息_材料编号": ball_info.get("材料编号"),
            "球头信息_球头基本信息_材料类别": ball_info.get("材料类别"),
            "球头信息_球头基本信息_加工工艺": ball_info.get("加工工艺"),
            "球头信息_球头基本信息_表面处理": ball_info.get("表面处理"),
        }
    
    def _prepare_sheet3_data(self, component: Dict, dataid: str) -> Dict:
        """准备sheet_3数据（成分组成）"""
        return {
            "dataid": dataid,
            "球头信息_球头_成分组成_成分": component.get("成分"),
            "球头信息_球头_成分组成_成分_2": self._parse_float(component.get("含量")),
        }
    
    def _prepare_sheet4_data(self, properties: Dict, dataid: str) -> Dict:
        """准备sheet_4数据（物理性能）"""
        return {
            "dataid": dataid,
            "球头信息_球头_物理性能_硬度_hv": properties.get("硬度"),
            "球头信息_球头_物理性能_表面粗糙度_μm": properties.get("表面粗糙度"),
            "球头信息_球头_物理性能_弹性模量_gpa": properties.get("弹性模量"),
            "球头信息_球头_物理性能_密度_kg_m³": properties.get("密度"),
        }
    
    def _insert_into_sheet1(self, data: Dict) -> int:
        """插入到sheet_1"""
        columns = [k for k, v in data.items() if v is not None]
        values = [data[k] for k in columns]
        placeholders = ','.join(['?'] * len(columns))
        
        sql = f"""
        INSERT OR REPLACE INTO sheet_1 ({','.join([f'"{c}"' for c in columns])})
        VALUES ({placeholders})
        """
        
        self.cursor.execute(sql, values)
        self.conn.commit()
        return 1
    
    def _insert_into_sheet2(self, data: Dict) -> int:
        """插入到sheet_2"""
        columns = [k for k, v in data.items() if v is not None]
        values = [data[k] for k in columns]
        placeholders = ','.join(['?'] * len(columns))
        
        sql = f"""
        INSERT OR REPLACE INTO sheet_2 ({','.join([f'"{c}"' for c in columns])})
        VALUES ({placeholders})
        """
        
        self.cursor.execute(sql, values)
        self.conn.commit()
        return 1
    
    def _insert_into_sheet3(self, data: Dict) -> int:
        """插入到sheet_3"""
        columns = [k for k, v in data.items() if v is not None]
        values = [data[k] for k in columns]
        placeholders = ','.join(['?'] * len(columns))
        
        sql = f"""
        INSERT INTO sheet_3 ({','.join([f'"{c}"' for c in columns])})
        VALUES ({placeholders})
        """
        
        self.cursor.execute(sql, values)
        self.conn.commit()
        return 1
    
    def _insert_into_sheet4(self, data: Dict) -> int:
        """插入到sheet_4"""
        columns = [k for k, v in data.items() if v is not None]
        values = [data[k] for k in columns]
        placeholders = ','.join(['?'] * len(columns))
        
        sql = f"""
        INSERT OR REPLACE INTO sheet_4 ({','.join([f'"{c}"' for c in columns])})
        VALUES ({placeholders})
        """
        
        self.cursor.execute(sql, values)
        self.conn.commit()
        return 1
    
    def _insert_experimental_data(self, data: Dict[str, Any], dataid: str) -> Dict[str, int]:
        """插入实验数据"""
        inserted_counts = {}
        
        # 插入摩擦腐蚀实验数据
        if "摩擦腐蚀实验" in data:
            exp_data = data["摩擦腐蚀实验"]
            # 插入到相应的表...
            pass
        
        return inserted_counts
    
    def _insert_generic_data(self, data: Dict[str, Any], dataid: str) -> Dict[str, int]:
        """插入通用数据"""
        return {"generic": 0}
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """解析浮点数"""
        if value is None:
            return None
        try:
            # 移除单位和其他文本
            if isinstance(value, str):
                import re
                numbers = re.findall(r'[-+]?\d*\.?\d+', value)
                if numbers:
                    return float(numbers[0])
            return float(value)
        except:
            return None
    
    def close(self):
        """关闭数据库连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            self.log_info("数据库连接已关闭")
        except Exception:
            pass  # 忽略关闭时的错误
    
    def __del__(self):
        """析构函数"""
        try:
            self.close()
        except Exception:
            pass  # 忽略析构时的错误
