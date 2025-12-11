"""
@file: InterParserAgent.py
@brief: 用户输入解析文件，包括InterParserResult类、InterParserAgent类
@author: 许锦辉
@date: start: 2025-10-20; end: 2025-11-10
       start: 2025-11-13; end: 2025-11-13
       start: 2025-11-14; end: 2025-11-14
       start: 2025-11-16; end: 2025-11-18
@version: 2.1 (升级到LangChain 1.0，增强多要素识别)
"""
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field
from typing import List, Optional


"""
@class: InterPaserResult
@brief: 用户输入解析结果数据模型类
        包含时间、地点、数据需求和原始输入四个字段
@see: 是InterParserAgent的辅助类
"""
class InterParserResult(BaseModel):
    time: Optional[List[str]] = Field(description="时间信息，格式为['起始年份', '结束年份']，如果只有一个年份则起始和结束相同")
    location: Optional[list[str]] = Field(description="地点信息，城市名称")
    data_requirement: Optional[List[str]] = Field(description="具体的数据需求列表，可以包含多个需求")
    original_input: str = Field(description="原始输入语句")


"""
@class: InterParserAgent
@brief: 用户输入解析类，负责解析用户输入
@see: 使用了辅助类InterParserResult
"""
class InterParserAgent():
    """
    @brief: 初始化函数，初始化了2个变量:
                mLlm: 使用的模型，接受外部参数
                agent: Agent实例
    @param inputBaseAgent: 输入的基模型，用该模型初始化
    """
    def __init__(self, inputBaseAgent):  
        self.mLlm = inputBaseAgent.mLlm
        self.mAgent = self.agentInit()
    
    """
    @brief: 初始化LangChain 1.0版本的Agent
    @return: 配置好的Agent实例
    @note: 使用ToolStrategy进行结构化输出，支持所有具备工具调用能力的模型
    """
    def agentInit(self):
        # 构建系统提示词
        system_prompt = """
        你是一个专业的城市土地数据查询解析器。你的任务只是分析用户输入，提取以下四个关键信息：
        1. **时间**：识别查询的时间范围，格式为['年份']
           - 如果没指定时间设为None                             
        2. **地点**：识别查询的城市名称
           - **行政级别标准化与格式规范**：
             * **直辖市**：直接使用"北京市"、"上海市"、"天津市"、"重庆市"
             * **地级市**：使用"省份+城市"格式，如"湖北省武汉市"、"江苏省南京市"、"广东省广州市"
             * **省级单位**：直接使用"湖北省"、"广东省"、"江苏省"等
             * **自治区**：使用"广西壮族自治区"、"新疆维吾尔自治区"等完整名称
             * **特别行政区**：使用"香港特别行政区"、"澳门特别行政区"
           - **特殊区域分解规则**：
             * "粤港澳大湾区" → ["广东省", "香港特别行政区", "澳门特别行政区"]
             * "长三角" / "长三角地区" → ["上海市", "江苏省", "浙江省", "安徽省"] 
             * "京津冀" / "京津冀地区" → ["北京市", "天津市", "河北省"]
             * "中部六省" → ["河南省", "湖北省", "湖南省", "安徽省", "江西省", "山西省"]
             * "江浙沪" → ["江苏省", "浙江省", "上海市"]
           - **简称标准化**：
             * "京" → "北京市"，"沪" → "上海市"，"津" → "天津市"，"渝" → "重庆市"
             * "粤" → "广东省"，"苏" → "江苏省"，"浙" → "浙江省"，"皖" → "安徽省"
             * "鄂" → "湖北省"，"湘" → "湖南省"，"豫" → "河南省"，"赣" → "江西省"
           - **格式示例**：
             * "武汉" → "湖北省武汉市"
             * "南京" → "江苏省南京市" 
             * "成都" → "四川省成都市"
             * "广州" → "广东省广州市"
             * "深圳" → "广东省深圳市"
             * "北京" → "北京市" (直辖市)
             * "上海" → "上海市" (直辖市)
           - 如果没指定地点设为None
        3. **数据需求**：描述用户具体需要什么数据
           - **核心土地数据需求**：城市扩张、土地利用、土地覆盖、耕地变化、建设用地变化等
           - **驱动因素数据需求**：人口数据、经济数据、GDP、人口密度、经济增长等
           - **其他数据需求**：卫星影像、遥感数据、NDVI、植被指数等
           - **重要规则**：
             * 区分核心土地数据需求、驱动因素数据需求与其他数据需求，优先将核心土地需求和驱动因素需求作为数据需求
             * 当用户明确请求其他数据（如"植被指数数据"）时，则也包含在数据需求中
             * 对于模拟和预测任务，必须提取所有提到的驱动因素
             * 如果用户的需求涉及城市功能区的模拟/预测, 在数据需求加入"土地利用"、"人口数据"、"经济数据", 同时数据需求中不得出现"城市功能区"
             * 如果用户的需求只是单纯的要求展示城市功能区数据，则正常在数据需求加入"城市功能区"。
           - **模拟预测场景示例**：
             * "驱动人口、经济因素，模拟武汉市的土地利用情况" → 数据需求: ["人口数据", "经济数据", "土地利用"]
             * "基于人口增长预测城市扩张" → 数据需求: ["人口数据", "城市扩张"]
             * "考虑GDP和交通因素的土地利用模拟" → 数据需求: ["GDP数据", "交通数据", "土地利用"]
             * "多情景耦合的城市土地利用模拟" → 数据需求: ["土地利用"]
             * "人口驱动的耕地变化预测" → 数据需求: ["人口数据", "耕地变化"]
           - **常规查询示例**：
             * "城市扩张卫星影像分析" → 数据需求: ["城市扩张"]
             * "耕地NDVI变化" → 数据需求: ["耕地变化"]
             * "土地利用数据和植被指数数据" → 数据需求: ["土地利用", "植被指数"]
             * "城市扩张和耕地变化监测" → 数据需求: ["城市扩张", "耕地变化"]
             * "基于遥感影像的土地利用分析" → 数据需求: ["土地利用"]
           - 如果没明确数据需求设为None
        4. **原始输入**：完整的用户原始输入语句
        重要说明：
        - 你只需要解析这四个字段，不要回答用户的问题
        - 不要添加任何解释或额外内容
        - 必须严格按照指定的结构化格式输出
        - **特别注意**：对于包含"驱动"、"模拟"、"预测"、"因素"等关键词的查询，要仔细识别所有相关数据需求"""
        empty_tools = []# 创建空工具列表
        # 创建Agent实例
        agent = create_agent(
            model=self.mLlm,
            tools=empty_tools,
            system_prompt=system_prompt,
            response_format=ToolStrategy(# 使用ToolStrategy进行结构化输出
              schema=InterParserResult,
              handle_errors=True  # 启用错误处理和重试
            )
        )
        return agent

    """
    @brief: 解析用户输入的自然语言，提取四个关键信息
    @param strUserInput: 用户输入的自然语言
    @return: InterPaserResult的对象，解析后的结构化数据，包含时间、地点、数据需求和原始输入
    @note: 使用LangChain 1.0的Agent invoke方法，直接从structured_response获取结果
    """
    def run(self, strUserInput: str) -> InterParserResult:
        try:
            response = self.mAgent.invoke(
                {"messages": [{"role": "user", "content": f"请解析以下用户输入：{strUserInput}"}]}
            )
            objResult = response["structured_response"] # 直接从structured_response获取解析结果
            objResult.original_input = strUserInput # 确保原始输入正确设置
            return objResult
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Authentication" in error_msg or "invalid" in error_msg.lower():
                raise Exception("API认证失败，请检查API密钥是否正确")
            elif "timeout" in error_msg.lower():
                raise Exception("API请求超时，请检查网络连接")
            elif "OUTPUT_PARSING_FAILURE" in error_msg:
                raise Exception("模型输出解析失败，请检查提示词和模型兼容性")
            else:
                raise Exception(f"API调用失败: {error_msg}")