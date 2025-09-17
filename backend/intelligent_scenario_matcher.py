"""
智能数据场景匹配引擎
基于相似度算法精确识别数据场景，为Gemini提供精准提示词
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import re
from collections import Counter
import json

class ScenarioMatcher:
    """智能场景匹配器 - 基于多维度特征的相似度计算"""
    
    def __init__(self):
        self.scenario_library = self._build_scenario_library()
        
    def _build_scenario_library(self) -> Dict[str, Dict]:
        """构建场景知识库 - 每个场景包含特征向量和提示词模板"""
        return {
            "电商销售分析": {
                "field_patterns": {
                    "商品名称": ["商品", "产品", "品名", "商品名", "产品名", "货品", "sku", "product", "item"],
                    "品牌信息": ["品牌", "厂商", "制造商", "brand", "manufacturer", "牌子"],
                    "销量数据": ["销量", "销售数量", "售出", "成交", "销售", "sales", "quantity", "sold"],
                    "价格信息": ["价格", "单价", "售价", "金额", "price", "cost", "amount", "元", "￥"],
                    "类别分类": ["类别", "分类", "种类", "category", "type", "class"]
                },
                "confidence_indicators": {
                    "strong_signals": ["商品.*销量", "品牌.*销售", "产品.*价格", "类别.*营收"],
                    "medium_signals": ["名称.*数量", "价格.*类型", "商品.*金额"],
                    "weak_signals": ["产品", "销量", "价格", "品牌"]
                },
                "analysis_focus": [
                    "品牌竞争力排名与市场份额分析",
                    "产品类别表现与销量分布",
                    "价格策略效果与价格敏感性",
                    "销售趋势与季节性特征"
                ],
                "gemini_context": {
                    "industry_expertise": "电商运营专家",
                    "analysis_methodology": "商业数据分析",
                    "output_requirements": ["具体数值结果", "排行榜数据", "市场份额", "竞争格局", "策略建议"]
                }
            },
            
            "汽车销售分析": {
                "field_patterns": {
                    "车型信息": ["车型", "型号", "款式", "model", "vehicle", "汽车", "轿车", "SUV"],
                    "品牌信息": ["品牌", "厂商", "制造商", "brand", "make", "牌子"],
                    "销量数据": ["销量", "销售数量", "售出", "成交", "sales", "units"],
                    "价格信息": ["价格", "售价", "指导价", "price", "msrp", "万元"]
                },
                "confidence_indicators": {
                    "strong_signals": ["车型.*销量", "品牌.*汽车", "售价.*车", "车.*价格"],
                    "medium_signals": ["型号.*数量", "品牌.*销售", "汽车.*金额"],
                    "weak_signals": ["车型", "品牌", "销量", "价格"]
                },
                "analysis_focus": [
                    "汽车品牌竞争格局与市场地位",
                    "热销车型排行榜与细分市场分析",
                    "价格区间竞争态势与定价策略",
                    "地区市场差异与渗透率分析"
                ],
                "gemini_context": {
                    "industry_expertise": "汽车行业分析师",
                    "analysis_methodology": "汽车市场研究",
                    "output_requirements": ["品牌排名", "车型热度", "价格竞争", "地区分析", "市场趋势"]
                }
            },
            
            "财务业绩分析": {
                "field_patterns": {
                    "收入数据": ["收入", "营收", "营业额", "revenue", "income", "turnover"],
                    "成本费用": ["成本", "费用", "支出", "cost", "expense", "expenditure"],
                    "利润指标": ["利润", "盈利", "净利", "profit", "earnings", "margin"],
                    "预算计划": ["预算", "计划", "目标", "budget", "target", "forecast"]
                },
                "confidence_indicators": {
                    "strong_signals": ["收入.*利润", "成本.*费用", "营收.*支出", "预算.*实际"],
                    "medium_signals": ["收入.*部门", "利润.*产品", "成本.*业务"],
                    "weak_signals": ["收入", "成本", "利润", "预算"]
                },
                "analysis_focus": [
                    "收入结构分析与增长驱动因素",
                    "成本控制效果与费用优化机会",
                    "利润率分析与盈利能力评估",
                    "预算执行情况与差异分析"
                ],
                "gemini_context": {
                    "industry_expertise": "财务分析专家",
                    "analysis_methodology": "财务数据分析",
                    "output_requirements": ["财务比率", "收支结构", "盈利分析", "预算对比", "风险评估"]
                }
            }
        }
    
    def analyze_data_fingerprint(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析数据指纹 - 提取多维度特征"""
        fingerprint = {
            "field_features": self._extract_field_features(df),
            "content_features": self._extract_content_features(df),
            "statistical_features": self._extract_statistical_features(df),
            "semantic_features": self._extract_semantic_features(df)
        }
        return fingerprint
    
    def _extract_field_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """提取字段级特征"""
        features = {
            "field_names": list(df.columns),
            "field_count": len(df.columns),
            "field_types": {},
            "field_semantics": {}
        }
        
        for col in df.columns:
            col_data = df[col].dropna()
            
            # 数据类型识别
            if pd.api.types.is_numeric_dtype(col_data):
                features["field_types"][col] = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                features["field_types"][col] = "datetime"
            else:
                unique_ratio = len(col_data.unique()) / len(col_data) if len(col_data) > 0 else 0
                if unique_ratio < 0.5 and len(col_data.unique()) < 50:
                    features["field_types"][col] = "categorical"
                else:
                    features["field_types"][col] = "text"
            
            # 语义识别
            features["field_semantics"][col] = self._identify_field_semantic(col, pd.Series(col_data))
        
        return features
    
    def _extract_content_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """提取内容特征"""
        features = {
            "row_count": len(df),
            "data_density": {},
            "content_keywords": []
        }
        
        # 数据密度计算
        for col in df.columns:
            non_null_ratio = df[col].count() / len(df) if len(df) > 0 else 0
            features["data_density"][col] = non_null_ratio
        
        # 内容关键词提取
        all_text_content = []
        for col in df.columns:
            all_text_content.append(col.lower())
            if df[col].dtype == 'object':
                unique_values = df[col].dropna().unique()[:10]
                all_text_content.extend([str(val).lower() for val in unique_values if isinstance(val, str)])
        
        features["content_keywords"] = list(set(all_text_content))
        return features
    
    def _extract_statistical_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """提取统计特征"""
        features = {
            "numeric_field_count": 0,
            "categorical_field_count": 0,
            "text_field_count": 0,
            "data_scale": "small",
            "complexity_score": 0
        }
        
        # 字段类型统计
        for col in df.columns:
            col_data = df[col].dropna()
            if pd.api.types.is_numeric_dtype(col_data):
                features["numeric_field_count"] += 1
            elif len(col_data.unique()) / len(col_data) < 0.5 if len(col_data) > 0 else False:
                features["categorical_field_count"] += 1
            else:
                features["text_field_count"] += 1
        
        # 数据规模评估
        total_cells = len(df) * len(df.columns)
        if total_cells < 1000:
            features["data_scale"] = "small"
        elif total_cells < 50000:
            features["data_scale"] = "medium"
        else:
            features["data_scale"] = "large"
        
        # 复杂度评分
        features["complexity_score"] = (
            features["numeric_field_count"] * 1 +
            features["categorical_field_count"] * 2 +
            features["text_field_count"] * 0.5
        )
        
        return features
    
    def _extract_semantic_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """提取语义特征"""
        features = {
            "business_domain_signals": {},
            "analysis_potential": {}
        }
        
        # 业务领域信号强度计算
        for scenario_name, scenario_config in self.scenario_library.items():
            signal_strength = self._calculate_scenario_signals(df, scenario_config)
            features["business_domain_signals"][scenario_name] = signal_strength
        
        # 分析潜力评估
        features["analysis_potential"] = {
            "ranking_analysis": self._assess_ranking_potential(df),
            "trend_analysis": self._assess_trend_potential(df),
            "comparison_analysis": self._assess_comparison_potential(df)
        }
        
        return features
    
    def _identify_field_semantic(self, field_name: str, field_data: pd.Series) -> str:
        """识别字段语义类型"""
        field_lower = field_name.lower()
        
        # 基于字段名的语义识别
        semantic_patterns = {
            "sales_metric": ["销量", "销售", "成交", "sales", "quantity", "sold"],
            "price_metric": ["价格", "单价", "费用", "金额", "price", "cost", "amount"],
            "brand_dimension": ["品牌", "厂商", "brand", "manufacturer"],
            "product_dimension": ["产品", "商品", "货品", "product", "item", "sku"],
            "category_dimension": ["类别", "分类", "种类", "category", "type"],
            "time_dimension": ["时间", "日期", "年", "月", "date", "time"]
        }
        
        for semantic, patterns in semantic_patterns.items():
            if any(pattern in field_lower for pattern in patterns):
                return semantic
        
        # 基于数据内容的语义识别
        if pd.api.types.is_numeric_dtype(field_data):
            return "numeric_metric"
        elif len(field_data.unique()) / len(field_data) < 0.1 if len(field_data) > 0 else False:
            return "category_dimension"
        else:
            return "text_attribute"
    
    def _calculate_scenario_signals(self, df: pd.DataFrame, scenario_config: Dict) -> float:
        """计算场景信号强度"""
        total_score = 0.0
        max_possible_score = 0.0
        
        field_patterns = scenario_config.get("field_patterns", {})
        confidence_indicators = scenario_config.get("confidence_indicators", {})
        
        # 字段模式匹配
        for pattern_type, patterns in field_patterns.items():
            max_possible_score += 10
            pattern_score = 0
            
            for col in df.columns:
                col_lower = col.lower()
                for pattern in patterns:
                    if pattern in col_lower:
                        pattern_score += 2
                        break
            
            total_score += min(pattern_score, 10)
        
        # 置信度指标匹配
        all_content = " ".join([col.lower() for col in df.columns])
        
        for signal_level, indicators in confidence_indicators.items():
            weight = {"strong_signals": 3, "medium_signals": 2, "weak_signals": 1}.get(signal_level, 1)
            max_possible_score += len(indicators) * weight
            
            for indicator in indicators:
                if re.search(indicator, all_content):
                    total_score += weight
        
        return total_score / max_possible_score if max_possible_score > 0 else 0.0
    
    def _assess_ranking_potential(self, df: pd.DataFrame) -> float:
        """评估排行榜分析潜力"""
        score = 0.0
        
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        categorical_cols = [col for col in df.columns 
                          if (len(df[col].unique()) / len(df[col]) < 0.5 if len(df[col]) > 0 else False)]
        
        if numeric_cols and categorical_cols:
            score += 0.5
            
            for cat_col in categorical_cols:
                cat_unique_count = df[cat_col].nunique()
                if 2 <= cat_unique_count <= 20:
                    score += 0.3
                    break
        
        return min(score, 1.0)
    
    def _assess_trend_potential(self, df: pd.DataFrame) -> float:
        """评估趋势分析潜力"""
        score = 0.0
        
        # 检查时间字段
        time_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        if time_cols:
            score += 0.6
        
        # 检查有序数据
        for col in df.columns:
            col_lower = col.lower()
            if any(time_word in col_lower for time_word in ["时间", "日期", "年", "月", "季度", "date", "time"]):
                score += 0.4
                break
        
        return min(score, 1.0)
    
    def _assess_comparison_potential(self, df: pd.DataFrame) -> float:
        """评估对比分析潜力"""
        score = 0.0
        
        categorical_cols = [col for col in df.columns 
                          if (len(df[col].unique()) / len(df[col]) < 0.5 if len(df[col]) > 0 else False)]
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        
        if len(categorical_cols) >= 2 and len(numeric_cols) >= 1:
            score += 0.8
        elif len(categorical_cols) >= 1 and len(numeric_cols) >= 2:
            score += 0.6
        
        return min(score, 1.0)
    
    def match_best_scenario(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        """匹配最佳场景"""
        fingerprint = self.analyze_data_fingerprint(df)
        
        scenario_scores = {}
        
        # 计算每个场景的匹配度
        for scenario_name, scenario_config in self.scenario_library.items():
            score = fingerprint["semantic_features"]["business_domain_signals"].get(scenario_name, 0)
            scenario_scores[scenario_name] = score
        
        # 选择最佳匹配场景
        best_scenario = max(scenario_scores.items(), key=lambda x: x[1])
        best_scenario_name, best_score = best_scenario
        
        # 如果最高分数太低，使用通用分析
        if best_score < 0.3:
            best_scenario_name = "通用数据分析"
            best_score = 0.5
        
        match_details = {
            "all_scores": scenario_scores,
            "confidence": best_score,
            "fingerprint": fingerprint
        }
        
        return best_scenario_name, best_score, match_details