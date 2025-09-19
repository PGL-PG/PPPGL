"""
增强版数据分析API
集成场景匹配和智能提示词生成系统
"""

import pandas as pd
import numpy as np
import json
import os
import requests

# 导入智能分析系统
from intelligent_scenario_matcher import ScenarioMatcher
from scenario_prompt_engine import ScenarioPromptEngine

# 定义数据转换函数
def safe_convert_value(value):
    """安全地转换值为可JSON序列化的类型"""
    if pd.isna(value) or value is None:
        return None
    elif isinstance(value, (bool, np.bool_)):
        return bool(value)
    elif isinstance(value, (int, float)) or str(type(value)).startswith("<class 'numpy.int") or str(type(value)).startswith("<class 'numpy.float"):
        if 'int' in str(type(value)):
            return int(value)
        else:
            return float(value)
    elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return str(value)
    else:
        return value

# 从主文件中导入detect_data_type
def detect_data_type(series):
    """检测数据类型"""
    if series.empty or series.isna().all():
        return 'empty'
    
    # 去除空值
    non_null_series = series.dropna()
    
    # 检测数值类型
    if pd.api.types.is_numeric_dtype(series):
        return 'numeric'
    
    # 检测日期时间类型
    if pd.api.types.is_datetime64_any_dtype(series):
        return 'datetime'
    
    # 尝试转换为日期时间
    try:
        pd.to_datetime(non_null_series.head(10))
        return 'datetime'
    except:
        pass
    
    # 检测分类数据
    if len(non_null_series) > 0:
        unique_ratio = len(non_null_series.unique()) / len(non_null_series)
        unique_count = len(non_null_series.unique())
        
        # 如果唯一值比例低且类别数不多，认为是分类数据
        if unique_ratio < 0.5 and unique_count < 20:
            return 'categorical'
    
    return 'text'

