<template>
  <div class="gis-container">
    <!-- 头部区域 -->
    <div class="app-header">
      <div class="header-title">
        <i class="fas fa-map"></i> CityLLM
      </div>
      <div class="header-tools">
        <button class="header-btn" @click="exportMap">
          <i class="fas fa-download"></i> 导出
        </button>
        <button class="header-btn chat-btn" @click="toggleChatPanel" v-if="!chatVisible">
          <i class="fas fa-comments"></i> Chat
        </button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧数据图层面板 -->
      <DataLayerPanel
        :layers="dataLayers"
        @toggle-layer="handleToggleLayer"
        @toggle-expand="handleToggleExpand"
      />

      <!-- 地图面板 -->
      <div class="map-panel" :style="{ flex: mapFlex }">
        <div class="map-content">
          <MapView
            v-if="shouldRenderMap"
            :layerUrls="activeLayerUrls"
            :taskType="currentTaskType"
            :dataType="currentDataType"
                      />
          <div v-else class="placeholder">
            <i class="fas fa-map-marked-alt" style="font-size: 48px; color: #ccc; margin-bottom: 16px;"></i>
            <div>等待渲染结果</div>
          </div>
        </div>

        <!-- 地图控制按钮 -->
        <div class="map-controls">
          <div class="map-control" @click="zoomIn" title="放大">
            <i class="fas fa-plus"></i>
          </div>
          <div class="map-control" @click="zoomOut" title="缩小">
            <i class="fas fa-minus"></i>
          </div>
        </div>

      </div>

      <!-- 调整条（Map 和 Chat 之间） -->
      <div
        v-if="chatVisible"
        class="horizontal-resizer"
        @mousedown="startHorizontalResize"
      >
        <div class="resizer-handle"></div>
      </div>

      <!-- 右侧聊天面板 -->
      <ChatPanel
        v-show="chatVisible"
        class="chat-panel"
        :style="{ flex: chatFlex }"
        @backend-response="handleBackendResponse"
        @close="closeChatPanel"
      />
    </div>

    <!-- 模拟指示器 -->
    <div v-if="simulating" class="simulation-indicator">
      <i class="fas fa-sync-alt fa-spin"></i> 正在运行模拟...
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import MapView from './components/MapView.vue'
import ChatPanel from './components/ChatPanel.vue'
import DataLayerPanel from './components/DataLayerPanel.vue'

const tifUrl = ref(null)
const shouldRenderMap = ref(true)  // 默认显示地图，加载省级行政区划底图
// 支持多图层叠加：存储所有勾选图层的URL数组，按显示顺序（后加载的在数组后面，显示在上层）
const activeLayerUrls = ref([])
const chatVisible = ref(true)
const simulating = ref(false)

// 数据图层列表
const dataLayers = ref([])

// 当前任务类型和数据类型（用于地图配色）
const currentTaskType = ref(null)
const currentDataType = ref(null)

// 计算当前激活的图层
const activeLayers = computed(() => {
  return dataLayers.value.filter(layer => layer.checked)
})

/**
 * 根据图层名称识别数据类型
 * @param {string} name - 图层名称
 * @param {number} taskType - 任务类型
 * @returns {string} - 数据类型标识
 */
function detectDataType(name, taskType) {
  const lowerName = name.toLowerCase()

  // 模拟预测任务 (task_type = 2)
  if (taskType === 2) {
    if (lowerName.includes('land') || lowerName.includes('土地利用') || lowerName.includes('用地')) {
      return 'sim_landuse'
    }
    if (lowerName.includes('pop') || lowerName.includes('人口')) {
      return 'sim_population'
    }
    if (lowerName.includes('gdp')) {
      return 'sim_gdp'
    }
  }

  // 数据展示任务 (task_type = 1)
  if (lowerName.includes('land') || lowerName.includes('土地覆盖') || lowerName.includes('覆盖')) {
    return 'landcover'
  }
  if (lowerName.includes('pop') || lowerName.includes('人口')) {
    return 'population'
  }
  if (lowerName.includes('gdp')) {
    return 'gdp'
  }

  // 默认返回 landcover
  return 'landcover'
}

// 面板宽度比例（使用 flex 值）
const mapFlex = ref(5)
const chatFlex = ref(2)
const MIN_MAP_FLEX = 2
const MIN_CHAT_FLEX = 1

// 水平拖动调整
let isHorizontalResizing = false
let startX = 0
let startMapFlex = 0
let startChatFlex = 0

