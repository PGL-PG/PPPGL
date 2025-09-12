from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import json
from datetime import datetime
import re

def safe_convert_value(value):
    """安全地转换值为可JSON序列化的类型"""
    if pd.isna(value) or value is None:
        return None
    elif isinstance(value, (bool, np.bool_)):
        return bool(value)
    elif isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return str(value)
    else:
        return value

def detect_business_scenario(df, columns_info):
    """智能识别业务场景"""
    all_columns = [col.lower() for col in df.columns]
    column_text = " ".join(all_columns)
    
    # 业务场景关键词
    scenarios = {
        "销售分析": {
            "keywords": ["销售", "销量", "营收", "收入", "业绩", "成交", "订单", "客户"],
            "priority": 0
        },
        "产品分析": {
            "keywords": ["产品", "商品", "型号", "品牌", "类别", "库存", "价格"],
            "priority": 0
        },
        "财务分析": {
            "keywords": ["成本", "利润", "费用", "支出", "预算", "财务", "资金"],
            "priority": 0
        },
        "人员分析": {
            "keywords": ["员工", "人员", "部门", "岗位", "工资", "薪酬", "考勤"],
            "priority": 0
        },
        "时间分析": {
            "keywords": ["日期", "时间", "年", "月", "季度", "周"],
            "priority": 0
        }
    }
    
    # 计算每个场景的匹配度
    for scenario, info in scenarios.items():
        match_count = sum(1 for keyword in info["keywords"] if keyword in column_text)
        scenarios[scenario]["priority"] = match_count
    
    # 返回匹配度最高的场景
    best_scenario = max(scenarios.items(), key=lambda x: x[1]["priority"])
    return best_scenario[0] if best_scenario[1]["priority"] > 0 else "通用分析"

def identify_key_fields(df, columns_info):
    """智能识别关键业务字段"""
    key_fields = {
        "数值字段": [],
        "分类字段": [], 
        "时间字段": [],
        "金额字段": [],
        "数量字段": [],
        "名称字段": []
    }
    
    for col in df.columns:
        col_lower = col.lower()
        col_type = columns_info.get(col, {}).get('type', 'text')
        
        # 数值字段分类
        if col_type == 'numeric':
            key_fields["数值字段"].append(col)
            
            # 进一步细分数值字段
            if any(keyword in col_lower for keyword in ['金额', '价格', '收入', '成本', '费用', 'money', 'price', 'cost', 'revenue', '元', '￥']):
                key_fields["金额字段"].append(col)
            elif any(keyword in col_lower for keyword in ['数量', '销量', '库存', 'quantity', 'amount', '个', '件', '台']):
                key_fields["数量字段"].append(col)
                
        # 分类字段
        elif col_type == 'categorical' or (col_type == 'text' and df[col].nunique() < len(df) * 0.5):
            key_fields["分类字段"].append(col)
            
        # 时间字段
        elif col_type == 'datetime':
            key_fields["时间字段"].append(col)
            
        # 名称字段（唯一值较多的文本字段）
        elif col_type == 'text' and df[col].nunique() > len(df) * 0.8:
            key_fields["名称字段"].append(col)
    
    return key_fields

