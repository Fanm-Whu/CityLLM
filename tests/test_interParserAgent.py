"""
@file: Test_interParseAgent.py
@brief: InterParserAgent测试文件
@author: 许锦辉
@date: 2025-11-10
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
            # ========== 1. 正常对话测试用例 ==========
            "C++是什么？",
            "鲁迅是什么水平的作家？都有什么代表作？",
            "近五年值得一玩的主机游戏有哪些？",
            "广东省的知名互联网企业有哪些？",
            "深圳的知名互联网企业有哪些？",
            "2024年值得一玩的3A游戏有哪些？",
            "什么是土地利用？",
            "如何理解城市扩张？",
            "请解释一下什么是遥感技术？",
            "什么是城市功能分区？",
            
            # ========== 2. 智能查询与可视化测试用例 ==========
            # 2.1 土地利用相关查询
            "展示武汉市2023年土地利用数据",
            "显示2021年益阳市的土地利用情况",
            "我想看看上海2024年的土地利用数据",
            "查看北京市2015-2020年土地利用变化",
            "展示上海市耕地面积统计",
            "近5年广州市城市扩张情况",
            "2023年深圳市建设用地分布",
            "南京市2019-2023年土地类型分布",
            
            # 2.2 人口经济相关查询
            "展示武汉市2023年的人口数据",
            "输出粤港澳大湾区2018年的经济数据",
            "查看2021年湖北省的人口、经济数据",
            "展示北京市近10年人口变化情况",
            "显示上海市2022年GDP数据",
            
            # 2.3 混合数据查询
            "展示2020年广州市土地利用数据和人口数据",
            "查看武汉市2021年土地利用和经济数据",
            "显示北京市2022年人口密度和土地利用情况",
            
            # ========== 3. 土地利用模拟与预测测试用例 ==========
            # 3.1 单驱动因素模拟/预测
            "考虑人口因素，模拟2021年武汉市土地利用情况",
            "基于经济因素，预测2026年武汉市城市扩张",
            "驱动人口因素，模拟2025年北京市土地利用变化",
            
            # 3.2 多驱动因素模拟/预测（不分解）
            "考虑人口和经济因素，模拟2021年武汉市土地利用状况",
            "基于人口和交通因素，预测2026年武汉市土地利用情况",
            "耦合人口、经济因素，模拟2021年武汉市土地利用情况",
            
            # 3.3 多情景发展策略
            "以紧凑态势模拟2021年武汉市城市土地利用情况",
            "基于稳定态势预测2026年武汉市城市功能分区状况",
            "基于蔓延态势进行2025年武汉市城市功能区、人口、经济模拟",
            
            # 3.4 城市功能分区相关
            "2017年，香港的城市功能分区是怎样的？",
            "模拟2023年武汉市城市功能分区情况",
            "预测2025年上海市城市功能分区变化",
            
            # ========== 4. 需要分解的复杂查询测试用例 ==========
            # 4.1 分别考虑多个因素
            "分别考虑人口、经济因素，模拟2021年武汉市土地利用状况",
            "先后考虑人口、经济因素，模拟2021年武汉市土地利用状况",
            "分别分析人口和经济因素对城市扩张的影响",
            
            # 4.2 多个时间点
            "预测2020年和2025年武汉市城市扩张",
            "展示2018年武汉市土地利用数据，并预测2023年城市扩张",
            
            # 4.3 多个地点
            "预测2025年北京市和上海市的城市扩张情况",
            "分析北京市和上海市的人口密度变化",
            
            # 4.4 多个任务类型组合
            "考虑人口、经济因素，模拟2021年武汉市土地利用状况，并展示出2018年武汉市土地利用状况，我想作对比",
            "模拟2021年武汉市土地利用状况，并展示2018年武汉市土地利用状况",
            "展示2020年广州市土地利用数据，并模拟2023年耕地变化",
            
            # 4.5 多重复杂组合
            "分别考虑人口、经济、交通因素，模拟2021年武汉市土地利用状况，并展示2018年数据",
            "预测2025年北京、上海、广州的城市扩张，并展示2020年数据",
            "模拟2021年武汉市土地利用，预测2025年城市扩张，展示2018年数据",
            
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
                result = self.objParser.run(test_input)  # 执行解析
                if self._validateResult(result, test_input):  # 验证结果
                    success_count += 1
                    print("测试通过")
                else:
                    print("测试结果验证警告")
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
        if result.time is not None:  # 时间格式验证
            if not isinstance(result.time, list):
                print("时间格式错误，应为列表")
                return False
            if len(result.time) != 2:
                print("时间列表长度错误，应为2")
                return False
        if result.location is not None:  # 地点验证（如果存在）
            if not isinstance(result.location, list):
                print("地点格式错误，应为列表")
                return False
        if result.data_requirement is not None:  # 数据需求验证（如果存在）
            if not isinstance(result.data_requirement, list):
                print("数据需求格式错误，应为列表")
                return False
        return True
    

    """
    @brief: 显示解析结果
    @param result: 解析结果
    """
    def _displayResult(self, result: InterParserResult):
        print("解析结果详情:")
        print(f"   时间: {result.time}")
        print(f"   地点: {result.location}")
        print(f"   数据需求: {result.data_requirement}")
        print(f"   原始输入: {result.original_input}")
    

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
    #test_agent.test()  # 执行完整测试套件
    print("\n" + "=" * 60)  # 可选：执行额外的手动测试
    print("       额外手动测试")
    print("=" * 60)
    # 可以在这里添加额外的测试用例
    additional_tests = [
        #"""
        #"耦合人口、经济因素，模拟2021年武汉市土地利用情况",
        #"请你考虑人口因素和交通因素，预测2026年武汉市土地利用情况",
        #"基于人口因素和经济因素，模拟2018年武汉市土地利用情况",
        #"考虑人口、经济因素，模拟2021年武汉市土地利用状况，并展示出2018年武汉市土地利用状况，我想作对比",
        #"南京市2022年土地利用",
        #"近3年杭州市变化",
        #"2024年北京市土地规划",
        #"近15年上海市城市发展",
        #"2010-2025年广州市土地资源",
        #"C++是什么？",
        #"鲁迅是什么水平的作家？都有什么代表作？",
        #"近五年值得一玩的主机游戏有哪些？",
        #"广东省的知名互联网企业有哪些？",
        #"我想看看2021年湖北省的人口、经济数据。",
        #"显示2021年益阳市的土地利用情况"
        #"""
        "深圳的知名互联网企业有哪些？",
        "2024年值得一玩的3A游戏有哪些？",
        "展示武汉市2023年的人口数据",
        "输出粤港澳大湾区2018年的经济数据",
        "2017年，香港的城市功能分区是怎样的？",
        "我想看看上海2024年的土地利用数据",
        "以紧凑态势模拟2021年武汉市城市土地利用情况",
        "基于稳定态势预测2026年武汉市城市功能分区状况",
        "基于蔓延态势进行2025年武汉市城市功能区、人口、经济模拟",
        "考虑人口、经济因素，模拟2021年武汉市土地利用状况，并展示出2018年武汉市土地利用状况，我想作对比",
    ]
    for test_input in additional_tests:
        test_agent.runSingleTest(test_input)


"""
@brief: 程序入口
"""
if __name__ == "__main__":
    main()