"""
@file: AlgorithmExeAgent.py
@brief: 算法执行文件，包括AlgorithmExeResult类、AlgorithmExeAgent类
@author: 樊明
@date: start: 2025-12-28; end: 2025-12-30
       start: 2026-01-20; end: 2026-01-21
@version: 1.1
"""
import os
from typing import List, Optional
from pydantic import Field
from src.agents import BaseAgent
from src.agents import DataDemandResult
from src.algorithms import bClipTifWithShp
from src.algorithms import MutiElementsSimulator
from langchain.chat_models.base import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


"""
@class: AlgorithmExeResult
@brief: 算法执行结果数据模型类
@see: 是AlgorithmExeAgent的返回结果类
"""
class AlgorithmExeResult():
    task_type: int = Field(description="任务类型：0-自然对话，1-数据展示，2-模拟预测")
    original_input: str = Field(description="用户的原始输入语句")
    result_paths: List[str] = Field(description="结果文件路径列表")
    result_names: Optional[List[str]] = Field(description="结果名称列表，数据展示任务中和DataDemandResult.data_require保持一致")
    exe_status: Optional[List[int]] = Field(description="执行状态列表：0-失败，1-成功")
    
    """
    @brief: 初始化函数
    @param nInputTaskType: 任务类型
    @param inputDataRequires: 数据需求列表
    @param strOriginalInput: 原始输入语句
    @param strLocation: 地点信息
    @param llm: 语言模型实例
    """
    def __init__(self, nInputTaskType: int, inputTime: Optional[str], inputDataRequires: Optional[List[str]], strOriginalInput: str, strLocation: Optional[str], nScenario: int, llm: BaseChatModel):
        try:
            # 验证任务类型和原始输入
            if nInputTaskType not in [0, 1, 2]:
                raise ValueError(f"未知的nTaskType值: {nInputTaskType}")
            if not strOriginalInput or not isinstance(strOriginalInput, str):
                raise ValueError(f"无效的原始输入: {strOriginalInput}")
            # 设置任务类型和原始输入
            task_type = nInputTaskType
            original_input = strOriginalInput
            input_time = inputTime
            # 根据任务类型初始化结果
            if nInputTaskType == 0:  # 自然对话任务
                if inputDataRequires is not None:
                    raise ValueError("自然对话任务的strDataRequires应为None")
                result_names = None
                result_paths = [""]  # 只有一个元素，用来存储模型回复
                exe_status = None
            elif nInputTaskType == 1:  # 数据展示任务
                if inputDataRequires is None:
                    raise ValueError("数据展示任务的strDataRequires不应为None")
                # 初始化结果列表和执行状态
                nResultNumbers = len(inputDataRequires)
                result_names = [""] * nResultNumbers
                result_paths = [""] * nResultNumbers
                exe_status = [0] * nResultNumbers
                # 使用LLM生成result_names
                self.vSetResultNames4TaskType1(result_names, inputDataRequires, strLocation, llm) 
            else:  # 模拟预测任务
                result_names = [""] * 3
                self.vSetResultNames4TaskType2(result_names, input_time, nScenario, strLocation)
                result_paths = []
                exe_status = []
            self.task_type=task_type
            self.original_input=original_input
            self.result_paths=result_paths
            self.result_names=result_names
            self.exe_status=exe_status
        except Exception as e:
            raise Exception(f"AlgorithmExeResult初始化失败: {e}") from e
    
    """
    @brief: 为数据展示任务设置result_names
    @param resultNamesListstr: 属性result_names，作为参数传递 
    @param dataRequiresListStr: 数据需求列表
    @param strLocation: 地点
    @see: 是__init__()的辅助函数
    """
    def vSetResultNames4TaskType1(self, resultNamesListStr: List[str], dataRequiresListStr: List[str], strLocation: str, llm: BaseChatModel):
        try:
            if not dataRequiresListStr:
                raise ValueError(f"未知的dataRequiresListStr值: {e}") from e
            # 构建系统提示词
            system_prompt = """
            你是一个数据名称生成专家。你的任务是根据原始数据需求描述和地点信息，生成更合适、更完整的结果名称。
            
            生成规则：
            1. 如果数据需求中已经包含具体的地点信息（如省份或城市名），则保持原样
            2. 如果数据需求中不包含地点信息，但提供了location参数，则将地点信息添加到数据需求中
            3. 生成的结果名称应该简洁明了，包含年份、地点和数据类型
            
            示例：
            输入: data_require="2020人口数据", location="湖北省武汉市" -> 输出: 2020湖北省武汉市人口数据
            输入: data_require="2021湖北省土地覆盖数据", location="湖北省" -> 输出: 2021湖北省土地覆盖数据
            输入: data_require="2020经济数据", location="北京市" ->  输出: 2020北京市经济数据
            输入: data_require="2019四川省土地数据", location="四川省" -> 输出: 2019四川省土地覆盖数据

            注意：只输出生成的结果名称字符串，不要添加任何额外的解释、引号或格式标记。
            """
            # 循环处理每个数据需求
            for i, data_require in enumerate(dataRequiresListStr):
                try:
                    user_content = f"""请根据以下原始数据需求描述和地点信息生成结果名称：data_require={data_require}, location={strLocation}"""  # 准备用户输入
                    # 创建提示词模板和链
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        ("user", "{query}")])
                    chain = prompt | llm | StrOutputParser()
                    strIthResultName = chain.invoke({"query": user_content})
                    strIthResultName = strIthResultName.strip().strip('"').strip("'")  # 清理结果（去除可能的引号和空白字符）
                    resultNamesListStr[i] = strIthResultName # 设置到self.result_names[i]
                except Exception as e:
                    raise Exception(f"处理数据需求'{data_require}'时失败: {e}") from e
        except Exception as e:
            raise Exception(f"result_names设置失败: {e}") from e
        
    """
    @brief: 为模拟预测任务设置result_names
    @param resultNamesListstr: 属性result_names，作为参数传递
    @param dataRequiresListStr: 数据需求列表
    @param strLocation: 地点
    @see: 这里无论用户要模拟的数据是什么，统一设置resultNamesListstr为目标年份、给定发展态势下的土地、人口、经济数据
          是__init__()的辅助函数
    """
    def vSetResultNames4TaskType2(self, resultNamesListStr: List[str], strTime: str, nScenario: int, strLocation: str):
        strScenario = "natural"
        if nScenario == 0:
            strScenario = "slow"
        elif nScenario == 1: 
            strScenario = "natural"
        elif nScenario == 2: 
            strScenario = "quick"
        resultNamesListStr[0] = f"land_{strTime}_{strScenario}_{strLocation}.tif"
        resultNamesListStr[1] = f"pop_{strTime}_{strScenario}_{strLocation}.tif"
        resultNamesListStr[2] = f"gdp_{strTime}_{strScenario}_{strLocation}.tif"



