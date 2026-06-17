<template>
  <div class="chat-wrapper">
    <!-- 聊天头部 -->
    <div class="chat-header">
      <div class="chat-title">
        <i class="fas fa-comments"></i> Chat
      </div>
      <button class="close-btn" @click="closePanel" title="关闭">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <!-- 消息容器 -->
    <div class="messages-container" ref="chatBox" :style="{ flex: messagesFlex }">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message"
        :class="[msg.role + '-message', { 'loading-message': msg.isLoading }]"
      >
        <div v-if="msg.isLoading" class="loading-content">
          <span class="spinner"></span>
          <span>{{ msg.content }}</span>
        </div>
        <div v-else v-html="formatMessage(msg.content)"></div>
      </div>
    </div>

    <!-- 垂直调整条 -->
    <div class="vertical-resizer" @mousedown="startVerticalResize">
      <div class="resizer-handle"></div>
    </div>

    <!-- 输入区域 -->
    <div class="input-container" :style="{ flex: inputFlex }">
      <div class="input-row">
        <textarea
          v-model="input"
          placeholder="输入您的问题或指令... (例如: '显示2035年规划图' 或 '分析交通可达性')"
          @keydown.enter.prevent="handleEnter"
        ></textarea>
      </div>
      <div class="action-buttons">
        <button class="btn btn-primary" @click="sendMessage">
          <i class="fas fa-paper-plane"></i> 发送消息
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { chatWithBackend } from '../api/chat'

const emit = defineEmits(['backend-response', 'close'])

const input = ref('')
const messages = ref([
  { role: 'system', content: '您好，我是CityLLM，您有什么问题？' }
])
const chatBox = ref(null)

// 加载状态
const isLoading = ref(false)

// 任务类型配置
const TASK_CONFIG = {
  0: {
    texts: ['正在解析用户输入...', '自然对话输出中...'],
    duration: 5000
  },
  1: {
    texts: ['任务分解中...', '正在解析用户输入...', '正在检索数据...', '正在渲染地图...'],
    duration: 8000
  },
  2: {
    texts: ['任务分解中...', '正在解析用户输入...', '正在检索数据...', '正在执行模拟算法...'],
    duration: 11500,
    stepDurations: [2500, 2500, 2500, 4000] // 前3步各2.5s，最后一步4s
  }
}

// 根据用户输入判断 task_type（写死匹配规则用于展示）
function detectTaskType(userInput) {
  const input = userInput.trim()

  // task_type 0: 自然对话
  const type0Inputs = [
    '城市空间演化主要受到哪些因素影响？'
  ]
  if (type0Inputs.includes(input)) {
    return 0
  }

  // task_type 1: 数据展示
  const type1Inputs = [
    '我想了解下北京市2018年的土地利用和人口分布情况。',
    '我想了解下武汉市2010年、2020年的土地利用分布情况。'
  ]
  if (type1Inputs.includes(input)) {
    return 1
  }

  // task_type 2: 模拟预测
  const type2Inputs = [
    '假设未来5年武汉城市规模快速扩张，模拟2030年武汉市的土地利用情况。',
    '假设未来5年武汉城市实现紧凑发展，模拟2030年武汉市的土地利用情况。',
    '按照历史发展趋势，预测一下武汉市2030年的土地利用、人口分布、经济发展状况，其空间分布如何？'
  ]
  if (type2Inputs.includes(input)) {
    return 2
  }

  // 默认使用自然对话
  return 0
}

// 高度比例（使用 flex 值）
const messagesFlex = ref(3)
const inputFlex = ref(1)
const MIN_MESSAGES_FLEX = 1
const MIN_INPUT_FLEX = 0.5

// 垂直拖动调整
let isVerticalResizing = false
let startY = 0
let startMessagesFlex = 0
let startInputFlex = 0
let chatWrapperHeight = 0

