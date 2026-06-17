"""
@file: DataDemandAgent.py
@brief: 数据需求处理文件，包括DataDemandResult类、DataDemandAgent类
@author: 樊明
@date: start: 2025-11-18; end: 2025-11-18
       start: 2025-12-17; end: 2025-12-18
@version: 1.1
"""
from .InterParserAgent import InterParserResult
from langchain.chat_models.base import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional, List
from pydantic import Field


"""
@class: DataDemandResult
@brief: 数据需求解析结果数据模型类
@see: 是DataDemandAgent的返回结果类
"""
class DataDemandResult():
    task_type: int = Field(description="任务类型：0-自然对话，1-数据展示，2-模拟预测")
    time: Optional[str] = Field(description="时间信息，可能为None/str")
    original_input: str = Field(description="用户的原始输入语句")
    location: Optional[str] = Field(description="地点信息，可能为None/str")
    admin_level: Optional[int] = Field(description="行政等级：0-省级，1-地级，2-县级，None-未知或无")
    shp_path: Optional[List[str]] = Field(description="行政边界shp文件路径列表，一般长度为1")
    data_requires: Optional[List[str]] = Field(description="数据需求描述列表，使用结构化语言描述")
    data_paths: Optional[List[str]] = Field(description="对应数据需求的实际文件路径列表")
    require_status: Optional[List[int]] = Field(description="数据检索状态列表：0-没找到，1-找到了")
    """
    @brief: 初始化函数
    @param nTaskType: 数据需求列表
    @param strOriginalInput: 原始输入语句
    """
    def __init__(self, nTaskType: int, strOriginalInput: str, strLocation: str, strTime: str):
        try:
            self.task_type = nTaskType
            self.time = strTime
            self.original_input = strOriginalInput
            self.location = strLocation
            self.admin_level = None
            self.shp_path = None
            self.data_requires = None
            self.data_paths = None
            self.require_status = None
        except Exception as e:
            raise Exception(f"DataDemandResult初始化失败: {e}") from e
        