def perform_excel_basic_analysis(df, key_fields):
    """执行Excel基础分析"""
    results = {
        "数据概览": {},
        "基础统计": {},
        "排行榜": {},
        "分组统计": {},
        "图表建议": []
    }
    
    try:
        # 数据概览
        results["数据概览"] = {
            "总行数": len(df),
            "总列数": len(df.columns),
            "数值字段数": len(key_fields["数值字段"]),
            "分类字段数": len(key_fields["分类字段"]),
            "缺失值统计": {col: df[col].isnull().sum() for col in df.columns if df[col].isnull().sum() > 0}
        }
        
        # 数值字段基础统计
        if key_fields["数值字段"]:
            numeric_stats = {}
            for col in key_fields["数值字段"][:3]:  # 最多分析3个数值字段
                data = df[col].dropna()
                if len(data) > 0:
                    numeric_stats[col] = {
                        "总和": safe_convert_value(data.sum()),
                        "平均值": safe_convert_value(data.mean()),
                        "最大值": safe_convert_value(data.max()),
                        "最小值": safe_convert_value(data.min()),
                        "中位数": safe_convert_value(data.median()),
                        "记录数": len(data)
                    }
            results["基础统计"] = numeric_stats
        
        # 生成排行榜（分类字段 × 数值字段）
        if key_fields["分类字段"] and key_fields["数值字段"]:
            rankings = {}
            
            for cat_field in key_fields["分类字段"][:2]:  # 最多2个分类字段
                for num_field in key_fields["数值字段"][:2]:  # 最多2个数值字段
                    try:
                        df_clean = df[[cat_field, num_field]].dropna()
                        if len(df_clean) > 0:
                            # 按分类分组求和
                            grouped = df_clean.groupby(cat_field)[num_field].agg(['sum', 'mean', 'count']).round(2)
                            grouped_sorted = grouped.sort_values('sum', ascending=False)
                            
                            rank_key = f"{cat_field}按{num_field}排行"
                            rankings[rank_key] = {}
                            
                            for idx, (category, stats) in enumerate(grouped_sorted.head(10).iterrows()):
                                rankings[rank_key][str(category)] = {
                                    "排名": idx + 1,
                                    "总计": safe_convert_value(stats['sum']),
                                    "平均": safe_convert_value(stats['mean']),
                                    "数量": safe_convert_value(stats['count'])
                                }
                    except:
                        continue
                        
            results["排行榜"] = rankings
        
        # 分组统计
        if key_fields["分类字段"]:
            group_stats = {}
            
            for cat_field in key_fields["分类字段"][:3]:
                try:
                    value_counts = df[cat_field].value_counts().head(10)
                    group_stats[f"{cat_field}分布"] = {
                        str(k): safe_convert_value(v) for k, v in value_counts.items()
                    }
                except:
                    continue
                    
            results["分组统计"] = group_stats
        
        # 图表建议
        chart_suggestions = []
        
        # 柱状图建议
        if key_fields["分类字段"] and key_fields["数值字段"]:
            chart_suggestions.append({
                "图表类型": "柱状图",
                "推荐字段": f"{key_fields['分类字段'][0]} × {key_fields['数值字段'][0]}",
                "用途": "对比不同类别的数值大小"
            })
            
        # 饼图建议
        if key_fields["分类字段"]:
            chart_suggestions.append({
                "图表类型": "饼图", 
                "推荐字段": key_fields['分类字段'][0],
                "用途": "显示各类别的占比分布"
            })
            
        # 折线图建议
        if key_fields["时间字段"] and key_fields["数值字段"]:
            chart_suggestions.append({
                "图表类型": "折线图",
                "推荐字段": f"{key_fields['时间字段'][0]} × {key_fields['数值字段'][0]}",
                "用途": "显示数值随时间的变化趋势"
            })
            
        results["图表建议"] = chart_suggestions
        
    except Exception as e:
        print(f"Excel基础分析失败: {e}")
        
    return results

def perform_multi_dimensional_analysis(df, key_fields, dimension_level="概览"):
    """执行多维度分析"""
    results = {}
    
    try:
        if dimension_level == "概览":
            # 概览级别：整体情况
            results = perform_overview_analysis(df, key_fields)
        elif dimension_level == "细分":
            # 细分级别：按主要维度细分
            results = perform_detailed_analysis(df, key_fields)  
        elif dimension_level == "深度":
            # 深度级别：交叉分析
            results = perform_deep_analysis(df, key_fields)
            
    except Exception as e:
        print(f"多维度分析失败: {e}")
        results = {"error": str(e)}
        
    return results

