# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_squared_error

df = pd.read_excel(r'C:\Users\Zhongym\Desktop\多要素强耦合模型\数据\预测GDP分级.xlsx')

years= df['年份']
pop= df['级别1'] # 级别8


# Holt's Exponential Smoothing model
model = ExponentialSmoothing(pop, trend='additive', seasonal=None, damped_trend=True)
fit = model.fit()

forecast_years = np.arange(2025, 2031, 5)  # Corrected to start from 2025 and increment by 5
forecast = fit.forecast(len(forecast_years))

predicted_pop = fit.fittedvalues
mse = mean_squared_error(pop, predicted_pop)
rmse = np.sqrt(mse)

plt.figure(figsize=(10, 6))
plt.plot(years, pop, label='Actual Population', marker='o')
plt.plot(years, predicted_pop, label='Fitted Population', marker='x')
plt.plot(forecast_years, forecast, label='Forecast Population', marker='o', linestyle='--')
plt.axvline(x=2020, color='grey', linestyle='--', linewidth=0.8)  # Line to indicate start of forecast
plt.title('Population Forecast with Holt\'s Exponential Smoothing')
plt.xlabel('Year')
plt.ylabel('Population')
plt.legend()
plt.grid(True)
plt.tight_layout()

# RMSE
plt.text(2025, pop.min(), f'RMSE: {rmse:.2f}', fontsize=9, bbox=dict(facecolor='white', alpha=0.5))
plt.show()

# 使用 .iloc 访问Pandas Series中的元素
forecast_2025 = forecast.iloc[0]
forecast_2030 = forecast.iloc[-1]

print(forecast_2025, forecast_2030, rmse)