function startHorizontalResize(e) {
  isHorizontalResizing = true
  startX = e.clientX
  startMapFlex = mapFlex.value
  startChatFlex = chatFlex.value

  document.addEventListener('mousemove', handleHorizontalResize)
  document.addEventListener('mouseup', stopHorizontalResize)
}

function handleHorizontalResize(e) {
  if (!isHorizontalResizing) return

  const deltaX = e.clientX - startX
  const containerWidth = document.querySelector('.main-content').clientWidth
  const deltaFlex = (deltaX / containerWidth) * 7

  const newMapFlex = startMapFlex + deltaFlex
  const newChatFlex = startChatFlex - deltaFlex

  if (newMapFlex >= MIN_MAP_FLEX && newChatFlex >= MIN_CHAT_FLEX) {
    mapFlex.value = newMapFlex
    chatFlex.value = newChatFlex
  }
}

function stopHorizontalResize() {
  isHorizontalResizing = false
  document.removeEventListener('mousemove', handleHorizontalResize)
  document.removeEventListener('mouseup', stopHorizontalResize)
}

function handleBackendResponse(res) {
  console.log('App.vue 接收到后端结果:', res)

  // task_type = 0: 自然对话任务，只隐藏TIF图层，保留地图底图
  if (res.task_type === 0) {
    // 不清空数据，只是不显示TIF图层
    tifUrl.value = null
    currentTaskType.value = null
    currentDataType.value = null
    return
  }

  // task_type = 1 或 2: 数据展示或模拟预测任务
  if (
    (res.task_type === 1 || res.task_type === 2) &&
    res.result_paths &&
    res.result_paths.length > 0
  ) {
    // 设置任务类型
    currentTaskType.value = res.task_type

    // 显示第一个TIF文件
    tifUrl.value = res.result_paths[0]
    shouldRenderMap.value = true

    // 使用layerMapping维护name和path的对应关系（优先）
    // 或者使用result_names和result_paths数组
    let firstItemName = null

    if (res.layerMapping && res.layerMapping.length > 0) {
      // 使用字典(layerMapping)来维护name-path对应关系
      // 新数据添加到列表开头（最上层）
      for (let i = res.layerMapping.length - 1; i >= 0; i--) {
        const item = res.layerMapping[i]
        const exists = dataLayers.value.some(layer => layer.name === item.name)
        if (!exists) {
          // 使用 unshift 将新数据添加到列表开头
          dataLayers.value.unshift({
            name: item.name,
            path: item.path,
            checked: true, // 新数据默认勾选
            expanded: true, // 默认展开图例
            dataType: detectDataType(item.name, res.task_type) // 数据类型
          })
          // 取消其他图层的勾选
          dataLayers.value.forEach((layer, idx) => {
            if (idx !== 0) layer.checked = false
          })
        }
        // 记录第一个图层名称用于识别数据类型
        if (firstItemName === null) {
          firstItemName = item.name
        }
      }
    } else if (res.result_names && res.result_names.length > 0) {
      // 使用两个列表维护对应关系
      // 新数据添加到列表开头（最上层）
      for (let i = res.result_names.length - 1; i >= 0; i--) {
        const name = res.result_names[i]
        const path = res.result_paths[i] || ''

        // 检查是否已存在
        const exists = dataLayers.value.some(layer => layer.name === name)
        if (!exists) {
          // 使用 unshift 将新数据添加到列表开头
          dataLayers.value.unshift({
            name: name,
            path: path,
            checked: true, // 新数据默认勾选
            expanded: true, // 默认展开图例
            dataType: detectDataType(name, res.task_type) // 数据类型
          })
          // 取消其他图层的勾选
          dataLayers.value.forEach((layer, idx) => {
            if (idx !== 0) layer.checked = false
          })
        }
        // 记录第一个图层名称用于识别数据类型
        if (firstItemName === null) {
          firstItemName = name
        }
      }
    }

    // 根据当前加载的第一个图层名称识别数据类型（顶层图层）
    if (firstItemName) {
      currentDataType.value = detectDataType(firstItemName, res.task_type)
    }

    // 更新显示的图层URL列表（按数据框从上到下 = 地图从下到上）
    updateActiveLayerUrls()

    console.log('设置任务类型:', currentTaskType.value, '数据类型:', currentDataType.value, '活跃图层:', activeLayerUrls.value)
  }
}

