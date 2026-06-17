from src.algorithms import GDPSimulator

if __name__ == "__main__":
    # 初始化GDP模拟器（自然增长情景）
    gdpSimulator = GDPSimulator(
        strTargetYearLandFunctionPath=r"D:\Data\result\tmp\land_2030_natural.tif",
        nTargetYear=2030,
        nScenario=1)
    # 运行GDP模拟
    resultPath = gdpSimulator.strRun()
    print(f"GDP模拟完成，结果保存在: {resultPath}")
