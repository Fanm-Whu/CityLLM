"""
@file: ChainAgent.py
@brief: 链式代理文件，串联TaskDecomposerAgent、InterParserAgent、DataDemandAgent、AlgorithmExeAgent
@author: Claude
@date: 2026-03-30
@version: 1.0
"""
from typing import List
from src.agents import BaseAgent
from src.agents import InterParserAgent
from src.agents import TaskDecomposerAgent
from src.agents import DataDemandAgent
from src.agents import AlgorithmExeAgent, AlgorithmExeResult


"""
@class: ChainAgent
@brief: 链式代理类，串联多个Agent完成复杂任务
@see: 执行流程：TaskDecomposer -> InterParser -> DataDemand -> AlgorithmExe
"""
class ChainAgent:
    """
    @brief: 初始化函数，内部申请BaseAgent
    """
    def __init__(self):
        try:
            self.mBaseAgent = BaseAgent()
            self.mTaskDecomposerAgent = TaskDecomposerAgent(self.mBaseAgent)
        except Exception as e:
            raise Exception(f"ChainAgent初始化失败: {e}") from e

    """
    @brief: 执行单个子任务
    @param input_str: 子任务输入字符串
    @return: AlgorithmExeResult对象
    """
    def singleTaskRun(self, input_str: str) -> AlgorithmExeResult:
        try:
            # 步骤1: InterParserAgent解析
            inter_parser_agent = InterParserAgent(self.mBaseAgent)
            inter_result = inter_parser_agent.run(input_str)
            # 步骤2: DataDemandAgent分析数据需求
            data_demand_agent = DataDemandAgent(self.mBaseAgent, inter_result)
            data_demand_result = data_demand_agent.run()
            # 步骤3: AlgorithmExeAgent执行
            algorithm_exe_agent = AlgorithmExeAgent(self.mBaseAgent, data_demand_result)
            algorithm_exe_result = algorithm_exe_agent.run()
            return algorithm_exe_result
        except Exception as e:
            raise Exception(f"singleTaskRun执行失败: {e}") from e

    """
    @brief: 执行完整流程
    @param input_str: 用户输入
    @return: List[AlgorithmExeResult]列表
    """
    def run(self, input_str: str) -> List[AlgorithmExeResult]:
        try:
            print(f"\n开始执行任务: {input_str}")
            # 步骤1: TaskDecomposerAgent分解任务
            print("\n[1] TaskDecomposerAgent分解任务...")
            task_decomposer_agent = TaskDecomposerAgent(self.mBaseAgent)
            decomposer_result = task_decomposer_agent.run(input_str)
            simple_tasks = decomposer_result.simple_tasks
            print(f"任务分解完成，共{len(simple_tasks)}个子任务")
            # 步骤2: 循环执行每个子任务
            print(f"\n[2] 依次执行子任务...")
            results = []
            for i, task in enumerate(simple_tasks, 1):
                print(f"\n执行子任务 {i}/{len(simple_tasks)}: {task}")
                result = self.singleTaskRun(task)
                results.append(result)
                print(f"子任务 {i} 执行成功")
            print(f"\n所有子任务执行完成，共{len(results)}个结果")
            return results
        except Exception as e:
            raise Exception(f"ChainAgent run执行失败: {e}") from e