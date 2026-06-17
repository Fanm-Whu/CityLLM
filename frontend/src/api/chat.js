// src/api/chat.js

import axios from 'axios'

// Flask后端API基础URL
const API_BASE_URL = 'http://localhost:5000'

/**
 * 与后端Flask API通信
 * 接收用户输入，返回AlgorithmExeResult列表
 */
export async function chatWithBackend(userInput) {
  console.log('【API】发送给后端的内容:', userInput)

  try {
    const response = await axios.post(`${API_BASE_URL}/api/chat`, {
      message: userInput
    })

    if (response.data.success) {
      // 后端返回的是AlgorithmExeResult列表
      const results = response.data.data
      console.log('【API】后端返回结果:', results)

      // 如果结果为空，返回默认响应
      if (!results || results.length === 0) {
        return {
          task_type: 0,
          reply: '未获取到有效结果',
          result_paths: [],
          result_names: [],
          exe_status: []
        }
      }

      // 处理多个结果，合并所有结果
      // 获取第一个非对话任务的结果作为主task_type
      const firstTask = results[0]
      const taskType = firstTask.task_type

      // 如果是对话任务，直接返回
      if (taskType === 0) {
        return {
          task_type: 0,
          reply: firstTask.result_paths[0] || '已收到您的消息',
          result_paths: [],
          result_names: [],
          exe_status: firstTask.exe_status || []
        }
      }

      // 合并所有结果的图层数据
      const allValidResults = []
      results.forEach(result => {
        const resultNames = result.result_names || []
        const resultPaths = result.result_paths || []
        const exeStatus = result.exe_status || []

        for (let i = 0; i < resultNames.length; i++) {
          if (exeStatus[i] === 1 && resultPaths[i]) {
            allValidResults.push({
              name: resultNames[i],
              path: resultPaths[i]
            })
          }
        }
      })

      // 构造合并后的响应
      if (taskType === 1) {
        return {
          task_type: 1,
          reply: allValidResults.length > 0
            ? `数据展示完成，共${allValidResults.length}个数据层`
            : '数据展示失败，未找到有效数据',
          result_paths: allValidResults.map(r => r.path),
          result_names: allValidResults.map(r => r.name),
          exe_status: allValidResults.map(() => 1),
          // 保留完整的name-path映射供App.vue使用
          layerMapping: allValidResults
        }
      } else if (taskType === 2) {
        return {
          task_type: 2,
          reply: allValidResults.length > 0
            ? `模拟预测完成，共${allValidResults.length}个结果`
            : '模拟预测失败',
          result_paths: allValidResults.map(r => r.path),
          result_names: allValidResults.map(r => r.name),
          exe_status: allValidResults.map(() => 1),
          // 保留完整的name-path映射供App.vue使用
          layerMapping: allValidResults
        }
      }

      // 默认返回
      return {
        task_type: taskType,
        reply: '处理完成',
        result_paths: allValidResults.map(r => r.path),
        result_names: allValidResults.map(r => r.name),
        exe_status: allValidResults.map(() => 1)
      }
    } else {
      // 后端返回错误
      return {
        task_type: 0,
        reply: `错误: ${response.data.error || '未知错误'}`,
        result_paths: [],
        result_names: [],
        exe_status: []
      }
    }
  } catch (error) {
    console.error('【API】请求失败:', error)
    return {
      task_type: 0,
      reply: `连接后端失败: ${error.message || '请检查后端服务是否启动'}`,
      result_paths: [],
      result_names: [],
      exe_status: []
    }
  }
}

/**
 * 健康检查
 */
export async function checkHealth() {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/health`)
    return response.data
  } catch (error) {
    return { status: 'error', message: error.message }
  }
}
