"""
@file: __init__.py
@brief: algorithms 包初始化文件
@author: 许锦辉
@date: 2026-01-25
@version: 1.0
"""

# 包元数据
__version__ = "1.0.0"
__author__ = "樊明"
__description__ = "CityLLM项目Algorithms模块"

# 导入Simulation.py中的主要类，使其可以直接从包中导入
from .ImprovedCA import ImprovedCA
from .LandSimulator import LandSimulator
from .PopulationSimulator import PopulationSimulator
from .GDPSimulator import GDPSimulator
from .MutiElementsSimulator import MutiElementsSimulator
from .GeoProcessor import bClipTifWithShp
from .GeoProcessor import strNormalizeRaster
from .SimulateHelper import predictLandFuncPixel
from .SimulateHelper import predictGDP

# 定义包的公开接口
__all__ = [
    "ImprovedCA",
    "LandSimulator",
    "PopulationSimulator",
    "GDPSimulator",
    "MutiElementsSimulator",
    "bClipTifWithShp",
    "strNormalizeRaster",
    "predictLandFuncPixel",
    "predictGDP"
]