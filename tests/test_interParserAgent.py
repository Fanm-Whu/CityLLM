"""
@file: test_interParserAgent.py
@brief: 用户语言解析器测试文件
@author: 许锦辉
@date: start: 2025-10-05; end: 2025-10-06
@version: 1.0
"""

import sys
import os
import time
from typing import List, Dict, Any

# 添加父目录到Python路径，以便导入land_use_parser模块
# 因为test文件在test文件夹中，需要导入上级目录的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(
    
))))

from interParserAgent import LandUseSystem

"""
@class: TestLandUseParser
@brief: 土地查询解析器测试类
    包含30个测试用例，测试意图识别效果
"""

class TestLandUseParser:
    """
    @brief: 初始化测试类
    """
    def __init__(self):
        try:
            self.mObjParser = LandUseSystem()
            print("✅ 测试环境初始化成功")
        except Exception as e:
            print(f"❌ 测试环境初始化失败: {e}")
            raise
    
    """
    @brief: 运行单个测试用例
    @param strTestCase: 测试用例描述
    @param strUserInput: 用户输入文本
    @return: 无
    @note: 时间复杂度: O(1)
            空间复杂度: O(1)
    """
    def _runSingleTest(self, strTestCase: str, strUserInput: str):
        print(f"\n{'='*60}")
        print(f"测试用例: {strTestCase}")
        print(f"用户输入: {strUserInput}")
        print(f"{'-'*60}")
        
        nStartTime = time.time()
        objResult = self.mObjParser.objParseUserInput(strUserInput)
        nEndTime = time.time()
        
        print(f"解析耗时: {nEndTime - nStartTime:.2f}秒")
        print(f"时间信息: {objResult.time}")
        print(f"地点信息: {objResult.location}")
        print(f"数据需求: {objResult.data_requirement}")
        print(f"原始输入: {objResult.original_input}")
    
    """
    @brief: 运行所有测试用例
    @return: 无
    @note: 时间复杂度: O(n)，其中n是测试用例数量
            空间复杂度: O(1)
    """
    def runAllTests(self):
        print("🚀 开始运行土地查询解析器测试")
        print(f"{'='*80}")
        
        # 测试用例列表
        listTestCases = [
            # 1-5: 标准格式的土地查询
            ("标准时间地点查询", "北京市2020-2023年土地利用变化数据"),
            ("单年份查询", "上海市2022年耕地面积统计"),
            ("近些年查询", "广州市近5年建设用地扩张情况"),
            ("模糊时间查询", "深圳市土地利用类型分布"),
            ("完整格式查询", "成都市2018年至2022年林地覆盖变化"),
            
            # 6-10: 不同土地数据类型
            ("耕地数据查询", "天津市耕地保护情况分析"),
            ("建设用地查询", "武汉市建设用地规模统计"),
            ("水域数据查询", "杭州市水域面积变化"),
            ("植被指数查询", "南京市NDVI植被指数数据"),
            ("遥感影像查询", "西安市卫星遥感影像"),
            
            # 11-15: 不同城市和地区
            ("直辖市查询", "重庆市土地覆盖分类"),
            ("省会城市查询", "郑州市城市扩张监测"),
            ("地级市查询", "苏州市土地利用规划"),
            ("简称查询", "京郊土地利用变化"),
            ("区域查询", "长三角地区土地资源调查"),
            
            # 16-20: 复杂句式查询
            ("复杂句式1", "我想了解北京市在2015到2020年期间的耕地变化情况"),
            ("复杂句式2", "请帮我查询上海市近三年建设用地扩张的数据"),
            ("复杂句式3", "需要广州市2021年各类土地利用面积的详细统计"),
            ("复杂句式4", "获取深圳市卫星影像用于土地覆盖分析"),
            ("复杂句式5", "分析成都市过去十年城市扩张对耕地的影响"),
            
            # 21-25: 边界和异常情况
            ("无时间查询", "北京市土地利用现状"),
            ("无地点查询", "2020-2023年耕地变化趋势"),
            ("无数据需求", "北京市2022年"),
            ("超长时间范围", "北京市1990-2023年土地变化"),
            ("模糊地点", "我国主要城市土地利用"),
            
            # 26-30: 非土地相关查询（测试鲁棒性）
            ("天气查询", "今天北京的天气怎么样"),
            ("编程问题", "Python中如何实现快速排序"),
            ("常识问题", "珠穆朗玛峰有多高"),
            ("数学问题", "计算圆的面积公式是什么"),
            ("闲聊", "你好，最近怎么样")
        ]
        
        nTotalCases = len(listTestCases)
        nCurrentCase = 0
        
        for strTestCase, strUserInput in listTestCases:
            nCurrentCase += 1
            print(f"\n📊 进度: {nCurrentCase}/{nTotalCases}")
            try:
                self._runSingleTest(strTestCase, strUserInput)
            except Exception as e:
                print(f"❌ 测试用例执行失败: {e}")
        
        print(f"\n{'='*80}")
        print("🎉 所有测试用例执行完成！")
        print("💡 请检查解析结果是否符合预期")

"""
@brief: 主函数 - 运行测试
@return: 无
@note: 时间复杂度: O(n)，其中n是测试用例数量
        空间复杂度: O(1)
"""
def main():
    print("🏁 土地查询解析器测试程序启动")
    print()
    
    try:
        objTester = TestLandUseParser()
        objTester.runAllTests()
    except Exception as e:
        print(f"❌ 测试程序运行失败: {e}")
        print("请检查:")
        print("1. land_use_parser.py 文件是否存在")
        print("2. .env 文件中是否设置了正确的 DEEPSEEK_API_KEY")
        print("3. 网络连接是否正常")

if __name__ == "__main__":
    main()