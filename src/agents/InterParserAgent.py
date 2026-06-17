"""
@file: InterParserAgent.py
@brief: 用户输入解析文件，包括InterParserResult类、InterParserAgent类
@author: 许锦辉&樊明
@date: start: 2025-10-20; end: 2025-11-10
       start: 2025-11-13; end: 2025-11-13
       start: 2025-11-16; end: 2025-11-18
       start: 2025-12-15; end: 2025-12-16
       start: 2026-01-08; end: 2026-01-08
       start: 2026-01-30; end: 2026-01-30
@version: 2.4
"""
from langchain.chat_models.base import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field
from typing import Optional


"""
@class: InterParserResult
@brief: 用户输入解析结果数据模型类
        包含任务类型、时间、地点和原始输入四个字段
@see: 是InterParserAgent的辅助类
"""
class InterParserResult():
    task_type: int = Field(description="任务类型：0表示自然对话，1表示数据展示，2表示模拟和预测")
    time: Optional[str] = Field(description="时间信息，可能为None/str")
    location: Optional[str] = Field(description="地点信息，可能为None/str")
    original_input: str = Field(description="原始输入语句")
    """
    @brief: 初始化函数
    """
    def __init__(self):
        self.task_type = 0
        self.time = None
        self.location = None
        self.original_input = ""


