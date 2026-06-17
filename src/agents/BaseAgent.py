"""
@file: BaseAgent.py
@brief: 智能体基类文件，包括BaseAgent类
@author: 樊明
@date: start: 2025-11-13; end: 2025-11-14
@version: 1.0
"""
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
load_dotenv()


"""
@class: BaseAgent
@brief: 智能体类，统一管理 LLM 初始化
@see: 是InterParserAgent、DataDemandAgent、AlgorithmExeAgent的辅助类
"""
class BaseAgent:
    """
    @brief: 智能体基类初始化函数，提供统一的 LLM 初始化 
    @throw: 未找到DEEPSEEK_API_KEY、未能初始化mLlm时抛出错误
    """
    def __init__(self):
        #初始化密钥
        self.mStrApiKey = os.getenv("DEEPSEEK_API_KEY")
        if not self.mStrApiKey:
            raise ValueError("未找到 DEEPSEEK_API_KEY 环境变量，请检查 .env 文件")
        #初始化模型
        try:
            self.mLlm = init_chat_model(
                model="deepseek-chat",
                model_provider="deepseek", 
                api_key=self.mStrApiKey,
                temperature=0,
                max_tokens=1024,
                timeout=30
            )
        except Exception as e:
            raise ValueError(f"模型初始化失败: {e}")