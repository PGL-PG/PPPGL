"""
智能数据分析系统 - 资深数据分析师思维模式
模拟专业数据分析师的分析逻辑，生成针对性的Gemini提示词
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any

class IntelligentAnalysisEngine:
    """智能分析引擎 - 像资深数据分析师一样思考"""
    
    def __init__(self):
        self.business_scenarios = {
            "电商数据分析": {
                "key_metrics": ["销量", "销售额", "单价", "转化率", "客单价"],
                "dimensions": ["品牌", "类别", "渠道", "地区", "时间"],
                "analysis_focus": ["市场份额", "产品竞争力", "销售趋势", "价格策略"]
            },
            "汽车销售分析": {
                "key_metrics": ["销量", "售价", "市场份额", "利润率"],
                "dimensions": ["品牌", "车型", "配置", "地区", "经销商"],
                "analysis_focus": ["品牌竞争", "车型热度", "价格区间", "地区差异"]
            },
            "市场竞争分析": {
                "key_metrics": ["市场份额", "增长率", "排名变化", "竞争指数"],
                "dimensions": ["品牌", "产品线", "价格段", "渠道"],
                "analysis_focus": ["竞争格局", "市场集中度", "品牌地位", "增长潜力"]
            },
            "客户行为分析": {
                "key_metrics": ["活跃度", "转化率", "留存率", "生命周期价值"],
                "dimensions": ["用户群体", "行为类型", "时间周期", "触点"],
                "analysis_focus": ["用户画像", "行为模式", "价值分层", "流失原因"]
            }
        }
    
    def detect_analysis_scenario(self, df: pd.DataFrame, columns: List[str]) -> str:
        """智能识别分析场景"""
        column_text = " ".join([col.lower() for col in columns])
        
        scenario_scores = {}
        for scenario, config in self.business_scenarios.items():
            score = 0
            # 检查关键指标匹配
            for metric in config["key_metrics"]:
                if metric.lower() in column_text:
                    score += 3
            # 检查维度匹配
            for dim in config["dimensions"]:
                if dim.lower() in column_text:
                    score += 2
            scenario_scores[scenario] = score
        
        # 返回得分最高的场景
        best_scenario = max(scenario_scores.items(), key=lambda x: x[1])
        return best_scenario[0] if best_scenario[1] > 2 else "商业数据分析"
    
    def classify_data_fields(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """智能分类数据字段 - 基于业务语义"""
        field_classification = {
            "核心KPI": [],      # 关键业绩指标
            "业务维度": [],      # 分析维度
            "度量指标": [],      # 可计算指标
            "时间维度": [],      # 时间相关
            "辅助字段": []       # 其他字段
        }
        
        for col in df.columns:
            col_lower = col.lower()
            col_data = df[col].dropna()
            
            # 检测数据类型
            is_numeric = pd.api.types.is_numeric_dtype(df[col])
            is_datetime = pd.api.types.is_datetime64_any_dtype(df[col])
            unique_ratio = len(col_data.unique()) / len(col_data) if len(col_data) > 0 else 0
            
            # 核心KPI识别
            if is_numeric and any(kw in col_lower for kw in [
                '销量', '销售额', '收入', '利润', '成本', '份额', '排名', '评分'
            ]):
                field_classification["核心KPI"].append(col)
                
            # 业务维度识别
            elif (not is_numeric and unique_ratio < 0.5) or any(kw in col_lower for kw in [
                '品牌', '类别', '地区', '渠道', '客户', '产品', '车型'
            ]):
                field_classification["业务维度"].append(col)
                
            # 时间维度识别
            elif is_datetime or any(kw in col_lower for kw in [
                '日期', '时间', '年', '月', '季度'
            ]):
                field_classification["时间维度"].append(col)
                
            # 度量指标识别
            elif is_numeric:
                field_classification["度量指标"].append(col)
                
            else:
                field_classification["辅助字段"].append(col)
        
        return field_classification
    
    def generate_analysis_strategy(self, scenario: str, field_classification: Dict[str, List[str]], 
                                 df: pd.DataFrame) -> Dict[str, Any]:
        """生成分析策略 - 资深分析师的思维逻辑"""
        
        strategy = {
            "primary_analysis": None,
            "secondary_analysis": [],
            "chart_recommendations": [],
            "insight_focus": []
        }
        
        kpis = field_classification["核心KPI"]
        dimensions = field_classification["业务维度"]
        time_fields = field_classification["时间维度"]
        
        if scenario == "电商数据分析":
            # 电商分析策略
            if kpis and dimensions:
                strategy["primary_analysis"] = {
                    "type": "竞争力分析",
                    "focus": f"{dimensions[0]}的{kpis[0]}表现",
                    "method": "排行榜 + 市场份额分析"
                }
                
                strategy["secondary_analysis"] = [
                    {"type": "价格策略分析", "fields": [col for col in kpis if '价格' in col or '单价' in col]},
                    {"type": "销售趋势分析", "fields": time_fields + [kpis[0]] if time_fields else []},
                    {"type": "品类对比分析", "fields": dimensions[:2] + [kpis[0]]}
                ]
                
        elif scenario == "汽车销售分析":
            # 汽车行业分析策略
            strategy["primary_analysis"] = {
                "type": "市场格局分析",
                "focus": "品牌竞争力与销量表现",
                "method": "市场份额 + 竞争定位分析"
            }
            
        elif scenario == "市场竞争分析":
            # 竞争分析策略
            strategy["primary_analysis"] = {
                "type": "竞争态势分析",
                "focus": "市场集中度与竞争格局",
                "method": "HHI指数 + 马太效应分析"
            }
            
        # 图表推荐逻辑
        if kpis and dimensions:
            strategy["chart_recommendations"] = [
                {"type": "bar", "purpose": "竞争排行", "fields": [dimensions[0], kpis[0]]},
                {"type": "pie", "purpose": "市场份额", "fields": [dimensions[0]]},
            ]
            
        if time_fields and kpis:
            strategy["chart_recommendations"].append({
                "type": "line", "purpose": "趋势分析", "fields": [time_fields[0], kpis[0]]
            })
        
        # 洞察重点
        strategy["insight_focus"] = [
            "市场领导者识别",
            "竞争差距分析", 
            "增长机会点",
            "风险预警"
        ]
        
        return strategy
    
    def create_gemini_prompt(self, scenario: str, strategy: Dict[str, Any], 
                           df_sample: Dict, custom_requirements: str = "") -> str:
        """生成专业的Gemini分析提示词"""
        
        # 基础提示词模板
        base_prompt = f"""你是一位资深的{scenario}专家，拥有10年以上的数据分析经验。