"""
@class: InterParserAgent
@brief: 用户输入解析类，负责解析用户输入
@see: 使用了辅助类InterParserResult
"""
class InterParserAgent():
    """
    @brief: 初始化函数
    @param inputBaseAgent: 输入的基模型，用该模型初始化
    """
    def __init__(self, inputBaseAgent):  
        try:
            self.mLlm: BaseChatModel = inputBaseAgent.mLlm
        except Exception as e:
            raise Exception(f"InterParserAgent初始化失败: {e}") from e
    
    """
    @brief: 设置原始输入
    @param resultIPR: InterParserResult对象
    @param strUserInput: 用户输入字符串
    """
    def vSetOriginalInput(self, resultIPR: InterParserResult, strUserInput: str):
        try:
            resultIPR.original_input = strUserInput
        except Exception as e:
            raise Exception(f"设置原始输入失败: {e}") from e
    
    """
    @brief: 设置任务类型
    @param resultIPR: InterParserResult对象
    @param strUserInput: 用户输入字符串
    """
    def vSetTaskType(self, resultIPR: InterParserResult, strUserInput: str):
        try:
            # 构建系统提示词
            system_prompt = """
            你是一个任务类型识别专家。根据用户输入，判断任务类型。

            任务类型定义：
            0 (自然对话)：用户在进行一般的对话交流，这类问题既不是数据展示问题，也不是模拟/预测问题
            1 (数据展示)：用户请求查看或展示特定的数据，通常包含这样的关键词："展示"、"显示"、"查看"、"输出"、"呈现"、"数据"等
            2 (模拟和预测)：用户请求进行分析、模拟、预测，通常包含这样的关键词："模拟"、"预测"、"推演"、"分析"、"驱动"、"耦合"、"态势"等

            判断规则：
            1. 如果输入是纯粹的知识问答或一般对话，返回0
            2. 如果输入明确要求展示或查看数据，返回1
            3. 如果输入要求进行分析、模拟或预测，返回2

            示例：
            输入：C++是什么？ -> 输出：0
            输入：展示武汉市2023年土地覆盖数据 -> 输出：1
            输入：考虑人口和经济因素，模拟2021年武汉市土地利用状况 -> 输出：2
            输入：预测2025年北京市城市扩张 -> 输出：2
            输入：广东省的知名互联网企业有哪些？ -> 输出：0
            输入：查看2020年上海市经济数据 -> 输出：1

            注意：只输出数字（0、1或2），不要有任何额外的文本、解释或格式。
            """
            # 创建提示模板和链
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "请判断以下用户输入的任务类型：{input}")
            ])
            chain = prompt | self.mLlm | StrOutputParser()
            task_type_str = chain.invoke({"input": strUserInput})
            # 清理结果并转换为整数
            task_type_str = task_type_str.strip()
            resultIPR.task_type = int(task_type_str)
            # 验证任务类型值
            if resultIPR.task_type not in [0, 1, 2]:
                raise ValueError(f"无效的任务类型值: {resultIPR.task_type}")
        except ValueError as e:
            raise ValueError(f"任务类型设置失败: {e}") from e
        except Exception as e:
            raise Exception(f"任务类型设置失败: {e}") from e
    
    """
    @brief: 设置地点信息
    @param resultIPR: InterParserResult对象
    @param strUserInput: 用户输入字符串
    """
    def vSetLocation(self, resultIPR: InterParserResult, strUserInput: str):
        try:
            # 构建系统提示词
            system_prompt = """
            你是一个地点信息提取专家。根据用户输入，提取地点信息并进行标准化。

            地点标准化规则：
            1. 直辖市：直接使用"北京市"、"上海市"、"天津市"、"重庆市"
            2. 地级市：使用"省份+城市"格式，如"湖北省武汉市"、"江苏省南京市"、"广东省广州市"
            3. 省级单位：直接使用"湖北省"、"广东省"、"江苏省"等
            4. 自治区：使用"广西壮族自治区"、"新疆维吾尔自治区"等完整名称
            5. 特别行政区：使用"香港特别行政区"、"澳门特别行政区"

            简称标准化：
            "京"："北京市"，"沪"："上海市"，"津"："天津市"，"渝"："重庆市"
            "粤"："广东省"，"苏"："江苏省"，"浙"："浙江省"，"皖"："安徽省"
            "鄂"："湖北省"，"湘"："湖南省"，"豫"："河南省"，"赣"："江西省"

            格式示例：
            "武汉" -> "湖北省武汉市"
            "南京" -> "江苏省南京市"
            "成都" -> "四川省成都市"
            "广州" -> "广东省广州市"
            "深圳" -> "广东省深圳市"
            "北京" -> "北京市"
            "上海" -> "上海市"

            注意：
            1. 如果用户输入中没有明确的地点信息，返回"湖北省武汉市"
            2. 只输出标准化后的地点字符串，不要有任何额外的文本、解释或格式
            """
            # 创建提示模板和链
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "请从以下用户输入中提取并标准化地点信息：{input}")
            ])
            chain = prompt | self.mLlm | StrOutputParser()
            location = chain.invoke({"input": strUserInput})
            # 清理结果
            location = location.strip().strip('"').strip("'")
            resultIPR.location = location
        except Exception as e:
            raise Exception(f"地点设置失败: {e}") from e
    
    """
    @brief: 设置时间信息
    @param resultIPR: InterParserResult对象
    @param strUserInput: 用户输入字符串
    """
    def vSetTime(self, resultIPR: InterParserResult, strUserInput: str):
        try:
            # 构建系统提示词
            system_prompt = """
            你是一个时间信息提取专家。根据用户输入，提取时间信息。

            提取规则：
            1. 只提取一个具体的年份（如"2023"、"2021"等）
            2. 如果用户输入中包含多个年份，提取最相关的一个
            3. 如果用户输入中没有明确的时间信息，返回"2020"
            4. 只输出年份字符串，不要有任何额外的文本、解释或格式

            示例：
            输入：展示2023年武汉市土地覆盖数据 -> 输出：2023
            输入：预测2025年北京市城市扩张 -> 输出：2025
            输入：查看土地覆盖数据 -> 输出：2020
            输入：分析2018-2020年变化趋势 -> 输出：2020
            """
            # 创建提示模板和链
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "请从以下用户输入中提取时间信息（年份）：{input}")
            ])
            chain = prompt | self.mLlm | StrOutputParser()
            time = chain.invoke({"input": strUserInput})
            # 清理结果
            time = time.strip().strip('"').strip("'")
            resultIPR.time = time
        except Exception as e:
            raise Exception(f"时间设置失败: {e}") from e

    """
    @brief: 解析用户输入的自然语言，提取关键信息
    @param strUserInput: 用户输入的自然语言
    @return: InterParserResult的对象，解析后的结构化数据
    """
    def run(self, strUserInput: str) -> InterParserResult:
        try:
            # 1. 申请一个InterParserResult的对象resultIPR
            resultIPR = InterParserResult()
            # 2. 先通过vSetOriginalInput()函数设置resultIPR.original_input
            self.vSetOriginalInput(resultIPR, strUserInput)
            # 3. 在vSetTaskType()函数中，基于大语言模型设置resultIPR.task_type
            self.vSetTaskType(resultIPR, strUserInput)
            # 4. 根据task_type的不同进行处理
            if resultIPR.task_type == 0:
                # task_type == 0，设置location = None、设置time为None
                resultIPR.location = None
                resultIPR.time = None
            elif resultIPR.task_type in [1, 2]:
                # task_type == 1/2，依次调用vSetLocation()、vSetTime()
                self.vSetLocation(resultIPR, strUserInput)
                self.vSetTime(resultIPR, strUserInput)
            else:
                raise ValueError(f"未知的任务类型: {resultIPR.task_type}")
            return resultIPR
        except ValueError as e:
            raise ValueError(f"InterParserAgent执行失败: {e}") from e
        except Exception as e:
            raise Exception(f"InterParserAgent执行失败: {e}") from e