"""
@class: DataDemandAgent
@brief: 数据需求分析智能体，负责解析数据需求并检索数据路径
@see: 依赖InterParserResult作为输入
"""
class DataDemandAgent:
    """
    @brief: 初始化函数
    @param inputBaseAgent: BaseAgent实例，提供LLM模型
    @param interParserResult: InterParserAgent的解析结果
    """
    def __init__(self, inputBaseAgent, interParserResult):
        try:
            self.mLlm: BaseChatModel = inputBaseAgent.mLlm
            self.mInput: InterParserResult = interParserResult
            self.mResultDataDR: DataDemandResult = DataDemandResult(self.mInput.task_type, self.mInput.original_input, self.mInput.location, self.mInput.time)
        except Exception as e:
            raise Exception(f"DataDemandAgent初始化失败: {e}") from e

    
    """
    @brief: 主执行函数，依次执行各个步骤
    @return: DataDemandResult对象
    """
    def run(self) -> DataDemandResult:
        try:
            nTaskType = self.mInput.task_type
            if nTaskType not in [0, 1, 2]:
                raise ValueError(f"未知的nTaskType值: {nTaskType}") from e
            # 对于自然对话任务，直接返回基本结果，不需要数据需求分析
            if nTaskType == 0:
                return self.mResultDataDR
            # 对于数据展示和模拟预测任务，执行完整的数据需求分析流程
            elif nTaskType == 1:
                try:
                    self.vSetAdminLevel() # 设置行政等级
                    self.vSetShpPath() # 设置shp路径
                    self.vSetDataRequires() # 设置数据需求列表
                    self.vSetDataPathsAndRequireStatuses() # 设置数据路径列表和数据需求状态列表
                    return self.mResultDataDR
                except Exception as e:
                    raise Exception(f"数据展示任务DataDemandAgent执行失败: {e}") from e
            elif nTaskType == 2:
                try:
                    if self.mResultDataDR.location != "湖北省武汉市":
                        raise ValueError(f"仅支持湖北省武汉市的模拟任务，选择的location是: {e}") from e
                    nTime = int(self.mResultDataDR.time)
                    if nTime <= 2025 or nTime%5 != 0:
                        raise ValueError(f"模拟任务时间有误，选择的time是: {e}") from e
                    else:
                        self.mResultDataDR.admin_level = 1 # 设置行政等级
                        self.mResultDataDR.shp_path = "D:\\Data\\data\\shp\\city\\湖北省\\武汉市\\武汉市.shp" # 设置shp路径
                        self.mResultDataDR.data_requires = None # 设置数据需求列表
                        self.mResultDataDR.data_paths = None # 设置数据路径列表
                        self.mResultDataDR.require_status = None # 设置数据需求状态列表
                        return self.mResultDataDR
                except Exception as e:
                    raise Exception(f"模拟预测任务DataDemandAgent执行失败: {e}") from e
        except Exception as e:
                    raise Exception(f"DataDemandAgent执行失败: {e}") from e
    
    """
    @brief: 设置行政等级
    @note: 基于location信息判断行政级别
    """
    def vSetAdminLevel(self):
        systemPrompt = """
        你是一个行政级别判断专家。根据给定的地点名称，判断其行政级别。

        行政级别定义：
        0 - 省级（省、自治区、直辖市、特别行政区）
        1 - 地级（地级市、地区、自治州、盟）
        2 - 县级（市辖区、县级市、县、自治县、旗、自治旗）

        示例：
        输入：新疆市石河子市 -> 输出：1
        输入：湖北省武汉市 -> 输出：1
        输入：湖北省 -> 输出：0
        输入：北京市 -> 输出：0

        只输出数字，不要解释。
        """
        try:
            strLocation = self.mInput.location
            if not strLocation: # 地址为空
                raise ValueError("mInput.location属性值为空")
            response = self.mLlm.invoke([
                {"role": "system", "content": systemPrompt},
                {"role": "user", "content": f"判断以下地点的行政级别：{strLocation}"}])
            nAdminLevel = response.content.strip()
            self.mResultDataDR.admin_level = int(nAdminLevel)
        except ValueError as e:
            raise ValueError(f"行政等级判别失败，数值错误: {e}") from e
        except Exception as e:
            raise Exception(f"行政等级判别失败，未预期的错误: {e}") from e
    
    """
    @brief: 设置shp文件路径
    @note: 基于location信息和admin_level设置shp文件路径
    """
    def vSetShpPath(self):
        try:
            strLocation = self.mInput.location
            if not strLocation:
                raise ValueError("mInput.location属性值为空")
            nAdminLevel = self.mResultDataDR.admin_level
            if nAdminLevel not in [0, 1, 2]:
                raise ValueError("mInput.admin_level属性值为空")
            # 根据admin_level选择不同的提示词
            if nAdminLevel == 0:  # 省级
                systemPrompt = """
                你是一个地理信息系统路径生成专家。根据给定的省级地点名称，生成对应的shp文件路径。
                
                数据存储结构说明：
                D:\\Data\\data\\shp\\province\\[省份名称]\\[省份名称].shp
                
                示例：
                输入：湖北省 -> 输出：D:\\Data\\data\\shp\\province\\湖北省\\湖北省.shp
                输入：北京市 -> 输出：D:\\Data\\data\\shp\\province\\北京市\\北京市.shp
                输入：广西壮族自治区 -> 输出：D:\\Data\\data\\shp\\province\\广西壮族自治区\\广西壮族自治区.shp
                
                输出一个完整文件路径，不要解释，不要使用任何引号、括号或其他标记。
                """
            elif nAdminLevel == 1:  # 地级
                systemPrompt = """
                你是一个地理信息系统路径生成专家。根据给定的地级市地点名称，生成对应的shp文件路径。
                
                数据存储结构说明：
                D:\\Data\\data\\shp\\city\\[省份名称]\\[城市名称]\\[城市名称].shp
                
                注意：你需要先从城市名称中提取省份信息。
                
                示例：
                输入：湖北省武汉市 -> 输出：D:\\Data\\data\\shp\\city\\湖北省\\武汉市\\武汉市.shp
                输入：广东省广州市 -> 输出：D:\\Data\\data\\shp\\city\\广东省\\广州市\\广州市.shp
                输入：江苏省南京市 -> 输出：D:\\Data\\data\\shp\\city\\江苏省\\南京市\\南京市.shp
                
                输出一个完整文件路径，不要解释，不要使用任何引号、括号或其他标记。
                """
            # elif nAdminLevel == 2:  # 县级
            #     system_prompt = """
            #     你是一个地理信息系统路径生成专家。根据给定的县级地点名称，生成对应的shp文件路径。
                
            #     数据存储结构：
            #     D:/Data/process_data/shp/county/[省份名称]/[城市名称]/[区县名称].shp
                
            #     注意：你需要先从区县名称中提取省份和城市信息。
                
            #     示例：
            #     输入：武汉市武昌区 -> 输出：D:/Data/process_data/shp/county/湖北省/武汉市/武昌区.shp
            #     输入：北京市朝阳区 -> 输出：D:/Data/process_data/shp/county/北京市/北京市/朝阳区.shp
            #     输入：广州市天河区 -> 输出：D:/Data/process_data/shp/county/广东省/广州市/天河区.shp
                
            #     只输出完整的文件路径，不要解释。
            #     """
            else:
                raise ValueError(f"未知的nAdminLevel值：{nAdminLevel}")
            # 创建提示模板
            systemPrompt = ChatPromptTemplate.from_messages([
                ("system", systemPrompt),
                ("user", "请生成以下地点的shp文件路径：{location}")
            ])
            chain = systemPrompt | self.mLlm | StrOutputParser() # 创建链：提示词 -> 模型 -> 输出解析器
            strShpPath = chain.invoke({"location": strLocation}) # 调用链并获取结果
            strShpPath = strShpPath.strip().strip('"').strip("'") # 清理可能的空白字符和引号
            self.mResultDataDR.shp_path = [strShpPath]
        except ValueError as e:
            raise ValueError(f"shp文件路径设置失败: {e}") from e
        except Exception as e:
            raise Exception(f"shp文件路径设置失败: {e}") from e
    
    """
    @brief: 设置数据需求列表data_requires
    @note: 加载提示词模板，设置数据需求为结构化语句，使用JsonOutputParser()进行结构化输出
    """
    def vSetDataRequires(self):
        try:
            nTaskType = self.mResultDataDR.task_type
            # 根据任务类型选择不同的提示词
            if nTaskType == 1:  # 数据展示
                # 构建系统提示词
                systemPrompt = """
                你是一个专业的地理数据需求分析专家。根据用户查询，分析用户需要展示的具体数据项。如果用户查询中包含多个数据需求，需要分别提取

                系统可用数据说明：
                1. 土地覆盖数据：
                   - 数据范围：2000-2021年
                   - 空间范围：中国34个省级行政单位
                   - 数据格式：.tif文件
                   - 命名规则：[年份][省份][土地覆盖数据]
                   - 用户可能使用的替代说法：土地数据、土地覆盖、用地类型、地表覆盖、土地资源等
                2. 人口数据：
                   - 数据范围：年度数据
                   - 空间范围：全国汇总，不区分省份
                   - 数据格式：.tif文件
                   - 命名规则：[年份][人口数据]
                   - 用户可能使用的替代说法：人口数量、人口密度、人口分布、人口统计等
                3. 经济数据：
                   - 数据范围：年度数据
                   - 空间范围：全国汇总，不区分省份
                   - 数据格式：.tif文件
                   - 命名规则：[年份][经济数据]
                   - 用户可能使用的替代说法：经济指标、GDP数据、经济统计、经济状况等

                数据需求提取规则：
                1. 对于土地覆盖数据：需要根据用户指定的地点和时间，确定对应的省份数据
                   - 如果用户只提到省级单位，直接使用该省份
                   - 如果用户提到市级或县级单位，需要找到所属省份
                   - 示例：输入："时间：2021，地点：湖北省武汉市，查询：展示2021年武汉市土地覆盖数据" -> 输出：["2021湖北省土地覆盖数据"]
                2. 对于人口数据：只需要时间，不需要地点
                   - 示例：输入："时间：2021，地点：湖北省武汉市，查询：展示2021年武汉市人口数据" -> 输出：["2021人口数据"]
                3. 对于经济数据：只需要时间，不需要地点
                   - 示例：输入："时间：2021，地点：湖北省武汉市，查询：展示2021年武汉市经济数据" -> 输出：["2021经济数据"]
                4. 对于除土地覆盖数据、人口数据、经济数据以外的数据：使用[时间]+[地点]+[数据]的方式
                   - 示例：输入："时间：2023，地点：湖北省武汉市，查询：展示2023年武汉市天气数据" -> 输出：["2023湖北省武汉市天气数据"]
                5. 如果用户没有指定数据需求，返回空字符串
                   - 示例：输入："时间：2023，地点：湖北省武汉市，查询：展示2023武汉市数据" -> 输出：[""]

                示例：
                输入："时间：2023，地点：湖南省益阳市，查询：展示2023年益阳市地表覆盖数据、并输出该地的人口分布图" -> 输出：["2023湖南省土地覆盖数据", "2023人口数据"]
                输入："时间：2018，地点：新疆维吾尔自治区石河子市，查询：展示2018年石河子市土地利用情况、并显示同年经济数据" -> 输出：["2018新疆维吾尔自治区经济数据", "2018经济数据"]

                输出要求：
                输出一个JSON格式的列表，例如：["2021湖北省土地覆盖数据", "2021人口数据"]。不要有任何额外的文本、解释或markdown标记。
                """
                # 创建提示模板
                strDataRequireQuery = f"时间：{self.mInput.time}，地点：{self.mInput.location}，用户原始输入：{self.mResultDataDR.original_input}" # 构建查询信息
                systemPrompt = ChatPromptTemplate.from_messages([
                    ("system", systemPrompt),
                    ("user", "请分析以下用户查询的数据需求：{query}")
                ])
                chain = systemPrompt | self.mLlm | JsonOutputParser() # 创建链：提示词 -> 模型 -> 输出解析器
                dataRequireListStr = chain.invoke({"query": strDataRequireQuery}) # 调用链并获取结果
                if dataRequireListStr == "":
                    raise ValueError("查询语句有误，检测不到数据需求")
                else:
                    self.mResultDataDR.data_requires = dataRequireListStr
            else:
                raise ValueError(f"未知的nTaskType值: {nTaskType}")
        except ValueError as e:
            raise ValueError(f"数据需求分析失败: {e}") from e
        except Exception as e:
            raise Exception(f"数据需求分析失败: {e}") from e
    
    """
    @brief: 设置数据路径列表data_paths和检索状态列表require_status
    @note: 加载提示词，设置数据路径列表，和检索状态列表，使用StrOutputParser()进行结构化输出。
    """
    def vSetDataPathsAndRequireStatuses(self):
        try:
            # 初始化列表
            nDataRequireLen = len(self.mResultDataDR.data_requires)
            if nDataRequireLen == 0:
                raise ValueError(f"未知的nDataRequireLen值：{nDataRequireLen}")
            else:
                self.mResultDataDR.data_paths = [""] * nDataRequireLen
                self.mResultDataDR.require_status = [0] * nDataRequireLen
            # 加载提示词，每次处理的是self.mResultDataDR.data_require列表中的单个元素，也就是单个数据需求。
            if self.mInput.task_type == 1: # 数据展示任务
                system_prompt = """
                你是一个数据路径生成器。根据给定的数据需求，生成对应的文件路径。

                系统现有数据说明：
                1. 土地覆盖数据：
                   - 存储路径：D:\\Data\\data\\land\\[年份]\\[省份].tif
                   - 示例：输入：2021湖北省土地覆盖数据 -> 输出：D:\\Data\\data\\land\\2021\\湖北省.tif
                   - 数据范围：2000-2021年，34个省级行政单位
                2. 人口数据：
                   - 存储路径：D:\\Data\\data\\population\\[年份].tif
                   - 示例：输入：2021人口数据 -> 输出：D:\\Data\\data\\population\\2021.tif
                   - 数据范围：2000-2022年，全国汇总
                3. 经济数据：
                   - 存储路径：D:\\Data\\data\\gdp\\[年份].tif
                   - 示例：输入：2021经济数据 -> 输出：D:\\Data\\data\\gdp\\2021.tif
                   - 数据范围：2000年、2005年、2010年、2015年、2020年，全国汇总
                
                数据路径生成规则：
                1. 如果数据需求匹配以上三种数据类型，返回对应的完整文件路径
                2. 如果数据需求不匹配以上数据类型（如天气数据、交通数据等），返回空字符串
                3. 数据年份必须严格匹配，否则返回空字符串：
                   - 对于土地覆盖数据：年份必须在2000-2021范围内（包含2000和2021）
                   - 对于人口数据：年份必须在2000-2022范围内（包含2000和2022）
                   - 对于经济数据：年份必须是以下之一：2000、2005、2010、2015、2020

                示例：
                输入：2021湖北省土地覆盖数据 -> 输出：D:\\Data\\data\\land\\2021\\湖北省.tif
                输入：2021人口数据 -> 输出：D:\\Data\\data\\population\\2021.tif
                输入：2020经济数据 -> 输出：D:\\Data\\data\\gdp\\2020.tif
                输入：2021经济数据 -> 输出：""
                输入：2021湖北省武汉市天气数据 -> 输出：""
                输入：2022湖北省武汉市交通数据 -> 输出：""
                
                注意：只返回文件路径，不要解释。如果数据不存在，返回空字符串。
                """
            else:
                raise ValueError(f"未知的task_type值：{self.mInput.task_type}")
            # 遍历每个数据需求
            for i in range(nDataRequireLen):
                strIthDataRequire = self.mResultDataDR.data_requires[i]
                try:
                    # 构建查询信息
                    strIthDataPathQuery = f"数据需求：{strIthDataRequire}"
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        ("user", "请为以下数据需求生成文件路径：{query}")
                    ])
                    chain = prompt | self.mLlm | StrOutputParser() # 创建链：提示词 -> 模型 -> 输出解析器
                    strIthDataPath = chain.invoke({"query": strIthDataPathQuery}) # 调用链并获取结果
                    strIthDataPath = strIthDataPath.strip('"\'') # 去除可能的引号
                    self.mResultDataDR.data_paths[i] = strIthDataPath # 设置数据路径
                    # 根据路径是否为空设置检索状态
                    if strIthDataPath != "":
                        self.mResultDataDR.require_status[i] = 1
                    else:
                        self.mResultDataDR.require_status[i] = 0
                except Exception as e:
                    print(f"遍历数据需求'{strIthDataRequire}' 时出错: {e}")
                    self.mResultDataDR.data_paths[i] = ""
                    self.mResultDataDR.require_status[i] = 0
        except ValueError as e:
            raise ValueError(f"数据路径设置失败: {e}") from e 
        except Exception as e:
            raise Exception(f"数据路径设置失败: {e}") from e