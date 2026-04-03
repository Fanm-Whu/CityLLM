"""
@file: GeoProcessor.py
@brief: 地理数据处理工具模块，包含常见的GIS操作函数(目前有基于shp的tif裁剪、栅格数据标准化，预测建成区面积)
@author: 樊明
@date: start: 2026-01-29; end: 2026-02-01
@version: 1.0
"""
import os
from osgeo import gdal, ogr
import numpy as np


"""
@brief: 使用矢量shp文件裁剪栅格tif数据
@param raster_path: 输入栅格数据路径
@param shp_path: 矢量shp文件路径
@param output_path: 输出栅格数据路径
@return: bool - 成功裁剪返回 True，任何裁剪失败返回 False
"""
def bClipTifWithShp(strRasterPath: str, strShpPath: str, strOutputPath: str) -> bool:
    try:
        # 打开栅格数据
        rasterDataset = gdal.Open(strRasterPath)
        if not rasterDataset:
            print(f"无法打开栅格文件: {strRasterPath}")
            return False
        # 打开矢量数据
        shpDataset = ogr.Open(strShpPath)
        if not shpDataset:
            print(f"无法打开矢量文件: {strShpPath}")
            rasterDataset = None
            return False
        # 设置裁剪选项
        warpOption = gdal.WarpOptions(
            format='GTiff',
            cutlineDSName=strShpPath,
            cropToCutline=True,
            dstNodata=0)
        gdal.Warp(strOutputPath, rasterDataset, options=warpOption)  # 执行裁剪
        # 清理资源
        rasterDataset = None
        shpDataset = None
        # 检查输出文件是否创建成功
        if os.path.exists(strOutputPath):
            print(f"裁剪成功: {strOutputPath}")
            return True
        else:
            print(f"裁剪失败，输出文件未创建: {strOutputPath}")
            return False
    except Exception as e:
        print(f"裁剪过程中出错: {e}")
        return False
    
"""
@brief: 对已分配的人口和GDP栅格进行0-1标准化，并保存结果
@param strInputRasterPath: 输入的栅格数据路径
@param strInputDataType: 输入的栅格数据类型，主要有人口(pop)、GDP(gdp)两种，用来构建输出时的文件名
@param strInputDataYear: 输入的栅格数据年份，用来构建输出时的文件名
@return: bool - 成功返回 True，任何失败返回 False
"""
def strNormalizeRaster(strInputRasterPath: str, strInputDataType: str, nInputDataYear: int) -> str:
    try:
        strOutputDir = r"D:\Data\result\tmp"
        # 检查输入文件是否存在
        if not os.path.exists(strInputRasterPath):
            raise Exception(f"栅格文件不存在: {strInputRasterPath}") from e
        # 加载栅格数据
        inputRaster = gdal.Open(strInputRasterPath)
        if inputRaster is None:
            raise Exception(f"无法打开栅格文件: {strInputRasterPath}") from e
        inputRasterArray = inputRaster.GetRasterBand(1).ReadAsArray().astype(float)
        inputRasterArray[inputRasterArray < 0] = 0  # 处理可能的nodata负值
        # 获取投影和地理变换（以人口文件为准）
        projection = inputRaster.GetProjection()
        geotransform = inputRaster.GetGeoTransform()
        width = inputRaster.RasterXSize
        height = inputRaster.RasterYSize
        # 标准化
        min = inputRasterArray.min()
        max = inputRasterArray.max()
        if max <= min:
            raise Exception("栅格数据最大值 <= 最小值，无法标准化") from e
        pop_normalized = (inputRasterArray - min) / (max - min)
        # 输出路径 - 使用原文件名_normalized.tif
        strBaseName = os.path.splitext(os.path.basename(strInputRasterPath))[0]
        outputFilename = f"{strBaseName}_normalized.tif"
        outputPath = os.path.join(strOutputDir, outputFilename)
        driver = gdal.GetDriverByName('GTiff')
        ouputDs = driver.Create(
            outputPath,
            width, height, 1,
            gdal.GDT_Float32
        )
        ouputDs.SetProjection(projection)
        ouputDs.SetGeoTransform(geotransform)
        ouputDs.GetRasterBand(1).WriteArray(pop_normalized)
        ouputDs.FlushCache()
        ouputDs = None
        return outputPath
    except Exception as e:
        raise(f"标准化过程中发生错误: {e}") from e

"""
@brief: 给tif文件中值为0的位置添加一个微小值0.0001
@param strInputRasterPath: 输入的栅格数据路径
@return: str - 输出文件路径（原文件名_0.1.tif，保存于D:\Data\result\tmp）
@throw: Exception - 处理失败时抛出异常
"""
def strAddTinyValueAtZero4Tif(strInputRasterPath: str) -> str:
    try:
        strOutputDir = r"D:\Data\result\tmp"
        # 检查输入文件是否存在
        if not os.path.exists(strInputRasterPath):
            raise Exception(f"栅格文件不存在: {strInputRasterPath}")
        # 加载栅格数据
        inputRaster = gdal.Open(strInputRasterPath)
        if inputRaster is None:
            raise Exception(f"无法打开栅格文件: {strInputRasterPath}")
        inputRasterArray = inputRaster.GetRasterBand(1).ReadAsArray().astype(float)
        # 获取投影和地理变换
        projection = inputRaster.GetProjection()
        geotransform = inputRaster.GetGeoTransform()
        width = inputRaster.RasterXSize
        height = inputRaster.RasterYSize
        # 为0的位置添加微小值0.0001
        inputRasterArray[inputRasterArray == 0] = 0.0001
        # 构建输出路径：原文件名_0.1.tif
        strBaseName = os.path.splitext(os.path.basename(strInputRasterPath))[0]
        strOutputFilename = f"{strBaseName}_0.1.tif"
        strOutputRasterPath = os.path.join(strOutputDir, strOutputFilename)
        # 创建输出栅格
        driver = gdal.GetDriverByName('GTiff')
        outputDs = driver.Create(
            strOutputRasterPath,
            width, height, 1,
            gdal.GDT_Float32
        )
        outputDs.SetProjection(projection)
        outputDs.SetGeoTransform(geotransform)
        outputDs.GetRasterBand(1).WriteArray(inputRasterArray)
        outputDs.FlushCache()
        outputDs = None
        inputRaster = None
        return strOutputRasterPath
    except Exception as e:
        raise Exception(f"添加微小值过程中发生错误: {e}") from e