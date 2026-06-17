"""
@file: __init__.py
@brief: src 包初始化文件
@author: 许锦辉
@date: 2025-11-10
@version: 1.0
"""

# 包元数据
__version__ = "1.0.0"
__author__ = "许锦辉"
__description__ = "CityLLM 项目src模块"

# 导入子包，使其可以通过 src 包直接访问
from . import agents
from . import algorithms
from . import ui
from . import utils

# 定义包的公开接口
__all__ = ["agents", "algorithms", "ui", "utils"]