"""
智能数据分析系统测试脚本
"""

import pandas as pd
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intelligent_scenario_matcher import ScenarioMatcher
from scenario_prompt_engine import ScenarioPromptEngine

def test_scenario_matching():
    """测试场景匹配功能"""
    print("🔍 测试场景匹配功能...")
    
    # 创建测试数据
    # 电商数据
    ecommerce_data = pd.DataFrame({
        '商品名称': ['iPhone 14', 'Samsung Galaxy', 'Huawei P50', 'Xiaomi 12', 'OPPO Reno'],
        '品牌': ['Apple', 'Samsung', 'Huawei', 'Xiaomi', 'OPPO'], 
        '销量': [1000, 800, 600, 1200, 500],
        '价格': [6999, 5999, 4999, 3999, 3499],
        '类别': ['手机', '手机', '手机', '手机', '手机']
    })
    
    # 汽车数据
    auto_data = pd.DataFrame({
        '车型': ['Model Y', 'BYD Han', '理想ONE', '小鹏P7', 'BMW X3'],
        '品牌': ['Tesla', 'BYD', '理想', '小鹏', 'BMW'],
        '销量': [2000, 1500, 1200, 1000, 800],
        '售价': [30, 25, 35, 28, 45],
        '配置': ['长续航', '旗舰版', '增程版', '鹏翼版', '豪华版']
    })
    
    # 财务数据
    finance_data = pd.DataFrame({
        '部门': ['销售部', '市场部', '研发部', '运营部', '财务部'],
        '收入': [5000000, 3000000, 2000000, 1500000, 500000],
        '成本': [3000000, 2000000, 1800000, 1200000, 400000],
        '利润': [2000000, 1000000, 200000, 300000, 100000],
        '预算': [5500000, 3200000, 2200000, 1600000, 600000]
    })
    
    # 测试场景匹配器
    matcher = ScenarioMatcher()
    
    test_cases = [
        ("电商数据", ecommerce_data),
        ("汽车数据", auto_data), 
        ("财务数据", finance_data)
    ]
    
    for name, data in test_cases:
        print(f"\n📊 测试数据集：{name}")
        print(f"数据规模：{len(data)}行 x {len(data.columns)}列")
        print(f"字段：{list(data.columns)}")
        
        # 场景匹配
        best_scenario, confidence, match_details = matcher.match_best_scenario(data)
        
        print(f"✅ 匹配结果：{best_scenario}")
        print(f"🎯 置信度：{confidence:.3f}")
        print(f"📋 所有评分：")
        for scenario, score in match_details["all_scores"].items():
            print(f"   - {scenario}: {score:.3f}")
        
        print("-" * 50)
    
    return True

def test_prompt_generation():
    """测试提示词生成功能"""
    print("\n📝 测试提示词生成功能...")
    
    # 创建电商测试数据
    data = pd.DataFrame({
        '商品名称': ['iPhone 14', 'Samsung Galaxy', 'Huawei P50'],
        '品牌': ['Apple', 'Samsung', 'Huawei'],
        '销量': [1000, 800, 600],
        '价格': [6999, 5999, 4999]
    })
    
    # 创建提示词引擎
    prompt_engine = ScenarioPromptEngine()
    matcher = ScenarioMatcher()
    
    # 匹配场景
    best_scenario, confidence, match_details = matcher.match_best_scenario(data)
    
    print(f"场景：{best_scenario} (置信度: {confidence:.3f})")
    
    # 生成提示词
    enhanced_prompt = prompt_engine.generate_scenario_prompt(
        scenario=best_scenario,
        df=data,
        match_details=match_details,
        custom_requirements="请特别关注品牌竞争力分析"
    )
    
    print(f"\n📏 生成的提示词长度：{len(enhanced_prompt)} 字符")
    print(f"📋 提示词前500字符预览：")
    print(enhanced_prompt[:500] + "...")
    
    # 生成可视化补充
    viz_supplement = prompt_engine.create_visualization_prompt_supplement(data, best_scenario)
    print(f"\n📊 可视化补充长度：{len(viz_supplement)} 字符")
    
    return True

def test_data_fingerprint():
    """测试数据指纹分析功能"""
    print("\n🔍 测试数据指纹分析功能...")
    
    # 创建复杂的测试数据
    data = pd.DataFrame({
        '产品ID': ['P001', 'P002', 'P003', 'P004'],
        '产品名称': ['笔记本电脑', '智能手机', '平板电脑', '智能手表'],
        '品牌': ['联想', '华为', '小米', '苹果'],
        '销量': [500, 1200, 800, 300],
        '单价': [4999.0, 3999.0, 2999.0, 2499.0],
        '上市时间': pd.to_datetime(['2023-01-15', '2023-03-20', '2023-05-10', '2023-07-01']),
        '库存': [50, 200, 150, 80]
    })
    
    matcher = ScenarioMatcher()
    
    # 分析数据指纹
    fingerprint = matcher.analyze_data_fingerprint(data)
    
    print("📊 数据指纹分析结果：")
    print(f"字段特征：{len(fingerprint['field_features']['field_names'])}个字段")
    print(f"数据规模：{fingerprint['content_features']['row_count']}行")
    print(f"数值字段：{fingerprint['statistical_features']['numeric_field_count']}个")
    print(f"分类字段：{fingerprint['statistical_features']['categorical_field_count']}个")
    print(f"复杂度评分：{fingerprint['statistical_features']['complexity_score']:.2f}")
    
    print("\n🎯 业务领域信号强度：")
    for domain, strength in fingerprint['semantic_features']['business_domain_signals'].items():
        print(f"   - {domain}: {strength:.3f}")
    
    print("\n📈 分析潜力评估：")
    for analysis_type, potential in fingerprint['semantic_features']['analysis_potential'].items():
        print(f"   - {analysis_type}: {potential:.3f}")
    
    return True

def main():
    """主测试函数"""
    print("🚀 启动智能数据分析系统测试")
    print("=" * 60)
    
    try:
        # 测试场景匹配
        test_scenario_matching()
        
        # 测试提示词生成  
        test_prompt_generation()
        
        # 测试数据指纹
        test_data_fingerprint()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！智能分析系统运行正常")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()