def perform_overview_analysis(df, key_fields):
    """概览级别分析"""
    results = {
        "分析级别": "概览",
        "主要发现": [],
        "关键指标": {},
        "快速洞察": []
    }
    
    # 关键指标计算
    if key_fields["数值字段"]:
        main_numeric = key_fields["数值字段"][0]
        data = df[main_numeric].dropna()
        
        results["关键指标"] = {
            "主要指标": main_numeric,
            "总计": safe_convert_value(data.sum()),
            "平均值": safe_convert_value(data.mean()),
            "记录总数": len(df)
        }
        
        # 快速洞察
        results["快速洞察"].append(f"📊 数据包含{len(df)}条记录")
        results["快速洞察"].append(f"💰 {main_numeric}总计: {data.sum():,.0f}")
        results["快速洞察"].append(f"📈 {main_numeric}平均: {data.mean():.1f}")
    
    # 分类字段概览
    if key_fields["分类字段"]:
        main_category = key_fields["分类字段"][0]
        unique_count = df[main_category].nunique()
        results["快速洞察"].append(f"🏷️ 共有{unique_count}个不同的{main_category}")
    
    return results

def perform_detailed_analysis(df, key_fields):
    """细分级别分析"""
    results = {
        "分析级别": "细分",
        "细分维度": [],
        "详细统计": {},
        "对比分析": {}
    }
    
    # 按主要分类字段细分
    if key_fields["分类字段"] and key_fields["数值字段"]:
        main_category = key_fields["分类字段"][0]
        main_numeric = key_fields["数值字段"][0]
        
        df_clean = df[[main_category, main_numeric]].dropna()
        grouped = df_clean.groupby(main_category)[main_numeric].agg(['sum', 'mean', 'count', 'std']).round(2)
        
        results["细分维度"].append(main_category)
        results["详细统计"][main_category] = {}
        
        for category, stats in grouped.iterrows():
            results["详细统计"][main_category][str(category)] = {
                "合计": safe_convert_value(stats['sum']),
                "平均": safe_convert_value(stats['mean']),
                "数量": safe_convert_value(stats['count']),
                "标准差": safe_convert_value(stats['std']) if not pd.isna(stats['std']) else 0
            }
        
        # 对比分析
        top_category = grouped.sort_values('sum', ascending=False).index[0]
        top_value = grouped.loc[top_category, 'sum']
        total_value = grouped['sum'].sum()
        
        results["对比分析"] = {
            "最高类别": str(top_category),
            "最高值": safe_convert_value(top_value),
            "占比": f"{(top_value/total_value)*100:.1f}%" if total_value > 0 else "0%"
        }
    
    return results

def perform_deep_analysis(df, key_fields):
    """深度级别分析"""
    results = {
        "分析级别": "深度",
        "交叉分析": {},
        "相关性分析": {},
        "异常值检测": {}
    }
    
    # 双维度交叉分析
    if len(key_fields["分类字段"]) >= 2 and key_fields["数值字段"]:
        cat1, cat2 = key_fields["分类字段"][:2]
        num_field = key_fields["数值字段"][0]
        
        try:
            df_clean = df[[cat1, cat2, num_field]].dropna()
            cross_table = pd.crosstab(df_clean[cat1], df_clean[cat2], 
                                    values=df_clean[num_field], aggfunc='sum', fill_value=0)
            
            # 找出最大值组合
            max_value = 0
            max_combination = ""
            
            for idx in cross_table.index:
                for col in cross_table.columns:
                    value = cross_table.loc[idx, col]
                    if value > max_value:
                        max_value = value
                        max_combination = f"{idx} × {col}"
            
            results["交叉分析"] = {
                "分析维度": f"{cat1} × {cat2}",
                "最佳组合": max_combination,
                "最佳组合值": safe_convert_value(max_value),
                "交叉表维度": f"{len(cross_table.index)} × {len(cross_table.columns)}"
            }
        except:
            pass
    
    # 简单相关性分析
    if len(key_fields["数值字段"]) >= 2:
        numeric_data = df[key_fields["数值字段"][:3]].dropna()
        if len(numeric_data) > 1:
            corr_matrix = numeric_data.corr()
            
            # 找出最强相关性
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    field1 = corr_matrix.columns[i]
                    field2 = corr_matrix.columns[j]
                    corr_value = corr_matrix.iloc[i, j]
                    
                    if not pd.isna(corr_value) and abs(corr_value) > 0.5:
                        strong_correlations.append({
                            "字段1": field1,
                            "字段2": field2,
                            "相关系数": round(corr_value, 3),
                            "相关性": "强正相关" if corr_value > 0.5 else "强负相关"
                        })
            
            results["相关性分析"] = strong_correlations
    
    # 异常值检测
    if key_fields["数值字段"]:
        main_numeric = key_fields["数值字段"][0]
        data = df[main_numeric].dropna()
        
        if len(data) > 0:
            q1, q3 = data.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = data[(data < lower_bound) | (data > upper_bound)]
            
            results["异常值检测"] = {
                "检测字段": main_numeric,
                "异常值数量": len(outliers),
                "异常值比例": f"{(len(outliers)/len(data))*100:.1f}%",
                "正常范围": f"{lower_bound:.1f} ~ {upper_bound:.1f}"
            }
    
    return results

