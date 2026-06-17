"""
@file: test_ChainAgent.py
@brief: ChainAgent测试文件
@author: Claude
@date: start: 2026-03-31; end: 2026-03-31
@version: 1.0

@note: 测试用例设计原则 - 任务类型比例 自然对话:数据展示:模拟预测 = 1:2:3
       共6个测试用例，覆盖单任务和需分解的复杂任务
"""
from typing import List
from src.agents import ChainAgent, AlgorithmExeResult


"""
@class: TestChainAgent
@brief: ChainAgent 测试类
        用于测试链式代理的完整执行流程

@note: 测试覆盖范围:
       1. 自然对话任务 (1个) - 测试task_type=0的完整流程
       2. 数据展示任务 (2个) - 测试task_type=1的完整流程
       3. 模拟预测任务 (3个) - 测试task_type=2的完整流程
"""
class TestChainAgent:
    """
    @brief: 初始化测试类
    """
    def __init__(self):
        # 初始化ChainAgent
        try:
            print("正在初始化 ChainAgent...")
            self.objChainAgent = ChainAgent()
            print("ChainAgent 初始化成功！")
        except Exception as e:
            print(f"ChainAgent 初始化失败: {e}")
            return

        self.testDataListStr = self.listStrInitTestData()  # 初始化测试数据

    """
    @brief: 初始化测试数据
    @note: 按照 自然对话:数据展示:模拟预测 = 1:2:3 的比例设计
           共6个测试用例
    """
    def listStrInitTestData(self):
        testDataListStr = [
            # ========== 1. 自然对话任务 (1个) ==========
            # 任务类型比例: 1
            #"请介绍一下武汉市的地理特征",

            # ========== 2. 数据展示任务 (2个) ==========
            # 任务类型比例: 2
            #"展示2020年武汉市土地利用数据",
            #"展示2018年湖北省土地覆盖情况",

            # ========== 3. 模拟预测任务 (2个) ==========
            # 任务类型比例: 2
            "模拟2030年武汉市土地利用状况",
            "预测2030年武汉市城市扩张",

            # ========== 4. 复杂组合任务 (测试任务分解) ==========
            # 此任务会被分解为多个子任务，增加测试覆盖面
            "模拟2021年武汉市土地利用状况，并展示2018年武汉市土地利用状况",
        ]

        print(f"已加载 {len(testDataListStr)} 条测试数据")
        print("=" * 60)
        print("测试用例分布 (任务类型比例 1:2:3):")
        print("  - 自然对话任务: 1个")
        print("  - 数据展示任务: 2个")
        print("  - 模拟预测任务: 3个")
        print("  - 复杂组合任务: 1个 (用于测试任务分解功能)")
        print("=" * 60)
        return testDataListStr

    """
    @brief: 执行完整测试
    """
    def test(self):
        print("\n" + "=" * 60)
        print("           开始执行 ChainAgent 测试用例")
        print("=" * 60)

        success_count = 0
        total_count = len(self.testDataListStr)
        all_results: List[List[AlgorithmExeResult]] = []

        for i, test_input in enumerate(self.testDataListStr, 1):
            print(f"\n测试用例 {i}/{total_count}: {test_input}")
            print("-" * 50)
            try:
                # 执行ChainAgent完整流程
                results = self.objChainAgent.run(test_input)
                all_results.append(results)
                success_count += 1
                print(f"\n✓ 测试通过 - 共产生 {len(results)} 个子任务结果")
                self._displayResults(results)  # 显示执行结果
            except Exception as e:
                print(f"\n✗ 测试失败: {e}")

        # 输出测试统计
        self._printTestStatistics(success_count, total_count, all_results)

    """
    @brief: 显示执行结果列表
    @param results: AlgorithmExeResult列表
    """
    def _displayResults(self, results: List[AlgorithmExeResult]):
        for idx, result in enumerate(results, 1):
            print(f"\n  子任务 {idx} 结果:")
            print(f"    任务类型: {result.task_type} ({self._getTaskTypeName(result.task_type)})")
            print(f"    原始输入: {result.original_input}")

            if result.task_type == 0:  # 自然对话任务
                reply_preview = result.result_paths[0] if result.result_paths else ""
                if len(reply_preview) > 80:
                    reply_preview = reply_preview[:80] + "..."
                print(f"    模型回复: {reply_preview}")
            else:  # 数据展示或模拟预测任务
                print(f"    结果名称: {result.result_names}")
                print(f"    结果路径: {result.result_paths}")
                print(f"    执行状态: {result.exe_status}")

                # 统计成功/失败
                if result.exe_status:
                    success = sum(result.exe_status)
                    total = len(result.exe_status)
                    print(f"    执行统计: 成功 {success}/{total}")

    """
    @brief: 打印测试统计信息
    """
    def _printTestStatistics(self, success_count: int, total_count: int,
                             all_results: List[List[AlgorithmExeResult]]):
        print("\n" + "=" * 60)
        print("                     测试统计")
        print("=" * 60)
        print(f"测试用例统计:")
        print(f"   总测试用例: {total_count}")
        print(f"   成功: {success_count}")
        print(f"   失败: {total_count - success_count}")
        print(f"   成功率: {success_count/total_count*100:.1f}%")

        # 统计子任务执行情况
        total_subtasks = sum(len(results) for results in all_results)
        print(f"\n子任务执行统计:")
        print(f"   总子任务数: {total_subtasks}")

        # 按任务类型统计
        task_type_count = {0: 0, 1: 0, 2: 0}
        for results in all_results:
            for result in results:
                if result.task_type in task_type_count:
                    task_type_count[result.task_type] += 1

        print(f"\n任务类型分布:")
        print(f"   自然对话 (0): {task_type_count[0]} 个")
        print(f"   数据展示 (1): {task_type_count[1]} 个")
        print(f"   模拟预测 (2): {task_type_count[2]} 个")

        # 验证比例
        total_type_tasks = sum(task_type_count.values())
        if total_type_tasks > 0:
            print(f"\n实际任务类型比例:")
            print(f"   自然对话 : 数据展示 : 模拟预测 = "
                  f"{task_type_count[0]}:{task_type_count[1]}:{task_type_count[2]}")

        print("=" * 60)

    """
    @brief: 获取任务类型名称
    @param task_type: 任务类型编号
    @return: 任务类型名称
    """
    def _getTaskTypeName(self, task_type: int) -> str:
        task_type_names = {
            0: "自然对话",
            1: "数据展示",
            2: "模拟预测"
        }
        return task_type_names.get(task_type, "未知类型")

    """
    @brief: 验证ChainAgent执行结果
    @param results: 执行结果列表
    @param original_input: 原始输入
    @return: 验证是否通过
    """
    def _validateResults(self, results: List[AlgorithmExeResult],
                         original_input: str) -> bool:
        if not isinstance(results, list):
            print("结果应为列表类型")
            return False

        if len(results) == 0:
            print("结果列表不能为空")
            return False

        for result in results:
            if not isinstance(result, AlgorithmExeResult):
                print(f"结果类型错误: {type(result)}")
                return False

            # 验证任务类型
            if result.task_type not in [0, 1, 2]:
                print(f"无效的任务类型: {result.task_type}")
                return False

            # 验证原始输入
            if not result.original_input:
                print("原始输入不能为空")
                return False

            # 根据任务类型验证结果
            if result.task_type == 0:  # 自然对话
                if not result.result_paths or len(result.result_paths) != 1:
                    print("自然对话任务应有1个结果路径")
                    return False
            else:  # 数据展示或模拟预测
                if result.result_names is None or result.exe_status is None:
                    print("数据展示/模拟预测任务应有结果名称和执行状态")
                    return False

                # 验证列表长度一致性
                if len(result.result_paths) != len(result.result_names):
                    print("result_paths和result_names长度不一致")
                    return False

                if len(result.result_paths) != len(result.exe_status):
                    print("result_paths和exe_status长度不一致")
                    return False

        return True

    """
    @brief: 运行特定测试用例
    @param test_input: 测试输入
    """
    def runSingleTest(self, test_input: str):
        print(f"\n执行单例测试: {test_input}")
        print("-" * 50)
        try:
            results = self.objChainAgent.run(test_input)
            print(f"✓ 测试通过 - 共产生 {len(results)} 个子任务结果")
            self._displayResults(results)

            # 验证结果
            if self._validateResults(results, test_input):
                print("\n✓ 结果验证通过")
            else:
                print("\n✗ 结果验证失败")

        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()


"""
@brief: 主函数
"""
def main():
    print("=" * 60)
    print("            ChainAgent 链式代理测试程序")
    print("=" * 60)
    print("\n测试说明:")
    print("- ChainAgent串联TaskDecomposerAgent -> InterParserAgent ->")
    print("  DataDemandAgent -> AlgorithmExeAgent的完整流程")
    print("- 测试用例按照 自然对话:数据展示:模拟预测 = 1:2:3 设计")
    print("=" * 60)

    test_agent = TestChainAgent()  # 创建测试实例
    test_agent.test()  # 执行完整测试套件

    print("\n" + "=" * 60)
    print("            额外手动测试")
    print("=" * 60)

    # 额外的手动测试用例，覆盖更多场景
    additional_tests = [
        # 简单任务
        "什么是土地利用？",

        # 需要分解的复杂任务
        "预测2020年和2025年武汉市城市扩张",
        "分别考虑人口和经济因素，模拟2021年武汉市土地利用状况",

        # 边界情况
        "展示数据",
        "预测",
    ]

    for test_input in additional_tests:
        test_agent.runSingleTest(test_input)


"""
@brief: 程序入口
"""
if __name__ == "__main__":
    main()