function handleToggleLayer(index, checked) {
  if (dataLayers.value[index]) {
    dataLayers.value[index].checked = checked

    // 更新显示的图层列表
    updateActiveLayerUrls()

    // 更新当前数据类型为顶层图层（列表最后一个）的类型
    const checkedLayers = dataLayers.value.filter(l => l.checked && l.path)
    if (checkedLayers.length > 0) {
      // 顶层图层是列表最后一个
      const topLayer = checkedLayers[checkedLayers.length - 1]
      currentDataType.value = detectDataType(topLayer.name, currentTaskType.value)
    }
    // 地图始终显示（保留行政区划底图），通过 layerUrls 控制 TIF 图层的显示
  }
}

function handleToggleExpand(index, expanded) {
  if (dataLayers.value[index]) {
    dataLayers.value[index].expanded = expanded
  }
}

/**
 * 更新活跃图层URL列表
 * 按数据框从上到下顺序（数组顺序），地图显示时后加载的在上层
 */
function updateActiveLayerUrls() {
  // 获取所有勾选的图层，保持数据框中的顺序（从上到下）
  activeLayerUrls.value = dataLayers.value
    .filter(layer => layer.checked && layer.path)
    .map(layer => layer.path)

  console.log('更新活跃图层:', activeLayerUrls.value)
}

function toggleChatPanel() {
  chatVisible.value = !chatVisible.value
}

function closeChatPanel() {
  chatVisible.value = false
}

function zoomIn() {
  window.dispatchEvent(new CustomEvent('map-zoom-in'))
}

function zoomOut() {
  window.dispatchEvent(new CustomEvent('map-zoom-out'))
}


function exportMap() {
  alert('导出功能将在完整版本中实现')
}
</script>

<style scoped>
.gis-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* 顶部头部 */
.app-header {
  height: 50px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #1a252f;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
  flex-shrink: 0;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-tools {
  display: flex;
  gap: 10px;
}

.header-btn {
  background-color: #34495e;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.2s;
}

.header-btn:hover {
  background-color: #3d566e;
}

.chat-btn {
  background-color: #2c6e9e;
}

.chat-btn:hover {
  background-color: #255a82;
}

/* 主内容区域 */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 地图面板 */
.map-panel {
  position: relative;
  background-color: #f5f7fa;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-width: 200px;
}

.map-content {
  flex: 1;
  width: 100%;
  position: relative;
}

.placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #777;
  font-size: 16px;
}

/* 地图控制按钮 */
.map-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.map-control {
  background-color: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #2c3e50;
  font-size: 14px;
  transition: all 0.2s;
}

.map-control:hover {
  background-color: #f8f9fa;
  box-shadow: 0 3px 8px rgba(0,0,0,0.15);
}

/* 地图容器 - 拖动时手型光标 */
.map-content :deep(.ol-viewport) {
  cursor: grab;
}

.map-content :deep(.ol-viewport:active) {
  cursor: grabbing;
}

/* 水平调整条 */
.horizontal-resizer {
  width: 3px;
  background-color: transparent;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
  transition: background-color 0.2s;
}

.horizontal-resizer:hover {
  background-color: #2c6e9e;
}

.resizer-handle {
  width: 4px;
  height: 30px;
  background-color: #999;
  border-radius: 2px;
  opacity: 0;                 /* 关键：默认完全透明 */
  transition: opacity 0.2s, background-color 0.2s;
}

.horizontal-resizer:hover .resizer-handle {
  opacity: 1;                /* 悬停时显示手柄 */
  background-color: white;   /* 改为白色，与背景色形成对比 */
}

/* 右侧聊天面板 */
.chat-panel {
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #d9d9d9;
  box-shadow: -2px 0 8px rgba(0,0,0,0.05);
  min-width: 250px;
}

/* 模拟指示器 */
.simulation-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(44, 110, 158, 0.9);
  color: white;
  padding: 15px 25px;
  border-radius: 8px;
  font-weight: 600;
  z-index: 2000;
  box-shadow: 0 6px 20px rgba(0,0,0,0.2);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 0.9; }
  50% { opacity: 1; }
  100% { opacity: 0.9; }
}

/* 响应式调整 */
@media (max-width: 900px) {
  .main-content {
    flex-direction: column;
  }

  .chat-panel {
    min-height: 350px;
    min-width: 100%;
  }

  .map-panel {
    min-height: calc(100vh - 350px);
  }

  .horizontal-resizer {
    display: none;
  }
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
