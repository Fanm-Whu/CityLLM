"""
@file: GDPSimulator.py
@brief: GDP模拟文件，包括GDPSimulator类，用于预测GDP密度和分配GDP
@author: 樊明
@date: start: 2026-02-11; end: 2026-02-11
@version: 1.0
"""
import GPy
from GPy.util.multioutput import ICM
import numpy as np
from osgeo import gdal
import warnings
from tqdm import tqdm
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 强制使用非交互式后端，避免在Flask环境中卡住
import matplotlib.pyplot as plt
import os
from src.algorithms.SimulateHelper import predictGDP
from src.algorithms.GeoProcessor import strNormalizeRaster
warnings.filterwarnings('ignore')


"""
@class: GDPSimulator
@brief: GDP模拟类，基于高斯过程回归预测GDP密度，基于循环模拟算法分配GDP
@see: 使用土地功能模拟结果作为输入
"""
class GDPSimulator:
    """
    @brief: 初始化函数
    @param strTargetYearLandFunctionPath: 目标年份土地功能模拟结果路径
    @param nTargetYear: 目标年份
    @param nScenario: 模拟情景（0-缓慢，1-自然，2-快速）
    @see: 使用了strGetScenarioName()、vSetScenarioParameters()两个辅助函数
    """
    def __init__(self, strTargetYearLandFunctionPath: str, nTargetYear: int, nScenario: int,):
        self.mStrInputDir = "D:/Data/data/simulation"  # GDP模拟过程中的静态数据文件夹
        self.mStrBufferPath = f"{self.mStrInputDir}/圈层去水去公园_processed.tif"  # 缓冲区路径
        self.mStrBaseYearGDPDensityPath = f"{self.mStrInputDir}/gdpdensity_2020.tif"  # 基期GDP密度数据
        self.mStrBaseYearGDPPath = f"{self.mStrInputDir}/gdp_2020.tif"  # 基期GDP数据
        self.mStrTargetYearLandFunctionPath = strTargetYearLandFunctionPath  # 目标年份土地利用模拟结果
        self.mnTargetYear = nTargetYear  # 目标年份
        self.mnScenario = nScenario  # 发展态势
        self.mStrScenario = self.strGetScenarioName()  # 设置发展态势str
        self.mStrOutputDir = "D:/Data/result/tmp"
        self.mnTargetYearGDP = predictGDP(self.mnTargetYear)  # 最大GDP增加值
        self.vSetScenarioParams()  # 根据发展态势设置参数
        self.vLoadBaseData(self.mStrBufferPath, self.mStrBaseYearGDPDensityPath, self.mStrTargetYearLandFunctionPath)  # 加载内部变量
        # 结果路径
        self.mStrGDPDensityPath = ""
        self.mStrFinalGDPAllocationPath = ""

    """
    @brief: 获取情景名称
    @see: 是__init__()的辅助函数
    @return: 情景名称字符串
    """
    def strGetScenarioName(self) -> str:
        if self.mnScenario == 0:
            return "slow"
        elif self.mnScenario == 1:
            return "natural"
        elif self.mnScenario == 2:
            return "quick"

    """
    @brief: 根据情景设置参数
    @see: 是__init__()的辅助函数
    """
    def vSetScenarioParams(self):
        if self.mnScenario == 0:  # 缓慢增长
            self.mBreaks = [0, 100, 300, 500, 1000, 1500, 2000, 3000, 3521]
            self.mDensityBreak = [0.127625033, 0.203389367, 0.256514939, 0.300682368, 0.325891655, 0.400545895, 0.553048183, 1]
        elif self.mnScenario == 1:  # 自然增长
            self.mBreaks = [0, 100, 300, 500, 1000, 1500, 2000, 3000, 3521]
            self.mDensityBreak = [0.107625033, 0.303389367, 0.326514939, 0.350682368, 0.405891655, 0.500545895, 0.633048183, 1]
        elif self.mnScenario == 2:  # 快速增长
            self.mBreaks = [0, 100, 300, 500, 1000, 1500, 2000, 3000, 3521]
            self.mDensityBreak = [0.197625033, 0.363389367, 0.406514939, 0.450682368, 0.505891655, 0.560545895, 0.663048183, 1]

    """
    @brief: 加载基础数据
    @see: 是strGenerateGDPDensity()和strAllocateGDP()的辅助函数
    """
    def vLoadBaseData(self, strBufferPath: str, strBaseYearGDPDensPath: str, strTargetYearLandFuncPath: str):
        # 加载缓冲区
        buffer = gdal.Open(strBufferPath)
        self.mBuffer = buffer.GetRasterBand(1).ReadAsArray().astype(float)
        # 加载基期GDP密度
        gdpDense = gdal.Open(strBaseYearGDPDensPath)
        self.mBaseGDPDens = gdpDense.GetRasterBand(1).ReadAsArray().astype(float)
        # 加载目标年份土地功能
        targetYearLandFunc = gdal.Open(strTargetYearLandFuncPath)
        self.mLandFunction = targetYearLandFunc.GetRasterBand(1).ReadAsArray().astype(float)
        # 获取投影和尺寸信息
        self.mWidth = buffer.RasterXSize
        self.mHeight = buffer.RasterYSize
        self.mGeotransform = buffer.GetGeoTransform()
        self.mProjection = buffer.GetProjection()
        # 处理nodata值和无效值
        self.mLandFunction[self.mLandFunction < 0] = 0
        # 清理GDP密度数据中的无效值
        self.mBaseGDPDens = np.nan_to_num(self.mBaseGDPDens, nan=0.0, posinf=0.0, neginf=0.0)

    """
    @brief: 加载驱动因子数据
    @return: 驱动因子数据列表
    @see: 是strGenerateGDPDensity()的辅助函数
    """
    def vLoadDrivingFactors(self):
        # 驱动因子文件名列表
        drivingFactorFiles = [
            "所有poi密度_标准化_processed.tif",
            "便利设施密度_标准化_processed.tif",
            "公共设施密度_标准化_processed.tif",
            "公司企业密度_标准化_processed.tif",
            "primary_processed.tif",
            "secondary_processed.tif",
            "teitiary_processed.tif",
            "motorway_processed.tif",
            "center_processed.tif",
            "water_processed.tif",
            "train_airport_processed.tif",
            "hightway_processed.tif",
            "DEM_processed.tif",
            "slope_processed.tif"]
        drivingFactorList = []
        for file in drivingFactorFiles:
            filePath = f"{self.mStrInputDir}/{file}"
            inDs = gdal.Open(filePath)
            inBand = inDs.GetRasterBand(1)
            data = inBand.ReadAsArray().astype(float)
            # 清洗数据：将nan和inf替换为0
            data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
            drivingFactorList.append(data)
        return drivingFactorList

    """
    @brief: 随机抽样函数
    @param X: 特征数据
    @param Y: 标签数据
    @param sampleSize: 抽样大小
    @return: 抽样后的特征和标签数据
    @see: 是strGenerateGDPDensity()的辅助函数
    """
    def randomSample(self, X, Y, sampleSize):
        # 原始随机抽样函数的实现
        assert len(X) == len(Y)
        if len(X) > sampleSize:
            indices = np.random.choice(len(X), sampleSize, replace=False)
        else:
            indices = np.arange(len(X))
        return X[indices], Y[indices]

    """
    @brief: 生成GDP密度预测图
    @return: GDP密度预测图文件路径
    @throw: ValueError - 文件加载失败或数据不一致
    @throw: Exception - 其他运行时错误
    @see: 使用了vLoadBaseData(), vLoadDrivingFactors(), randomSample()三个辅助函数
    """
    def strGenerateGDPDensity(self) -> str:
        try:
            drivingFactorList = self.vLoadDrivingFactors()  # 加载驱动因子
            # 按土地类型提取数据
            landTypes = [0, 1, 2, 3, 4]
            XList, YList = [], []
            for landType in landTypes:
                # 传统循环构建驱动因子列列表
                factor_columns = []
                for i in range(len(drivingFactorList)):
                    col = drivingFactorList[i][self.mLandFunction == landType].reshape(-1, 1)
                    factor_columns.append(col)
                X = np.hstack(factor_columns)
                Y = self.mBaseGDPDens[self.mLandFunction == landType].reshape(-1, 1)
                # 清洗Y值：去除nan和inf，确保非负
                Y = np.nan_to_num(Y, nan=0.0, posinf=0.0, neginf=0.0)
                Y = np.clip(Y, 0, None)
                XList.append(X)
                YList.append(Y)
            # 标记土地类型
            indexList = []
            for i, Y in enumerate(YList):
                index = np.ones_like(Y) * i
                indexList.append(index)
            # 构建带索引的输入数据
            XIndexedList = []
            for i in range(len(XList)):
                XIndexed = np.hstack((XList[i], indexList[i]))
                XIndexedList.append(XIndexed)
            print('总数据集输入完毕')
            print('开始随机抽样')
            # 随机抽样（每类土地800个样本）
            XSampledList, YSampledList = [], []
            for X, Y in zip(XList, YList):
                XSampled, YSampled = self.randomSample(X, Y, 800)
                XSampledList.append(XSampled)
                YSampledList.append(YSampled)
            # 标记抽样数据
            indexSampledList = []
            for i, YSampled in enumerate(YSampledList):
                indexSampled = np.ones_like(YSampled) * i
                indexSampledList.append(indexSampled)
            # 构建带索引的抽样数据
            XIndexedSampledList = []
            for i in range(len(XSampledList)):
                XIndexedSampled = np.hstack((XSampledList[i], indexSampledList[i]))
                XIndexedSampledList.append(XIndexedSampled)
            # 定义高斯过程回归模型
            numOutputs = 5  # 5种土地功能类型
            kernel = GPy.kern.RBF(input_dim=14, active_dims=np.arange(14))
            icmKernel = ICM(input_dim=14, num_outputs=numOutputs, kernel=kernel)
            model = GPy.models.GPCoregionalizedRegression(XIndexedSampledList, YSampledList, kernel=icmKernel)
            model.optimize('bfgs', max_iters=100, messages=True)  # 模型优化
            # 批量预测函数
            def predictInBatches(gpModel, XNew, baseIndex, batchSize=100):
                numSamples = XNew.shape[0]
                numBatches = np.ceil(numSamples / batchSize).astype(int)
                predMeans, predVars = [], []
                for i in range(numBatches):
                    start = i * batchSize
                    end = min((i + 1) * batchSize, numSamples)
                    YMetadataBatch = {'output_index': baseIndex[start:end].astype(int)}
                    predMean, predVar = gpModel.predict(XNew[start:end], Y_metadata=YMetadataBatch)
                    predMeans.append(predMean)
                    predVars.append(predVar)
                return np.vstack(predMeans), np.vstack(predVars)
            # 对每种土地类型进行预测
            predMeansList = []
            batchSize = 200
            for landType in landTypes:
                XNew = XIndexedList[landType]
                baseIndex = np.zeros(XList[landType].shape[0]).astype(int)
                predMean, _ = predictInBatches(model, XNew, baseIndex, batchSize=batchSize)
                predMeansList.append(predMean)
            # 构建预测GDP密度栅格
            predictedGDP = np.zeros(self.mBuffer.shape)
            # 将每种土地功能类型的预测GDP密度映射到对应位置
            for i, landType in enumerate(landTypes):
                predictedGDP[self.mLandFunction == landType] = predMeansList[i][:, 0]
            print(predictedGDP.shape)
            # 最小-最大标准化
            gdpMin = predictedGDP.min()
            gdpMax = predictedGDP.max()
            gdpNormalized = (predictedGDP - gdpMin) / (gdpMax - gdpMin)
            # 保存人口密度预测图
            driver = gdal.GetDriverByName('GTiff')
            outputFilename = f"gdpdensity_{self.mnTargetYear}_{self.mStrScenario}.tif"
            self.mStrGDPDensityPath = f"{self.mStrOutputDir}/{outputFilename}"
            outDs = driver.Create(self.mStrGDPDensityPath, self.mWidth, self.mHeight, 1, gdal.GDT_Float32)
            outDs.SetGeoTransform(self.mGeotransform)
            outDs.SetProjection(self.mProjection)
            outDs.WriteArray(gdpNormalized)
            outDs.FlushCache()
            outDs = None
            # 强制垃圾回收，确保GDAL释放文件句柄
            import gc
            gc.collect()
            # 等待文件系统同步（Windows需要）
            import time
            time.sleep(0.5)
            # 验证文件是否真的写入成功
            if not os.path.exists(self.mStrGDPDensityPath):
                raise Exception(f"文件写入后不存在: {self.mStrGDPDensityPath}")
            print(f"GDP密度文件已生成: {self.mStrGDPDensityPath}")
            return self.mStrGDPDensityPath
        except ValueError as e:
            raise ValueError(f"GDP密度预测失败: {e}") from e
        except Exception as e:
            raise Exception(f"GDP密度预测失败: {e}") from e

    """
    @brief: 计算三角分布的基础值
    @param i: 类别索引
    @param breaks: 断点列表
    @param didCoff: 三角分布参数
    @return: 最小值、最大值、众数
    @see: 被strAllocateGDP()调用
    """
    def calculateValuesBase(self, i, breaks, didCoff):
        # 原始三角分布计算函数的实现
        minValue = breaks[i] if i > 0 else 0
        maxValue = breaks[i + 1] if i < len(breaks) - 1 else breaks[i]
        modeValue = minValue + (maxValue - minValue) / didCoff
        return minValue, maxValue, modeValue

    """
    @brief: 权重分配函数
    @param rows: 行索引
    @param cols: 列索引
    @param densityData: 密度数据
    @param valuesRangeData: 值范围数据
    @return: 分配结果
    @see: 被strAllocateGDP()调用
    """
    def weightedAllocation(self, rows, cols, densityData, valuesRangeData):
        # 原始权重分配函数的实现
        weights = densityData[rows, cols]
        exponentialWeights = np.power(weights, 3)
        normalizedWeights = exponentialWeights / np.sum(exponentialWeights)
        # 高值优先
        valuesRangeData = np.sort(valuesRangeData)[::-1]
        allocations = np.random.choice(valuesRangeData, size=len(rows), replace=True, p=normalizedWeights)
        return allocations

    """
    @brief: 调整密度断点
    @param densityBreak: 密度断点列表
    @param increaseLow: 是否增加低等级区间长度
    @param adjustmentFactor: 调整因子
    @param minIntervalLength: 最小区间长度
    @param highGradeMinLength: 高等级最小区间长度
    @return: 调整后的密度断点列表
    @see: 被strAllocateGDP()调用
    """
    def adjustDensityBreaks(self, densityBreak, increaseLow, adjustmentFactor, minIntervalLength=0.02, highGradeMinLength=0.05):
        # 原始密度断点调整函数的实现
        nBreaks = len(densityBreak)
        adjustmentFactors = np.linspace((nBreaks - 1) / 2, 1, nBreaks - 1) * adjustmentFactor
        if increaseLow:
            # 增加低等级区间长度
            for i in range(1, nBreaks - 1):
                densityBreak[i] += adjustmentFactors[i - 1] / nBreaks
        else:
            # 减少低等级区间长度（更激进的调整）
            for i in range(nBreaks - 2, 0, -1):
                densityBreak[i] -= adjustmentFactors[::-1][i - 1] / nBreaks * 3
        densityBreak = np.clip(np.sort(densityBreak), 0, 1)
        # 确保区间长度（使用更小的最小区间长度，允许更大调整空间）
        for i in range(1, nBreaks):
            if i < nBreaks - 1:
                requiredMinLength = minIntervalLength
            else:
                requiredMinLength = highGradeMinLength
            if densityBreak[i] - densityBreak[i - 1] < requiredMinLength:
                densityBreak[i] = min(densityBreak[i - 1] + requiredMinLength, 1)
        densityBreak = np.clip(np.sort(densityBreak), 0, 1)
        print('调整后密度划分区间为', densityBreak)
        return densityBreak

    """
    @brief: 输出误差值到Excel并绘制误差变化图
    @param errorValues: 误差值列表
    @see: 被strAllocateGDP()调用
    """
    def vOutputErrorValues(self, errorValues: list):
        # 输出误差值到Excel
        dfErrorValues = pd.DataFrame(errorValues, columns=['Error Value'])
        errorExcelPath = f"{self.mStrOutputDir}/error_values_gdp_{self.mnTargetYear}{self.mStrScenario}.xlsx"
        dfErrorValues.to_excel(errorExcelPath, index=False)
        print(f"误差值已保存到: {errorExcelPath}")
        # 绘制误差变化图
        plt.figure(figsize=(10, 6))
        plt.plot(errorValues)
        plt.xlabel('Iteration')
        plt.ylabel('Error Value')
        plt.title('Error Values Over Iterations')
        errorPlotPath = f"{self.mStrOutputDir}/error_values_gdp_{self.mnTargetYear}{self.mStrScenario}.png"
        plt.savefig(errorPlotPath)
        plt.close()
        print(f"误差变化图已保存到: {errorPlotPath}")

    """
    @brief: 生成GDP分配结果
    @return: GDP分配结果文件路径
    @throw: ValueError - 文件加载失败或数据不一致
    @throw: Exception - 其他运行时错误
    @see: 调用calculateValuesBase(), weightedAllocation(), adjustDensityBreaks(), vOutputErrorValues()
    """
    def strAllocateGDP(self) -> str:
        try:
            if not self.mStrGDPDensityPath:
                raise ValueError("请先生成GDP密度预测图")
            # 检查文件是否存在
            if not os.path.exists(self.mStrGDPDensityPath):
                raise ValueError(f"GDP密度文件不存在: {self.mStrGDPDensityPath}")
            # 打开文件并检查是否成功
            gdpDensityDs = gdal.Open(self.mStrGDPDensityPath)
            if gdpDensityDs is None:
                raise ValueError(f"无法打开GDP密度文件: {self.mStrGDPDensityPath}")
            targetYearGDPDensity = gdpDensityDs.GetRasterBand(1).ReadAsArray().astype(float)
            # 加载基期GDP数据
            dataset = gdal.Open(self.mStrBaseYearGDPPath)
            baseYearGDP = dataset.GetRasterBand(1).ReadAsArray().astype(float)
            # 处理nodata值
            nodataValue = dataset.GetRasterBand(1).GetNoDataValue()
            if nodataValue is not None:
                baseYearGDP[baseYearGDP == nodataValue] = 0
                targetYearGDPDensity[targetYearGDPDensity == nodataValue] = 0
            # 标记不可居住区域
            targetYearGDPDensity[(self.mLandFunction == 0)] = -100
            # 原始allocateGDP函数的实现
            totalToleranceError = self.mnTargetYearGDP * 0.05
            allocationAttempts = 0
            errorValues = []
            newGDP = np.zeros_like(targetYearGDPDensity, dtype=float)
            # 确保mDensityBreak是numpy数组以便正确更新
            self.mDensityBreak = np.array(self.mDensityBreak, dtype=float)
            while allocationAttempts < 80 or (len(errorValues) > 5 and np.std(errorValues[-5:]) < 2000):
                newGDP = np.zeros_like(targetYearGDPDensity, dtype=float)
                totalGDPAllocated = 0
                with tqdm(total=self.mnTargetYearGDP) as pbar:
                    for i, mean in enumerate(self.mDensityBreak):
                        lowerBound = self.mDensityBreak[i - 1] if i > 0 else 0
                        upperBound = self.mDensityBreak[i] if i < len(self.mDensityBreak) else targetYearGDPDensity.max() + 1
                        mask = (targetYearGDPDensity >= lowerBound) & (targetYearGDPDensity < upperBound)
                        rows, cols = np.where(mask)
                        selectedDensities = targetYearGDPDensity[rows, cols]
                        # 按密度从高到低排序
                        sortedIndices = np.argsort(selectedDensities)[::-1]
                        sortedRows, sortedCols = rows[sortedIndices], cols[sortedIndices]
                        if len(sortedRows) == 0:
                            continue
                        # 计算三角分布参数
                        minValue, maxValue, modeValue = self.calculateValuesBase(i, self.mBreaks, 6)
                        valuesBase = np.random.triangular(left=minValue, mode=modeValue,
                                                        right=maxValue, size=len(sortedRows))
                        # 权重分配
                        allocations = self.weightedAllocation(sortedRows, sortedCols, targetYearGDPDensity, valuesBase)
                        # 更新GDP数据
                        for j, val in enumerate(allocations):
                            newGDP[rows[j], cols[j]] += val
                            totalGDPAllocated += val
                            pbar.update(val)
                # 计算误差值并记录（减去容差，与原始代码一致）
                errorValue = np.abs(totalGDPAllocated - self.mnTargetYearGDP)
                errorValues.append(errorValue)
                # 检查是否超过容差范围
                if errorValue > totalToleranceError:
                    # 根据误差方向决定调整策略
                    if totalGDPAllocated > self.mnTargetYearGDP:
                        # GDP高于目标，增加低等级区间长度（降低GDP）
                        self.mDensityBreak = self.adjustDensityBreaks(self.mDensityBreak, increaseLow=True, adjustmentFactor=0.01)
                    else:
                        # GDP低于目标，减少低等级区间长度（提高GDP）
                        self.mDensityBreak = self.adjustDensityBreaks(self.mDensityBreak, increaseLow=False, adjustmentFactor=0.01)
                    print(f'当前GDP为 {totalGDPAllocated:.2f}, GDP误差为 {errorValue/self.mnTargetYearGDP:.2f}')
                    print(f'目前密度划分区间为 {self.mDensityBreak}')
                else:
                    print(f'最终GDP误差为 {errorValue/self.mnTargetYearGDP:.2f}')
                    break
                allocationAttempts += 1
            # 输出误差值到Excel并绘制误差变化图
            self.vOutputErrorValues(errorValues)
            # 保存结果
            driver = gdal.GetDriverByName('GTiff')
            outputFilename = f"predict_gdp_{self.mnTargetYear}_{self.mStrScenario}.tif"
            self.mStrFinalGDPAllocationPath = f"{self.mStrOutputDir}/{outputFilename}"
            outDs = driver.Create(self.mStrFinalGDPAllocationPath, self.mWidth, self.mHeight, 1, gdal.GDT_Float32)
            outDs.SetGeoTransform(self.mGeotransform)
            outDs.SetProjection(self.mProjection)
            outDs.WriteArray(newGDP)
            outDs.FlushCache()
            outDs = None
            return self.mStrFinalGDPAllocationPath
        except ValueError as e:
            raise ValueError(f"GDP分配失败: {e}") from e
        except Exception as e:
            raise Exception(f"GDP分配失败: {e}") from e

    """
    @brief: 运行完整的GDP模拟流程
    @return: GDP分配结果文件路径
    @see: 调用strGenerateGDPDensity()和strAllocateGDP()
    """
    def strRun(self) -> str:
        # GDP密度预测
        gdpDensityPath = self.strGenerateGDPDensity()
        print(f"GDP密度预测完成: {gdpDensityPath}")
        # 分配GDP
        gdpAllocationPath = self.strAllocateGDP()
        print(f"GDP分配完成: {gdpAllocationPath}")
        return gdpAllocationPath