function startVerticalResize(e) {
  isVerticalResizing = true
  startY = e.clientY
  startMessagesFlex = messagesFlex.value
  startInputFlex = inputFlex.value

  // 获取聊天面板高度（减去头部高度）
  const chatWrapper = document.querySelector('.chat-wrapper')
  if (chatWrapper) {
    chatWrapperHeight = chatWrapper.clientHeight - 50 // 50px 是头部高度
  }

  document.addEventListener('mousemove', handleVerticalResize)
  document.addEventListener('mouseup', stopVerticalResize)
}

function handleVerticalResize(e) {
  if (!isVerticalResizing) return

  const deltaY = e.clientY - startY
  const totalFlex = startMessagesFlex + startInputFlex
  const deltaFlex = (deltaY / chatWrapperHeight) * totalFlex

  const newMessagesFlex = startMessagesFlex + deltaFlex
  const newInputFlex = startInputFlex - deltaFlex

  // 限制最小高度
  if (newMessagesFlex >= MIN_MESSAGES_FLEX && newInputFlex >= MIN_INPUT_FLEX) {
    messagesFlex.value = newMessagesFlex
    inputFlex.value = newInputFlex
  }
}

function stopVerticalResize() {
  isVerticalResizing = false
  document.removeEventListener('mousemove', handleVerticalResize)
  document.removeEventListener('mouseup', stopVerticalResize)
}

function closePanel() {
  emit('close')
}

watch(messages, async () => {
  await nextTick()
  if (chatBox.value) {
    chatBox.value.scrollTop = chatBox.value.scrollHeight
  }
}, { deep: true })

function formatMessage(content) {
  // 简单处理换行
  return content.replace(/\n/g, '<br>')
}

function handleEnter(e) {
  if (!e.shiftKey) {
    sendMessage()
  } else {
    input.value += '\n'
  }
}

// 运行加载动画
async function runLoadingAnimation(loadingMsgRef, apiPromise, predictedTaskType) {
  const startTime = Date.now()
  const currentConfig = TASK_CONFIG[predictedTaskType] // 使用预测的配置启动
  let currentStep = 0

  // 计算每个步骤的开始时间
  const getStepStartTime = (stepIndex) => {
    if (currentConfig.stepDurations) {
      // 使用自定义步骤时长
      let time = 0
      for (let i = 0; i < stepIndex; i++) {
        time += currentConfig.stepDurations[i]
      }
      return time
    } else {
      // 平均分配时长
      const stepDuration = currentConfig.duration / (currentConfig.texts.length - 1)
      return stepIndex * stepDuration
    }
  }

  // 获取最小总时长（最后一步的结束时间）
  const getMinDuration = () => {
    if (currentConfig.stepDurations) {
      return currentConfig.stepDurations.reduce((a, b) => a + b, 0)
    } else {
      return currentConfig.duration
    }
  }

  // 文字轮播定时器
  const intervalId = setInterval(() => {
    const elapsed = Date.now() - startTime
    let newStep = currentStep

    // 找到当前应该显示的步骤
    for (let i = currentConfig.texts.length - 1; i >= 0; i--) {
      if (elapsed >= getStepStartTime(i)) {
        newStep = i
        break
      }
    }

    if (newStep !== currentStep) {
      currentStep = newStep
      if (loadingMsgRef.value) {
        loadingMsgRef.value.content = currentConfig.texts[currentStep]
      }
    }
  }, 100)

  // 等待 API 完成
  const apiResult = await apiPromise

  // 确保至少显示完所有文字步骤
  const elapsed = Date.now() - startTime
  const minDuration = getMinDuration()
  const remainingTime = Math.max(0, minDuration - elapsed)

  if (remainingTime > 0) {
    await new Promise(resolve => setTimeout(resolve, remainingTime))
  }

  clearInterval(intervalId)
  return apiResult
}

