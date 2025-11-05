"""
@file: linterParserAgent.py
@brief: 基于 DeepSeek 的城市土地查询解析器
@author: 许锦辉
@date: start: 2025-10-20; end: 2025-11-05
@version: 1.0
"""

import os
from dotenv import load_dotenv
from langchain.schema import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional

# 加载环境变量
load_dotenv()

"""
@class: LandUseQuery
@brief: 土地查询解析结果数据模型
    包含时间、地点、数据需求和原始输入四个字段
"""

class LandUseQuery(BaseModel):
    """土地查询解析结果"""
    time: Optional[List[str]] = Field(description="时间信息，格式为['起始年份', '结束年份']，如果只有一个年份则起始和结束相同")
    location: Optional[str] = Field(description="地点信息，城市名称")
    data_requirement: Optional[str] = Field(description="具体的数据需求描述")
    original_input: str = Field(description="原始输入语句")

"""
@class: DeepSeekInterParserAgent
@brief: DeepSeek 解析代理类
    负责初始化模型和解析用户输入
"""

class DeepSeekInterParserAgent:
    """
    @brief: 初始化 DeepSeek 解析代理
    @throws: 当环境变量中未找到 DEEPSEEK_API_KEY 时抛出 ValueError
    """
    def __init__(self):
        # 从环境变量获取 DeepSeek API 密钥
        self.mStrApiKey = os.getenv("DEEPSEEK_API_KEY")
        if not self.mStrApiKey:
            raise ValueError("未找到 DEEPSEEK_API_KEY 环境变量，请检查 .env 文件")
        
        # 初始化 DeepSeek 模型 
        self.mLlm = init_chat_model(
            model="deepseek-chat",
            model_provider="deepseek", 
            api_key=self.mStrApiKey,
            temperature=0,
            max_tokens=1024,
            timeout=30
        )
        
        self.mParser = PydanticOutputParser(pydantic_object=LandUseQuery)
        
        # 构建系统提示词 
        self.mSystemMessage = SystemMessage(content=f"""
        你是一个专业的城市土地数据查询解析器。你的任务只是分析用户输入，提取以下四个关键信息：
        
        1. **时间**：识别查询的时间范围，格式为['起始年份', '结束年份']
           - 如果用户说"近5年"，计算为当前年份-4到当前年份
           - 如果只有一个年份，起始和结束年份相同
           - 如果没指定时间，设为None
        
        2. **地点**：识别查询的城市名称
           - 优先提取地级市以上城市名称
           - 支持简称如"京"代表北京，"沪"代表上海
        
        3. **数据需求**：描述用户具体需要什么土地数据
           - 土地数据关键词：土地利用、土地覆盖、耕地、建设用地、林地、草地、水域、城市扩张、土地变化、土地类型、土地面积等
           - 遥感数据关键词：遥感影像、卫星图像、NDVI、植被指数等
        
        4. **原始输入**：完整的用户输入语句
        
        重要说明：
        - 你只需要解析这四个字段，不要回答用户的问题
        - 不要添加任何解释或额外内容
        - 必须严格按照指定JSON格式输出
        
        {self.mParser.get_format_instructions()}
        """)
    
    """
    @brief: 解析用户输入的自然语言，提取四个关键信息
    @param strUserInput: 用户输入的自然语言
    @return: LandUseQuery 解析后的结构化数据，包含时间、地点、数据需求和原始输入
    @note: 时间复杂度: O(1)，其中1是API调用次数
            空间复杂度: O(n)，其中n是输入字符串长度
    """
    def objParseQuery(self, strUserInput: str) -> LandUseQuery:
        try:
            # 构建消息 
            listMessages = [
                self.mSystemMessage,
                HumanMessage(content=f"请解析以下用户输入：{strUserInput}")
            ]
            
            # 调用 DeepSeek 模型
            response = self.mLlm.invoke(listMessages)
            
            # 解析输出
            objResult = self.mParser.parse(response.content)
            objResult.original_input = strUserInput
            
            # 后处理：确保时间格式正确
            if objResult.time and isinstance(objResult.time, list):
                objResult.time = self._listNormalizeTime(objResult.time)
            
            return objResult
            
        except Exception as e:
            print(f"解析过程中出现错误: {e}")
            # 返回默认结果
            return LandUseQuery(
                time=None,
                location=None,
                data_requirement=None,
                original_input=strUserInput
            )
    
    """
    @brief: 标准化时间格式
    @param listTime: 时间列表，格式为['起始年份', '结束年份']
    @return: 标准化后的时间列表，如果格式无效则返回None
    @note: 时间复杂度: O(1)
            空间复杂度: O(1)
    """
    def _listNormalizeTime(self, listTime: List[str]) -> List[str]:
        if not listTime or len(listTime) < 2:
            return None
        
        strStartYear = str(listTime[0]).strip()
        strEndYear = str(listTime[1]).strip()
        
        # 简单的年份验证（1900-2100之间）
        if (strStartYear.isdigit() and strEndYear.isdigit() and 
            1900 <= int(strStartYear) <= 2100 and 
            1900 <= int(strEndYear) <= 2100):
            return [strStartYear, strEndYear]
        
        return None

