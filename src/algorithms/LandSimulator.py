"""
@file: LandSimulator.py
@brief: 土地模拟文件，包括LandSimulator类，用于计算土地发展概率、输出土地模拟图
@author: 樊明
@date: start: 2026-02-06; end: 2026-02-06
@version: 1.0
"""
from osgeo import gdal
import xgboost as xgb
from sklearn.model_selection import train_test_split
from src.algorithms.GeoProcessor import strNormalizeRaster, strAddTinyValueAtZero4Tif
from src.algorithms.ImprovedCA import ImprovedCA
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import os


"""
@class: LandSimulator
@brief: 土地模拟类，基于XGBoost计算土地发展概率，基于改进CA生成土地模拟结果
@see: 使用上一期土地、人口和GDP模拟结果作为输入
"""
class LandSimulator:
    """
    @brief: 初始化函数
    @param strPreviousLandSimuResult: 上一期土地模拟结果路径（e.g., land_2025_natural.tif）
    @param strPreviousPopSimuResult: 上一期人口模拟结果路径（e.g., pop_2025_natural.tif）
    @param strPreviousGDPSimuResult: 上一期GDP模拟结果路径（e.g., gdp_2025_natural.tif）
    @param nTargetYear: 本轮模拟的目标年份
    @param nScenario: 本轮模拟的发展态势（0-缓慢，1-自然，2-快速）
    """
    def __init__(self, strPreviousLandSimuResultPath: str, strPreviousPopSimuResultPath: str, strPreviousGDPSimuResultPath: str, nTargetYear: int, nScenario: int):
        self.mStrPreviousLandSimuResultPath = strPreviousLandSimuResultPath
        # 标准化人口和GDP栅格
        strPopNormalizedPath = strNormalizeRaster(strPreviousPopSimuResultPath, "pop", nTargetYear - 5)
        strGDNormalizedPath = strNormalizeRaster(strPreviousGDPSimuResultPath, "gdp", nTargetYear - 5)
        # 为标准化后的人口和GDP栅格中的0值添加微小值0.0001
        self.mStrPreviousPopSimuResultPath = strAddTinyValueAtZero4Tif(strPopNormalizedPath)
        self.mStrPreviousGDPSimuResultPath = strAddTinyValueAtZero4Tif(strGDNormalizedPath)
        self.mStrInputDir = "D:/Data/data/simulation"
        self.mnTargetYear = nTargetYear
        self.mnScenario = nScenario
        self.mStrLandDevelopProbabilityPath = ""
        self.vGenerateLandDevelopmentProbability()

    """
    @brief: 生成目标年份的土地发展概率，并返回文件路径
    @return: str-输出文件路径（landdevelop_{self.mnTargetYear}_{strScenario}.tif）
    @throw: ValueError - 文件加载失败或数据不一致
    @throw: Exception - 其他运行时错误
    """
    def vGenerateLandDevelopmentProbability(self) -> str:
        try:
            # 固定缓冲区路径
            strBufferPath = f"{self.mStrInputDir}/圈层去水去公园_processed.tif"
            buffer = gdal.Open(strBufferPath)
            # 加载上一期土地功能数据
            datasetLand = gdal.Open(self.mStrPreviousLandSimuResultPath)
            prevLandFunction = datasetLand.GetRasterBand(1).ReadAsArray().astype(float)
            # 获取投影和尺寸信息
            width = buffer.RasterXSize
            height = buffer.RasterYSize
            geotransform = buffer.GetGeoTransform()
            projection = buffer.GetProjection()
            # 处理nodata值
            prevLandFunction[prevLandFunction < 0] = 0
            # 驱动因子路径列表
            dirvingFactorPathListStr = [
                self.mStrPreviousPopSimuResultPath,
                self.mStrPreviousGDPSimuResultPath,
                f"{self.mStrInputDir}/圈层去水去公园_processed.tif",
                f"{self.mStrInputDir}/primary_processed.tif",
                f"{self.mStrInputDir}/secondary_processed.tif",
                f"{self.mStrInputDir}/teitiary_processed.tif",
                f"{self.mStrInputDir}/motorway_processed.tif",
                f"{self.mStrInputDir}/center_processed.tif",
                f"{self.mStrInputDir}/water_processed.tif",
                f"{self.mStrInputDir}/train_airport_processed.tif",
                f"{self.mStrInputDir}/hightway_processed.tif",
                f"{self.mStrInputDir}/DEM_processed.tif",
                f"{self.mStrInputDir}/slope_processed.tif",
                self.mStrPreviousLandSimuResultPath]
            #构建驱动因子列表
            drivingFactorList = []
            for strFile in dirvingFactorPathListStr:
                inDs = gdal.Open(strFile)
                if inDs is None:
                    raise ValueError(f"无法打开驱动因子文件: {strFile}")
                inBand = inDs.GetRasterBand(1)
                data = inBand.ReadAsArray().astype(float)
                drivingFactorList.append(data)
            # 构建完整数据集
            allData = np.hstack([drivingFactorList[i].reshape(-1, 1) for i in range(len(drivingFactorList))])
            # 按土地类型采样
            residentialLand = allData[allData[:, -1] == np.array(1).astype(np.float64)]
            commercialServiceLand = allData[allData[:, -1] == np.array(2).astype(np.float64)]
            industrialLand = allData[allData[:, -1] == np.array(3).astype(np.float64)]
            otherLand = allData[allData[:, -1] == np.array(4).astype(np.float64)]
            nonLand = allData[allData[:, -1] == np.array(0).astype(np.float64)]
            # 打乱数据集
            np.random.seed(345)
            np.random.shuffle(residentialLand)
            np.random.shuffle(commercialServiceLand)
            np.random.shuffle(industrialLand)
            np.random.shuffle(otherLand)
            np.random.shuffle(nonLand)
            # 随机采样8000点
            trainResidentialLand = residentialLand[:8000]
            trainCommercialServiceLand = commercialServiceLand[:8000]
            trainIndustrialLand = industrialLand[:8000]
            trainOtherLand = otherLand[:8000]
            trainNonLand = nonLand[:8000]
            # 构建训练集
            allTrainData = np.vstack((trainResidentialLand[:8000], trainCommercialServiceLand[:8000], trainIndustrialLand[:8000], trainOtherLand[:8000], trainNonLand[:8000]))
            np.random.seed(345)
            np.random.shuffle(allTrainData)
            X, Y = allTrainData[:, :len(drivingFactorList) - 1], allTrainData[:, -1]
            XTrain, XTest, YTrain, YTest = train_test_split(X, Y, train_size=0.8, random_state=42, shuffle=True)
            # XGBoost训练
            dTrain = xgb.DMatrix(XTrain, label=YTrain)
            dTest = xgb.DMatrix(XTest, label=YTest)
            # 参数设置
            param = {
                'max_depth': 6,
                'eta': 0.1,
                'learning_rate': 0.1,
                'objective': 'multi:softmax',
                'num_class': 5,
                'subsample': 0.7,
                'colsample_bytree': 0.8,
                'min_child_weight': 1,
                'eval_metric': 'mlogloss'
            }
            numRound = 100
            # 早停设置
            listEval = [(dTest, 'eval'), (dTrain, 'train')]
            # 训练模型
            bestModel = xgb.train(param, dTrain, numRound, listEval, early_stopping_rounds=10, verbose_eval=False)
            # 全数据集预测
            predictAllX = np.hstack([drivingFactorList[i].reshape(-1, 1) for i in range(len(drivingFactorList) - 1)])
            dPredict = xgb.DMatrix(predictAllX)
            # 获取原始得分
            predScores = bestModel.predict(dPredict, iteration_range=(0, bestModel.best_iteration + 1), output_margin=True)
            # softmax转换概率
            def softmax(x):
                e_x = np.exp(x - np.max(x, axis=1, keepdims=True))
                return e_x / e_x.sum(axis=1, keepdims=True)
            # 计算概率
            predProbabilities = softmax(predScores)
            predProbabilities = predProbabilities.reshape((height, width, 5))
            # 输出路径
            strScenario = "natural"
            if self.mnScenario == 0:
                strScenario = "slow"
            elif self.mnScenario == 1: 
                strScenario = "natural"
            elif self.mnScenario == 2: 
                strScenario = "quick"
            strOutputDir = "D:/Data/result/tmp"
            strOutputFilename = f'landdevelop_{self.mnTargetYear}_{strScenario}.tif'
            strOutputPath = os.path.join(strOutputDir, strOutputFilename)
            # 导出栅格
            driver = gdal.GetDriverByName('GTiff')
            outBand = driver.Create(strOutputPath, width, height, 5, gdal.GDT_Float32)
            outBand.SetProjection(projection)
            outBand.SetGeoTransform(geotransform)
            for i in range(5):
                outBand2 = outBand.GetRasterBand(i + 1)
                outBand2.WriteArray(predProbabilities[:, :, i])
            # 清理
            outBand = None
            self.mStrLandDevelopProbabilityPath = strOutputPath
        except ValueError as e:
            raise ValueError(f"土地发展概率计算失败: {e}") from e
        except Exception as e:
            raise Exception(f"土地发展概率计算失败: {e}") from e
        
    """
    @brief: 根据土地发展概率，基于改进CA模型，生成目标年份，给定发展态势下的土地利用模拟结果
    @return: 返回目标年份，给定发展态势下的土地利用模拟结果路径
    """
    def strRun(self) -> str:
        bufferPath = f"{self.mStrInputDir}/圈层去水去公园_processed.tif"
        trafficPath = f"{self.mStrInputDir}/武汉建成区2020_交通小区提取_processed.tif"
        centerDisPath = f"{self.mStrInputDir}/center_processed.tif"
        #定义
        caModel = ImprovedCA(
                strPreviousLandFunctionPath = self.mStrPreviousLandSimuResultPath,
                strLandDevelopProbabilityPath = self.mStrLandDevelopProbabilityPath,
                strBufferPath = bufferPath,
                strTrafficPath = trafficPath,
                strCenterDistance = centerDisPath,
                nTargetYear = self.mnTargetYear,
                nScenario = self.mnScenario)
        strLandUseSimuResultPath = caModel.strRun()
        return strLandUseSimuResultPath