import GPy
from GPy.kern import Kern
from GPy.util.multioutput import ICM
import numpy as np
from osgeo import gdal
import warnings
warnings.filterwarnings('ignore')

dataset1 = gdal.Open(r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\圈层去水去公园.tif')
Buffer = dataset1.GetRasterBand(1).ReadAsArray().astype(float)
dataset2 = gdal.Open(r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\Land_2020_pre_Normalized.tif')
Pop_pre= dataset2.GetRasterBand(1).ReadAsArray().astype(float)
dataset3 = gdal.Open(r'C:\Users\Zhongym\Desktop\多要素强耦合模型\实验结果\2025年土地功能模拟结果_自然.tif')
LandFunction = dataset3.GetRasterBand(1).ReadAsArray().astype(float)

# 投影
width = dataset1.RasterXSize
height = dataset1.RasterYSize
geotransform = dataset1.GetGeoTransform()
projection = dataset1.GetProjection()
# nodata处理
LandFunction[LandFunction<0]=0


# 驱动因子输入14个 (标准化、nodata)
input_files = [
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\所有poi密度_标准化.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\便利设施密度_标准化.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\公共设施密度_标准化.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\公司企业密度_标准化.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\primary.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\secondary.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\teitiary.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\motorway.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\center.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\water.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\train_airport.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\hightway.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\DEM.tif',
    r'C:\Users\Zhongym\Desktop\多要素强耦合模型\操作数据\slope.tif'
]

dataset_list=[]
for i, file in enumerate(input_files, start=1):
    in_ds = gdal.Open(file)
    in_band = in_ds.GetRasterBand(1)
    data = in_band.ReadAsArray().astype(float)
    dataset_list.append(data)
print('驱动因子数据集合并成功')
print('目前数据集size:',len(dataset_list))

print('采样准备')
# 随机抽取样本
def random_sample(X, Y, sample_size):
    assert len(X) == len(Y)
    if len(X) > sample_size:
        indices = np.random.choice(len(X), sample_size, replace=False)
    else:
        indices = np.arange(len(X))
    return X[indices], Y[indices]

print('输入不同类型土地与人口总数据')
# 土地特征以及对应人口密度
X_0 =  np.hstack([dataset_list[i][LandFunction==0].reshape(-1, 1) for i in range(len(dataset_list))])
Y_0 = Pop_pre[LandFunction==0].reshape(-1, 1)
X_1 =  np.hstack([dataset_list[i][LandFunction==1].reshape(-1, 1) for i in range(len(dataset_list))])
Y_1 = Pop_pre[LandFunction==1].reshape(-1, 1)
X_2 =  np.hstack([dataset_list[i][LandFunction==2].reshape(-1, 1) for i in range(len(dataset_list))])
Y_2 = Pop_pre[LandFunction==2].reshape(-1, 1)
X_3 =  np.hstack([dataset_list[i][LandFunction==3].reshape(-1, 1) for i in range(len(dataset_list))])
Y_3 = Pop_pre[LandFunction==3].reshape(-1, 1)
X_4 =  np.hstack([dataset_list[i][LandFunction==4].reshape(-1, 1) for i in range(len(dataset_list))])
Y_4 = Pop_pre[LandFunction==4].reshape(-1, 1)
# 标记土地
index_0 = np.zeros_like(Y_0)
index_1 = np.ones_like(Y_1)
index_2 = np.ones_like(Y_2)*2
index_3 = np.ones_like(Y_3)*3
index_4 = np.ones_like(Y_4)*4
# 将输入数据和index合并
X_0_indexed = np.hstack((X_0, index_0))
X_1_indexed = np.hstack((X_1, index_1))
X_2_indexed = np.hstack((X_2, index_2))
X_3_indexed = np.hstack((X_3, index_3))
X_4_indexed = np.hstack((X_4, index_4))
print('总数据集输入完毕')
print('开始随机抽样')
# 应用随机抽样
X_0_sampled, Y_0_sampled = random_sample(X_0, Y_0, 800)
X_1_sampled, Y_1_sampled = random_sample(X_1, Y_1, 800)
X_2_sampled, Y_2_sampled = random_sample(X_2, Y_2, 800)
X_3_sampled, Y_3_sampled = random_sample(X_3, Y_3, 800)
X_4_sampled, Y_4_sampled = random_sample(X_4, Y_4, 800)

# 标记
index_0_sampled = np.zeros_like(Y_0_sampled)
index_1_sampled = np.ones_like(Y_1_sampled)
index_2_sampled = np.ones_like(Y_2_sampled) * 2
index_3_sampled = np.ones_like(Y_3_sampled) * 3
index_4_sampled = np.ones_like(Y_4_sampled) * 4

# 将输入数据和index合并
X_0_indexed_sampled = np.hstack((X_0_sampled, index_0_sampled))
X_1_indexed_sampled = np.hstack((X_1_sampled, index_1_sampled))
X_2_indexed_sampled = np.hstack((X_2_sampled, index_2_sampled))
X_3_indexed_sampled = np.hstack((X_3_sampled, index_3_sampled))
X_4_indexed_sampled = np.hstack((X_4_sampled, index_4_sampled))
print('随机抽样数据集构建完毕')

print('开始训练模型')
input_dim = 15  # 包括14个驱动因子和1个土地类型指标
num_outputs = 5  # 5种土地功能类型

kernel = GPy.kern.RBF(input_dim=14, active_dims=np.arange(14))
icm_kernel = GPy.util.multioutput.ICM(input_dim=14, num_outputs=num_outputs, kernel=kernel)
m = GPy.models.GPCoregionalizedRegression([X_0_indexed_sampled, X_1_indexed_sampled, X_2_indexed_sampled, X_3_indexed_sampled, X_4_indexed_sampled],
                                          [Y_0_sampled, Y_1_sampled, Y_2_sampled, Y_3_sampled, Y_4_sampled], kernel=icm_kernel)

# 模型优化，启用消息输出以观察进度
m.optimize('bfgs', max_iters=100, messages=True)
print("模型训练、优化完毕")


print("开始预测不同土地的人口密度")

X_0_new = np.hstack((X_0, index_0))
X_1_new = np.hstack((X_1, index_1))
X_2_new = np.hstack((X_2, index_2))
X_3_new = np.hstack((X_3, index_3))
X_4_new = np.hstack((X_4, index_4))

# 逐批预测并提供进度更新
def predict_in_batches(model, X_new, base_index, batch_size=100):
    num_samples = X_new.shape[0]
    num_batches = np.ceil(num_samples / batch_size).astype(int)
    pred_means = []
    pred_vars = []

    for i in range(num_batches):
        start = i * batch_size
        end = min((i + 1) * batch_size, num_samples)
        print(f"正在预测批次 {i + 1}/{num_batches}...")

        # 动态生成每个批次的Y_metadata，以匹配批次的大小
        Y_metadata_batch = {'output_index': base_index[start:end].astype(int)}

        pred_mean, pred_var = model.predict(X_new[start:end], Y_metadata=Y_metadata_batch)
        pred_means.append(pred_mean)
        pred_vars.append(pred_var)

    print("该类别预测完成")
    return np.vstack(pred_means), np.vstack(pred_vars)

print("正在预测各类土地人口")

# Y_metadata告诉模型这是哪种类型的土地
batch_size = 200
base_index_0 = np.zeros(X_0.shape[0]).astype(int)
pred_mean_0, pred_var_0 = predict_in_batches(m, X_0_new, base_index_0, batch_size=batch_size)
print("正在预测第一类土地人口完毕")
base_index_1 = np.zeros(X_1.shape[0]).astype(int)
pred_mean_1, pred_var_1 = predict_in_batches(m, X_1_new, base_index_1, batch_size=batch_size)
print("正在预测第二类土地人口完毕")
base_index_2 = np.zeros(X_2.shape[0]).astype(int)
pred_mean_2, pred_var_2 = predict_in_batches(m, X_2_new, base_index_2, batch_size=batch_size)
print("正在预测第三类土地人口完毕")
base_index_3 = np.zeros(X_3.shape[0]).astype(int)
pred_mean_3, pred_var_3 = predict_in_batches(m, X_3_new, base_index_3, batch_size=batch_size)
print("正在预测第四类土地人口完毕")
base_index_4 = np.zeros(X_4.shape[0]).astype(int)
pred_mean_4, pred_var_4 = predict_in_batches(m, X_4_new, base_index_4, batch_size=batch_size)
print("正在预测第五类土地人口完毕")

print("准备合并结果到栅格")
# 构建空栅格方便合并结果
predicted_population = np.zeros(Buffer.shape)

print("准备人口密度映射")
# 将每种土地功能类型的预测人口密度映射对应位置
predicted_population[LandFunction==0] = pred_mean_0[:,0]
predicted_population[LandFunction==1] = pred_mean_1[:,0]
predicted_population[LandFunction==2] = pred_mean_2[:,0]
predicted_population[LandFunction==3] = pred_mean_3[:,0]
predicted_population[LandFunction==4] = pred_mean_4[:,0]
print(predicted_population.shape)

# 最小-最大标准化
Pop_min = predicted_population.min()
Pop_max = predicted_population.max()
Pop_normalized = (predicted_population- Pop_min) / (Pop_max - Pop_min)

print("人口预测完毕，准备导出")
driver = gdal.GetDriverByName('GTiff')
output_file = r'C:\Users\Zhongym\Desktop\多要素强耦合模型\实验结果\GPY预测人口密度_2025自然.tif'

out_ds = driver.Create(output_file, width, height, 1, gdal.GDT_Float32)
out_ds.SetGeoTransform(geotransform)
out_ds.SetProjection(projection)
out_ds.WriteArray(Pop_normalized )
out_ds.FlushCache()
out_ds = None

print("预测结果已经成功保存到：", output_file)