from src.algorithms.ImprovedCA import ImprovedCA

def main():
    try:
        caModel = ImprovedCA(
            strPreviousLandFunctionPath = r"D:\Data\data\simulation\2025年土地功能模拟结果_自然.tif",
            strLandDevelopProbabilityPath = r"D:\Data\result\tmp\land_develop_2030_natural.tif",
            strBufferPath = r"D:\Data\data\simulation\圈层去水去公园_processed.tif",
            strTrafficPath = r"D:\Data\data\simulation\武汉建成区2020_交通小区提取_processed.tif",
            strCenterDistance = r"D:\Data\data\simulation\center_processed.tif",
            nTargetYear = 2030,
            nScenario = 1  # 1表示自然增长
        )
        resultPath = caModel.strRun()
        print(f"模拟完成，结果文件路径: {resultPath}")
    except Exception as e:
            raise Exception(f"ImprovedCA测试失败: {e}") from e

if __name__ == "__main__":
    main()