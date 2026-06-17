"""
@file: PopulationSimulator.py
@brief: 人口模拟文件，包括PopulationSimulator类，用于预测人口密度和分配人口
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
import matplotlib.pyplot as plt
import os
from src.algorithms.SimulateHelper import predictPopulation
from src.algorithms.GeoProcessor import strNormalizeRaster
warnings.filterwarnings('ignore')


"""
@class: PopulationSimulator
@brief: 人口模拟类，基于高斯过程回归预测人口密度，基于循环模拟算法分配人口
@see: 使用土地功能模拟结果作为输入
"""
class PopulationSimulator:
    """
    @brief: 初始化函数
    @param strTargetYearLandFunctionPath: 目标年份土地功能模拟结果路径
    @param nTargetYear: 目标年份
    @param nScenario: 模拟情景（0-缓慢，1-自然，2-快速）
    @see: 使用了strGetScenarioName()、vSetScenarioParameters()两个辅助函数
    """
    def __init__(self, strTargetYearLandFunctionPath: str, nTargetYear: int, nScenario: int,):
        self.mStrInputDir = "D:/Data/data/simulation"  # 人口模拟过程中的静态数据文件夹
        self.mStrBufferPath = f"{self.mStrInputDir}/圈层去水去公园_processed.tif"  # 缓冲区路径
        self.mStrBaseYearPopDensityPath = f"{self.mStrInputDir}/popdensity_2020.tif"  # 基期人口密度数据
        self.mStrBaseYearPopPath = f"{self.mStrInputDir}/pop_2020.tif"  # 基期人口数据
        self.mStrTargetYearLandFunctionPath = strTargetYearLandFunctionPath  # 目标年份土地利用模拟结果
        self.mnTargetYear = nTargetYear  # 目标年份
        self.mnScenario = nScenario  # 发展态势
        self.mStrScenario = self.strGetScenarioName()  # 设置发展态势str
        self.mStrOutputDir = "D:/Data/result/tmp"
        self.mnTargetYearPop = predictPopulation(self.mnTargetYear)  # 最大人口增加值
        self.vSetScenarioParams()  # 根据发展态势设置参数
        self.vLoadBaseData(self.mStrBufferPath, self.mStrBaseYearPopDensityPath, self.mStrTargetYearLandFunctionPath)  # 加载内部变量
        # 结果路径
        self.mStrPopDensityPath = ""
        self.mStrFinalPopAllocationPath = ""
        
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
        # 设置不同情景的参数
        if self.mnScenario == 0:
            self.mBreaks = [1, 5, 20, 50, 100, 150, 250, 400, 530]
            self.mDensityBreak = [0.1364, 0.3093, 0.4092, 0.4572, 0.5792, 0.6347, 0.7072, 1]
        elif self.mnScenario == 1:
            self.mBreaks = [1, 5, 20, 50, 150, 250, 350, 450, 550]
            self.mDensityBreak = [0.2364, 0.4093, 0.4592, 0.5172, 0.5792, 0.6247, 0.6772, 1]
        elif self.mnScenario == 2:
            self.mBreaks = [1, 5, 20, 50, 100, 200, 300, 400, 530]
            self.mDensityBreak = [0.0364, 0.3093, 0.3592, 0.4572, 0.5792, 0.6347, 0.7572, 1]
    
    """
    @brief: 加载基础数据
    @see: 是strGeneratePopDensity()和strAllocatePopulation()的辅助函数
    """
    def vLoadBaseData(self, strBufferPath: str, strBaseYearPopDensPath: str, strTargetYearLandFuncPath: str):
        # 加载缓冲区
        buffer = gdal.Open(strBufferPath)
        self.mBuffer = buffer.GetRasterBand(1).ReadAsArray().astype(float)
        # 加载基期人口密度
        popDense = gdal.Open(strBaseYearPopDensPath)
        self.mBasePopDens = popDense.GetRasterBand(1).ReadAsArray().astype(float)
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
        # 清理人口密度数据中的无效值
        self.mBasePopDens = np.nan_to_num(self.mBasePopDens, nan=0.0, posinf=0.0, neginf=0.0)
    
    """
    @brief: 加载驱动因子数据
    @return: 驱动因子数据列表
    @see: 是strGeneratePopDensity()的辅助函数
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
    @see: 是strGeneratePopDensity()的辅助函数
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
    @brief: 生成人口密度预测图
    @return: 人口密度预测图文件路径
    @throw: ValueError - 文件加载失败或数据不一致
    @throw: Exception - 其他运行时错误
    @see: 使用了loadBaseData(), loadDrivingFactors(), randomSample()三个辅助函数
    """
    def strGeneratePopDensity(self) -> str:
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
                Y = self.mBasePopDens[self.mLandFunction == landType].reshape(-1, 1)
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
            model = GPy.models.GPCoregionalizedRegression(XIndexedSampledList, YSampledList, kernel=icmKernel)  # 创建多输出高斯过程回归模型
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
            # 构建预测人口密度栅格
            predictedPopulation = np.zeros(self.mBuffer.shape)
            # 将每种土地功能类型的预测人口密度映射到对应位置
            for i, landType in enumerate(landTypes):
                predictedPopulation[self.mLandFunction==landType] = predMeansList[i][:, 0]
            print(predictedPopulation.shape)
            # 最小-最大标准化
            popMin = predictedPopulation.min()
            popMax = predictedPopulation.max()
            popNormalized = (predictedPopulation - popMin) / (popMax - popMin)
            # 保存人口密度预测图
            driver = gdal.GetDriverByName('GTiff')
            outputFilename = f"popdensity_{self.mnTargetYear}_{self.mStrScenario}.tif"
            self.mStrPopDensityPath = f"{self.mStrOutputDir}/{outputFilename}"
            outDs = driver.Create(self.mStrPopDensityPath, self.mWidth, self.mHeight, 1, gdal.GDT_Float32)
            outDs.SetGeoTransform(self.mGeotransform)
            outDs.SetProjection(self.mProjection)
            outDs.WriteArray(popNormalized)
            outDs.FlushCache()
            outDs = None
            # 强制垃圾回收，确保GDAL释放文件句柄
            import gc
            gc.collect()
            # 等待文件系统同步（Windows需要）
            import time
            time.sleep(0.5)
            # 验证文件是否真的写入成功
            if not os.path.exists(self.mStrPopDensityPath):
                raise Exception(f"文件写入后不存在: {self.mStrPopDensityPath}")
            print(f"人口密度文件已生成: {self.mStrPopDensityPath}")
            return self.mStrPopDensityPath
        except ValueError as e:
            raise ValueError(f"人口密度预测失败: {e}") from e
        except Exception as e:
            raise Exception(f"人口密度预测失败: {e}") from e
    
    """
    @brief: 计算三角分布的基础值
    @param i: 类别索引
    @param breaks: 断点列表
    @param didCoff: 三角分布参数
    @return: 最小值、最大值、众数
    @see: 被strAllocatePopulation()调用
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
    @see: 被strAllocatePopulation()调用
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
    @see: 被strAllocatePopulation()调用
    """
    def adjustDensityBreaks(self, densityBreak, increaseLow, adjustmentFactor, minIntervalLength=0.1, highGradeMinLength=0.15):
        # 原始密度断点调整函数的实现
        nBreaks = len(densityBreak)
        adjustmentFactors = np.linspace((nBreaks - 1) / 2, 1, nBreaks - 1) * adjustmentFactor
        if increaseLow:
            # 增加低等级区间长度
            for i in range(1, nBreaks - 1):
                densityBreak[i] += adjustmentFactors[i - 1] / nBreaks
        else:
            # 减少低等级区间长度
            for i in range(nBreaks - 2, 0, -1):
                densityBreak[i] -= adjustmentFactors[::-1][i - 1] / nBreaks
        densityBreak = np.clip(np.sort(densityBreak), 0, 1)
        # 确保区间长度
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
    @see: 被strAllocatePopulation()调用
    """
    def vOutputErrorValues(self, errorValues: list):
        # 输出误差值到Excel
        dfErrorValues = pd.DataFrame(errorValues, columns=['Error Value'])
        errorExcelPath = f"{self.mStrOutputDir}/error_values_pop_{self.mnTargetYear}_{self.mStrScenario}.xlsx"
        dfErrorValues.to_excel(errorExcelPath, index=False)
        print(f"误差值已保存到: {errorExcelPath}")
        # 绘制误差变化图
        plt.figure(figsize=(10, 6))
        plt.plot(errorValues)
        plt.xlabel('Iteration')
        plt.ylabel('Error Value')
        plt.title('Error Values Over Iterations')
        errorPlotPath = f"{self.mStrOutputDir}/error_values_pop_{self.mnTargetYear}_{self.mStrScenario}.png"
        plt.savefig(errorPlotPath)
        plt.close()
        print(f"误差变化图已保存到: {errorPlotPath}")

    """
    @brief: 生成人口分配结果
    @return: 人口分配结果文件路径
    @throw: ValueError - 文件加载失败或数据不一致
    @throw: Exception - 其他运行时错误
    @see: 调用loadBaseData(), calculateValuesBase(), weightedAllocation(), adjustDensityBreaks()
    """
    def strAllocatePopulation(self) -> str:
        try:
            # 加载人口密度预测图
            if not self.mStrPopDensityPath:
                raise ValueError("请先生成人口密度预测图")
            # 检查文件是否存在
            if not os.path.exists(self.mStrPopDensityPath):
                raise ValueError(f"人口密度文件不存在: {self.mStrPopDensityPath}")
            # 打开文件并检查是否成功
            popDensityDs = gdal.Open(self.mStrPopDensityPath)
            if popDensityDs is None:
                raise ValueError(f"无法打开人口密度文件: {self.mStrPopDensityPath}")
            targetYearPopDensity = popDensityDs.GetRasterBand(1).ReadAsArray().astype(float)
            # 加载基期人口数据
            dataset = gdal.Open(self.mStrBaseYearPopPath)
            baseYearPop = dataset.GetRasterBand(1).ReadAsArray().astype(float)
            # 处理nodata值
            nodataValue = dataset.GetRasterBand(1).GetNoDataValue()
            if nodataValue is not None:
                baseYearPop[baseYearPop == nodataValue] = 0
                targetYearPopDensity[targetYearPopDensity == nodataValue] = 0
            # 标记不可居住区域
            targetYearPopDensity[(self.mLandFunction == 0)] = -100
            # 原始allocatePopulation函数的实现
            totalToleranceError = self.mnTargetYearPop * 0.05
            allocationAttempts = 0
            errorValues = []
            newPop = np.zeros_like(targetYearPopDensity, dtype=float)
            while allocationAttempts < 80 or (len(errorValues) > 5 and np.std(errorValues[-5:]) < 2000):
                newPop = np.zeros_like(targetYearPopDensity, dtype=float)
                totalPopulationAllocated = 0
                with tqdm(total=self.mnTargetYearPop) as pbar:
                    for i in range(8):
                        lowerBound = self.mDensityBreak[i - 1] if i > 0 else 0
                        upperBound = self.mDensityBreak[i] if i < len(self.mDensityBreak) else targetYearPopDensity.max() + 1
                        mask = (targetYearPopDensity >= lowerBound) & (targetYearPopDensity < upperBound)
                        rows, cols = np.where(mask)
                        selectedDensities = targetYearPopDensity[rows, cols]
                        # 按密度从高到低排序
                        sortedIndices = np.argsort(selectedDensities)[::-1]
                        sortedRows, sortedCols = rows[sortedIndices], cols[sortedIndices]
                        if len(sortedRows) == 0:
                            continue
                        # 计算三角分布参数
                        minValue, maxValue, modeValue = self.calculateValuesBase(i, self.mBreaks, 4)
                        valuesBase = np.random.triangular(left=minValue, mode=modeValue,
                                                        right=maxValue, size=len(sortedRows))
                        # 权重分配
                        allocations = self.weightedAllocation(sortedRows, sortedCols, targetYearPopDensity, valuesBase)
                        # 更新人口数据
                        for j, val in enumerate(allocations):
                            newPop[rows[j], cols[j]] += val
                            totalPopulationAllocated += val
                            pbar.update(val)
                # 计算误差值并记录
                errorValue = np.abs(totalPopulationAllocated - self.mnTargetYearPop)
                errorValues.append(errorValue)
                # 检查是否超过最大人口增加值
                if errorValue > totalToleranceError:
                    self.mDensityBreak = self.adjustDensityBreaks(self.mDensityBreak, increaseLow=True, adjustmentFactor=0.01)
                else:
                    break
                allocationAttempts += 1
            # 输出误差值到Excel并绘制误差变化图
            self.vOutputErrorValues(errorValues)
            # 保存结果
            driver = gdal.GetDriverByName('GTiff')
            outputFilename = f"predict_population_{self.mnTargetYear}_{self.mStrScenario}.tif"
            self.mStrFinalPopAllocationPath = f"{self.mStrOutputDir}/{outputFilename}"
            outDs = driver.Create(self.mStrFinalPopAllocationPath, self.mWidth, self.mHeight, 1, gdal.GDT_Float32)
            outDs.SetGeoTransform(self.mGeotransform)
            outDs.SetProjection(self.mProjection)
            outDs.WriteArray(newPop)
            outDs.FlushCache()
            outDs = None
            return self.mStrFinalPopAllocationPath
        except ValueError as e:
            raise ValueError(f"人口分配失败: {e}") from e
        except Exception as e:
            raise Exception(f"人口分配失败: {e}") from e
    
    """
    @brief: 运行完整的人口模拟流程
    @return: 人口分配结果文件路径
    @see: 调用strGeneratePopDensity()和strAllocatePopulation()
    """
    def strRun(self) -> str: 
        # 人口密度预测
        popDensityPath = self.strGeneratePopDensity()
        print(f"人口密度预测完成: {popDensityPath}")
        # 分配人口
        popAllocationPath = self.strAllocatePopulation()
        print(f"人口分配完成: {popAllocationPath}")
        return popAllocationPath
