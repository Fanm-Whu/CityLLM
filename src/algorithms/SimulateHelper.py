"""
@file: SimulateHelper.py
@brief: LandSimulator、PopSimulator、GDPSimulator
@author: 樊明
@date: start: 2026-02-06; end: 2026-02-07
@version: 1.0
"""
from typing import List
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

"""
@brief: 在目标年份、给定发展情景下，预测各土地功能的像素个数
@param nTargetYear: 目标年份（≥2020）
@param nScenario: 发展情景（0-自然增长，1-缓慢增长，2-快速增长）
@return: List[int] - [居住用地像素数，商业用地像素数，工业用地像素数，其他用地像素数]
"""
def predictLandFuncPixel(nTargetYear: int, nScenario: int) -> List[int]:
    try:
        # 公共的2020年基础数据
        fResidentialArea2020 = 270.46
        fCommercialArea2020 = 44.15
        fIndustrialArea2020 = 217.95
        nResidentialPixels2020 = 327939
        nCommercialPixels2020 = 40135
        nIndustrialPixels2020 = 304370
        nOtherPixels2020 = 183776
        # 情景参数（增长率单位：平方公里/年，实际为每5年增量；其他用地为每5年复合增长因子）
        scenarioParamsDict = {
            0: {  # 缓慢增长
                'res_growth_rate': 1.07,
                'com_growth_rate': 0.02,
                'ind_growth_rate': 0.75,
                'other_growth_factor': 1.029054033,},
            1: {  # 自然增长
                'res_growth_rate': 5.33,
                'com_growth_rate': 1.18,
                'ind_growth_rate': 6.31,
                'other_growth_factor': 1.01845295936,},
            2: {  # 快速增长
                'res_growth_rate': 27.14,
                'com_growth_rate': 4.95,
                'ind_growth_rate': 16.38,
                'other_growth_factor': 1.133719618,}}
        if nScenario not in scenarioParamsDict:
            raise ValueError(f"无效的情景编号: {nScenario}，应为 0、1 或 2")
        params = scenarioParamsDict[nScenario]
        # 步数（每5年为一步）
        pace = (nTargetYear - 2020) / 5
        # 计算目标年份各类用地面积（线性外推）
        fResidentialArea4TargetYear = round(fResidentialArea2020 + params['res_growth_rate'] * pace, 2)
        fCommercialArea4TargetYear = round(fCommercialArea2020 + params['com_growth_rate'] * pace, 2)
        fIndustrialArea4TargetYear = round(fIndustrialArea2020 + params['ind_growth_rate'] * pace, 2)
        # 计算像素个数（面积比例缩放）
        nResidentialPixels4TargetYear = round((fResidentialArea4TargetYear / fResidentialArea2020) * nResidentialPixels2020)
        nCommercialPixels4TargetYear = round((fCommercialArea4TargetYear / fCommercialArea2020) * nCommercialPixels2020)
        nIndustrialPixels4TargetYear = round((fIndustrialArea4TargetYear / fIndustrialArea2020) * nIndustrialPixels2020)
        # 其他用地按指数增长计算
        nOtherPixelsOfTargetYear = round(nOtherPixels2020 * pow(params['other_growth_factor'], pace))
        return [nResidentialPixels4TargetYear, nCommercialPixels4TargetYear,nIndustrialPixels4TargetYear, nOtherPixelsOfTargetYear]
    except Exception as e:
        raise ValueError(f"像素个数预测失败: {e}") from e
    