def generate_practical_insights(df, key_fields, analysis_results, business_scenario):
    """生成实用的业务洞察"""
    insights = []
    
    try:
        # 基于业务场景生成洞察
        if business_scenario == "销售分析":
            insights.extend(generate_sales_insights(df, key_fields, analysis_results))
        elif business_scenario == "产品分析":
            insights.extend(generate_product_insights(df, key_fields, analysis_results))
        elif business_scenario == "财务分析":
            insights.extend(generate_financial_insights(df, key_fields, analysis_results))
        else:
            insights.extend(generate_general_insights(df, key_fields, analysis_results))
            
    except Exception as e:
        insights.append(f"洞察生成过程中出现错误: {str(e)}")
        
    return insights

def generate_sales_insights(df, key_fields, analysis_results):
    """生成销售相关洞察"""
    insights = []
    
    if "排行榜" in analysis_results:
        for rank_name, rank_data in analysis_results["排行榜"].items():
            if rank_data:
                top_item = list(rank_data.keys())[0]
                top_value = rank_data[top_item]["总计"]
                insights.append(f"🏆 {rank_name}：{top_item}排名第一，总计{top_value:,.0f}")
    
    if "基础统计" in analysis_results:
        for field, stats in analysis_results["基础统计"].items():
            total = stats["总和"]
            avg = stats["平均值"]
            insights.append(f"💰 {field}业绩：总计{total:,.0f}，平均{avg:,.1f}")
    
    return insights

def generate_product_insights(df, key_fields, analysis_results):
    """生成产品相关洞察"""
    insights = []
    
    if "分组统计" in analysis_results:
        for group_name, group_data in analysis_results["分组统计"].items():
            if group_data:
                total_items = sum(group_data.values())
                top_item = max(group_data.items(), key=lambda x: x[1])
                insights.append(f"📦 {group_name}：共{total_items}个，其中{top_item[0]}数量最多({top_item[1]}个)")
    
    return insights

def generate_financial_insights(df, key_fields, analysis_results):
    """生成财务相关洞察"""
    insights = []
    
    if "基础统计" in analysis_results:
        for field, stats in analysis_results["基础统计"].items():
            if "成本" in field or "费用" in field:
                total = stats["总和"]
                insights.append(f"💸 {field}支出：总计{total:,.0f}")
            elif "收入" in field or "营收" in field:
                total = stats["总和"]
                insights.append(f"💰 {field}收入：总计{total:,.0f}")
    
    return insights

def generate_general_insights(df, key_fields, analysis_results):
    """生成通用洞察"""
    insights = []
    
    insights.append(f"📊 数据概览：{len(df)}条记录，{len(df.columns)}个字段")
    
    if key_fields["数值字段"]:
        insights.append(f"🔢 包含{len(key_fields['数值字段'])}个数值字段，可进行统计分析")
    
    if key_fields["分类字段"]:
        insights.append(f"🏷️ 包含{len(key_fields['分类字段'])}个分类字段，可进行分组分析")
    
    return insights