数据概况：{len(df_sample.get('columns', []))}个字段，数据样例已提供。

分析要求：
1. 请从专业角度进行深度分析，直接给出分析结论，避免过程描述
2. 重点关注{strategy.get('primary_analysis', {}).get('focus', '核心业务指标')}
3. 提供具体的数值结果和业务洞察
4. 给出可执行的建议

"""
        
        # 场景特定提示词
        if scenario == "电商数据分析":
            scenario_prompt = """
特别关注：
- 品牌竞争力排行榜（具体销量/销售额数据）
- 市场份额分布与集中度
- 价格策略效果分析
- 产品类别表现差异
- 增长潜力与机会点识别

输出格式：
## 市场竞争格局
[具体的排行榜数据和份额分析]

## 核心发现
[3-5个关键洞察，包含具体数值]

## 策略建议
[2-3个可执行的业务建议]
"""
        elif scenario == "汽车销售分析":
            scenario_prompt = """
特别关注：
- 品牌销量排行与市场地位
- 车型细分市场表现
- 价格区间竞争态势
- 地区市场差异分析
- 经销商绩效表现

输出格式：
## 品牌竞争分析
[品牌排行榜与市场份额]

## 车型表现
[热销车型与细分市场分析]

## 市场洞察
[价格策略与地区差异分析]

## 业务建议
[基于数据的策略建议]
"""
        else:
            scenario_prompt = """
特别关注：
- 关键指标的表现与排行
- 不同维度的对比分析
- 数据背后的业务逻辑
- 异常值与机会点

输出格式：
## 数据洞察
[关键发现与趋势]

## 对比分析
[维度间的差异分析]

