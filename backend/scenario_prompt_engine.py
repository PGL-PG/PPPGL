"""
场景化Gemini提示词引擎
根据匹配的数据场景生成精准的Gemini提示词，最大化分析效果
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json

class ScenarioPromptEngine:
    """场景化提示词生成引擎"""
    
    def __init__(self):
        self.prompt_templates = self._build_prompt_templates()
        
    def _build_prompt_templates(self) -> Dict[str, Dict]:
        """构建场景特定的提示词模板"""
        return {
            "电商销售分析": {
                "role_definition": "你是一位拥有15年经验的电商数据分析专家，专精于电商平台运营分析、品牌竞争情报和销售策略优化。",
                "product_positioning": """
【产品定位】这是一个专业的Excel数据分析助手，专门帮助电商运营人员和数据分析师：
- 快速识别销售数据中的关键业务指标
- 自动生成品牌竞争力排行榜和市场份额分析
- 提供基于数据的销售策略和优化建议
- 将复杂的数据分析转化为直观易懂的商业洞察
""",
                "analysis_directives": [
                    "🔍 **数据理解**：深入理解数据的业务含义，识别关键销售指标、品牌信息、产品分类等",
                    "📊 **竞争分析**：重点分析品牌竞争格局，生成具体的排行榜数据和市场份额",
                    "💡 **洞察挖掘**：发现数据背后的商业价值，如热销产品、价格策略效果、市场机会等",
                    "🎯 **策略建议**：基于分析结果提供可执行的运营优化建议"
                ],
                "output_schema": {
                    "数据特征观察": "观察数据结构特点，识别关键业务字段",
                    "竞争格局分析": "品牌/产品排行榜，市场份额分析，竞争强度评估",
                    "销售表现洞察": "热销品类识别，价格策略分析，销售趋势判断",
                    "商业价值发现": "市场机会识别，增长驱动因素，优化空间分析",
                    "可视化建议": "推荐3-4个最有价值的图表类型，包含具体字段搭配",
                    "策略建议": "针对性的运营优化建议，包含具体的执行方向"
                },
                "analysis_depth": "deep_business_insights"
            },
            
            "汽车销售分析": {
                "role_definition": "你是一位资深的汽车行业分析师，具备深厚的汽车市场研究经验和行业洞察力。",
                "product_positioning": """
【产品定位】专业的汽车销售数据分析平台，为汽车厂商、经销商和市场研究机构提供：
- 汽车品牌市场地位和竞争格局分析
- 车型热度排行和细分市场表现评估
- 地区销售差异和市场渗透率分析
- 价格竞争策略和定价效果评估
""",
                "analysis_directives": [
                    "🚗 **行业视角**：从汽车行业专业角度分析数据，关注品牌力、车型热度、市场渗透",
                    "📈 **市场格局**：深度分析汽车品牌竞争态势，识别市场领导者和挑战者",
                    "🎯 **细分市场**：按车型、价格区间、地区等维度分析细分市场表现",
                    "💰 **价格策略**：分析不同价格区间的竞争状况和市场接受度"
                ],
                "output_schema": {
                    "市场格局透视": "汽车品牌竞争排名，市场集中度分析",
                    "车型表现分析": "热销车型识别，细分市场表现评估",
                    "地区差异解读": "不同地区的销售表现和市场特征",
                    "价格竞争分析": "价格区间分布，定价策略效果评估",
                    "可视化方案": "汽车行业特色图表推荐",
                    "市场机会识别": "基于数据的市场拓展和策略建议"
                },
                "analysis_depth": "industry_expert_level"
            },
            
            "财务业绩分析": {
                "role_definition": "你是一位经验丰富的财务分析师，擅长财务数据解读和业绩评估。",
                "product_positioning": """
【产品定位】专业的财务数据分析工具，为财务管理人员和企业高管提供：
- 收入结构分析和增长驱动因素识别
- 成本控制效果评估和费用优化建议
- 利润率分析和盈利能力评估
- 预算执行监控和财务健康度评估
""",
                "analysis_directives": [
                    "💼 **财务专业性**：运用专业财务分析方法，关注关键财务指标和比率",
                    "📊 **结构分析**：深入分析收入结构、成本构成、利润来源等",
                    "🎯 **绩效评估**：评估财务表现，识别优势领域和改进空间",
                    "⚠️ **风险识别**：识别财务数据中的风险信号和预警指标"
                ],
                "output_schema": {
                    "财务健康度评估": "基于关键财务指标的整体健康度判断",
                    "收入结构分析": "收入来源分析，增长驱动因素识别",
                    "成本控制评估": "成本结构分析，费用控制效果评估",
                    "盈利能力分析": "利润率分析，盈利质量评估",
                    "预算执行监控": "预算vs实际对比，执行效果评估",
                    "财务建议": "基于分析的财务管理优化建议"
                },
                "analysis_depth": "financial_expert_level"
            },
            
            "通用数据分析": {
                "role_definition": "你是一位全能的数据分析专家，能够快速理解各种类型的数据并提供专业分析。",
                "product_positioning": """
