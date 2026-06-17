"""
@file: Test_InterParseAgent.py
@brief: InterParserAgent测试文件
@author: 许锦辉&樊明
@date: start: 2025-11-10; end: 2025-11-10
       start: 2025-12-16; end: 2025-12-17
@version: 1.1
"""
from src.agents import BaseAgent
from src.agents import InterParserAgent, InterParserResult


"""
@class: TestInterParserAgent
@brief: InterParserAgent 测试类
        用于测试土地查询解析器的功能
"""
class TestInterParserAgent:
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
        #初始化InterParserAgent
        try:
            print("正在初始化 InterParserAgent...")
            self.objParser = InterParserAgent(inputBaseAgent)
            print("InterParserAgent 初始化成功！")
        except Exception as e:
            print(f"InterParserAgent 初始化失败: {e}")
            return
        self.testDataListstr = self.listStrInitTestData()  # 初始化测试数据

    """
    @brief: 初始化测试数据
    """
    def listStrInitTestData(self):
        testDataListstr = [
            # ========== 4. 需要分解的复杂查询测试用例 ==========
            # 注意：这些测试用例应该先通过TaskDecomposer分解，这里测试的是分解后的简单任务
            # 4.1 分别考虑多个因素（分解后）
            "考虑人口因素，模拟2021年武汉市土地利用状况",  # 分解后的任务
            "考虑经济因素，模拟2021年武汉市土地利用状况",  # 分解后的任务
            # 4.2 多个时间点（分解后）
            "预测2020年武汉市城市扩张",  # 分解后的任务
            "预测2025年武汉市城市扩张",  # 分解后的任务
            # 4.3 多个地点（分解后）
            "预测2025年北京市城市扩张情况",  # 分解后的任务
            "预测2025年上海市城市扩张情况",  # 分解后的任务
            # 4.4 多个任务类型组合（分解后）
            "考虑人口和经济因素，模拟2021年武汉市土地利用状况",  # 分解后的任务
            "展示2018年武汉市土地利用状况",  # 分解后的任务
            # 4.5 多重复杂组合（分解后）
            "分别考虑人口、经济、交通因素，模拟2021年武汉市土地利用状况",  # 分解后的任务
            "展示2018年武汉市土地利用数据",  # 分解后的任务
            # ========== 5. 边界情况测试用例 ==========
            "土地利用数据",  # 无时间地点
            "2020年数据",    # 无地点
            "北京市数据",     # 无时间
            "土地",          # 极简输入
            "2023",          # 只有年份
            "展示数据",      # 极简查询
            "模拟",          # 极简查询
            "预测",          # 极简查询
        ]
        print(f"已加载 {len(testDataListstr)} 条测试数据")
        print(f"分类统计: 正常对话({10}条), 智能查询({14}条), 模拟预测({10}条), 分解后任务({8}条), 边界情况({8}条)")
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
                result = self.objParser.run(test_input)  # 执行解析
                success_count += 1
                print("测试通过")
                self._displayResult(result)  # 显示解析结果
            except Exception as e:
                print(f"测试失败: {e}")
        # 输出测试统计
        print("\n" + "=" * 60)
        print("测试统计:")
        print(f"   总测试用例: {total_count}")
        print(f"   成功: {success_count}")
        print(f"   失败: {total_count - success_count}")
        print(f"   成功率: {success_count/total_count*100:.1f}%")
        print("=" * 60)

    """
    @brief: 验证解析结果
    @param result: 解析结果
    @param original_input: 原始输入
    @return: 验证是否通过
    """
    def _validateResult(self, result: InterParserResult, original_input: str) -> bool:
        if not isinstance(result, InterParserResult):  # 基本验证
            print("结果类型错误")
            return False
        if result.original_input != original_input:
            print("原始输入不匹配")
            return False
        
        # 验证任务类型
        if not isinstance(result.task_type, int):
            print("任务类型格式错误，应为整数")
            return False
        if result.task_type not in [0, 1, 2]:
            print("任务类型值错误，应为0、1或2")
            return False
        
        # 验证时间（如果存在）
        if result.time is not None and not isinstance(result.time, str):
            print("时间格式错误，应为字符串")
            return False
        
        # 验证地点（如果存在）
        if result.location is not None and not isinstance(result.location, str):
            print("地点格式错误，应为字符串")
            return False
        
        return True

    """
    @brief: 显示解析结果
    @param result: 解析结果
    """
    def _displayResult(self, result: InterParserResult):
        print("解析结果详情:")
        print(f"   任务类型: {result.task_type} ({self._getTaskTypeName(result.task_type)})")
        print(f"   时间: {result.time}")
        print(f"   地点: {result.location}")
        print(f"   原始输入: {result.original_input}")
    
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
    @brief: 运行特定测试用例
    @param test_input: 测试输入
    """
    def runSingleTest(self, test_input: str):
        print(f"\n执行单例测试: {test_input}")
        try:
            result = self.objParser.run(test_input)
            self._displayResult(result)
        except Exception as e:
            print(f"测试失败: {e}")

"""
@brief: 主函数
"""
def main():
    print("=" * 60)
    print("       InterParserAgent 测试程序")
    print("=" * 60)
    test_agent = TestInterParserAgent()  # 创建测试实例
    #test_agent.test()
    print("\n" + "=" * 60)
    print("       额外手动测试")
    print("=" * 60)
    # 可以在这里添加额外的测试用例
    additional_tests = [
        "展示石河子市2025年的土地利用数据",
        "耦合人口、经济因素，模拟2021年武汉市土地利用情况",
        "请你考虑人口因素和交通因素，预测2026年武汉市土地利用情况",
        "基于人口因素和经济因素，模拟2018年武汉市土地利用情况",
        "南京市2022年土地利用",
        "近3年杭州市变化",
        "2024年北京市土地规划",
        "近15年上海市城市发展",
        "2010-2025年广州市土地资源",
        "我想看看2021年湖北省的人口、经济数据。",
        "显示2021年益阳市的土地利用情况",
        "我想看看2030年武汉市的土地利用状况",
        "考虑人口、经济因素，模拟2021年武汉市土地利用状况，并展示出2018年武汉市土地利用状况，我想作对比",
        "分别考虑人口、经济因素，模拟2021年武汉市土地利用状况",
        "先后考虑人口、经济因素，模拟2021年武汉市土地利用状况"
    ]
    for test_input in additional_tests:
        test_agent.runSingleTest(test_input)

"""
@brief: 程序入口
"""
if __name__ == "__main__":
    main()