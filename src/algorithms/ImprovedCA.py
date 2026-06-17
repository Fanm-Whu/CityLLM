"""
@file: ImprovedCA.py
@brief: 改进的元胞自动机（CA）土地模拟模型，支持多情景土地利用模拟
@author: 樊明
@date: 2025-12-19
@version: 1.0
"""
import os
import scipy.signal
import numpy as np
from osgeo import gdal
from typing import List
from src.algorithms.SimulateHelper import predictLandFuncPixel

"""
@class: ImprovedCA
@brief: 改进的元胞自动机土地模拟类，基于土地发展概率、邻域影响、中心距离等多要素进行土地利用模拟
@see: 支持自然增长、缓慢增长、快速增长等多种情景
"""
class ImprovedCA:
    """
    @brief: 初始化函数，加载所有必要的输入数据
    @param strPreviousLandtype: 前期土地类型文件路径（基准年）
    @param strFactorProbability: 土地发展概率文件路径（5波段）
    @param strBufferrings: 缓冲区文件路径（圈层）
    @param strMaskTaz: 交通小区掩膜文件路径
    @param strCenterDis: 中心距离文件路径
    @param nTargetYear: 目标预测年份
    @param nScenario: 模拟情景类型（0-缓慢增长，1-自然增长，2-快速增长）
    """
    def __init__(self, strPreviousLandFunctionPath: str, strLandDevelopProbabilityPath: str, strBufferPath: str,
                 strTrafficPath: str, strCenterDistance: str, nTargetYear: int, nScenario: int):
        try:
            # 数据成员：目标年份和情景类型
            self.mnTargetYear = nTargetYear
            self.mnScenario = nScenario
            # 加载所有输入数据集
            preLandFunc = gdal.Open(strPreviousLandFunctionPath)
            LandDevelopPro = gdal.Open(strLandDevelopProbabilityPath)
            buffer = gdal.Open(strBufferPath)
            traffic = gdal.Open(strTrafficPath)
            centerDis = gdal.Open(strCenterDistance)
            # 坐标和大小信息
            self.mGeotransform = preLandFunc.GetGeoTransform()
            self.mProjection = preLandFunc.GetProjection()
            self.mWidth = preLandFunc.RasterXSize
            self.mHeight = preLandFunc.RasterYSize
            # 读取栅格数据
            self.mPreviousLandFunction = preLandFunc.GetRasterBand(1).ReadAsArray().astype(float)
            self.mProbability_0 = LandDevelopPro.GetRasterBand(1).ReadAsArray().astype(float)
            self.mProbability_1 = LandDevelopPro.GetRasterBand(2).ReadAsArray().astype(float)
            self.mProbability_2 = LandDevelopPro.GetRasterBand(3).ReadAsArray().astype(float)
            self.mProbability_3 = LandDevelopPro.GetRasterBand(4).ReadAsArray().astype(float)
            self.mProbability_4 = LandDevelopPro.GetRasterBand(5).ReadAsArray().astype(float)
            self.mBuffer = buffer.GetRasterBand(1).ReadAsArray().astype(float)
            # 掩膜交通小区
            self.mTrafficPath = traffic.GetRasterBand(1).ReadAsArray().astype(float)
            self.mBuffer[self.mTrafficPath > 0] = 0
            # 中心距离处理
            self.mCenterDistance = centerDis.GetRasterBand(1).ReadAsArray().astype(float)
            self.mCenterDistance = 1 / (self.mCenterDistance + 0.001)
            self.mCenterDistance = (self.mCenterDistance - np.min(self.mCenterDistance)) / (np.max(self.mCenterDistance) - np.min(self.mCenterDistance))
            # 初始化模拟结果
            self.mSimulationResult = preLandFunc.GetRasterBand(1).ReadAsArray().astype(float)
            # 由函数设置目标年份要达到的目标像素数
            [self.mResidentialPixels, self.mCommercialPixels, self.mIndustrialPixels, self.mOtherPixels] = predictLandFuncPixel(self.mnTargetYear, self.mnScenario)
            # 当前已有的像素计数
            self.mSumOfPixels1 = (self.mSimulationResult == 1).sum() #为1的pixels：居住用地
            self.mSumOfPixels2 = (self.mSimulationResult == 2).sum() #为2的pixels：商业服务业用地
            self.mSumOfPixels3 = (self.mSimulationResult == 3).sum() #为3的pixels：工业用地
            self.mSumOfPixels4 = (self.mSimulationResult == 4).sum() #为4的pixels：其他用地
            # 随机干扰
            self.mDisrturb = np.random.rand(self.mHeight, self.mWidth)
            self.mDisrturb[self.mDisrturb == 0] = 0.001
            # 同类集聚卷积（相互吸引）
            self.mAttraction_0 = self.vGetNeighborWeight()
            self.mAttraction_1 = self.vGetNeighborWeight()
            self.mAttraction_2 = self.vGetNeighborWeight()
            self.mAttraction_3 = self.vGetNeighborWeight()
            self.mAttraction_4 = self.vGetNeighborWeight()
        except Exception as e:
            raise Exception(f"ImprovedCA初始化失败: {e}") from e

    """
    @brief: 计算邻域权重，基于当前模拟结果进行卷积运算
    @param nRadius: 邻域半径，默认为3
    @param fExpScale: 指数增强系数，默认为3.0
    @return: 邻域权重矩阵
    @see: 是vUpdate的辅助函数
    """
    def vGetNeighborWeight(self, nRadius: int = 3, fExpScale: float = 3.0):
        try:
            WNeighbor = np.zeros([self.mHeight, self.mWidth], dtype=float)
            For_cal = np.ones((nRadius, nRadius), dtype=float)
            t = scipy.signal.convolve((self.mSimulationResult), For_cal, mode='same')
            # 应用指数函数增强邻域影响
            max_t = np.max(t)
            if max_t > 0:  # 避免0
                t_normalized = t / max_t  # 归一化t值
                for i in range(self.mHeight):
                    for j in range(self.mWidth):
                        # 指数增强，根据exp_scale调整增强程度
                        WNeighbor[i, j] = np.exp(fExpScale * t_normalized[i, j]) - 1  # 减1使最小值为0
            WNeighbor[WNeighbor < 0] = 0
            return WNeighbor
        except Exception as e:
            raise Exception(f"vGetNeighborWeight失败: {e}") from e

    """
    @brief: 基于概率选择土地功能类型
    @param fProbabilities: 各类型土地的概率列表
    @return: 选择的土地类型索引（0-4），-1表示没有可选类型
    @see: 是vUpdate的辅助函数
    """
    def vChooseLandFunctionBasedOnProbability(self, fProbabilities: List[float]) -> int:
        try:
            # 更新概率，防止选择已满足数量限制的类型
            if self.mSumOfPixels1 >= self.mResidentialPixels:
                fProbabilities[1] = 0
            if self.mSumOfPixels2 >= self.mCommercialPixels:
                fProbabilities[2] = 0
            if self.mSumOfPixels3 >= self.mIndustrialPixels:
                fProbabilities[3] = 0
            if self.mSumOfPixels4 >= self.mOtherPixels:
                fProbabilities[4] = 0
            cumulative_probabilities = np.cumsum(fProbabilities)
            if cumulative_probabilities[-1] == 0:
                return -1  # 没有可选类型
            random_number = np.random.rand() * cumulative_probabilities[-1]
            for index, cum_prob in enumerate(cumulative_probabilities):
                if random_number < cum_prob:
                    return index
        except Exception as e:
            raise Exception(f"vChooseLandFunctionBasedOnProbability失败: {e}") from e

    """
    @brief: 单次更新迭代，处理缓冲区内的所有候选像元
    @see: 是strRun的辅助函数
    """
    def vUpdate(self):
        try:
            # 找出buffer大于0的所有位置的索引
            buffer_indices = np.argwhere(self.mBuffer > 0)
            eligible_mask = np.zeros_like(self.mBuffer, dtype=bool)
            for i, j in buffer_indices:
                if self.mSimulationResult[i, j] == 0:
                    eligible_mask[i, j] = True
            eligible_indices = np.argwhere(eligible_mask)
            # 获取邻域权重和中心距离矩阵
            neighbor_weight = self.vGetNeighborWeight()
            # 定义权重系数
            neighbor_weight_coefficient = 0.2  # 邻域权重的系数
            center_distance_coefficient = 0.8  # 中心距离的系数
            # 计算加权后的得分
            record = neighbor_weight * neighbor_weight_coefficient + self.mCenterDistance * center_distance_coefficient
            scores = np.array([record[i, j] for i, j in eligible_indices])
            # 邻域权重大优先
            sorted_indices = eligible_indices[np.argsort(-scores)]
            for idx in sorted_indices:
                i, j = idx[0], idx[1]
                combine_possibilities = [
                    self.mDisrturb[i, j] * self.mProbability_0[i, j] * self.mAttraction_0[i, j],
                    self.mDisrturb[i, j] * self.mProbability_1[i, j] * self.mAttraction_1[i, j],
                    self.mDisrturb[i, j] * self.mProbability_2[i, j] * self.mAttraction_2[i, j],
                    self.mDisrturb[i, j] * self.mProbability_3[i, j] * self.mAttraction_3[i, j],
                    self.mDisrturb[i, j] * self.mProbability_4[i, j] * self.mAttraction_4[i, j]
                ]
                selected_function = self.vChooseLandFunctionBasedOnProbability(combine_possibilities)
                if selected_function != -1:
                    # 更新模拟结果和像素计数
                    if selected_function == 1 and self.mSumOfPixels1 < self.mResidentialPixels:
                        self.mSimulationResult[i, j] = 1
                        self.mSumOfPixels1 += 1
                    elif selected_function == 2 and self.mSumOfPixels2 < self.mCommercialPixels:
                        self.mSimulationResult[i, j] = 2
                        self.mSumOfPixels2 += 1
                    elif selected_function == 3 and self.mSumOfPixels3 < self.mIndustrialPixels:
                        self.mSimulationResult[i, j] = 3
                        self.mSumOfPixels3 += 1
                    elif selected_function == 4 and self.mSumOfPixels4 < self.mOtherPixels:
                        self.mSimulationResult[i, j] = 4
                        self.mSumOfPixels4 += 1
                # 检查是否所有类别的数量都已达标，如果是，则终止更新
                if (self.mSumOfPixels1 >= self.mResidentialPixels and
                        self.mSumOfPixels2 >= self.mCommercialPixels and
                        self.mSumOfPixels3 >= self.mIndustrialPixels and
                        self.mSumOfPixels4 >= self.mOtherPixels):
                    break
        except Exception as e:
            raise Exception(f"vUpdate失败: {e}") from e

    """
    @brief: 启动模拟过程，并返回结果文件路径
    @param nIterations: 迭代次数
    @return: 模拟结果文件路径
    """
    def strRun(self) -> str:
        try:
            self.vUpdate()
            # 输出模拟结果
            #print(f"模拟居住用地像素数: {self.mResidentialPixels - self.mSumOfPixels1}")
            #print(f"模拟商业服务业用地像素数: {self.mCommercialPixels - self.mSumOfPixels2}")
            #print(f"模拟工业用地像素数: {self.mIndustrialPixels - self.mSumOfPixels3}")
            #print(f"模拟其他用地像素数: {self.mOtherPixels - self.mSumOfPixels4}")
            # 根据情景类型转换为字符串
            strScenario = "natural"
            if self.mnScenario == 0:
                strScenario = "slow"
            elif self.mnScenario == 1: 
                strScenario = "natural"
            elif self.mnScenario == 2: 
                strScenario = "quick"
            # 构建结果文件路径
            strOutputDir = 'D:/Data/result/tmp'
            strOutputFilename = f'land_{self.mnTargetYear}_{strScenario}.tif'
            strOutputPath = f"{strOutputDir}/{strOutputFilename}"
            # 保存结果文件
            driver = gdal.GetDriverByName('GTiff')
            out_band1 = driver.Create(strOutputPath, self.mWidth, self.mHeight, 1, gdal.GDT_Float32)
            out_band1.SetProjection(self.mProjection)
            out_band1.SetGeoTransform(self.mGeotransform)
            out_band1.WriteArray(self.mSimulationResult)
            out_band1.FlushCache()
            return strOutputPath
        except Exception as e:
            raise Exception(f"保存模拟结果失败: {e}") from e