【产品定位】智能化的通用数据分析助手，能够：
- 自动识别数据特征和分析潜力
- 根据数据类型选择最佳分析角度
- 提供标准化的数据洞察和可视化建议
- 生成通用的数据分析报告
""",
                "analysis_directives": [
                    "🔍 **数据探索**：全面了解数据结构，识别关键字段和分析维度",
                    "📊 **模式识别**：发现数据中的规律、趋势和异常",
                    "💡 **洞察生成**：基于数据特征生成有价值的分析洞察",
                    "🎯 **建议输出**：提供实用的数据应用和优化建议"
                ],
                "output_schema": {
                    "数据概况": "数据基本特征和质量评估",
                    "关键发现": "数据中的重要发现和规律",
                    "分析洞察": "基于数据的深度洞察",
                    "可视化建议": "最适合的图表类型和展示方式",
                    "应用建议": "数据的潜在应用价值和优化方向"
                },
                "analysis_depth": "comprehensive_analysis"
            }
        }
    
    def generate_scenario_prompt(self, scenario: str, df: pd.DataFrame, 
                                match_details: Dict, custom_requirements: str = "") -> str:
        """生成场景特定的Gemini提示词"""
        
        template = self.prompt_templates.get(scenario, self.prompt_templates["通用数据分析"])
        
        # 构建数据摘要
        data_summary = self._build_data_summary(df, scenario)
        
        # 构建核心提示词
        prompt = self._construct_core_prompt(template, data_summary, match_details)
        
        # 添加自定义需求
        if custom_requirements:
            prompt += f"\n\n**用户特殊要求：**\n{custom_requirements}\n请在标准分析基础上，特别关注用户提出的需求。"
        
        # 添加输出要求
        prompt += self._build_output_requirements(template)
        
        return prompt
    
    def _build_data_summary(self, df: pd.DataFrame, scenario: str) -> Dict[str, Any]:
        """构建数据摘要信息"""
        summary = {
            "basic_info": {
                "行数": len(df),
                "列数": len(df.columns),
                "字段列表": list(df.columns)
            },
            "data_sample": self._get_representative_sample(df),
            "field_analysis": self._analyze_fields_for_scenario(df, scenario),
            "statistical_overview": self._get_statistical_overview(df)
        }
        return summary
    
    def _get_representative_sample(self, df: pd.DataFrame, sample_size: int = 10) -> List[Dict]:
        """获取代表性数据样本"""
        sample_df = df.head(sample_size)
        sample_data = []
        
        for _, row in sample_df.iterrows():
            row_dict = {}
            for col, val in row.items():
                if pd.isna(val):
                    row_dict[col] = None
                elif isinstance(val, (np.integer, np.floating)):
                    row_dict[col] = float(val) if isinstance(val, np.floating) else int(val)
                else:
                    row_dict[col] = str(val)
            sample_data.append(row_dict)
        
        return sample_data
    
    def _analyze_fields_for_scenario(self, df: pd.DataFrame, scenario: str) -> Dict[str, Any]:
        """针对特定场景分析字段"""
        field_analysis = {
            "关键业务字段": {},
            "数值型指标": [],
            "分类维度": [],
            "时间维度": []
        }
        
        for col in df.columns:
            col_data = df[col].dropna()
            
            # 数值型字段
            if pd.api.types.is_numeric_dtype(col_data) and len(col_data) > 0:
                field_analysis["数值型指标"].append({
                    "字段名": col,
                    "数据类型": "数值型",
                    "总和": float(col_data.sum()),
                    "平均值": float(col_data.mean()),
                    "最大值": float(col_data.max()),
                    "最小值": float(col_data.min()),
                    "非空记录数": len(col_data)
                })
            
            # 分类型字段
            elif len(col_data) > 0:
                unique_ratio = len(col_data.unique()) / len(col_data)
                if unique_ratio < 0.8 and len(col_data.unique()) < 100:
                    value_counts = col_data.value_counts().head(10)
                    field_analysis["分类维度"].append({
                        "字段名": col,
                        "数据类型": "分类型",
                        "唯一值数量": len(col_data.unique()),
                        "前10排名": {str(k): int(v) for k, v in value_counts.items()}
                    })
        
        return field_analysis
    
    def _get_statistical_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """获取统计概览"""
        overview = {
            "数据质量": {
                "总记录数": len(df),
                "缺失值统计": {},
                "完整性评分": 0
            },
            "数据分布": {},
            "关键统计": {}
        }
        
        # 缺失值统计
        missing_data = df.isnull().sum()
        total_cells = len(df) * len(df.columns)
        total_missing = missing_data.sum()
        
        overview["数据质量"]["缺失值统计"] = {
            col: int(missing_count) for col, missing_count in missing_data.items() if missing_count > 0
        }
        overview["数据质量"]["完整性评分"] = round((1 - total_missing / total_cells) * 100, 2) if total_cells > 0 else 100
        
        # 数值字段的关键统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            for col in numeric_cols[:5]:  # 最多5个数值字段
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    overview["关键统计"][col] = {
                        "总计": float(col_data.sum()),
                        "均值": round(float(col_data.mean()), 2),
                        "中位数": float(col_data.median()),
                        "标准差": round(float(col_data.std()), 2) if len(col_data) > 1 else 0
                    }
        
        return overview
    
    def _construct_core_prompt(self, template: Dict, data_summary: Dict, match_details: Dict) -> str:
        """构建核心提示词"""
        
        # 角色定义
        prompt = f"{template['role_definition']}\n\n"
        
        # 产品定位
        prompt += f"{template['product_positioning']}\n"
        
        # 场景匹配信息
        confidence = match_details.get('confidence', 0)
        prompt += f"\n**场景匹配结果：**\n"
        prompt += f"- 匹配置信度：{confidence:.2f}\n"
        prompt += f"- 数据特征：{len(data_summary['basic_info']['字段列表'])}个字段，{data_summary['basic_info']['行数']}条记录\n"
        
        # 分析指导原则
        prompt += f"\n**分析指导原则：**\n"
        for directive in template['analysis_directives']:
            prompt += f"{directive}\n"
        
        # 数据信息
        prompt += f"\n**数据详情：**\n"
        prompt += f"```json\n{json.dumps(data_summary, ensure_ascii=False, indent=2)}\n```\n"
        
        return prompt
    
    def _build_output_requirements(self, template: Dict) -> str:
        """构建输出要求"""
        
        output_req = f"\n\n**输出要求：**\n"
        output_req += f"请严格按照以下结构输出分析结果，确保内容具体、数据准确、洞察深入：\n\n"
        
        for section, description in template['output_schema'].items():
            output_req += f"## {section}\n{description}\n\n"
        
        output_req += """
