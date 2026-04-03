"""
@file: test_AlgorithmExeAgent.py
@brief: AlgorithmExeAgent测试文件
@author: 樊明
@date: start: 2026-01-21; end: 2026-01-21
@version: 1.0
"""
from src.agents import BaseAgent
from src.agents import DataDemandAgent
from src.agents import AlgorithmExeAgent, AlgorithmExeResult
from src.agents import InterParserAgent


"""
@class: TestAlgorithmExeAgent
@brief: AlgorithmExeAgent 测试类
        用于测试算法执行器的功能
"""
class TestAlgorithmExeAgent:
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
        
        # 初始化InterParserAgent
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
            # 1. 土地覆盖数据测试（使用现有年份2000-2021）
            "展示2020年湖北省土地覆盖数据",
            "显示2018年北京市土地覆盖情况",
            "查看2015年广东省的土地覆盖数据",
            "输出2021年上海市土地覆盖",
            
            # 2. 人口数据测试（使用现有年份2000-2022）
            "展示2020年人口数据",
            "查看2019年人口统计",
            "输出2018年人口密度",
            
            # 3. 经济数据测试（使用现有年份2000、2005、2010、2015、2020）
            #"展示2020年经济数据",
            #"显示2015年GDP统计",
            #"查看2010年经济状况",
            #"输出2005年经济指标",
            
            # 4. 组合数据测试
            "展示2020年湖北省土地覆盖和人口数据",
            #"显示2018年北京市土地覆盖和经济数据",
            
            # 5. 不存在的数据测试
            "展示2023年湖北省天气数据",  # 年份超出范围
            "显示2025年湖北省交通数据",  # 不存在的数据类型
            "查看2010年北京市温度数据",  # 不存在的数据类型
            
            # ========== 边界情况测试用例 ==========
            "展示数据",           # 无时间地点
            "2020年数据",         # 无地点
            "北京市数据",         # 无时间
            "土地",              # 极简输入
            "2021",              # 只有年份
        ]
        print(f"已加载 {len(testDataListStr)} 条测试数据")
        print(f"分类统计: 自然对话({5}条), 土地覆盖数据({4}条), 人口数据({3}条), 经济数据({0}条), 组合数据({1}条), 不存在数据({3}条), 边界情况({5}条)")
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
                print(f"1. InterParser解析结果:")
                print(f"   任务类型: {interParserResult.task_type}")
                print(f"   时间: {interParserResult.time}")
                print(f"   地点: {interParserResult.location}")
                
                # 第二步：使用DataDemandAgent处理数据需求
                objDataDemand = DataDemandAgent(self.inputBaseAgent, interParserResult)
                dataDemandResult = objDataDemand.run()
                print(f"2. DataDemandAgent执行结果:")
                print(f"   行政等级: {dataDemandResult.admin_level}")
                print(f"   shp路径: {dataDemandResult.shp_path}")
                print(f"   数据需求: {dataDemandResult.data_requires}")
                print(f"   数据路径: {dataDemandResult.data_paths}")
                print(f"   检索状态: {dataDemandResult.require_status}")
                
                # 第三步：使用AlgorithmExeAgent处理
                objAlgorithmExe = AlgorithmExeAgent(self.inputBaseAgent, dataDemandResult)
                algorithmExeResult = objAlgorithmExe.run()
                success_count += 1
                print("3. AlgorithmExeAgent测试通过")
                self._displayResult(algorithmExeResult)  # 显示执行结果
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
    @brief: 验证执行结果
    @param result: 执行结果
    @param original_input: 原始输入
    @return: 验证是否通过
    """
    def _validateResult(self, result: AlgorithmExeResult, original_input: str) -> bool:
        if not isinstance(result, AlgorithmExeResult):
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
        
        # 验证结果路径
        if not isinstance(result.result_paths, list):
            print("result_paths格式错误，应为列表")
            return False
        
        # 根据任务类型验证其他属性
        if result.task_type == 0:  # 自然对话任务
            if result.result_names is not None:
                print("自然对话任务的result_names应为None")
                return False
            
            if result.exe_status is not None:
                print("自然对话任务的exe_status应为None")
                return False
                
            if len(result.result_paths) != 1:
                print("自然对话任务的result_paths长度应为1")
                return False
                
        elif result.task_type == 1:  # 数据展示任务
            if result.result_names is None:
                print("数据展示任务的result_names不应为None")
                return False
            
            if result.exe_status is None:
                print("数据展示任务的exe_status不应为None")
                return False
            
            if not isinstance(result.result_names, list):
                print("result_names格式错误，应为列表")
                return False
                
            if not isinstance(result.exe_status, list):
                print("exe_status格式错误，应为列表")
                return False
            
            # 验证列表长度一致性
            if len(result.result_paths) != len(result.result_names):
                print("result_paths和result_names长度不一致")
                return False
                
            if len(result.result_paths) != len(result.exe_status):
                print("result_paths和exe_status长度不一致")
                return False
            
            # 验证执行状态值
            for status in result.exe_status:
                if status not in [0, 1]:
                    print(f"无效的执行状态值: {status}")
                    return False
        
        return True

    """
    @brief: 显示执行结果
    @param result: 执行结果
    """
    def _displayResult(self, result: AlgorithmExeResult):
        print("AlgorithmExe执行结果详情:")
        print(f"   任务类型: {result.task_type} ({self._getTaskTypeName(result.task_type)})")
        print(f"   原始输入: {result.original_input}")
        
        if result.task_type == 0:  # 自然对话任务
            # 显示模型回复（限制长度）
            reply_preview = result.result_paths[0]
            if len(reply_preview) > 100:
                reply_preview = reply_preview[:100] + "..."
            print(f"   模型回复预览: {reply_preview}")
            print(f"   回复完整长度: {len(result.result_paths[0])} 字符")
        else:  # 数据展示任务
            print(f"   结果名称列表: {result.result_names}")
            print(f"   结果路径列表: {result.result_paths}")
            print(f"   执行状态列表: {result.exe_status}")
            
            # 统计执行结果
            success_count = sum(result.exe_status) if result.exe_status else 0
            total_count = len(result.exe_status) if result.exe_status else 0
            print(f"   执行统计: 成功 {success_count}/{total_count}")
            
            # 显示每个数据项的详细状态
            for i, (name, path, status) in enumerate(zip(result.result_names, result.result_paths, result.exe_status)):
                status_str = "成功" if status == 1 else "失败"
                print(f"      {i+1}. {name}: {status_str} ({path})")
    
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
        print("-" * 50)
        try:
            # 第一步：使用InterParserAgent解析用户输入
            interParserResult = self.objInterParser.run(test_input)
            print(f"1. InterParser解析结果:")
            print(f"   任务类型: {interParserResult.task_type}")
            print(f"   时间: {interParserResult.time}")
            print(f"   地点: {interParserResult.location}")
            
            # 第二步：使用DataDemandAgent处理数据需求
            objDataDemand = DataDemandAgent(self.inputBaseAgent, interParserResult)
            dataDemandResult = objDataDemand.run()
            print(f"2. DataDemandAgent执行结果:")
            print(f"   行政等级: {dataDemandResult.admin_level}")
            print(f"   shp路径: {dataDemandResult.shp_path}")
            print(f"   数据需求: {dataDemandResult.data_requires}")
            print(f"   数据路径: {dataDemandResult.data_paths}")
            print(f"   检索状态: {dataDemandResult.require_status}")
            
            # 第三步：使用AlgorithmExeAgent处理
            objAlgorithmExe = AlgorithmExeAgent(self.inputBaseAgent, dataDemandResult)
            algorithmExeResult = objAlgorithmExe.run()
            print(f"3. AlgorithmExeAgent执行结果:")
            self._displayResult(algorithmExeResult)
            
            # 验证结果
            if self._validateResult(algorithmExeResult, test_input):
                print("✓ 结果验证通过")
            else:
                print("✗ 结果验证失败")
                
        except Exception as e:
            print(f"测试失败: {e}")

"""
@brief: 主函数
"""
def main():
    print("=" * 60)
    print("       AlgorithmExeAgent 测试程序")
    print("=" * 60)
    test_agent = TestAlgorithmExeAgent()  # 创建测试实例
    #test_agent.test()  # 执行完整测试套件
    
    print("\n" + "=" * 60)
    print("       手动测试用例")
    print("=" * 60)
    
    # 精选测试用例，涵盖不同场景
    test_cases = [
        "显示2018年北京市土地覆盖情况",
        "展示2020年广州市人口数据",
        "展示2023年武汉市天气数据",
    ]
    
    for test_input in test_cases:
        test_agent.runSingleTest(test_input)

"""
@brief: 程序入口
"""
if __name__ == "__main__":
    main()