"""
@brief: 使用Holt指数平滑模型预测武汉市常住总人口
@param nTargetYear: 目标年份（应大于2000且不等于2025等预测年份时需大于2024）
@return: 预测年份的常住人口数量（单位：人），四舍五入取整
@note: 数据来源于2000-2024年武汉市统计公报，文件路径已在函数内硬编码
"""
def predictPopulation(nTargetYear: int) -> int:
    try:
        # 固定数据文件路径（请根据实际存储位置调整）
        strFilePath = r'D:\Data\data\simulation\history_pop_gdp_in_wuhan.xlsx'
        strSheetName = 'wuhan'
        strYearCol = 'Year'
        strPopCol = '人口'  # 列名未变，但数据已改为“人”
        # 读取数据
        data = pd.read_excel(strFilePath, sheet_name=strSheetName).sort_values(by=strYearCol)
        yearsListn = data[strYearCol].astype(int).tolist()
        popListf = data[strPopCol].astype(float).tolist()
        # 检查目标年份是否在历史数据中
        if nTargetYear in yearsListn:
            # 找到目标年份所在的行
            row = data[data[strYearCol] == nTargetYear]
            if not row.empty:
                nActualPop = row.iloc[0][strPopCol]
            return int(round(nActualPop))
        # 检查目标年份是否大于最大历史年份
        nMaxYear = max(yearsListn)
        if nTargetYear <= nMaxYear:
            raise ValueError(f"无效的目标年份: {nTargetYear}")
        # 拟合Holt模型（带阻尼趋势）
        model = ExponentialSmoothing(popListf, trend='additive', seasonal=None, damped_trend=True)
        fit = model.fit()
        # 计算预测步数
        nSteps = nTargetYear - nMaxYear
        forecast = fit.forecast(nSteps)
        # 提取目标年份预测值
        if isinstance(forecast, pd.Series):
            fPred = forecast.iloc[-1]
        else:
            fPred = forecast[-1]
        return int(round(fPred))
    except FileNotFoundError as e:
        raise ValueError(f"人口数据文件未找到: {e}") from e
    except Exception as e:
        raise ValueError(f"人口预测失败: {e}") from e

"""
@brief: 使用Holt指数平滑模型预测武汉市GDP
@param nTargetYear: 目标年份（应大于2000且不等于2025等预测年份时需大于2024）
@param nScenario: 发展情景（0-缓慢增长，1-自然增长，2-快速增长）
@return: 预测年份的GDP（单位：万元），四舍五入取整
@note: 数据来源于2000-2024年武汉市统计公报，文件路径已在函数内硬编码
"""
def predictGDP(nTargetYear: int) -> int:
    try:
        # 固定数据文件路径（请根据实际存储位置调整）
        strFilePath = r'D:\Data\data\simulation\history_pop_gdp_in_wuhan.xlsx'
        strSheetName = 'wuhan'
        strYearCol = 'Year'
        strGDPCol = 'GDP'  # GDP列
        # 读取数据
        data = pd.read_excel(strFilePath, sheet_name=strSheetName).sort_values(by=strYearCol)
        yearsListn = data[strYearCol].astype(int).tolist()
        gdpListf = data[strGDPCol].astype(float).tolist()
        # 检查目标年份是否在历史数据中
        if nTargetYear in yearsListn:
            # 找到目标年份所在的行
            row = data[data[strYearCol] == nTargetYear]
            if not row.empty:
                nActualGDP = row.iloc[0][strGDPCol]
            return int(round(nActualGDP))
        # 检查目标年份是否大于最大历史年份
        nMaxYear = max(yearsListn)
        if nTargetYear <= nMaxYear:
            raise ValueError(f"无效的目标年份: {nTargetYear}")
        # 拟合Holt模型（带阻尼趋势）
        model = ExponentialSmoothing(gdpListf, trend='additive', seasonal=None, damped_trend=True)
        fit = model.fit()
        # 计算预测步数
        nSteps = nTargetYear - nMaxYear
        forecast = fit.forecast(nSteps)
        # 提取目标年份预测值
        if isinstance(forecast, pd.Series):
            fPred = forecast.iloc[-1]
        else:
            fPred = forecast[-1]
        return int(round(fPred))
    except FileNotFoundError as e:
        raise ValueError(f"GDP数据文件未找到: {e}") from e
    except Exception as e:
        raise ValueError(f"GDP预测失败: {e}") from e