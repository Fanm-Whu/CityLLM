from osgeo import gdal
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
dataset1 = gdal.Open(r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\圈层去水去公园.tif')
buffer = dataset1.GetRasterBand(1).ReadAsArray().astype(float)
dataset3 = gdal.Open(r'C:\Users\Zhongym\Desktop\多要素强耦合模型\实验结果\2025年土地功能模拟结果_缓慢.tif')
land = dataset3.GetRasterBand(1).ReadAsArray().astype(float)
data_path = r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\pop_2020_adjusted_for_land.tif'
density_path = r'C:\Users\Zhongym\Desktop\多要素强耦合模型\实验结果\GPY预测人口密度_2025缓慢.tif'

# 加载人口数值数据
dataset = gdal.Open(data_path)
band = dataset.GetRasterBand(1)
data = band.ReadAsArray().astype(float)

# 加载人口密度数据
dataset2 = gdal.Open(density_path)
band2 = dataset2.GetRasterBand(1)
density = band2.ReadAsArray().astype(float)

# 确保处理无数据值
nodata_value = band.GetNoDataValue()
data[data == nodata_value] = 0
density[density == nodata_value] = 0
# 投影
width = dataset1.RasterXSize
height = dataset1.RasterYSize
geotransform = dataset1.GetGeoTransform()
projection = dataset1.GetProjection()

# 基础参数设置 # 自然断点-八类别
max_increase =13898020
breaks =  [1,5,20,50,100,150,250,400,530]
density_break= [0.1364, 0.3093, 0.4092, 0.4572, 0.5792, 0.6347, 0.7072, 1]
class_means =[3.2451256156872463, 14.779449257500513, 37.97088506694408, 65.36651165320497, 97.22190714484293, 144.87362637362637, 208.06369675654554, 295.2615740740741]
indice_map=np.array([i for i in range(0,2331*2724)]).reshape(2331,2724)
print('检查输入各类别数组长度',len(density_break),len(class_means),len(breaks))
allocation_attempts_times=80 # 总迭代时间
did_coff=4

# print(len(data[(density >= 0.8) & (density < 0.888)]))


# 计算values_base--使用三角分布生成 values_base，峰值向左靠(低值)
def calculate_values_base(i, breaks):
    min_value = breaks[i] if i > 0 else 0
    max_value = breaks[i + 1] if i < len(breaks) - 1 else breaks[i]  # 防止索引越界
    # 调整mode_value，使靠近min_value
    mode_value = min_value + (max_value - min_value) / did_coff
    return min_value, max_value, mode_value


def weighted_allocation(rowss, colss, density_data, values_range_data):
    # 权重概率 确保索引为高密度到低密度排列
    weights = density_data[rowss, colss]
    exponential_weights = np.power(weights, 3)
    normalized_weights = exponential_weights / np.sum(exponential_weights)
    # 高值优先
    values_range_data = np.sort(values_range_data)[::-1]

    allocations = np.random.choice(values_range_data, size=len(rowss), replace=True, p=normalized_weights)

    return allocations


def adjust_density_breaks(density_break, increase_low, adjustment_factor, min_interval_length=0.1, high_grade_min_length=0.15): # 区间滑块
    n_breaks = len(density_break)
    # 根据等级生成调整因子数组，为高等级区间留出更多空间
    adjustment_factors = np.linspace((n_breaks - 1) / 2,1, n_breaks - 1) * adjustment_factor

    if increase_low:
        # 增加低等级区间长度
        for i in range(1, n_breaks - 1):  # 保留最后一个区间，避免它变得太小
            density_break[i] += adjustment_factors[i - 1] / n_breaks
    else:
        # 减少低等级区间长度
        for i in range(n_breaks - 2, 0, -1):  # 逆向处理，保护最高等级区间
            density_break[i] -= adjustment_factors[::-1][i - 1] / n_breaks

    density_break = np.clip(np.sort(density_break), 0, 1)

    # 确保每个区间长度至少为min_interval_length，高等级区间不低于high_grade_min_length
    for i in range(1, n_breaks):
        if i < n_breaks - 1:  # 对非最后一个区间使用min_interval_length
            required_min_length = min_interval_length
        else:  # 对最后一个区间使用high_grade_min_length
            required_min_length = high_grade_min_length

        if density_break[i] - density_break[i - 1] < required_min_length:
            density_break[i] = min(density_break[i - 1] + required_min_length, 1)

    density_break = np.clip(np.sort(density_break), 0, 1)  # 最终确认

    print('调整后密度划分区间为', density_break)
    return density_break

def allocate_population(density, density_break, class_means, max_increase,Total_tolerance_error=max_increase*0.05):
    density[(land == 0)] = -100  # 标记不可居住区域
    allocation_attempts = 0
    error_values = []  # 初始化误差值列表
    new_pop = np.zeros_like(density, dtype=float)
    while allocation_attempts < allocation_attempts_times or (len(error_values) > 5 and np.std(error_values[-5:]) < 2000):
        new_pop = np.zeros_like(density, dtype=float)  # 每轮尝试前重置new_pop
        total_population_allocated = 0

        with tqdm(total=max_increase) as pbar:  # 初始化进度条

            for i, mean in enumerate(class_means):
                lower_bound = density_break[i - 1] if i > 0 else 0
                upper_bound = density_break[i] if i < len(density_break) else density.max() + 1

                mask = (density >= lower_bound) & (density < upper_bound)
                rows, cols = np.where(mask)
                selected_densities = density[rows, cols]

                # 获取这些密度值排序后的索引（高到低）
                sorted_indices = np.argsort(selected_densities)[::-1]

                # 使用排序后的索引重新排序行和列的索引
                sorted_rows, sorted_cols = rows[sorted_indices], cols[sorted_indices]

                if len(sorted_rows) == 0:
                    continue

                min_value, max_value, mode_value = calculate_values_base(i, breaks)
                values_base = np.random.triangular(left=min_value, mode=mode_value, right=max_value, size=len(sorted_rows))
                # 确保输入的区间元素按照密度值由高到低排列
                allocations = weighted_allocation(sorted_rows, sorted_cols, density, values_base)

                # 更新new_pop数组和进度条
                for j, val in enumerate(allocations):
                    new_pop[rows[j], cols[j]] += val
                    total_population_allocated += val
                    pbar.update(val)

        error_value = np.abs(total_population_allocated - max_increase) - Total_tolerance_error
        error_values.append(error_value)  # 收集每次迭代的误差值

        # 检查是否超过最大人口增加值
        if np.abs(total_population_allocated - max_increase)>Total_tolerance_error :

            adjust_density_breaks(density_break, increase_low=True, adjustment_factor=0.01)
            error_value=np.abs(total_population_allocated - max_increase) - Total_tolerance_error
            print('当前人口为',total_population_allocated ,'人口误差为',error_value/max_increase)
            print('目前密度划分区间为', density_break)
        else:
            error_value = np.abs(total_population_allocated - max_increase) - Total_tolerance_error
            print('最终人口误差为', error_value/max_increase)
            break  # 如果没有超过，满足条件，退出循环

        allocation_attempts += 1  # 更新尝试次数

    # 输出误差值到Excel
    df_error_values = pd.DataFrame(error_values, columns=['Error Value'])
    df_error_values.to_excel(r'C:\Users\Zhongym\Desktop\多要素强耦合模型\输出文档和图\error_values_2025_pop缓慢.xlsx', index=False)

        # 绘制误差值变化图
    plt.plot(error_values)
    plt.xlabel('Iteration')
    plt.ylabel('Error Value')
    plt.title('Error Values Over Iterations')
    plt.savefig(r'C:\Users\Zhongym\Desktop\多要素强耦合模型\输出文档和图\error_values_2025_pop缓慢.png')
    plt.show()

    print('总共迭代', allocation_attempts, '最终密度划分区间为',density_break)

    return new_pop




adjusted_allocated_population = allocate_population(density, density_break, class_means, max_increase)


# 保存结果到栅格文件
driver = gdal.GetDriverByName('GTiff')
output_file = r'C:\Users\Zhongym\Desktop\多要素强耦合模型\实验结果\final_allocated_population_2025缓慢.tif'
out_ds = driver.Create(output_file, width, height, 1, gdal.GDT_Float32)
out_ds.SetGeoTransform(geotransform)
out_ds.SetProjection(projection)
out_ds.WriteArray(adjusted_allocated_population)
out_ds.FlushCache()
out_ds = None
print('ok!')