"""
@file: test_MutiElementsSimulator.py
@brief: MutiElementsSimulator测试文件，测试2030年三种发展态势
@author: Claude
@date: 2026-03-30
@version: 1.0
"""
from src.algorithms import MutiElementsSimulator

def main():
    """
    @brief: 测试2030年三种发展态势
    """
    target_year = 2030
    scenarios = [(0, "缓慢发展"),(1, "自然发展"),(2, "快速发展")]
    print("=" * 70)
    print(f"MutiElementsSimulator 测试 - 目标年份: {target_year}")
    print("=" * 70)
    for scenario_code, scenario_name in scenarios:
        print(f"\n{'#' * 70}")
        print(f"# 测试场景: {scenario_name} (code={scenario_code})")
        print(f"{'#' * 70}")
        try:
            simulator = MutiElementsSimulator(nTargetYear=target_year, nScenario=scenario_code)
            result = simulator.run()
            print(f"\n{scenario_name} 测试完成!")
            print(f"  土地结果: {result.mStrTargetYearLandFunc}")
            print(f"  人口结果: {result.mStrTargetYearPop}")
            print(f"  GDP结果: {result.mStrTargetYearGDP}")
        except Exception as e:
            print(f"\n{scenario_name} 测试失败: {e}")
            continue
    print(f"\n{'=' * 70}")
    print("所有测试完成")
    print("=" * 70)

if __name__ == "__main__":
    main()