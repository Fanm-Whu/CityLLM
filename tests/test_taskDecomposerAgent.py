"""
@file: test_taskDecomposerAgent.py
@brief: TaskDecomposerAgent测试文件
@author: [您的姓名]
@date: 2025-11-18
@version: 1.1 (移除验证逻辑)
"""
from src.agents import BaseAgent
from src.agents import TaskDecomposerAgent, TaskDecomposerResult


"""
@class: TestTaskDecomposerAgent
@brief: TaskDecomposerAgent 测试类
        用于测试复杂任务分解器的功能
"""
class TestTaskDecomposerAgent:
    """
    @brief: 初始化测试类
    """
    def __init__(self):
        #初始化BaseAgent
        try:
            print("正在初始化 BaseAgent...")
            inputBaseAgent = BaseAgent()
            print("BaseAgent 初始化成功！")
        except Exception as e:
            print(f"BaseAgent 初始化失败: {e}")
            return
        
        #初始化TaskDecomposerAgent
        try:
            print("正在初始化 TaskDecomposerAgent...")
            self.objDecomposer = TaskDecomposerAgent(inputBaseAgent)
            print("TaskDecomposerAgent 初始化成功！")
        except Exception as e:
            print(f"TaskDecomposerAgent 初始化失败: {e}")
            return
        
        self.testDataListstr = self.listStrInitTestData()  # 初始化测试数据

    """
    @brief: 初始化测试数据
    """
    def listStrInitTestData(self):
        testDataListstr = [
            # 需要分解的复杂查询 - 10个
            "分别考虑人口、经济因素，模拟2021年武汉市土地利用状况",
            "先后考虑人口、经济因素，模拟2021年武汉市土地利用状况",
            "考虑人口、经济因素，模拟2021年武汉市土地利用状况，并展示出2018年武汉市土地利用状况，我想作对比",
            "预测2025年北京市和上海市的城市扩张情况",
            "展示2020年广州市土地利用数据，并模拟2023年耕地变化",
            "分别分析人口和经济因素对城市扩张的影响",
            "模拟2021年武汉市土地利用状况，并展示2018年武汉市土地利用状况",
            "预测2020年和2025年武汉市城市扩张",
            "分析北京市和上海市的人口密度变化",
            "展示2018年武汉市土地利用数据，并预测2023年城市扩张",

            # 混合复杂查询 - 5个
            "分别考虑人口、经济、交通因素，模拟2021年武汉市土地利用状况，并展示2018武汉市土地利用数据",
            "预测2025年北京、上海、广州的城市扩张，并展示2020年武汉市人口数据",
            "模拟2021年武汉市土地利用，预测2025年该市的土地利用情况，展示2018年武汉市的土地利用数据数据",
            "考虑人口因素模拟广州市2021年土地利用，考虑经济因素预测广州市2025年土地利用",
            
            # 不需要分解的简单查询 - 5个
            "考虑人口和经济因素，模拟2021年武汉市土地利用状况",
            "展示2020年武汉市土地利用数据",
            "预测2025年武汉市城市扩张",
            "模拟2021年武汉市土地利用状况",
            "分析人口因素对城市扩张的影响",

            #非土地利用模拟问题
            "深圳的知名互联网企业有哪些？",
            "2024年值得一玩的3A游戏有哪些？",
            "展示武汉市2023年的人口数据",
        ]
        print("已加载" + str(len(testDataListstr)) + "条测试数据")
        return testDataListstr

    """
    @brief: 执行测试
    """
    def test(self):
        print("\n" + "=" * 60)
        print("           开始执行测试用例")
        print("=" * 60)
        success_count = 0
        total_count = len(self.testDataListstr)
        #控制循环次数
        for i, test_input in enumerate(self.testDataListstr, 1):
            print(f"\n测试用例 {i}/{total_count}: {test_input}")
            print("-" * 50)
            try:
                result = self.objDecomposer.run(test_input)  # 执行分解
                success_count += 1
                print("测试通过")
                self._displayResult(result)  # 显示分解结果
            except Exception as e:
                print(f"测试失败: {e}")
        # 输出测试统计
        print("\n" + "=" * 60)
        print("测试统计:")
        print(f"   总测试用例: {total_count}")
        print(f"   成功: {success_count}")
        print(f"   失败: {total_count - success_count}")
        print("=" * 60)
    

    """
    @brief: 显示分解结果
    @param result: 分解结果
    """
    def _displayResult(self, result: TaskDecomposerResult):
        print("分解结果详情:")
        print(f"   简单任务数量: {len(result.simple_tasks)}")
        for i, task in enumerate(result.simple_tasks, 1):
            print(f"   任务{i}: {task}")
        print(f"   原始输入: {result.original_input}")
    

    """
    @brief: 运行特定测试用例
    @param test_input: 测试输入
    """
    def runSingleTest(self, test_input: str):
        print(f"\n执行单例测试: {test_input}")
        try:
            result = self.objDecomposer.run(test_input)
            self._displayResult(result)
        except Exception as e:
            print(f"测试失败: {e}")


"""
@brief: 主函数
"""
def main():
    print("=" * 60)
    print("       TaskDecomposerAgent 测试程序")
    print("=" * 60)
    test_agent = TestTaskDecomposerAgent()  # 创建测试实例
    test_agent.test()  # 执行完整测试套件
    print("\n" + "=" * 60)  # 可选：执行额外的手动测试
    print("       额外手动测试")
    print("=" * 60)
    # 可以在这里添加额外的测试用例
    additional_tests = [
        "分别考虑人口、经济因素，模拟2021年武汉市土地利用状况",
        "考虑人口和经济因素，模拟2021年武汉市土地利用状况",
        "考虑人口、经济因素，模拟2021年武汉市土地利用状况、分别。",
        "分别考虑人口、经济、交通因素，模拟2021年武汉市土地利用状况",
        "模拟2021年武汉市土地利用状况，并展示2018年数据",
        "预测2025年北京和上海的城市扩张",
        "展示数据",
        "分别考虑",
        "这是一个不需要分解的简单任务",
        "分别考虑人口、经济因素，模拟2021年武汉市土地利用状况，并展示2018年数据，预测2025年城市扩张"
    ]
    for test_input in additional_tests:
        test_agent.runSingleTest(test_input)


"""
@brief: 程序入口
"""
if __name__ == "__main__":
    main()