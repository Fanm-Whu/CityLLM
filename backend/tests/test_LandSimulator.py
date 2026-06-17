"""
@file: test_LandSimulator.py
@brief: LandSimulator 类的测试文件
@author: 樊明
@date: 2026-02-08
@version: 1.0
"""
import os
from src.algorithms import LandSimulator

def vTestLandDevelopProbability():
    # 测试用例：预测2030年自然增长情景
    # 请替换为你的实际文件路径（确保文件存在）
    previous_land_path = r"D:\Data\data\simulation\land_2025_natural.tif"
    previous_pop_path  = r"D:\Data\data\simulation\pop_2025_natural.tif"
    previous_gdp_path  = r"D:\Data\data\simulation\gdp_2025_natural.tif"
    # 检查文件是否存在（防止运行时崩溃）
    for path in [previous_land_path, previous_pop_path, previous_gdp_path]:
        if not os.path.exists(path):
            print(f"文件不存在，无法测试: {path}")
            return
    try:
        # 1. 实例化 LandSimulator
        simulator = LandSimulator(
            strPreviousLandSimuResultPath=previous_land_path,
            strPreviousPopSimuResultPath=previous_pop_path,
            strPreviousGDPSimuResultPath=previous_gdp_path,
            nTargetYear=2030,
            nScenario=1)
        print("LandSimulator 初始化成功，开始生成2030年土地发展概率...")
        # 2. 调用核心方法
        output_path = simulator.strRun()
        # 3. 输出结果
        if os.path.exists(output_path):
            print(f"测试成功！")
            print(f"土地利用模拟结果文件已生成: ")
            print(f"  → {output_path}")
            print(f"文件大小：{os.path.getsize(output_path) / (1024 * 1024):.2f} MB")
        else:
            print("输出文件未生成，请检查运行日志。")
    except ValueError as ve:
        print("值错误：", ve)
    except Exception as e:
        print("运行时异常：", e)


if __name__ == "__main__":
    print("=" * 60)
    print("          LandSimulator 测试程序")
    print("=" * 60)
    vTestLandDevelopProbability()