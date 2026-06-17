"""
@file: MutiElementsSimulator.py
@brief: 多要素模拟器，协调土地、人口、GDP的多轮模拟
@author: Claude
@date: 2026-03-30
@version: 1.0
"""
import os
import shutil
from src.algorithms.LandSimulator import LandSimulator
from src.algorithms.PopulationSimulator import PopulationSimulator
from src.algorithms.GDPSimulator import GDPSimulator


"""
@class: SimulateResult
@brief: 模拟结果类，存储目标年份的土地、人口、GDP模拟结果路径
"""
class SimulateResult:
    """
    @brief: 初始化函数
    @param strTargetYearLandFunc: 目标年份土地利用结果路径
    @param strTargetYearPop: 目标年份人口结果路径
    @param strTargetYearGDP: 目标年份GDP结果路径
    """
    def __init__(self, strTargetYearLandFunc: str, strTargetYearPop: str, strTargetYearGDP: str):
        self.mStrTargetYearLandFunc = strTargetYearLandFunc
        self.mStrTargetYearPop = strTargetYearPop
        self.mStrTargetYearGDP = strTargetYearGDP


"""
@class: MutiElementsSimulator
@brief: 多要素模拟器类，协调土地、人口、GDP的多轮模拟
@see: 每轮模拟使用上一轮的结果作为输入，时间步长为5年
"""
class MutiElementsSimulator:
    """
    @brief: 初始化函数
    @param nTargetYear: 目标年份，必须是5的倍数
    @param nScenario: 发展态势（0-缓慢，1-自然，2-快速）
    @throw: ValueError - 如果nTargetYear不是5的倍数
    """
    def __init__(self, nTargetYear: int, nScenario: int):
        try:
            # 检查目标年份是否为5的倍数
            if nTargetYear % 5 != 0:
                raise ValueError(f"目标年份必须是5的倍数，当前输入: {nTargetYear}")
            self.mnTargetYear = nTargetYear
            self.mnScenario = nScenario
            self.mStrScenario = self.strGetScenarioName(nScenario)
            self.mStrInputDir = "D:/Data/data/simulation"
        except Exception as e:
            raise Exception(f"初始化失败: {e}") from e

    """
    @brief: 将最终模拟结果从临时文件夹移动到结果文件夹
    @param strLandPath: 土地结果路径
    @param strPopPath: 人口结果路径
    @param strGDPPath: GDP结果路径
    @return: 移动后的 (土地路径, 人口路径, GDP路径) 元组
    """
    def moveFinalResults(self, strLandPath: str, strPopPath: str, strGDPPath: str) -> tuple:
        try:
            # 构建目标路径
            strOutputDir = "D:/Data/result"
            strLandFileName = f"land_{self.mnTargetYear}_{self.mStrScenario}.tif"
            strPopFileName = f"pop_{self.mnTargetYear}_{self.mStrScenario}.tif"
            strGDPFileName = f"gdp_{self.mnTargetYear}_{self.mStrScenario}.tif"
            strNewLandPath = os.path.join(strOutputDir, strLandFileName)
            strNewPopPath = os.path.join(strOutputDir, strPopFileName)
            strNewGDPPath = os.path.join(strOutputDir, strGDPFileName)
            # 依次移动土地、人口、GDP文件至指定位置
            shutil.move(strLandPath, strNewLandPath)
            shutil.move(strPopPath, strNewPopPath)
            shutil.move(strGDPPath, strNewGDPPath)
            return strNewLandPath, strNewPopPath, strNewGDPPath
        except Exception as e:
            raise Exception(f"移动文件失败: {e}") from e

    """
    @brief: 获取情景名称
    @param nScenario: 发展态势值
    @return: 情景名称字符串
    """
    def strGetScenarioName(self, nScenario: int) -> str:
        try:
            if nScenario == 0:
                return "slow"
            elif nScenario == 1:
                return "natural"
            elif nScenario == 2:
                return "quick"
        except Exception as e:
            raise Exception(f"未知的发展态势值: {e}") from e

    """
    @brief: 构建初始数据路径（2025年基期数据）
    @return: 初始土地、人口、GDP数据路径元组
    """
    def tupleGetInitialDataPaths(self) -> tuple:
        try:
            # 2025年基期数据路径
            strBaseLandPath = f"{self.mStrInputDir}/land_2025_{self.mStrScenario}.tif"
            strBasePopPath = f"{self.mStrInputDir}/pop_2025_{self.mStrScenario}.tif"
            strBaseGDPPath = f"{self.mStrInputDir}/gdp_2025_{self.mStrScenario}.tif"
            return strBaseLandPath, strBasePopPath, strBaseGDPPath
        except Exception as e:
            raise Exception(f"未知的发展态势值: {e}") from e

    """
    @brief: 执行单轮模拟（一个5年周期）
    @param nNextYear: 目标年份
    @param strPrevLandPath: 上一期土地模拟结果路径
    @param strPrevPopPath: 上一期人口模拟结果路径
    @param strPrevGDPPath: 上一期GDP模拟结果路径
    @return: 元组 (土地结果路径, 人口结果路径, GDP结果路径)
    """
    def tupleRunSingleRound(self, nNextYear: int, strPrevLandPath: str, strPrevPopPath: str, strPrevGDPPath: str) -> tuple:
        try:
            # 步骤1: 土地模拟
            print(f"\n[1/3] 执行土地模拟...")
            landSimulator = LandSimulator(strPrevLandPath, strPrevPopPath, strPrevGDPPath, nNextYear, self.mnScenario)
            strLandResultPath = landSimulator.strRun()
            print(f"土地模拟完成: {strLandResultPath}")
            # 步骤2: 人口模拟（使用土地模拟结果）
            print(f"\n[2/3] 执行人口模拟...")
            popSimulator = PopulationSimulator(strLandResultPath, nNextYear, self.mnScenario)
            strPopResultPath = popSimulator.strRun()
            print(f"人口模拟完成: {strPopResultPath}")
            # 步骤3: GDP模拟（使用土地模拟结果）
            print(f"\n[3/3] 执行GDP模拟...")
            gdpSimulator = GDPSimulator(strLandResultPath, nNextYear, self.mnScenario)
            strGDPResultPath = gdpSimulator.strRun()
            print(f"GDP模拟完成: {strGDPResultPath}")
            return strLandResultPath, strPopResultPath, strGDPResultPath
        except Exception as e:
            raise Exception(f"单轮模拟运行失败: {e}") from e

    """
    @brief: 运行完整的多要素模拟流程
    @return: SimulateResult对象，包含目标年份的土地、人口、GDP结果路径
    """
    def run(self) -> SimulateResult:
        try:
            # 计算模拟轮数
            nRounds = (self.mnTargetYear - 2025) // 5
            if nRounds <= 0:
                raise ValueError(f"目标年份 {self.mnTargetYear} 必须大于2025")
            print(f"\n{'#'*70}")
            print(f"# 开始多要素模拟")
            print(f"# 目标年份: {self.mnTargetYear}")
            print(f"# 发展态势: {self.mStrScenario})")
            print(f"# 模拟轮数: {nRounds}")
            print(f"{'#'*70}")
            # 获取初始数据路径（2025年基期数据）
            strLandPath, strPopPath, strGDPPath = self.tupleGetInitialDataPaths()
            print(f"\n初始数据路径:")
            print(f" - 土地: {strLandPath}")
            print(f" - 人口: {strPopPath}")
            print(f" - GDP: {strGDPPath}")
            # 循环执行模拟
            for i in range(nRounds):
                nCurrentYear = 2025 + i * 5
                nNextYear = nCurrentYear + 5
                # 执行单轮模拟
                print(f"# 当前年份: {nCurrentYear}")
                strLandPath, strPopPath, strGDPPath = self.tupleRunSingleRound(nNextYear, strLandPath, strPopPath, strGDPPath)
            # 最后一轮：将结果从临时文件夹移动到结果文件夹
            print(f"\n{'='*60}")
            print(f"正在将最终结果移动到结果文件夹...")
            print(f"{'='*60}")
            strLandPath, strPopPath, strGDPPath = self.moveFinalResults(strLandPath, strPopPath, strGDPPath)
            print(f"\n{'#'*70}")
            print(f"# 多要素模拟全部完成!")
            print(f"# 最终年份: {self.mnTargetYear}")
            print(f"# 土地结果: {strLandPath}")
            print(f"# 人口结果: {strPopPath}")
            print(f"# GDP结果: {strGDPPath}")
            print(f"{'#'*70}")
            # 返回模拟结果
            result = SimulateResult(strLandPath, strPopPath, strGDPPath)
            return result
        except Exception as e:
            raise Exception(f"模拟运行失败: {e}") from e