"""
@file: test_dataDemandAgent.py
@brief: DataDemandAgent测试文件
@author: 樊明
@date: start: 2025-12-18; end: 2025-12-19
@version: 1.0
"""
from src.agents import BaseAgent
from src.agents import DataDemandAgent, DataDemandResult
from src.agents import InterParserAgent


"""
@class: TestDataDemandAgent
@brief: DataDemandAgent 测试类
        用于测试数据需求分析器的功能
"""
class TestDataDemandAgent:
    """
    @brief: 初始化测试类
    """
    def __init__(self):
        # 初始化BaseAgent
        try:
            print("正在初始化 BaseAgent...")
            self.inputBaseAgent = BaseAgent()
            print("BaseAgent 初始化成功！")
        except Exception as e:
            print(f"BaseAgent 初始化失败: {e}")
            return
        
        # 初始化InterParserAgent（用于生成测试数据）
        try:
            print("正在初始化 InterParserAgent...")
            self.objInterParser = InterParserAgent(self.inputBaseAgent)
            print("InterParserAgent 初始化成功！")
        except Exception as e:
            print(f"InterParserAgent 初始化失败: {e}")
            return
        
        self.testDataListStr = self.listStrInitTestData()  # 初始化测试数据

    """
    @brief: 初始化测试数据
    """
    def listStrInitTestData(self):
        testDataListStr = [
            # ========== 自然对话任务测试用例 ==========
            "C++是什么？",
            "介绍一下武汉市",
            "今天天气怎么样？",
            "什么是土地利用？",
            "请解释一下GDP的含义",
            
            # ========== 数据展示任务测试用例 ==========
            # 1. 土地覆盖数据测试
            "展示2021年武汉市土地覆盖数据",
            "显示2020年北京市土地覆盖情况",
            "查看2018年广东省的土地覆盖数据",
            "输出2021年上海市土地覆盖",
            "展示石河子市2025年的土地覆盖数据",
            
            # 2. 人口数据测试
            "展示2020年人口数据",
            "查看2019年人口统计",
            "输出2022年人口密度",
            "展示武汉市2021年人口数据",
            
            # 3. 经济数据测试
            "展示2020年经济数据",
            "显示2021年GDP统计",
            "查看2019年经济状况",
            "输出2015年经济指标",
            "展示湖北省2020年经济数据",
            
            # 4. 组合数据测试
            "展示2021年武汉市土地覆盖和人口数据",
            "显示2020年北京市土地覆盖和经济数据",
            "查看2018年广东省土地覆盖、人口和经济数据",
            
            # 5. 不存在的数据测试
            "展示2023年武汉市天气数据",
            "显示2025年湖北省交通数据",
            "查看2010年北京市温度数据",
            
            # ========== 边界情况测试用例 ==========
            "展示数据",           # 无时间地点
            "2020年数据",         # 无地点
            "北京市数据",         # 无时间
            "土地",              # 极简输入
            "2021",              # 只有年份
        ]
        print(f"已加载 {len(testDataListStr)} 条测试数据")
        print(f"分类统计: 自然对话({5}条), 土地覆盖数据({5}条), 人口数据({5}条), 经济数据({5}条), 组合数据({3}条), 不存在数据({3}条), 边界情况({5}条)")
        return testDataListStr

    """
    @brief: 执行完整测试
    """
    def test(self):
        print("\n" + "=" * 60)
        print("           开始执行测试用例")
        print("=" * 60)
        success_count = 0
        total_count = len(self.testDataListStr)
        
        for i, test_input in enumerate(self.testDataListStr, 1):
            print(f"\n测试用例 {i}/{total_count}: {test_input}")
            print("-" * 50)
            try:
                # 第一步：使用InterParserAgent解析用户输入
                interParserResult = self.objInterParser.run(test_input)
                print(f"1. InterParser解析结果: 任务类型={interParserResult.task_type}, "
                      f"时间={interParserResult.time}, 地点={interParserResult.location}")
                
                # 第二步：使用DataDemandAgent处理数据需求
                objDataDemand = DataDemandAgent(self.inputBaseAgent, interParserResult)
                dataDemandResult = objDataDemand.run()
                success_count += 1
                print("2. DataDemandAgent测试通过")
                self._displayResult(dataDemandResult)  # 显示解析结果
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
    def _validateResult(self, result: DataDemandResult, original_input: str) -> bool:
        if not isinstance(result, DataDemandResult):
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
        
        # 对于数据展示和模拟预测任务，检查其他属性
        if result.task_type in [1, 2]:
            if result.location is not None and not isinstance(result.location, str):
                print("地点格式错误")
                return False

            if result.admin_level is not None and not isinstance(result.admin_level, int):
                print("行政等级格式错误")
                return False
            
            if result.shp_path is not None and not isinstance(result.shp_path, list):
                print("shp_path格式错误，应为列表")
                return False
            
            if result.data_requires is not None and not isinstance(result.data_requires, list):
                print("data_requires格式错误，应为列表")
                return False
            
            if result.data_paths is not None and not isinstance(result.data_paths, list):
                print("data_paths格式错误，应为列表")
                return False
            
            if result.require_status is not None and not isinstance(result.require_status, list):
                print("require_status格式错误，应为列表")
                return False
        
        return True

    """
    @brief: 显示解析结果
    @param result: 解析结果
    """
    def _displayResult(self, result: DataDemandResult):
        print("DataDemand解析结果详情:")
        print(f"   任务类型: {result.task_type} ({self._getTaskTypeName(result.task_type)})")
        print(f"   原始输入: {result.original_input}")
        print(f"   地    点: {result.location}")
        print(f"   行政等级: {result.admin_level}")
        print(f"   shp路径: {result.shp_path}")
        print(f"   数据需求: {result.data_requires}")
        print(f"   数据路径: {result.data_paths}")
        print(f"   检索状态: {result.require_status}")
    
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
            # 第一步：使用InterParserAgent解析用户输入
            interParserResult = self.objInterParser.run(test_input)
            print(f"InterParser解析结果:")
            print(f"  任务类型: {interParserResult.task_type}")
            print(f"  时间: {interParserResult.time}")
            print(f"  地点: {interParserResult.location}")
            
            # 第二步：使用DataDemandAgent处理数据需求
            objDataDemand = DataDemandAgent(self.inputBaseAgent, interParserResult)
            dataDemandResult = objDataDemand.run()
            self._displayResult(dataDemandResult)
        except Exception as e:
            print(f"测试失败: {e}")

"""
@brief: 主函数
"""
def main():
    print("=" * 60)
    print("       DataDemandAgent 测试程序")
    print("=" * 60)
    test_agent = TestDataDemandAgent()  # 创建测试实例
    test_agent.test()  # 执行完整测试套件
    
    print("\n" + "=" * 60)
    print("       额外手动测试")
    print("=" * 60)
    # 可以在这里添加额外的测试用例
    additional_tests = [
        "模拟2021年武汉市土地利用情况",
        "模拟2018年武汉市土地利用情况",
        "南京市2022年土地覆盖",
        "近3年杭州市变化",
        "2024年北京市土地覆盖状况",
        "我想看看2021年湖北省的人口、经济数据",
        "显示2021年益阳市的土地覆盖情况",
        "我想看看2030年武汉市的土地利用状况",
        "模拟"
    ]
    for test_input in additional_tests:
        test_agent.runSingleTest(test_input)

"""
@brief: 程序入口
"""
if __name__ == "__main__":
    main()