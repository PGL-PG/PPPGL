"""
AI可视化建议转SQL代码生成器
将大模型的可视化建议转化为精准的SQL查询，提升分析质量
"""

import pandas as pd
import sqlite3
import tempfile
import os
from typing import Dict, List, Any, Optional
import json

class SQLBasedAnalysisEngine:
    """基于SQL的精准分析引擎"""
    
    def __init__(self):
        self.temp_db_path = None
        self.connection = None
        
    def create_temp_database(self, df: pd.DataFrame, table_name: str = "data_table") -> str:
        """将DataFrame转换为临时SQLite数据库"""
        # 创建临时数据库文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = temp_file.name
        temp_file.close()
        
        # 连接数据库并创建表
        self.connection = sqlite3.connect(self.temp_db_path)
        df.to_sql(table_name, self.connection, index=False, if_exists='replace')
        
        return self.temp_db_path
    
    def generate_sql_from_ai_suggestion(self, suggestion: Dict, table_name: str = "data_table") -> str:
        """根据AI建议生成精准的SQL查询 - 智能识别最合理的展示方式"""
        chart_type = suggestion.get('type', 'bar')
        title = suggestion.get('title', '')
        dimension_field = suggestion.get('dimension_field', '')
        measure_field = suggestion.get('measure_field', '')
        
        # 🎯 智能分析标题和字段，优化展示方式
        title_lower = title.lower()
        
        if chart_type == 'bar' and dimension_field and measure_field:
            if '排行' in title or '对比' in title or 'top' in title_lower:
                # 排行榜类型 - 包含排名和市场份额
                sql = f"""
                SELECT 
                    [{dimension_field}] as category,
                    SUM([{measure_field}]) as value,
                    RANK() OVER (ORDER BY SUM([{measure_field}]) DESC) as ranking,
                    ROUND(SUM([{measure_field}]) * 100.0 / (SELECT SUM([{measure_field}]) FROM {table_name}), 2) as market_share,
                    COUNT(*) as item_count
                FROM {table_name} 
                WHERE [{dimension_field}] IS NOT NULL AND [{measure_field}] IS NOT NULL
                GROUP BY [{dimension_field}]
                ORDER BY value DESC
                LIMIT 10
                """
            elif '平均' in title or 'avg' in title_lower or '均价' in title:
                # 平均值分析
                sql = f"""
                SELECT 
                    [{dimension_field}] as category,
                    ROUND(AVG([{measure_field}]), 2) as value,
                    COUNT(*) as sample_count,
                    MIN([{measure_field}]) as min_value,
                    MAX([{measure_field}]) as max_value
                FROM {table_name} 
                WHERE [{dimension_field}] IS NOT NULL AND [{measure_field}] IS NOT NULL
                GROUP BY [{dimension_field}]
                ORDER BY value DESC
                LIMIT 10
                """
            else:
                # 默认求和分析
                sql = f"""
                SELECT 
                    [{dimension_field}] as category,
                    SUM([{measure_field}]) as value,
                    COUNT(*) as record_count
                FROM {table_name} 
                WHERE [{dimension_field}] IS NOT NULL AND [{measure_field}] IS NOT NULL
                GROUP BY [{dimension_field}]
                ORDER BY value DESC
                LIMIT 12
                """
                
        elif chart_type == 'pie' and dimension_field:
            if measure_field:
                # 基于度量字段的占比分析 - 更精确的百分比计算
                sql = f"""
                SELECT 
                    [{dimension_field}] as category,
                    SUM([{measure_field}]) as value,
                    ROUND(SUM([{measure_field}]) * 100.0 / (SELECT SUM([{measure_field}]) FROM {table_name} WHERE [{measure_field}] IS NOT NULL), 1) as percentage,
                    COUNT(*) as item_count
                FROM {table_name} 
                WHERE [{dimension_field}] IS NOT NULL AND [{measure_field}] IS NOT NULL
                GROUP BY [{dimension_field}]
                HAVING SUM([{measure_field}]) > 0
                ORDER BY value DESC
                LIMIT 8
                """
            else:
                # 基于计数的分布分析
                sql = f"""
                SELECT 
                    [{dimension_field}] as category,
                    COUNT(*) as value,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {table_name} WHERE [{dimension_field}] IS NOT NULL), 1) as percentage
                FROM {table_name} 
                WHERE [{dimension_field}] IS NOT NULL
                GROUP BY [{dimension_field}]
                ORDER BY value DESC
                LIMIT 8
                """
                
        elif chart_type == 'line' and dimension_field and measure_field:
            if '趋势' in title or '时间' in title or 'trend' in title_lower:
                # 时间趋势分析 - 包含环比增长
                sql = f"""
                SELECT 
                    [{dimension_field}] as category,
                    SUM([{measure_field}]) as value,
                    LAG(SUM([{measure_field}])) OVER (ORDER BY [{dimension_field}]) as prev_value,
                    ROUND(
                        (SUM([{measure_field}]) - LAG(SUM([{measure_field}])) OVER (ORDER BY [{dimension_field}])) * 100.0 / 
                        NULLIF(LAG(SUM([{measure_field}])) OVER (ORDER BY [{dimension_field}]), 0), 2
                    ) as growth_rate
                FROM {table_name} 
                WHERE [{dimension_field}] IS NOT NULL AND [{measure_field}] IS NOT NULL
                GROUP BY [{dimension_field}]
                ORDER BY [{dimension_field}]
                LIMIT 15
                """
            else:
                # 序列分析
                sql = f"""
                SELECT 
                    [{dimension_field}] as category,
                    AVG([{measure_field}]) as value,
                    COUNT(*) as data_points
                FROM {table_name} 
                WHERE [{dimension_field}] IS NOT NULL AND [{measure_field}] IS NOT NULL
                GROUP BY [{dimension_field}]
                ORDER BY [{dimension_field}]
                LIMIT 15
                """
                
        elif chart_type == 'scatter' and dimension_field and measure_field:
            # 散点图 - 智能采样和相关性分析
            sql = f"""
            SELECT 
                [{dimension_field}] as x_value,
                [{measure_field}] as y_value,
                ROW_NUMBER() OVER (ORDER BY RANDOM()) as point_id
            FROM {table_name} 
            WHERE [{dimension_field}] IS NOT NULL 
                AND [{measure_field}] IS NOT NULL
                AND [{dimension_field}] > 0
                AND [{measure_field}] > 0
            ORDER BY RANDOM()
            LIMIT 100
            """
        else:
            # 兜底查询 - 基础数据展示
            if dimension_field:
                sql = f"""
                SELECT 
                    [{dimension_field}] as category,
                    COUNT(*) as value
                FROM {table_name} 
                WHERE [{dimension_field}] IS NOT NULL
                GROUP BY [{dimension_field}]
                ORDER BY value DESC
                LIMIT 10
                """
            else:
                sql = f"SELECT * FROM {table_name} LIMIT 10"
        
        return sql
    
    def _generate_bar_chart_sql(self, dimension_field: str, measure_field: str, table_name: str, title: str) -> str:
        """生成柱状图的SQL查询"""
        if '排行' in title or '对比' in title:
            # 排行榜类型 - 按度量字段降序排列
            sql = f"""
            SELECT 
                [{dimension_field}] as category,
                SUM([{measure_field}]) as value,
                ROUND(SUM([{measure_field}]) * 100.0 / (SELECT SUM([{measure_field}]) FROM {table_name}), 2) as percentage
            FROM {table_name} 
            WHERE [{dimension_field}] IS NOT NULL AND [{measure_field}] IS NOT NULL
            GROUP BY [{dimension_field}]
            ORDER BY value DESC
            LIMIT 10
            """
        elif '平均' in title:
            # 平均值对比
            sql = f"""
            SELECT 
                [{dimension_field}] as category,
                ROUND(AVG([{measure_field}]), 2) as value,
                COUNT(*) as count
            FROM {table_name} 
            WHERE [{dimension_field}] IS NOT NULL AND [{measure_field}] IS NOT NULL
            GROUP BY [{dimension_field}]
            ORDER BY value DESC
            LIMIT 10
            """
        else:
            # 默认求和对比
            sql = f"""
            SELECT 
                [{dimension_field}] as category,
                SUM([{measure_field}]) as value
            FROM {table_name} 
            WHERE [{dimension_field}] IS NOT NULL AND [{measure_field}] IS NOT NULL
            GROUP BY [{dimension_field}]
            ORDER BY value DESC
            LIMIT 15
            """
        return sql
    
    def _generate_pie_chart_sql(self, dimension_field: str, measure_field: str, table_name: str, title: str) -> str:
        """生成饼图的SQL查询"""
        if measure_field:
            # 基于度量字段的占比分析
            sql = f"""
            SELECT 
                [{dimension_field}] as category,
                SUM([{measure_field}]) as value,
                ROUND(SUM([{measure_field}]) * 100.0 / (SELECT SUM([{measure_field}]) FROM {table_name}), 1) as percentage
            FROM {table_name} 
            WHERE [{dimension_field}] IS NOT NULL AND [{measure_field}] IS NOT NULL
            GROUP BY [{dimension_field}]
            ORDER BY value DESC
            LIMIT 8
            """
        else:
            # 基于计数的分布分析
            sql = f"""
            SELECT 
                [{dimension_field}] as category,
                COUNT(*) as value,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {table_name}), 1) as percentage
            FROM {table_name} 
            WHERE [{dimension_field}] IS NOT NULL
            GROUP BY [{dimension_field}]
            ORDER BY value DESC
            LIMIT 8
            """
        return sql
    
    def _generate_line_chart_sql(self, dimension_field: str, measure_field: str, table_name: str, title: str) -> str:
        """生成折线图的SQL查询"""
        if '趋势' in title or '时间' in title:
            # 时间趋势分析
            sql = f"""
            SELECT 
                "{dimension_field}" as time_period,
                SUM("{measure_field}") as value,
                ROW_NUMBER() OVER (ORDER BY "{dimension_field}") as sequence
            FROM {table_name} 
            WHERE "{dimension_field}" IS NOT NULL AND "{measure_field}" IS NOT NULL
            GROUP BY "{dimension_field}"
            ORDER BY "{dimension_field}"
            LIMIT 20
            """
        else:
            # 序列分析
            sql = f"""
            SELECT 
                "{dimension_field}" as category,
                AVG("{measure_field}") as value
            FROM {table_name} 
            WHERE "{dimension_field}" IS NOT NULL AND "{measure_field}" IS NOT NULL
            GROUP BY "{dimension_field}"
            ORDER BY "{dimension_field}"
            LIMIT 15
            """
        return sql
    
    def _generate_scatter_chart_sql(self, dimension_field: str, measure_field: str, table_name: str, title: str) -> str:
        """生成散点图的SQL查询"""
        sql = f"""
        SELECT 
            [{dimension_field}] as x_value,
            [{measure_field}] as y_value,
            ROW_NUMBER() OVER (ORDER BY RANDOM()) as point_id
        FROM {table_name} 
        WHERE [{dimension_field}] IS NOT NULL 
            AND [{measure_field}] IS NOT NULL
            AND [{dimension_field}] != 0
            AND [{measure_field}] != 0
        ORDER BY RANDOM()
        LIMIT 100
        """
        return sql
    
    def _generate_default_sql(self, dimension_field: str, measure_field: str, table_name: str) -> str:
        """生成默认SQL查询"""
        if dimension_field and measure_field:
            return f"""
            SELECT 
                "{dimension_field}" as category,
                SUM("{measure_field}") as value
            FROM {table_name} 
            WHERE "{dimension_field}" IS NOT NULL AND "{measure_field}" IS NOT NULL
            GROUP BY "{dimension_field}"
            ORDER BY value DESC
            LIMIT 10
            """
        else:
            return f"SELECT * FROM {table_name} LIMIT 10"
    
    def execute_sql_analysis(self, sql_query: str) -> List[Dict]:
        """执行SQL查询并返回结果"""
        if not self.connection:
            raise Exception("数据库连接未建立")
        
        try:
            # 执行查询
            cursor = self.connection.cursor()
            cursor.execute(sql_query)
            
            # 获取列名
            column_names = [description[0] for description in cursor.description]
            
            # 获取数据
            rows = cursor.fetchall()
            
            # 转换为字典列表
            result = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[column_names[i]] = value
                result.append(row_dict)
            
            return result
            
        except Exception as e:
            return []
    
    def generate_enhanced_chart_data(self, suggestion: Dict, df: pd.DataFrame) -> Dict:
        """生成增强的图表数据"""
        try:
            # 验证和修正字段名
            dimension_field = suggestion.get('dimension_field')
            measure_field = suggestion.get('measure_field')
            
            # 智能匹配字段名
            if dimension_field:
                matched_dim = self._find_best_matching_column(df, dimension_field)
                if matched_dim:
                    dimension_field = matched_dim
                    suggestion['dimension_field'] = matched_dim
                else:
                    return None
                    
            if measure_field:
                matched_measure = self._find_best_matching_column(df, measure_field)
                if matched_measure:
                    measure_field = matched_measure
                    suggestion['measure_field'] = matched_measure
                else:
                    return None
            
            # 创建临时数据库
            self.create_temp_database(df)
            
            # 生成SQL查询
            sql_query = self.generate_sql_from_ai_suggestion(suggestion)
            
            # 执行查询
            query_result = self.execute_sql_analysis(sql_query)
            
            if not query_result:
                return None
            
            # 转换为图表数据格式
            chart_data = self._convert_to_chart_format(query_result, suggestion)
            
            # 添加SQL信息到结果中
            chart_data['sql_query'] = sql_query
            chart_data['sql_powered'] = True
            
            return chart_data
            
        except Exception as e:
            return None
        finally:
            self._cleanup()
    
    def _convert_to_chart_format(self, query_result: List[Dict], suggestion: Dict) -> Dict:
        """将SQL查询结果转换为图表格式 - 智能处理复杂查询结果"""
        chart_type = suggestion.get('type', 'bar')
        title = suggestion.get('title', '')
        

        if chart_type in ['bar', 'line']:
            # 柱状图和折线图格式 - 智能处理多种数据结构
            data = []
            enhanced_subtitle = suggestion.get('expected_insight', '')
            
            for row in query_result:
                if 'category' in row and 'value' in row:
                    item = {
                        'name': str(row['category']),
                        'value': float(row['value']) if row['value'] is not None else 0
                    }
                    
                    # 🎯 智能添加额外信息到tooltip
                    extra_info = []
                    if 'market_share' in row and row['market_share'] is not None:
                        extra_info.append(f"市场份额: {row['market_share']}%")
                    if 'ranking' in row and row['ranking'] is not None:
                        extra_info.append(f"排名: 第{row['ranking']}位")
                    if 'item_count' in row and row['item_count'] is not None:
                        extra_info.append(f"项目数: {row['item_count']}")
                    if 'growth_rate' in row and row['growth_rate'] is not None:
                        extra_info.append(f"增长率: {row['growth_rate']}%")
                    
                    if extra_info:
                        item['extra_info'] = ' | '.join(extra_info)
                    
                    data.append(item)
            
            # 🎯 智能生成副标题
            if data and not enhanced_subtitle:
                if '排行' in title:
                    top_item = data[0] if data else None
                    if top_item:
                        enhanced_subtitle = f"{top_item['name']} 排名第一，共分析 {len(data)} 个类别"
                elif '平均' in title:
                    enhanced_subtitle = f"平均值分析，共 {len(data)} 个维度"
                else:
                    total_value = sum(item['value'] for item in data)
                    enhanced_subtitle = f"总计 {total_value:,.0f}，共 {len(data)} 个类别"
            
            return {
                'type': chart_type,
                'title': title,
                'data': data,
                'subtitle': enhanced_subtitle,
                'ai_driven': True,
                'sql_powered': True
            }
            
        elif chart_type == 'pie':
            # 饼图格式 - 智能处理百分比数据
            data = []
            enhanced_subtitle = suggestion.get('expected_insight', '')
            
            for row in query_result:
                if 'category' in row:
                    # 优先使用percentage，其次使用value计算百分比
                    if 'percentage' in row and row['percentage'] is not None:
                        percentage = float(row['percentage'])
                    elif 'value' in row and row['value'] is not None:
                        total = sum(r.get('value', 0) for r in query_result if r.get('value') is not None)
                        percentage = (float(row['value']) / total * 100) if total > 0 else 0
                    else:
                        percentage = 0
                    
                    data.append({
                        'name': str(row['category']),
                        'value': round(percentage, 1)
                    })
            
            # 🎯 智能生成副标题
            if data and not enhanced_subtitle:
                top_item = data[0] if data else None
                if top_item:
                    enhanced_subtitle = f"{top_item['name']} 占比最高 ({top_item['value']}%)，共 {len(data)} 个类别"
            
            return {
                'type': chart_type,
                'title': title,
                'data': data,
                'subtitle': enhanced_subtitle,
                'ai_driven': True,
                'sql_powered': True
            }
            
        elif chart_type == 'scatter':
            # 散点图格式 - 智能处理相关性数据
            data = []
            for row in query_result:
                if 'x_value' in row and 'y_value' in row:
                    x_val = float(row['x_value']) if row['x_value'] is not None else 0
                    y_val = float(row['y_value']) if row['y_value'] is not None else 0
                    if x_val > 0 and y_val > 0:  # 过滤无效数据点
                        data.append([x_val, y_val])
            
            # 🎯 智能计算相关性
            enhanced_subtitle = suggestion.get('expected_insight', '')
            if data and len(data) > 2 and not enhanced_subtitle:
                # 简单的相关性计算
                x_values = [point[0] for point in data]
                y_values = [point[1] for point in data]
                
                import statistics
                if len(set(x_values)) > 1 and len(set(y_values)) > 1:
                    # 计算皮尔逊相关系数的简化版本
                    x_mean = statistics.mean(x_values)
                    y_mean = statistics.mean(y_values)
                    
                    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
                    x_sq_sum = sum((x - x_mean) ** 2 for x in x_values)
                    y_sq_sum = sum((y - y_mean) ** 2 for y in y_values)
                    
                    if x_sq_sum > 0 and y_sq_sum > 0:
                        correlation = numerator / (x_sq_sum * y_sq_sum) ** 0.5
                        enhanced_subtitle = f"相关系数: {correlation:.3f}，数据点: {len(data)} 个"
            
            return {
                'type': chart_type,
                'title': title,
                'data': data,
                'subtitle': enhanced_subtitle,
                'ai_driven': True,
                'sql_powered': True,
                'xLabel': suggestion.get('dimension_field', '数值1'),
                'yLabel': suggestion.get('measure_field', '数值2')
            }
        
        # 兜底处理
        return {
            'type': chart_type,
            'title': title,
            'data': [],
            'subtitle': f'暂不支持 {chart_type} 类型的数据转换',
            'ai_driven': True,
            'sql_powered': False
        }
    
    def _cleanup(self):
        """清理临时资源"""
        if self.connection:
            self.connection.close()
            self.connection = None
        
        if self.temp_db_path and os.path.exists(self.temp_db_path):
            try:
                os.unlink(self.temp_db_path)
            except:
                pass
            self.temp_db_path = None
    
    def _find_best_matching_column(self, df: pd.DataFrame, target_field: str) -> str:
        """查找最匹配的列名"""
        if not target_field:
            return None
            
        # 直接匹配
        if target_field in df.columns:
            return target_field
        
        # 模糊匹配（忽略大小写和空格）
        target_lower = target_field.lower().replace(' ', '').replace('_', '')
        
        for col in df.columns:
            col_lower = str(col).lower().replace(' ', '').replace('_', '')
            if target_lower == col_lower:
                return col
        
        # 部分匹配
        for col in df.columns:
            col_lower = str(col).lower()
            if target_lower in col_lower or col_lower in target_lower:
                return col
        return None

