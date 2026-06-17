import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

"""
@brief: 使用Holt-Winters指数平滑模型预测未来年份的建成区总面积
@param nPredictYear: 预测的目标年份（例如2030）
@return: float - 该年份的预测建成区面积（单位与历史数据一致，例如平方公里）
@throw: ValueError - 如果输入年份无效或模型拟合失败
@note: 基于历史数据（2010-2020年建成区面积）预测未来年份的建成区总面积
"""
def fPredictBuiltUpArea(nPredictYear: int) -> float:
    try:
        # 历史建成区面积数据（单位：平方公里，与你的代码一致）,对应年份（2010-2020）
        historyBuildUpArea = np.array([732.21, 768.16, 807.70, 807.70, 804.63, 816.79, 828.95, 840.19,864.53, 864.53, 864.53])
        # 检查预测年份是否合理（必须晚于2020）
        if nPredictYear <= 2020:
            raise ValueError(f"预测年份必须大于2020，当前输入: {nPredictYear}")
        # Holt-Winters指数平滑模型（加法趋势，无季节性，启用阻尼）
        model = ExponentialSmoothing(
            historyBuildUpArea,
            trend='additive',
            seasonal=None,
            damped_trend=True)
        # 模型拟合
        fitModel = model.fit()
        # 计算需要预测的步数
        nSteps = nPredictYear - 2020
        # 进行预测
        mForecast = fitModel.forecast(nSteps)
        # 返回目标年份的预测值（最后一个值）
        fPredictedArea = mForecast[-1]
        return fPredictedArea
    except Exception as e:
        raise ValueError(f"建成区面积预测失败: {e}") from e

def test():
    predict2025 = fPredictBuiltUpArea(2025)
    predict2030 = fPredictBuiltUpArea(2030)
    print(predict2025)
    print(predict2030)

if __name__ == "__main__":
    test()