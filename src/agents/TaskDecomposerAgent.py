"""
@file: TaskDecomposerAgent.py
@brief: 任务分解文件，包括TaskDecomposerResult类、TaskDecomposerAgent类
@author: 樊明
@date: start: 2025-12-01; end: 2025-12-04
       start: 2025-12-12; end: 2025-12-13
@version: 1.1
"""
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field
from typing import List


"""
@class: TaskDecomposerResult
@brief: 任务分解结果数据模型类
        包含简单任务列表和原始输入两个字段
@see: 是TaskDecomposerAgent的辅助类
"""
class TaskDecomposerResult(BaseModel):
    simple_tasks: List[str] = Field(description="分解后的简单任务列表，每个元素是一个完整的任务描述")
    original_input: str = Field(description="原始输入语句")


"""
@class: TaskDecomposerAgent
@brief: 复杂任务分解类，负责将复杂查询分解为多个简单任务
@see: 使用了辅助类TaskDecomposerResult
"""
class TaskDecomposerAgent():
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
        你是一个专业的任务分解器。你的任务是将复杂的土地利用查询分解为多个独立的简单任务。
        请根据用户查询的自然语义，结合以下原则，判断用户输入是否需要分解以及如何分解。

        核心原则：
        1. 只有当查询确实包含多个独立任务时才分解
        2. 每个分解后的任务都应该是完整、可独立执行的
        3. 保持原始查询的核心意图不变

        注意以下规则：
        1. 系统已预定义模拟/预测任务的驱动因子，不要将"考虑人口、经济因素"这样的表述分解为多个任务
        2. 当查询同时包含"模拟"和"展示"两种不同类型的任务时，必须按任务类型分解
        3. 当查询涉及多个完全不同时间点的相同任务时，可以按时间分解，对于连续时间范围（如"2021年到2025年"、"1999年-2004年"、"2005年至2010年"），应当依次分解
        4. 当查询涉及多个完全不同地点的相同任务时，可以按地点分解
           如果涉及到特殊区域，可参考如下的分解：
           - "粤港澳大湾区" 分解为 "广东省"、"香港特别行政区"、"澳门特别行政区"
           - "长三角" / "长三角地区" 分解为 "上海市"、"江苏省"、"浙江省"、"安徽省"
           - "京津冀" / "京津冀地区" 分解为 "北京市"、"天津市"、"河北省"
           - "中部六省" 分解为 "河南省"、"湖北省"、"湖南省"、"安徽省"、"江西省"、"山西省"
           - "江浙沪" 分解为 "江苏省"、"浙江省"、"上海市"
           - "全国" 分解为 "河北省"、"山西省"、"辽宁省"、"吉林省"、"黑龙江省"、"江苏省"、"浙江省"、"安徽省"、"福建省"、"江西省"、"山东省"、"河南省"、"湖北省"、"湖南省"、"广东省"、"海南省"、"四川省"、"贵州省"、"云南省"、"陕西省"、"甘肃省"、"青海省"、"台湾省"、"内蒙古自治区"、"广西壮族自治区"、"西藏自治区"、"宁夏回族自治区"、"新疆维吾尔自治区"、"北京市"、"天津市"、"上海市"、"重庆市"、"香港特别行政区"、"澳门特别行政区"
        
        示例：
        输入：分别考虑人口、经济因素，模拟2021年武汉市土地利用状况
        输出：{
        "simple_tasks": [
            "分别考虑人口、经济因素，模拟2021年武汉市土地利用状况"
            ]
        }
        
        输入：考虑人口、经济因素，模拟2021年武汉市土地利用状况
        输出：{
        "simple_tasks": [
            "考虑人口、经济因素，模拟2021年武汉市土地利用状况"
            ]
        }
        
        输入：考虑人口、经济因素，模拟2021年武汉市土地利用状况，并展示出2018年武汉市土地利用状况
        输出：{
        "simple_tasks": [
            "考虑人口和经济因素，模拟2021年武汉市土地利用状况",
            "展示2018年武汉市土地利用状况"
            ]
        }
        
        输入：模拟2021年到2025年武汉市土地利用状况
        输出：{
        "simple_tasks": [
            "模拟2021年武汉市土地利用状况",
            "模拟2022年武汉市土地利用状况", 
            "模拟2023年武汉市土地利用状况",
            "模拟2024年武汉市土地利用状况",
            "模拟2025年武汉市土地利用状况"
            ]
        }
        
        输入：模拟2021年-2025年武汉市土地利用状况
        输出：{
        "simple_tasks": [
            "模拟2021年武汉市土地利用状况",
            "模拟2022年武汉市土地利用状况",
            "模拟2023年武汉市土地利用状况",
            "模拟2024年武汉市土地利用状况",
            "模拟2025年武汉市土地利用状况"
            ]
        }
        
        输入：展示1999年至2004年武汉市土地利用状况
        输出：{
        "simple_tasks": [
            "展示1999年武汉市土地利用状况",
            "展示2000年武汉市土地利用状况",
            "展示2001年武汉市土地利用状况",
            "展示2002年武汉市土地利用状况", 
            "展示2003年武汉市土地利用状况",
            "展示2004年武汉市土地利用状况"
            ]
        }
        
        输入：预测2025年北京市和上海市的城市扩张情况
        输出：{
        "simple_tasks": [
            "预测2025年北京市城市扩张情况",
            "预测2025年上海市城市扩张情况"
            ]
        }
        
        输入：分别模拟2021年到2023年武汉市和北京市土地利用状况
        输出：{
        "simple_tasks": [
            "模拟2021年武汉市土地利用状况",
            "模拟2022年武汉市土地利用状况",
            "模拟2023年武汉市土地利用状况",
            "模拟2021年北京市土地利用状况",
            "模拟2022年北京市土地利用状况",
            "模拟2023年北京市土地利用状况"
            ]
        }
        
        输入：考虑人口因素，展示2018年、2020年和2022年武汉市土地利用状况
        输出：{
        "simple_tasks": [
            "考虑人口因素，展示2018年武汉市土地利用状况",
            "考虑人口因素，展示2020年武汉市土地利用状况",
            "考虑人口因素，展示2022年武汉市土地利用状况"
            ]
        }
        
        输入：模拟2021年武汉市土地利用状况
        输出：{
        "simple_tasks": [
            "模拟2021年武汉市土地利用状况"
            ]
        }
        
        输入：考虑人口和经济因素，预测2030年北京市城市扩张
        输出：{
        "simple_tasks": [
            "考虑人口和经济因素，预测2030年北京市城市扩张"
            ]
        }

        输入：预测2030年粤港澳地区的土地利用情况
        输出：{
        "simple_tasks": [
            "预测2030年广东省的土地利用情况",
            "预测2030年香港特别行政区的土地利用情况",
            "预测2030年澳门特别行政区的土地利用情况"
            ]
        }

        输入：模拟2025年京津冀地区的土地利用情况，并展示2025年京津冀地区的土地利用数据
        输出：{
        "simple_tasks": [
            "模拟2025年北京市的土地利用情况",
            "模拟2025年天津市地区的土地利用情况",
            "模拟2025年河北省地区的土地利用情况",
            "展示2025年北京市的土地利用数据",
            "展示2025年天津市地区的土地利用数据",
            "展示2025年河北省地区的土地利用数据"
            ]
        }
        只输出JSON格式的结果，不要解释。
        """
        
        # 创建Agent实例
        agent = create_agent(
            model=self.mLlm,
            tools=[],  # 不需要工具
            system_prompt=system_prompt,
            response_format=ToolStrategy(
                schema=TaskDecomposerResult,
                handle_errors=True
            )
        )
        return agent

    """
    @brief: 分解复杂任务
    @param strUserInput: 用户输入的复杂查询
    @return: TaskDecomposerResult的对象，包含分解后的简单任务列表和原始输入
    @note: 使用LangChain 1.0的Agent invoke方法，直接从structured_response获取结果
    """
    def run(self, strUserInput: str) -> TaskDecomposerResult:
        try:
            response = self.mAgent.invoke(
                {"messages": [{"role": "user", "content": f"请分解以下查询：{strUserInput}"}]}
            )
            objResult = response["structured_response"]  # 直接从structured_response获取解析结果
            objResult.original_input = strUserInput  # 确保原始输入正确设置
            return objResult
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Authentication" in error_msg or "invalid" in error_msg.lower():
                raise Exception("API认证失败，请检查API密钥是否正确")
            elif "timeout" in error_msg.lower():
                raise Exception("API请求超时，请检查网络连接")
            elif "OUTPUT_PARSING_FAILURE" in error_msg:
                raise Exception("任务分解失败，请检查提示词和模型兼容性")
            else:
                raise Exception(f"任务分解失败: {error_msg}")