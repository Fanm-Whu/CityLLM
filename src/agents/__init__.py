"""
@file: __init__.py
@brief: agents 包初始化文件
@author: 许锦辉
@date: 2025-11-10
@version: 1.0
"""

# 导入包中的主要类，使其可以直接从包中导入
from .InterParserAgent import InterParserAgent, InterPaserResult, objCreateLandUseParser

# 定义包的公开接口
__all__ = [
    "InterParserAgent",
    "InterPaserResult", 
    "objCreateLandUseParser"
]

# 包元数据
__version__ = "1.0.0"
__author__ = "许锦辉"
__description__ = "基于 DeepSeek 的城市土地查询解析器"