"""
@class: LandUseSystem
@brief: 基于 DeepSeek 的城市土地模拟系统 - 仅解析版本
    负责系统初始化和用户输入解析
"""

class LandUseSystem:
    """
    @brief: 初始化土地用途系统
    @throws: 当 DeepSeekInterParserAgent 初始化失败时抛出异常
    """
    def __init__(self):
        try:
            self.mObjParserAgent = DeepSeekInterParserAgent()
            print("✅ DeepSeek 解析代理初始化成功")
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            raise
    
    """
    @brief: 解析用户输入，返回结构化数据
    @param strUserInput: 用户输入的自然语言
    @return: LandUseQuery 解析后的结构化数据
    @note: 时间复杂度: O(1)，主要取决于API调用
            空间复杂度: O(n)，其中n是输入字符串长度
    """
    def objParseUserInput(self, strUserInput: str) -> LandUseQuery:
        print(f"🔍 开始解析用户输入: {strUserInput}")
        
        # 解析用户输入
        objResult = self.mObjParserAgent.objParseQuery(strUserInput)
        
        print(f"📊 解析完成")
        return objResult

"""
@brief: 主函数 - 命令行交互界面
@return: 无
@note: 时间复杂度: O(m)，其中m是用户输入的查询次数
        空间复杂度: O(n)，其中n是单个查询的长度
"""
def main():
    print("=" * 60)
    print("       城市土地模拟系统 - InterParserAgent (仅解析版)")
    print("=" * 60)
    print()
    
    try:
        # 初始化系统
        objSystem = LandUseSystem()
        
        print("✅ 系统初始化成功！")
        print()
        print("使用说明：")
        print("- 输入任何查询，系统会解析时间、地点、数据需求和原始输入")
        print("- 解析结果将传递给后续处理步骤")
        print("- 输入 '退出' 或 'exit' 结束程序")
        print()
        print("示例：")
        print("  - 北京市2015-2020年土地利用变化")
        print("  - 上海市耕地面积统计")
        print("  - Python是什么编程语言？")
        print("  - 今天的天气怎么样？")
        print()
        
        while True:
            print("-" * 40)
            strUserInput = input("请输入您的查询: ").strip()
            
            if strUserInput.lower() in ['退出', 'exit', 'quit']:
                print("感谢使用！再见！")
                break
            
            if not strUserInput:
                print("输入不能为空，请重新输入。")
                continue
            
            # 解析查询
            objResult = objSystem.objParseUserInput(strUserInput)
            
            print()
            print("📋 解析结果:")
            print(f"   时间: {objResult.time}")
            print(f"   地点: {objResult.location}")
            print(f"   数据需求: {objResult.data_requirement}")
            print(f"   原始输入: {objResult.original_input}")
            
            print()
            print("💡 提示: 这些解析结果已准备好传递给后续处理步骤")
            print()
            
    except Exception as e:
        print(f"❌ 系统运行出错: {e}")
        print("请检查：")
        print("1. 是否在 .env 文件中设置了 DEEPSEEK_API_KEY")
        print("2. API密钥是否有效")
        print("3. 网络连接是否正常")

"""
@brief: 创建并返回一个土地用途解析器实例
@return: LandUseSystem 初始化的土地用途解析系统
@note: 时间复杂度: O(1)
        空间复杂度: O(1)
"""
def objCreateLandUseParser():
    return LandUseSystem()

if __name__ == "__main__":
    # 直接运行此文件时启动命令行交互界面
    main()