**重要说明：**
1. 所有分析必须基于提供的真实数据，给出具体数值和结论
2. 避免空洞的方法论描述，直接给出分析结果
3. 每个洞察都要有数据支撑，包含具体的数字和比例
4. 可视化建议要指定具体的字段组合和图表类型
5. 策略建议要可执行，结合数据特点给出针对性建议
"""
        
        return output_req
    
    def enhance_prompt_with_context(self, base_prompt: str, analysis_context: Dict) -> str:
        """使用分析上下文增强提示词"""
        
        enhanced_prompt = base_prompt
        
        # 添加字段语义信息
        if 'field_semantics' in analysis_context:
            enhanced_prompt += f"\n\n**字段语义识别：**\n"
            for field, semantic in analysis_context['field_semantics'].items():
                enhanced_prompt += f"- {field}: {semantic}\n"
        
        # 添加分析潜力信息
        if 'analysis_potential' in analysis_context:
            enhanced_prompt += f"\n\n**分析潜力评估：**\n"
            potential = analysis_context['analysis_potential']
            if potential.get('ranking_analysis', 0) > 0.5:
                enhanced_prompt += "- 🏆 数据具备良好的排行榜分析潜力\n"
            if potential.get('trend_analysis', 0) > 0.5:
                enhanced_prompt += "- 📈 数据适合进行趋势分析\n"
            if potential.get('comparison_analysis', 0) > 0.5:
                enhanced_prompt += "- ⚖️ 数据支持多维度对比分析\n"
        
        return enhanced_prompt
    
    def create_visualization_prompt_supplement(self, df: pd.DataFrame, scenario: str) -> str:
        """创建可视化专用的提示词补充"""
        
        viz_prompt = f"\n\n**可视化分析专项要求：**\n"
        viz_prompt += f"基于数据特征，请推荐3-4个最有价值的可视化图表：\n\n"
        
        # 检测适合的图表类型
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = [col for col in df.columns 
                          if len(df[col].unique()) / len(df[col]) < 0.5 and len(df[col].unique()) < 50]
        
        viz_recommendations = []
        
        # 排行榜图表
        if categorical_cols and numeric_cols:
            viz_recommendations.append(f"柱状图：{categorical_cols[0]} × {numeric_cols[0]} 排行榜")
        
        # 分布图表
        if categorical_cols:
            viz_recommendations.append(f"饼图：{categorical_cols[0]} 分布占比")
        
        # 相关性图表
        if len(numeric_cols) >= 2:
            viz_recommendations.append(f"散点图：{numeric_cols[0]} vs {numeric_cols[1]} 相关性")
        
        for i, rec in enumerate(viz_recommendations[:3], 1):
            viz_prompt += f"{i}. **{rec}**\n"
            viz_prompt += f"   - 预期洞察：[基于业务场景的具体洞察]\n"
            viz_prompt += f"   - 推荐理由：[数据特征支撑的理由]\n\n"
        
        return viz_prompt