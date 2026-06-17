from src.algorithms import PopulationSimulator

if __name__ == "__main__":
    # 初始化人口模拟器（缓慢增长情景）
    popSimulator = PopulationSimulator(
        strTargetYearLandFunctionPath=r"D:\Data\result\tmp\land_2030_natural.tif",
        nTargetYear=2030,
        nScenario=1)
    # 运行人口模拟
    resultPath = popSimulator.strRun()
    print(f"人口模拟完成，结果保存在: {resultPath}")