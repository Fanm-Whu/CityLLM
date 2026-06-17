"""
@file: __init__.py
@brief: agents 包初始化文件
@author: 许锦辉
@date: 2025-11-10
@version: 1.0
"""

# 包元数据
__version__ = "1.0.0"
__author__ = "许锦辉"
__description__ = "CityLLM项目Agents模块"

# 导入InterParserAgent.py, BaseAgent, TaskDecomposerAgent中的主要类，使其可以直接从包中导入
from .BaseAgent import BaseAgent
from .InterParserAgent import InterParserAgent, InterParserResult
from .TaskDecomposerAgent import TaskDecomposerAgent, TaskDecomposerResult
from .DataDemandAgent import DataDemandAgent, DataDemandResult
from .AlgorithmExeAgent import AlgorithmExeAgent, AlgorithmExeResult
from .ChainAgent import ChainAgent

# 定义包的公开接口
__all__ = [
    "BaseAgent",
    "InterParserAgent",
    "InterParserResult", 
    "TaskDecomposerAgent",
    "TaskDecomposerResult",
    "DataDemandAgent",
    "DataDemandResult",
    "AlgorithmExeAgent",
    "AlgorithmExeResult",
    "ChainAgent",
]