## 行动建议
[基于数据的建议]
"""
        
        # 自定义需求
        custom_prompt = f"\n\n补充要求：{custom_requirements}" if custom_requirements else ""
        
        # 数据样例
        data_sample_prompt = f"\n\n数据样例：\n{json.dumps(df_sample, ensure_ascii=False, indent=2)[:1000]}"
        
        return base_prompt + scenario_prompt + custom_prompt + data_sample_prompt
    
    def analyze_with_business_logic(self, df: pd.DataFrame, scenario: str, 
                                  field_classification: Dict[str, List[str]]) -> Dict[str, Any]:
        """基于业务逻辑的本地分析"""
        
        results = {
            "business_metrics": {},
            "competitive_analysis": {},
            "performance_ranking": {},
            "market_insights": []
        }
        
        kpis = field_classification["核心KPI"]
        dimensions = field_classification["业务维度"]
        
        try:
            # 核心业务指标计算
            if kpis:
                for kpi in kpis[:3]:  # 分析前3个核心指标
                    kpi_data = df[kpi].dropna()
                    if len(kpi_data) > 0:
                        results["business_metrics"][kpi] = {
                            "总量": float(kpi_data.sum()),
                            "均值": float(kpi_data.mean()),
                            "中位数": float(kpi_data.median()),
                            "变异系数": float(kpi_data.std() / kpi_data.mean()) if kpi_data.mean() != 0 else 0,
                            "集中度": self._calculate_concentration(kpi_data)
                        }
            
            # 竞争分析（维度 × 指标）
            if kpis and dimensions:
                for dim in dimensions[:2]:
                    for kpi in kpis[:2]:
                        try:
                            analysis_df = df[[dim, kpi]].dropna()
                            if len(analysis_df) > 0:
                                # 竞争排行
                                ranking = analysis_df.groupby(dim)[kpi].agg(['sum', 'mean', 'count']).sort_values('sum', ascending=False)
                                
                                # 市场份额计算
                                total = ranking['sum'].sum()
                                market_share = (ranking['sum'] / total * 100).round(2)
                                
                                results["performance_ranking"][f"{dim}_{kpi}排行"] = {
                                    "排行榜": ranking.head(10).to_dict('index'),
                                    "市场份额": market_share.head(10).to_dict(),
                                    "HHI指数": self._calculate_hhi(market_share.values),
                                    "CR3集中度": market_share.head(3).sum()
                                }
                        except Exception as e:
                            continue
            
            # 市场洞察生成
            if scenario == "电商数据分析":
                results["market_insights"] = self._generate_ecommerce_insights(results, df)
            elif scenario == "汽车销售分析":
                results["market_insights"] = self._generate_automotive_insights(results, df)
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def _calculate_concentration(self, data: pd.Series) -> float:
        """计算数据集中度（基尼系数思路）"""
        try:
            sorted_data = data.sort_values()
            n = len(sorted_data)
            cumsum = sorted_data.cumsum()
            return float((2 * cumsum.sum() - (n + 1) * sorted_data.sum()) / (n * sorted_data.sum()))
        except:
            return 0.0
    
    def _calculate_hhi(self, market_shares: np.ndarray) -> float:
        """计算HHI指数（市场集中度）"""
        try:
            return float((market_shares ** 2).sum())
        except:
            return 0.0
    
    def _generate_ecommerce_insights(self, results: Dict, df: pd.DataFrame) -> List[str]:
        """生成电商分析洞察"""
        insights = []
        
        try:
            # 从排行榜数据中提取洞察
            for ranking_key, ranking_data in results["performance_ranking"].items():
                if "排行榜" in ranking_data:
                    top_performer = list(ranking_data["排行榜"].keys())[0]
                    hhi = ranking_data.get("HHI指数", 0)
                    cr3 = ranking_data.get("CR3集中度", 0)
                    
                    insights.append(f"🏆 {ranking_key}：{top_performer}领先市场")
                    
                    if hhi > 2500:
                        insights.append(f"📊 市场高度集中，HHI指数{hhi:.0f}，寡头竞争格局")
                    elif hhi > 1500:
                        insights.append(f"📊 市场中等集中，前三名占比{cr3:.1f}%")
                    else:
                        insights.append(f"📊 市场竞争激烈，格局相对分散")
        except:
            insights.append("📈 数据分析完成，建议关注核心竞争指标")
        
        return insights[:5]  # 限制洞察数量
    
    def _generate_automotive_insights(self, results: Dict, df: pd.DataFrame) -> List[str]:
        """生成汽车行业洞察"""
        insights = []
        
        try:
            # 汽车行业特有的分析逻辑
            for ranking_key, ranking_data in results["performance_ranking"].items():
                if "品牌" in ranking_key and "排行榜" in ranking_data:
                    top_brands = list(ranking_data["排行榜"].keys())[:3]
                    insights.append(f"🚗 汽车市场三强：{', '.join(top_brands)}")
                    
                    market_share = ranking_data.get("市场份额", {})
                    if market_share:
                        leader_share = list(market_share.values())[0]
                        if leader_share > 30:
                            insights.append(f"👑 {top_brands[0]}以{leader_share:.1f}%市占率稳居榜首")
                        else:
                            insights.append(f"⚔️ 市场竞争激烈，领先品牌份额仅{leader_share:.1f}%")
        except:
            insights.append("🚗 汽车市场分析完成")
        
        return insights[:5]