async function sendMessage() {
  if (!input.value.trim() || isLoading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: input.value })

  const userInput = input.value
  input.value = ''
  isLoading.value = true

  // 根据用户输入预测 task_type
  const predictedTaskType = detectTaskType(userInput)

  // 添加 loading 消息
  const loadingMsgIndex = messages.value.length
  const loadingMsg = {
    role: 'system',
    content: TASK_CONFIG[predictedTaskType].texts[0],
    isLoading: true
  }
  messages.value.push(loadingMsg)

  // 创建 loading 消息的引用
  const loadingMsgRef = ref(messages.value[loadingMsgIndex])

  // 监听 messages 数组变化，更新引用
  watch(() => messages.value[loadingMsgIndex], (newVal) => {
    if (newVal) {
      loadingMsgRef.value = newVal
    }
  }, { immediate: true })

  try {
    // 启动 API 请求和加载动画（传入预测的 task_type）
    const res = await runLoadingAnimation(
      loadingMsgRef,
      chatWithBackend(userInput),
      predictedTaskType
    )

    // 移除 loading 消息
    messages.value.splice(loadingMsgIndex, 1)

    // 触发后端响应事件
    emit('backend-response', res)

    // 根据响应添加系统消息
    if (res.reply) {
      messages.value.push({ role: 'system', content: res.reply })
    } else if (res.task_type === 0) {
      messages.value.push({ role: 'system', content: '已理解您的问题，请继续提问。' })
    } else if (res.result_paths && res.result_paths.length > 0) {
      messages.value.push({ role: 'system', content: '处理完成，结果已显示在地图上。' })
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    // 移除 loading 消息
    messages.value.splice(loadingMsgIndex, 1)
    messages.value.push({ role: 'system', content: '请求失败，请稍后重试。' })
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.chat-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 聊天头部 */
.chat-header {
  height: 50px;
  background-color: #2c6e9e;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #1d4f73;
  flex-shrink: 0;
}

.chat-title {
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 5px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

/* 消息容器 */
.messages-container {
  overflow-y: auto;
  padding: 20px;
  background-color: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 15px;
  min-height: 100px;
}

/* 消息气泡 */
.message {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

.user-message {
  align-self: flex-end;
  background-color: #2c6e9e;
  color: white;
  border-bottom-right-radius: 4px;
}

.system-message {
  align-self: flex-start;
  background-color: white;
  color: #333;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 4px;
}

/* Loading 消息样式 */
.loading-message {
  background-color: #f0f9ff;
  border: 1px solid #bae6fd;
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #2c6e9e;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 垂直调整条 */
.vertical-resizer {
  height: 3px;
  background-color: transparent;
  cursor: row-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 10;
  transition: background-color 0.2s;
}

.vertical-resizer:hover {
  background-color: #2c6e9e;
}

.resizer-handle {
  width: 30px;
  height: 4px;
  background-color: #999;
  border-radius: 2px;
  opacity: 0;                 /* 默认完全透明 */
  transition: opacity 0.2s, background-color 0.2s;
}

.vertical-resizer:hover .resizer-handle {
  opacity: 1;                /* 悬停时显示手柄 */
  background-color: white;   /* 白色手柄与蓝色背景搭配 */
}

/* 输入区域 */
.input-container {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  background-color: white;
  display: flex;
  flex-direction: column;
  gap: 15px;
  min-height: 120px;
}

.input-row {
  display: flex;
  gap: 10px;
  flex: 1;
}

textarea {
  flex: 1;
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  resize: none;
  min-height: 60px;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}

textarea:focus {
  outline: none;
  border-color: #2c6e9e;
  box-shadow: 0 0 0 3px rgba(44, 110, 158, 0.1);
}

/* 按钮 */
.btn {
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-primary {
  background-color: #2c6e9e;
  color: white;
}

.btn-primary:hover {
  background-color: #255a82;
  box-shadow: 0 4px 8px rgba(44, 110, 158, 0.2);
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
}

/* 响应式 */
@media (max-width: 900px) {
  .action-buttons {
    justify-content: center;
  }
}
</style>
