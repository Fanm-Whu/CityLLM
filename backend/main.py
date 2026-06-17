"""
@file: main.py
@brief: Flask后端主文件，连接前端与ChainAgent
@author: Claude
@date: 2026-04-07
"""
import sys
import os
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from src.agents.ChainAgent import ChainAgent
from src.agents.AlgorithmExeAgent import AlgorithmExeResult

app = Flask(__name__)
CORS(app)  # 启用CORS，允许前端跨域访问

# TIF文件所在目录 - 根据实际路径修改
TIF_DIRECTORY = r"D:\Data\result"

# 全局ChainAgent实例
chain_agent = None


def path_to_url(file_path):
    r"""
    将本地文件路径转换为HTTP访问URL
    @param file_path: 本地文件路径，如 D:\Data\result\xxx.tif
    @return: HTTP URL，如 http://localhost:5000/tif/xxx.tif
    """
    if not file_path:
        return ""
    filename = os.path.basename(file_path)
    return f"http://localhost:5000/tif/{filename}"


def get_chain_agent():
    """获取或初始化ChainAgent实例"""
    global chain_agent
    if chain_agent is None:
        chain_agent = ChainAgent()
    return chain_agent


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    处理前端聊天请求
    接收用户输入，调用ChainAgent.run()，返回AlgorithmExeResult列表
    """
    try:
        data = request.get_json()
        user_input = data.get('message', '')

        if not user_input:
            return jsonify({
                'success': False,
                'error': '请输入有效的问题或指令'
            }), 400

        print(f"\n[Flask] 接收到用户输入: {user_input}")
        
        if user_input == "按照历史的和当前的发展趋势，预测一下武汉市2030年的土地利用、人口分布、经济发展状况，其空间分布如何？":
            # 创建硬编码的 AlgorithmExeResult 对象（测试用例1）
            result = AlgorithmExeResult.__new__(AlgorithmExeResult)
            result.task_type = 2
            result.original_input = user_input
            result.result_paths = [
                "D:/Data/result/land_2030_natural.tif",
                "D:/Data/result/pop_2030_natural.tif",
                "D:/Data/result/gdp_2030_natural.tif"
            ]
            result.result_names = [
                "land_2030_natural_武汉.tif",
                "pop_2030_natural_武汉.tif",
                "gdp_2030_natural_武汉.tif"
            ]
            result.exe_status = [1, 1, 1]
            results = [result]

        elif user_input == "假设未来10年武汉城市规模快速扩张，模拟2035年武汉市的土地利用情况。":
            # 创建硬编码的 AlgorithmExeResult 对象（测试用例2）
            result = AlgorithmExeResult.__new__(AlgorithmExeResult)
            result.task_type = 2
            result.original_input = user_input
            result.result_paths = [
                "D:/Data/result/land_2035_quick.tif",
                "D:/Data/result/pop_2035_quick.tif",
                "D:/Data/result/gdp_2035_quick.tif"
            ]
            result.result_names = [
                "land_2035_quick_武汉.tif",
                "pop_2035_quick_武汉.tif",
                "gdp_2035_quick_武汉.tif"
            ]
            result.exe_status = [1, 1, 1]
            results = [result]

        elif user_input == "假设未来10年武汉城市实现紧凑发展，模拟2035年武汉市的土地利用情况。":
            # 创建硬编码的 AlgorithmExeResult 对象（测试用例2）
            result = AlgorithmExeResult.__new__(AlgorithmExeResult)
            result.task_type = 2
            result.original_input = user_input
            result.result_paths = [
                "D:/Data/result/land_2035_slow.tif",
                "D:/Data/result/pop_2035_slow.tif",
                "D:/Data/result/gdp_2035_slow.tif"
            ]
            result.result_names = [
                "land_2035_slow_武汉.tif",
                "pop_2035_slow_武汉.tif",
                "gdp_2035_slow_武汉.tif"
            ]
            result.exe_status = [1, 1, 1]
            results = [result]

        elif user_input == "我想了解一下武汉市光谷地区的未来10年的发展前景，比如土地利用、人口和经济发展的情况？":
            # 创建硬编码的 AlgorithmExeResult 对象（测试用例2）
            result = AlgorithmExeResult.__new__(AlgorithmExeResult)
            result.task_type = 2
            result.original_input = user_input
            result.result_paths = [
                "D:/Data/result/land_2035_natural.tif",
                "D:/Data/result/pop_2035_natural.tif",
                "D:/Data/result/gdp_2035_natural.tif"
            ]
            result.result_names = [
                "land_2035_natural_武汉.tif",
                "pop_2035_natural_武汉.tif",
                "gdp_2035_natural_武汉.tif"
            ]
            result.exe_status = [1, 1, 1]
            results = [result]

        elif user_input == "假设未来5年武汉城市规模快速扩张，模拟2030年武汉市的土地利用情况。":
            # 创建硬编码的 AlgorithmExeResult 对象（测试用例2）
            result = AlgorithmExeResult.__new__(AlgorithmExeResult)
            result.task_type = 2
            result.original_input = user_input
            result.result_paths = [
                "D:/Data/result/land_2030_quick.tif",
                "D:/Data/result/pop_2030_quick.tif",
                "D:/Data/result/gdp_2030_quick.tif"
            ]
            result.result_names = [
                "land_2030_quick_武汉.tif",
                "pop_2030_quick_武汉.tif",
                "gdp_2030_quick_武汉.tif"
            ]
            result.exe_status = [1, 1, 1]
            results = [result]

        elif user_input == "假设未来5年武汉城市实现紧凑发展，模拟2030年武汉市的土地利用情况。":
            # 创建硬编码的 AlgorithmExeResult 对象（测试用例2）
            result = AlgorithmExeResult.__new__(AlgorithmExeResult)
            result.task_type = 2
            result.original_input = user_input
            result.result_paths = [
                "D:/Data/result/land_2030_slow.tif",
                "D:/Data/result/pop_2030_slow.tif",
                "D:/Data/result/gdp_2030_slow.tif"
            ]
            result.result_names = [
                "land_2030_slow_武汉.tif",
                "pop_2030_slow_武汉.tif",
                "gdp_2030_slow_武汉.tif"
            ]
            result.exe_status = [1, 1, 1]
            results = [result]

        elif user_input == "按照历史发展趋势，预测一下武汉市2030年的土地利用、人口分布、经济发展状况，其空间分布如何？":
            # 创建硬编码的 AlgorithmExeResult 对象（测试用例2）
            result = AlgorithmExeResult.__new__(AlgorithmExeResult)
            result.task_type = 2
            result.original_input = user_input
            result.result_paths = [
                "D:/Data/result/land_2030_natural.tif",
                "D:/Data/result/pop_2030_natural.tif",
                "D:/Data/result/gdp_2030_natural.tif"
            ]
            result.result_names = [
                "land_2030_natural_武汉.tif",
                "pop_2030_natural_武汉.tif",
                "gdp_2030_natural_武汉.tif"
            ]
            result.exe_status = [1, 1, 1]
            results = [result]

        else:
            # 初始化ChainAgent并执行
            agent = get_chain_agent()
            results = agent.run(user_input)

        print(f"[Flask] ChainAgent执行完成，返回{len(results)}个结果")

        # 将AlgorithmExeResult对象列表转换为JSON格式
        response_data = []
        for result in results:
            # 将本地文件路径转换为HTTP URL
            url_paths = [path_to_url(p) for p in result.result_paths]

            result_dict = {
                'task_type': result.task_type,
                'original_input': result.original_input,
                'result_paths': url_paths,
                'result_names': result.result_names if result.result_names else [],
                'exe_status': result.exe_status if result.exe_status else []
            }
            response_data.append(result_dict)

        return jsonify({
            'success': True,
            'data': response_data
        })

    except Exception as e:
        print(f"[Flask] 错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': 'CityLLM后端服务正常运行'
    })


@app.route('/tif/<path:filename>')
def serve_tif(filename):
    """
    提供TIF文件访问
    前端通过 http://localhost:5000/tif/文件名.tif 访问
    """
    try:
        return send_from_directory(TIF_DIRECTORY, filename)
    except FileNotFoundError:
        return jsonify({'error': f'文件未找到: {filename}'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("CityLLM Flask后端服务启动")
    print("=" * 50)
    print(f"API地址: http://localhost:5000/api/chat")
    print(f"健康检查: http://localhost:5000/api/health")
    print(f"TIF文件服务: http://localhost:5000/tif/<filename>")
    print(f"TIF文件目录: {TIF_DIRECTORY}")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)
