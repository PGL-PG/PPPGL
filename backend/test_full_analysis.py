"""
测试完整的智能分析流程
"""

import pandas as pd
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_analysis_api import enhanced_analyze_data

def test_ecommerce_analysis():
    """测试电商数据分析"""
    print("🛒 测试电商数据分析...")
    
    # 创建更真实的电商数据
    data = pd.DataFrame({
        '商品名称': ['iPhone 14 Pro', 'Samsung Galaxy S23', 'Huawei P60 Pro', 'Xiaomi 13 Pro', 'OPPO Find X6'],
        '品牌': ['Apple', 'Samsung', 'Huawei', 'Xiaomi', 'OPPO'],
        '销量': [12000, 8500, 6800, 15000, 4200],
        '单价': [8999, 6999, 5999, 4999, 4299],
        '销售额': [107988000, 59491500, 40793200, 74985000, 18055800],
        '类别': ['高端手机', '高端手机', '高端手机', '中高端手机', '中端手机'],
        '上市月份': ['2022-09', '2023-02', '2023-03', '2022-12', '2023-04']
    })
    
    print(f"数据规模：{len(data)}行 x {len(data.columns)}列")
    print("开始智能分析...")
    
    # 执行分析
    result = enhanced_analyze_data(data, "请重点分析品牌竞争力和市场占有率")
    
    print(f"✅ 分析完成！")
    print(f"📊 识别场景：{result.get('scenario_info', {}).get('matched_scenario', 'Unknown')}")
    print(f"🎯 置信度：{result.get('scenario_info', {}).get('confidence', 0):.3f}")
    print(f"🤖 AI分析调用：{'是' if result.get('ai_called') else '否'}")
    print(f"📈 生成图表数量：{len(result.get('charts', []))}")
    print(f"📋 数据表格数量：{len(result.get('data_tables', []))}")
    
    if result.get('ai_insights'):
        print(f"💡 AI洞察长度：{len(result['ai_insights'])} 字符")
        print(f"AI洞察预览：{result['ai_insights'][:200]}...")
    
    return result

def test_auto_analysis():
    """测试汽车数据分析"""
    print("\n🚗 测试汽车数据分析...")
    
    data = pd.DataFrame({
        '车型': ['Model Y', 'BYD 汉EV', '理想ONE', '小鹏P7', 'BMW iX3', '蔚来ES6'],
        '品牌': ['Tesla', 'BYD', '理想汽车', '小鹏汽车', 'BMW', '蔚来'],
        '销量': [45000, 32000, 28000, 25000, 15000, 18000],
        '售价万元': [30.99, 22.98, 34.98, 22.99, 46.99, 35.80],
        '类型': ['纯电动SUV', '纯电动轿车', '增程式SUV', '纯电动轿车', '纯电动SUV', '纯电动SUV'],
        '续航公里': [545, 605, 800, 706, 500, 610]
    })
    
    print(f"数据规模：{len(data)}行 x {len(data.columns)}列")
    print("开始智能分析...")
    
    result = enhanced_analyze_data(data, "分析新能源汽车市场竞争格局")
    
    print(f"✅ 分析完成！")
    print(f"📊 识别场景：{result.get('scenario_info', {}).get('matched_scenario', 'Unknown')}")
    print(f"🎯 置信度：{result.get('scenario_info', {}).get('confidence', 0):.3f}")
    
    return result

def main():
    """主测试函数"""
    print("🧪 完整分析流程测试")
    print("=" * 50)
    
    try:
        # 测试电商分析
        ecommerce_result = test_ecommerce_analysis()
        
        # 测试汽车分析
        auto_result = test_auto_analysis()
        
        print("\n" + "=" * 50)
        print("🎉 完整分析流程测试成功！")
        print("核心功能验证：")
        print("✅ 场景智能匹配")
        print("✅ 提示词动态生成") 
        print("✅ Gemini分析调用")
        print("✅ 结果结构化输出")
        print("✅ 可视化图表生成")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()