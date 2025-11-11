"""
@file: Test_interParseAgent.py
@brief: InterParserAgent 测试类
@author: 许锦辉
@date: 2025-11-10
@version: 1.1
"""

import sys
import os

sys.path.append('D:/py/code/CityLLM/CityLLM')
from src.agents import InterParserAgent, InterPaserResult

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
        self.objParser = None
        self.bInitialized = False
        self.testDataListstr = []
        
        try:
            print("正在初始化 InterParserAgent...")
            self.objParser = InterParserAgent()
            self.bInitialized = True
            print("InterParserAgent 初始化成功！")
        except Exception as e:
            print(f"InterParserAgent 初始化失败: {e}")
            self.bInitialized = False
            return
        
        self._initTestData()  # 初始化测试数据
        print(f"已加载 {len(self.testDataListstr)} 条测试数据")
    

    """
    @brief: 初始化测试数据
    """
    def _initTestData(self):
        self.testDataListstr = [
            # 标准格式测试 - 10个
            "北京市2015-2020年土地利用变化",
            "上海市耕地面积统计",
            "近5年广州市城市扩张情况",
            "2023年深圳市建设用地分布",
            "天津市2018-2022年林地覆盖变化",
            "重庆市近10年草地资源监测",
            "杭州市2021年水域面积统计",
            "南京市2019-2023年土地类型分布",
            "成都市近3年城市扩张遥感分析",
            "武汉市2020-2022年耕地保护情况",
            
            # 边界情况测试 - 5个
            "土地利用数据",  # 无时间地点
            "2020年数据",    # 无地点
            "北京市数据",     # 无时间
            "土地",          # 极简输入
            "2023",          # 只有年份
            
            # 复杂查询测试 - 5个
            "2018年至2022年武汉市和长沙市的林地覆盖变化对比分析",
            "近10年长三角地区城市扩张与耕地变化遥感监测",
            "2015-2020年京津冀地区土地利用变化及驱动力分析",
            "2021年北上广深四个一线城市建设用地对比",
            "近5年长江中游城市群土地覆盖分类与变化监测",
            
            # 简短查询测试 - 5个
            "北京土地",
            "上海2023",
            "广州近5年",
            "深圳建设用地",
            "成都遥感",
            
            # 特殊格式测试 - 5个
            "京沪近三年土地利用",
            "2021-2022年北上广深土地类型分布",
            "江浙沪地区耕地保护政策实施效果评估",
            "近五年粤港澳大湾区城市扩张卫星影像分析",
            "2020-2023年中部六省土地利用变化趋势"
        ]
    

    """
    @brief: 执行测试
    """
    def test(self):
        if not self.bInitialized:
            print("测试中止：InterParserAgent 未正确初始化")
            return
        print("\n" + "=" * 60)
        print("           开始执行测试用例")
        print("=" * 60)
        success_count = 0
        total_count = len(self.testDataListstr)
        
        for i, test_input in enumerate(self.testDataListstr, 1):
            print(f"\n测试用例 {i}/{total_count}: {test_input}")
            print("-" * 50)
            try:
                result = self.objParser.objParseQuery(test_input)  # 执行解析
                if self._validateResult(result, test_input):  # 验证结果
                    success_count += 1
                    print("测试通过")
                else:
                    print("测试结果验证警告")
                self._displayResult(result)  # 显示解析结果
            except Exception as e:
                print(f"测试失败: {e}")

        print("\n" + "=" * 60)  # 输出测试统计
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
    def _validateResult(self, result: InterPaserResult, original_input: str) -> bool:
        if not isinstance(result, InterPaserResult):  # 基本验证
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
    def _displayResult(self, result: InterPaserResult):
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
        if not self.bInitialized:
            print("InterParserAgent 未正确初始化")
            return
        print(f"\n执行单例测试: {test_input}")
        try:
            result = self.objParser.objParseQuery(test_input)
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
    if test_agent.bInitialized:  # 如果初始化成功，执行测试
        test_agent.test()  # 执行完整测试套件
        print("\n" + "=" * 60)  # 可选：执行额外的手动测试
        print("       额外手动测试")
        print("=" * 60)
        # 可以在这里添加额外的测试用例
        additional_tests = [
            "南京市2022年土地利用",
            "近3年杭州市变化",
            "2024年北京市土地规划",
            "近15年上海市城市发展",
            "2010-2025年广州市土地资源"
        ]
        
        for test_input in additional_tests:
            test_agent.runSingleTest(test_input)
    else:
        print("测试程序无法继续，因为解析器初始化失败")


"""
@brief: 程序入口
"""
if __name__ == "__main__":
    main()