"""
@class: AlgorithmExeAgent
@brief: 算法执行智能体，负责执行具体算法任务
@see: 依赖DataDemandResult作为输入
"""
class AlgorithmExeAgent:
    """
    @brief: 初始化函数
    @param inputBaseAgent: BaseAgent实例，提供LLM模型
    @param dataDemandResult: DataDemandAgent的解析结果
    """
    def __init__(self, inputBaseAgent: BaseAgent, dataDemandResult: DataDemandResult):
        try:
            self.mLlm: BaseChatModel = inputBaseAgent.mLlm
            self.mInput: DataDemandResult = dataDemandResult
            self.nScenario = self.nIdentifyScenario(self.mInput.original_input, self.mLlm)
            self.mResultAlgorithmER: AlgorithmExeResult = AlgorithmExeResult(
                self.mInput.task_type,
                self.mInput.time,
                self.mInput.data_requires, 
                self.mInput.original_input, 
                self.mInput.location, 
                self.nScenario,
                self.mLlm)
        except Exception as e:
            raise Exception(f"AlgorithmExeAgent初始化失败: {e}") from e
        
    """
    @brief: 根据用户原始输入识别模拟的发展态势，返回对应的整数编码
    @param strOriginalInput: 用户的原始自然语言输入
    @param llm: LangChain的语言模型实例
    @return: int - 发展态势编码
             0 → 缓慢增长 (slow / 紧凑 / 限制扩张)
             1 → 自然增长 (natural / 基准 / 默认 / 无特别干预)
             2 → 快速增长 (fast / 蔓延 / 外延 / 摊大饼)
    @throw: ValueError - 如果模型输出无法解析为0/1/2
    """
    def nIdentifyScenario(self, strOriginalInput: str, llm: BaseChatModel) -> int:
        try:
            # 系统提示词（严格约束输出格式）
            system_prompt = """
            你是一个城市发展情景识别专家。

            你的唯一任务是根据用户输入判断他想要模拟的城市发展态势，并严格只输出以下三种数字之一：
            0 → 缓慢增长（紧凑发展、高密度、内填、限制外延、控制扩张、compact）
            1 → 自然增长（基准情景、自然发展、无特别干预、常规趋势、natural）
            2 → 快速增长（蔓延发展、低密度、外延扩张、摊大饼、sprawl）

            规则：
            - 如果用户明确提到“紧凑”“高密度”“限制蔓延”“内填式”“控制扩张”，输出 0
            - 如果用户提到“蔓延”“外延”“低密度”“摊大饼”“无限制扩张”“快速扩张”，输出 2
            - 如果用户没有明确倾向，或提到“自然”“基准”“常规”“不干预”“默认”，输出 1
            - 如果输入同时包含多种倾向，以最强烈的关键词为准；实在无法判断，默认输出 1

            示例：
            输入：模拟武汉市2035年在紧凑发展政策下的土地利用状况 -> 输出：0
            输入：请按自然发展趋势预测2030年武汉的土地、人口和经济 -> 只输出：1
            输入：考虑低密度蔓延情景，模拟2040年武汉市的土地、人口、经济状况 -> 只输出：2

            只输出一个数字：0 或 1 或 2，不要输出任何文字、解释、标点、空格或换行。
            """
            # 用户输入内容
            user_content = f"请根据以下用户输入识别发展态势，只输出0/1/2：\n{strOriginalInput}"
            # 创建提示词模板和链
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{query}")
            ])
            chain = prompt | llm | StrOutputParser()
            # 调用模型
            raw_output = chain.invoke({"query": user_content})
            cleaned = raw_output.strip()
            # 严格解析为整数
            if cleaned in ["0", "1", "2"]:
                nScenario = int(cleaned)
                return nScenario
            else:
                raise ValueError(f"模型输出有误，无法解析有效的nScenario: {cleaned}")
        except Exception as e:
            raise Exception(f"发展态势识别失败: {e}") from e

    """
    @brief: 处理自然对话任务
    @return: AlgorithmExeResult对象
    """
    def handelNaturalConverSation(self) -> AlgorithmExeResult:
        try:
            # 调用模型获取回复
            response = self.mLlm.invoke([
                {"role": "system", "content": "你是一个有帮助的助手。"},
                {"role": "user", "content": self.mResultAlgorithmER.original_input}
            ])
            # 设置结果路径为模型回复
            self.mResultAlgorithmER.result_paths[0] = response.content
            return self.mResultAlgorithmER
        except Exception as e:
            raise Exception(f"自然对话处理失败: {e}") from e

    """
    @brief: 处理数据展示任务
    @return: AlgorithmExeResult对象
    """
    def handleDataDisplay(self) -> AlgorithmExeResult:
        try:
            # 检查必要数据
            if not self.mInput.shp_path or not self.mInput.data_paths:
                raise ValueError("缺少必要的shp_path或data_paths数据")
            # 确保结果目录存在
            strResultDir = "D:\\Data\\result"
            os.makedirs(strResultDir, exist_ok=True)
            # 遍历所有数据需求
            for i in range(len(self.mInput.require_status)):
                strIthDataRequire = self.mInput.data_requires[i]
                strIthDataPath = self.mInput.data_paths[i]
                nIthRequireStatus = self.mInput.require_status[i]
                strIthResultName = self.mResultAlgorithmER.result_names[i]
                # 如果数据路径为空（数据不存在），设置对应结果
                if nIthRequireStatus == 0:
                    self.mResultAlgorithmER.result_paths[i] = ""
                    self.mResultAlgorithmER.exe_status[i] = 0
                    continue
                try:
                    # 构建输出路径
                    strIthOutputFileName = f"{strIthResultName}.tif"
                    strIthOuputPath = os.path.join(strResultDir, strIthOutputFileName)
                    # 使用shp裁剪tif数据
                    success = bClipTifWithShp(strIthDataPath, self.mInput.shp_path[0], strIthOuputPath)
                    #裁剪成功设置结果列表和执行状态列表
                    if success:
                        self.mResultAlgorithmER.result_paths[i] = strIthOuputPath
                        self.mResultAlgorithmER.exe_status[i] = 1
                    #裁剪失败
                    else:
                        self.mResultAlgorithmER.result_paths[i] = ""
                        self.mResultAlgorithmER.exe_status[i] = 0
                #意料之外的错误
                except Exception as e:
                    self.mResultAlgorithmER.result_paths[i] = ""
                    self.mResultAlgorithmER.exe_status[i] = 0
                    print(f"处理数据需求'{strIthDataRequire}'时出错")
            return self.mResultAlgorithmER
        except ValueError as e:
            raise ValueError(f"数据展示任务处理失败: {e}") from e
        except Exception as e:
            raise Exception(f"数据展示任务处理失败: {e}") from e
        
    """
    @brief: 处理模拟/预测任务
    @return: AlgorithmExeResult对象
    """
    def handleSimulation(self) -> AlgorithmExeResult:
        try:
            nTargetYear = int(self.mInput.time)
            if nTargetYear % 5 != 0:  # 检查年份是否为5的倍数
                raise ValueError(f"目标年份必须是5的倍数，当前输入: {nTargetYear}")
            if nTargetYear <= 2025:  # 检查年份是否大于2025
                raise ValueError(f"目标年份必须大于2025，当前输入: {nTargetYear}")
            print(f"\n开始执行模拟预测任务:")
            print(f"  目标年份: {nTargetYear}")
            print(f"  发展态势: {self.nScenario} ({'slow' if self.nScenario == 0 else 'natural' if self.nScenario == 1 else 'quick'})")
            print(f"  地点: {self.mInput.location}")
            # 创建多要素模拟器并执行模拟
            simulator = MutiElementsSimulator(
                nTargetYear=nTargetYear,
                nScenario=self.nScenario)
            simulateResult = simulator.run()
            # 设置结果路径（与result_names对应：土地、人口、GDP）
            self.mResultAlgorithmER.result_paths = [
                simulateResult.mStrTargetYearLandFunc,
                simulateResult.mStrTargetYearPop,
                simulateResult.mStrTargetYearGDP]
            # 设置执行状态（全部成功）
            self.mResultAlgorithmER.exe_status = [1, 1, 1]
            print(f"\n模拟预测任务完成!")
            print(f"  土地结果: {self.mResultAlgorithmER.result_paths[0]}")
            print(f"  人口结果: {self.mResultAlgorithmER.result_paths[1]}")
            print(f"  GDP结果: {self.mResultAlgorithmER.result_paths[2]}")
            return self.mResultAlgorithmER
        except ValueError as e:
            # 设置失败状态
            self.mResultAlgorithmER.result_paths = ["", "", ""]
            self.mResultAlgorithmER.exe_status = [0, 0, 0]
            raise ValueError(f"模拟预测任务处理失败: {e}") from e
        except Exception as e:
            # 设置失败状态
            self.mResultAlgorithmER.result_paths = ["", "", ""]
            self.mResultAlgorithmER.exe_status = [0, 0, 0]
            raise Exception(f"模拟预测任务处理失败: {e}") from e

    """
    @brief: 主执行函数
    @return: AlgorithmExeResult对象
    """
    def run(self) -> AlgorithmExeResult:
        try:
            nTaskType = self.mInput.task_type
            if nTaskType == 0:  # 自然对话任务
                return self.handelNaturalConverSation()
            elif nTaskType == 1:  # 数据展示任务
                return self.handleDataDisplay()
            elif nTaskType == 2:  # 模拟预测任务
                return self.handleSimulation()
            else:
                raise ValueError(f"未知的task_type值: {nTaskType}") from e
        except ValueError as e:
            raise ValueError(f"AlgorithmExeAgent执行失败: {e}") from e
        except Exception as e:
            raise Exception(f"AlgorithmExeAgent执行失败: {e}") from e