class EnhancedAnalysisAPI:
    """增强版分析API"""
    
    def __init__(self):
        self.scenario_matcher = ScenarioMatcher()
        self.prompt_engine = ScenarioPromptEngine()
        self.api_key = "AIzaSyBQkCLkovABnjZeOVRV-FoxkFPkayvNXVQ"
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
    def enhanced_analyze(self, df: pd.DataFrame, custom_requirements: str = "") -> dict:
        """增强版数据分析流程"""
        
        try:
            print(f"开始分析数据: {len(df)}行 x {len(df.columns)}列")
            
            # 1. 智能场景匹配
            best_scenario, confidence, match_details = self.scenario_matcher.match_best_scenario(df)
            print(f"场景匹配结果: {best_scenario} (置信度: {confidence:.3f})")
            
            # 2. 生成场景化提示词
            enhanced_prompt = self.prompt_engine.generate_scenario_prompt(
                scenario=best_scenario,
                df=df,
                match_details=match_details,
                custom_requirements=custom_requirements
            )
            
            # 3. 添加可视化提示词补充
            viz_supplement = self.prompt_engine.create_visualization_prompt_supplement(df, best_scenario)
            final_prompt = enhanced_prompt + viz_supplement
            
            print(f"生成提示词长度: {len(final_prompt)} 字符")
            
            # 4. 调用Gemini进行智能分析
            ai_insights = ""
            ai_called = False
            
            if self.api_key and self.api_key != "YOUR_API_KEY_HERE":
                headers = {
                    "Content-Type": "application/json",
                    "X-goog-api-key": self.api_key
                }
                
                body = {"contents": [{"role": "user", "parts": [{"text": final_prompt}]}]}
                
                try:
                    response = requests.post(self.api_url, headers=headers, json=body, timeout=30)
                    response.raise_for_status()
                    result = response.json()
                    ai_insights = result["candidates"][0]["content"]["parts"][0]["text"]
                    ai_called = True
                    print(f"Gemini分析成功，返回内容长度: {len(ai_insights)} 字符")
                except Exception as e:
                    print(f"Gemini API调用失败: {e}")
                    ai_insights = f"AI分析服务暂时不可用: {str(e)}"
            else:
                ai_insights = "API密钥未配置，使用本地分析"
            
            # 5. 生成基础统计概览
            basic_stats_overview = self._generate_basic_stats_overview(df, best_scenario)
            
            # 6. 生成数据表格
            data_tables = self._generate_data_tables(df, basic_stats_overview)
            
            # 7. 智能解析Gemini的可视化建议并生成图表
            charts = self._generate_charts_from_ai_suggestions(df, ai_insights, best_scenario)
            
            # 8. 过滤AI洞察中的图表标题
            filtered_ai_insights = self._filter_visualization_suggestions(ai_insights)
            
            # 9. 构建返回结果
            result = {
                "status": "success",
                "analysis_type": f"scenario_based_analysis_{best_scenario}",
                "scenario_info": {
                    "matched_scenario": best_scenario,
                    "confidence": confidence,
                    "all_scores": match_details.get("all_scores", {})
                },
                "basic_stats_overview": basic_stats_overview,
                "data_tables": data_tables,
                "data_overview": {
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "missing_data": self._get_missing_data_info(df)
                },
                "ai_insights": filtered_ai_insights,
                "charts": charts,
                "recommendations": self._generate_recommendations(best_scenario, confidence),
                "ai_called": ai_called
            }
            
            return self._sanitize_for_json(result)
            
        except Exception as e:
            print(f"分析过程出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "ai_called": False
            }
    
    def _generate_basic_stats_overview(self, df: pd.DataFrame, scenario: str) -> dict:
        """生成基础统计概览"""
        overview = {
            "data_scale": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "business_scenario": scenario
            },
            "field_summary": {},
            "data_quality": {
                "missing_data_fields": [],
                "duplicate_rows": 0,
                "completeness_score": 100.0
            }
        }
        
        # 字段统计
        for col in df.columns:
            col_data = pd.Series(df[col])
            field_type = detect_data_type(col_data)
            
            stats = {
                "type": field_type,
                "non_null_count": int(col_data.count()),
                "null_count": int(col_data.isnull().sum()),
                "null_percentage": round(col_data.isnull().sum() / len(df) * 100, 2) if len(df) > 0 else 0
            }
            
            if field_type == 'numeric' and col_data.count() > 0:
                clean_data = col_data.dropna()
                stats.update({
                    "mean": round(float(clean_data.mean()), 2),
                    "median": round(float(clean_data.median()), 2),
                    "min": float(clean_data.min()),
                    "max": float(clean_data.max()),
                    "std": round(float(clean_data.std()), 2) if len(clean_data) > 1 else 0
                })
            elif field_type in ['categorical', 'text'] and col_data.count() > 0:
                clean_data = col_data.dropna()
                value_counts = clean_data.value_counts()
                stats.update({
                    "unique_count": len(clean_data.unique()),
                    "most_frequent": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                    "most_frequent_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0
                })
            
            overview["field_summary"][col] = stats
            
            # 数据质量检查
            if stats["null_count"] > 0:
                overview["data_quality"]["missing_data_fields"].append(col)
        
        # 重复行检查
        overview["data_quality"]["duplicate_rows"] = len(df) - len(df.drop_duplicates())
        
        # 完整性评分
        total_cells = len(df) * len(df.columns)
        missing_cells = sum(overview["field_summary"][col]["null_count"] for col in df.columns)
        overview["data_quality"]["completeness_score"] = round((1 - missing_cells / total_cells) * 100, 2) if total_cells > 0 else 100
        
        return overview
    
    def _generate_data_tables(self, df: pd.DataFrame, basic_stats_overview: dict) -> list:
        """生成数据表格"""
        data_tables = []
        
        # 字段统计表
        field_stats_table = []
        for field, stats in basic_stats_overview['field_summary'].items():
            row = {
                "字段名": field,
                "数据类型": stats['type'],
                "有效记录数": stats['non_null_count'],
                "缺失率": f"{stats['null_percentage']}%"
            }
            
            if stats['type'] == 'numeric':
                row.update({
                    "平均值": stats.get('mean'),
                    "中位数": stats.get('median'),
                    "最小值": stats.get('min'),
                    "最大值": stats.get('max')
                })
            elif stats['type'] in ['categorical', 'text']:
                row.update({
                    "唯一值数量": stats.get('unique_count'),
                    "最常见值": stats.get('most_frequent'),
                    "最常见值出现次数": stats.get('most_frequent_count')
                })
            
            field_stats_table.append(row)
        
        data_tables.append({
            "title": "字段统计分析表",
            "type": "stats_table",
            "data": field_stats_table,
            "description": f"共分析{len(field_stats_table)}个字段的基础统计信息"
        })
        
        return data_tables
    
    def _generate_charts_from_ai_suggestions(self, df: pd.DataFrame, ai_insights: str, scenario: str) -> list:
        """基于Gemini的智能建议生成图表"""
        charts = []
        
        try:

            # 解析AI返回的可视化建议
            viz_suggestions = self._parse_visualization_suggestions(ai_insights)
            
            if not viz_suggestions:
                # 如果AI没有返回结构化的建议，使用默认逻辑
                print("未发现AI可视化建议，使用默认逻辑")
                return self._generate_charts(df, scenario)
            
            print(f"解析到{len(viz_suggestions)}个可视化建议")
            
            # 根据AI建议生成图表
            for i, suggestion in enumerate(viz_suggestions[:4]):  # 最多4个图表
                chart = self._create_chart_from_suggestion(df, suggestion, i)
                if chart:
                    charts.append(chart)
            
            # 如果没有成功生成任何图表，使用默认逻辑
            if not charts:
                print("没有成功生成AI建议图表，使用默认逻辑")
                return self._generate_charts(df, scenario)
                
        except Exception as e:
            print(f"解析AI可视化建议失败: {e}")
            # 如果解析失败，使用默认逻辑
            return self._generate_charts(df, scenario)
        
        return charts
    
    def _parse_visualization_suggestions(self, ai_insights: str) -> list:
        """解析AI返回的可视化建议"""
        suggestions = []
        
        if not ai_insights or not isinstance(ai_insights, str):
            return suggestions
        
        try:
            # 查找可视化建议章节
            viz_section_start = ai_insights.find("📊 Excel可视化建议")
            if viz_section_start == -1:
                viz_section_start = ai_insights.find("可视化建议")
            if viz_section_start == -1:
                viz_section_start = ai_insights.find("Excel多维度可视化")
            if viz_section_start == -1:
                viz_section_start = ai_insights.find("多维度可视化")
            
            if viz_section_start == -1:
                return suggestions
            
            viz_section = ai_insights[viz_section_start:]
            lines = viz_section.split('\n')
            
            current_chart = None
            
            for line in lines:
                line = line.strip()
                
                # 检测图表标题 - 支持多种格式
                if line.startswith('###'):
                    if current_chart:
                        suggestions.append(current_chart)
                    
                    # 解析图表信息 - 支持 "### 图表1：[类型] - [标题]" 格式
                    title_part = line.replace('###', '').strip()
                    
                    # 处理 "图表1：柱状图 - 品牌销量排行" 格式
                    if '：' in title_part and '-' in title_part:
                        parts = title_part.split('：', 1)
                        if len(parts) >= 2:
                            chart_num = parts[0].strip()  # "图表1"
                            type_title = parts[1].strip()  # "柱状图 - 品牌销量排行"
                            
                            if '-' in type_title:
                                type_part, title_part = type_title.split('-', 1)
                                chart_info = type_part.strip()  # "柱状图"
                                title = title_part.strip()     # "品牌销量排行"
                            else:
                                chart_info = type_title
                                title = f"图表{len(suggestions) + 1}"
                    
                    # 处理 "### 柱状图：品牌销量排行" 格式（原格式）
                    elif ('：' in title_part or ':' in title_part):
                        separator = '：' if '：' in title_part else ':'
                        chart_type_title = title_part.split(separator, 1)
                        if len(chart_type_title) >= 2:
                            chart_info = chart_type_title[0].strip()
                            title = chart_type_title[1].strip()
                        else:
                            chart_info = title_part
                            title = f"图表{len(suggestions) + 1}"
                    else:
                        # 如果没有分隔符，尝试从整行提取
                        chart_info = title_part
                        title = f"图表{len(suggestions) + 1}"
                    
                    # 提取图表类型
                    chart_type = self._extract_chart_type(chart_info)
                    
                    current_chart = {
                        'type': chart_type,
                        'title': title,
                        'dimension_field': None,
                        'measure_field': None,
                        'reason': '',
                        'expected_insight': ''
                    }
                
                # 解析字段信息 - 支持多种格式
                elif current_chart and ('维度字段' in line or '度量字段' in line or '分析目标' in line or '预期洞察' in line or '图表说明' in line):
                    # 清理行内容，移除markdown格式
                    clean_line = line.replace('- **', '').replace('**', '').replace('-', '').strip()
                    
                    if '维度字段' in clean_line:
                        field_info = clean_line.split('：', 1) if '：' in clean_line else clean_line.split(':', 1)
                        if len(field_info) >= 2:
                            field_value = field_info[1].strip().replace('[', '').replace(']', '').replace('**', '')
                            # 如果有多个字段，取第一个
                            if ',' in field_value:
                                field_value = field_value.split(',')[0].strip()
                            current_chart['dimension_field'] = field_value
                    
                    elif '度量字段' in clean_line:
                        field_info = clean_line.split('：', 1) if '：' in clean_line else clean_line.split(':', 1)
                        if len(field_info) >= 2:
                            field_value = field_info[1].strip().replace('[', '').replace(']', '').replace('**', '')
                            # 如果有多个字段，取第一个
                            if ',' in field_value:
                                field_value = field_value.split(',')[0].strip()
                            current_chart['measure_field'] = field_value
                    
                    elif '预期洞察' in clean_line:
                        insight_info = clean_line.split('：', 1) if '：' in clean_line else clean_line.split(':', 1)
                        if len(insight_info) >= 2:
                            current_chart['expected_insight'] = insight_info[1].strip().replace('[', '').replace(']', '').replace('**', '')
                    
                    elif '图表说明' in clean_line:
                        reason_info = clean_line.split('：', 1) if '：' in clean_line else clean_line.split(':', 1)
                        if len(reason_info) >= 2:
                            current_chart['reason'] = reason_info[1].strip().replace('[', '').replace(']', '').replace('**', '')
            
            # 添加最后一个图表
            if current_chart:
                suggestions.append(current_chart)
            
        except Exception as e:
            print(f"解析可视化建议失败: {e}")
        
        return suggestions
    
    def _extract_chart_type(self, chart_info: str) -> str:
        """从图表信息中提取图表类型"""
        chart_info_lower = chart_info.lower()
        
        if '柱状图' in chart_info or 'bar' in chart_info_lower:
            return 'bar'
        elif '饼图' in chart_info or 'pie' in chart_info_lower:
            return 'pie'
        elif '折线图' in chart_info or 'line' in chart_info_lower:
            return 'line'
        elif '散点图' in chart_info or 'scatter' in chart_info_lower:
            return 'scatter'
        elif '直方图' in chart_info or 'histogram' in chart_info_lower:
            return 'histogram'
        else:
            return 'bar'  # 默认使用柱状图
    
    def _create_chart_from_suggestion(self, df: pd.DataFrame, suggestion: dict, index: int) -> dict:
        """根据AI廚议创建具体图表"""
        try:
            chart_type = suggestion.get('type', 'bar')
            title = suggestion.get('title', f'图表{index + 1}')
            dimension_field = suggestion.get('dimension_field')
            measure_field = suggestion.get('measure_field')
            expected_insight = suggestion.get('expected_insight', '')
            

            
            # 验证和修正字段名
            if dimension_field:
                dimension_field = self._find_best_matching_column(df, dimension_field)
                if not dimension_field:
                    print(f"无法找到匹配的维度字段")
                    return None
            
            if measure_field:
                measure_field = self._find_best_matching_column(df, measure_field)
                if not measure_field:
                    print(f"无法找到匹配的度量字段")
                    return None
            
            chart_data = []
            subtitle = expected_insight
            
            if chart_type == 'bar' and dimension_field and measure_field:
                # 柱状图：维度 x 度量
                grouped = df.groupby(dimension_field)[measure_field].sum().sort_values(ascending=False).head(10)
                chart_data = [{'name': str(name), 'value': float(value)} for name, value in grouped.items()]
                if not subtitle:
                    subtitle = f'{dimension_field}在{measure_field}上的表现排名'
            
            elif chart_type == 'pie' and dimension_field:
                # 饼图：维度分布
                value_counts = df[dimension_field].value_counts().head(8)
                total = value_counts.sum()
                chart_data = []
                for name, count in value_counts.items():
                    percentage = (count / total * 100) if total > 0 else 0
                    chart_data.append({'name': str(name), 'value': round(percentage, 1)})
                if not subtitle:
                    subtitle = f'{dimension_field}的分布情况'
            
            elif chart_type == 'scatter' and dimension_field and measure_field:
                # 散点图：两个数值字段的关系
                clean_data = df[[dimension_field, measure_field]].dropna()
                if len(clean_data) > 5:
                    sample_data = clean_data.sample(min(50, len(clean_data)))
                    chart_data = [[float(row[dimension_field]), float(row[measure_field])] for _, row in sample_data.iterrows()]
                    if not subtitle:
                        correlation = df[dimension_field].corr(df[measure_field])
                        subtitle = f'{dimension_field}与{measure_field}的相关性：{correlation:.3f}'
            
            elif chart_type == 'line' and dimension_field and measure_field:
                # 折线图：时间趋势或序列分析
                if pd.api.types.is_datetime64_any_dtype(df[dimension_field]):
                    # 时间维度
                    time_series = df.groupby(dimension_field)[measure_field].sum().sort_index()
                    chart_data = [{'name': str(name), 'value': float(value)} for name, value in time_series.items()]
                else:
                    # 非时间维度，使用排序
                    grouped = df.groupby(dimension_field)[measure_field].sum().sort_values(ascending=False).head(15)
                    chart_data = [{'name': str(name), 'value': float(value)} for name, value in grouped.items()]
                if not subtitle:
                    subtitle = f'{dimension_field}随{measure_field}的变化趋势'
            
            # 如果没有生成数据，返回空
            if not chart_data:
                print(f"图表 {title} 没有生成数据")
                return None
            
            return {
                'type': chart_type,
                'title': title,
                'data': chart_data,
                'subtitle': subtitle,
                'ai_driven': True  # 标记这是AI驱动的图表
            }
            
        except Exception as e:
            print(f"创建图表失败: {e}")
            return None
    
    def _generate_charts(self, df: pd.DataFrame, scenario: str) -> list:
        charts = []
        
        try:
            # 识别字段类型
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            categorical_cols = [col for col in df.columns 
                              if (len(df[col].unique()) / len(df[col]) < 0.5 and len(df[col].unique()) < 50)]
            
            # 图表1：排行榜（如果有分类和数值字段）
            if categorical_cols and numeric_cols:
                cat_field = categorical_cols[0]
                num_field = numeric_cols[0]
                
                grouped = df.groupby(cat_field)[num_field].sum().sort_values(ascending=False).head(10)
                chart_data = [{'name': str(name), 'value': float(value)} for name, value in grouped.items()]
                
                charts.append({
                    'type': 'bar',
                    'title': f'{cat_field} {num_field} 排行榜',
                    'data': chart_data,
                    'subtitle': f'显示 {cat_field} 在 {num_field} 上的表现排名',
                    'ai_driven': False  # 标记这是默认逻辑生成的
                })
            
            # 图表2：分布图（如果有分类字段）
            if categorical_cols:
                cat_field = categorical_cols[0]
                value_counts = df[cat_field].value_counts().head(8)
                total = value_counts.sum()
                
                chart_data = []
                for name, count in value_counts.items():
                    percentage = (count / total * 100) if total > 0 else 0
                    chart_data.append({'name': str(name), 'value': round(percentage, 1)})
                
                charts.append({
                    'type': 'pie',
                    'title': f'{cat_field} 分布情况',
                    'data': chart_data,
                    'subtitle': f'{cat_field} 的分布情况，{value_counts.index[0]} 占比最高',
                    'ai_driven': False  # 标记这是默认逻辑生成的
                })
            
            # 图表3：相关性分析（如果有多个数值字段）
            if len(numeric_cols) >= 2:
                field1, field2 = numeric_cols[0], numeric_cols[1]
                clean_data = df[[field1, field2]].dropna()
                
                if len(clean_data) > 5:
                    sample_data = clean_data.sample(min(50, len(clean_data)))
                    chart_data = [[float(row[field1]), float(row[field2])] for _, row in sample_data.iterrows()]
                    
                    correlation = df[field1].corr(df[field2])
                    
                    charts.append({
                        'type': 'scatter',
                        'title': f'{field1} vs {field2} 相关性',
                        'data': chart_data,
                        'subtitle': f'相关系数: {correlation:.3f}',
                        'xLabel': field1,
                        'yLabel': field2,
                        'ai_driven': False  # 标记这是默认逻辑生成的
                    })
            
        except Exception as e:
            print(f"图表生成出错: {e}")
            # 生成默认图表
            charts.append({
                'type': 'bar',
                'title': '数据概览',
                'data': [{'name': '数据行数', 'value': len(df)}, {'name': '字段数', 'value': len(df.columns)}],
                'subtitle': '基础数据统计'
            })
        
        return charts
    
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
    
    def _get_missing_data_info(self, df: pd.DataFrame) -> dict:
        """获取缺失数据信息"""
        missing_info = {}
        for col in df.columns:
            missing_count = int(pd.Series(df[col]).isnull().sum())
            if missing_count > 0:
                missing_info[col] = missing_count
        return missing_info
    
    def _generate_recommendations(self, scenario: str, confidence: float) -> list:
        """生成分析建议"""
        recommendations = [
            f"✅ 数据场景识别为：{scenario} (置信度: {confidence:.1%})",
            f"🎯 基于场景特征生成了专业化的分析提示词",
            f"🧠 Gemini分析结果针对{scenario}场景进行了深度优化"
        ]
        
        if confidence > 0.7:
            recommendations.append("🔥 场景匹配度很高，分析结果具有很强的针对性")
        elif confidence > 0.5:
            recommendations.append("👍 场景匹配度较好，分析角度相对准确")
        else:
            recommendations.append("💡 场景匹配度一般，使用通用分析方法")
        
        return recommendations
    
    def _filter_visualization_suggestions(self, ai_insights: str) -> str:
        """完全过滤掉可视化建议章节，包括八个图表的所有相关内容"""
        if not ai_insights or not isinstance(ai_insights, str):
            return ai_insights
        
        try:
            import re
            lines = ai_insights.split('\n')
            filtered_lines = []
            skip_section = False
            
            for line in lines:
                line_stripped = line.strip()
                
                # 检测可视化建议章节的开始
                if (line_stripped.startswith('##') and 
                    ('可视化建议' in line_stripped or 
                     'Excel可视化' in line_stripped or 
                     'Excel多维度可视化' in line_stripped or
                     '多维度可视化' in line_stripped or
                     '图表建议' in line_stripped or
                     '推荐图表' in line_stripped or
                     ('📊' in line_stripped and ('Excel' in line_stripped or '可视化' in line_stripped)))):
                    skip_section = True
                    continue
                
                # 检测新章节的开始（非可视化相关）
                elif line_stripped.startswith('##') and skip_section:
                    # 如果是新的非可视化章节，停止跳过
                    if not ('可视化' in line_stripped or '图表' in line_stripped or '📊' in line_stripped):
                        skip_section = False
                        filtered_lines.append(line)
                    continue
                
                # 如果在跳过状态，继续跳过
                if skip_section:
                    continue
                
                # 过滤单独的图表相关行
                if (re.match(r'^💡\s*图表\d+[：:]\s*(柱状图|饼图|折线图|散点图|热力图|箱线图|直方图)', line_stripped) or
                    re.match(r'^###\s*图表\d+[：:]', line_stripped) or
                    '维度字段：' in line_stripped or
                    '度量字段：' in line_stripped or
                    '推荐理由：' in line_stripped or
                    '预期洞察：' in line_stripped or
                    ('图表类型：' in line_stripped and ('柱状图' in line_stripped or '饼图' in line_stripped or '折线图' in line_stripped))):
                    continue
                
                # 保留其他内容
                filtered_lines.append(line)
            
            filtered_content = '\n'.join(filtered_lines)
            
            # 清理多余的空行
            filtered_content = re.sub(r'\n\s*\n\s*\n', '\n\n', filtered_content)
            
            # 如果过滤后内容为空，返回简单的分析完成提示
            if not filtered_content.strip():
                return "## 📊 数据分析完成\n\n基于您的数据，我们已完成深度分析并生成了专业的可视化图表。所有图表均基于数据特征智能生成，为您提供直观的数据洞察。"
            
            return filtered_content.strip()
            
        except Exception as e:
            print(f"过滤可视化建议失败: {e}")
            return ai_insights

    def _sanitize_for_json(self, obj):
        """递归将对象中的numpy/pandas类型转为原生Python类型"""
        if isinstance(obj, dict):
            return {str(k): self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(v) for v in obj]
        elif isinstance(obj, (int, float)) or str(type(obj)).startswith("<class 'numpy.int"):
            return int(obj)
        elif isinstance(obj, (int, float)) or str(type(obj)).startswith("<class 'numpy.float"):
            return float(obj)
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif pd.isna(obj):
            return None
        else:
            try:
                return obj
            except:
                return str(obj)

# 创建API实例
enhanced_api = EnhancedAnalysisAPI()

def enhanced_analyze_data(df: pd.DataFrame, custom_requirements: str = "") -> dict:
    """对外接口：增强版数据分析"""
    return enhanced_api.enhanced_analyze(df, custom_requirements)