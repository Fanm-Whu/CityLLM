<template>
  <div class="data-layer-panel" :style="{ flex: panelFlex }">
    <!-- 图层列表 -->
    <div class="layer-list">
      <div v-if="layers.length === 0" class="empty-tip">
        <i class="fas fa-info-circle"></i>
        <span>暂无数据图层</span>
      </div>
      <div
        v-for="(layer, index) in layers"
        :key="index"
        class="layer-item"
        :class="{ checked: layer.checked }"
      >
        <!-- 图层头部：展开按钮 + 复选框 + 名称 -->
        <div class="layer-header">
          <!-- 展开/收起按钮 -->
          <button
            class="expand-btn"
            @click="toggleExpand(index)"
            :title="layer.expanded ? '收起图例' : '展开图例'"
          >
            <span class="expand-icon">{{ layer.expanded ? '−' : '+' }}</span>
          </button>

          <label class="layer-label">
            <input
              type="checkbox"
              v-model="layer.checked"
              @change="toggleLayer(index)"
            />
            <span class="checkmark"></span>
            <span class="layer-name" :title="layer.name">{{ layer.name }}</span>
          </label>
        </div>

        <!-- 图例区域 -->
        <div v-if="layer.expanded && isCategoricalType(layer.dataType)" class="legend-container">
          <div class="categorical-legend">
            <div
              v-for="(item, idx) in getCategoricalLegend(layer.dataType)"
              :key="idx"
              class="legend-item"
            >
              <span
                class="legend-color-box"
                :style="{ backgroundColor: item.color }"
              ></span>
              <span class="legend-label">{{ item.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧调整条 -->
    <div class="resizer" @mousedown="startResize">
      <div class="resizer-handle"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  layers: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['toggle-layer', 'update:layers', 'toggle-expand'])

// 面板宽度（flex值）
const panelFlex = ref(1.5)
const MIN_FLEX = 0.8
const MAX_FLEX = 4

// 调整大小
let isResizing = false
let startX = 0
let startFlex = 0
let containerWidth = 0

function startResize(e) {
  isResizing = true
  startX = e.clientX
  startFlex = panelFlex.value

  const container = document.querySelector('.main-content')
  if (container) {
    containerWidth = container.clientWidth
  }

  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
}

function handleResize(e) {
  if (!isResizing) return

  const deltaX = e.clientX - startX
  const deltaFlex = (deltaX / containerWidth) * 8.5 // 总flex约为8.5

  const newFlex = startFlex + deltaFlex
  if (newFlex >= MIN_FLEX && newFlex <= MAX_FLEX) {
    panelFlex.value = newFlex
  }
}

function stopResize() {
  isResizing = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

function toggleLayer(index) {
  emit('toggle-layer', index, props.layers[index].checked)
}

function toggleExpand(index) {
  const layer = props.layers[index]
  if (layer) {
    layer.expanded = !layer.expanded
    emit('toggle-expand', index, layer.expanded)
  }
}

// 判断是否为分类数据类型（土地覆盖/土地利用）
function isCategoricalType(dataType) {
  return ['landcover', 'sim_landuse'].includes(dataType)
}

// 获取分类图例数据
function getCategoricalLegend(dataType) {
  // 土地覆盖分类 - 9类 (1-9)，0为NoData
  if (dataType === 'landcover') {
    return [
      { color: '#FBE59C', label: '耕地' },
      { color: '#436F32', label: '森林' },
      { color: '#33A02B', label: '灌木' },
      { color: '#ABD37B', label: '草地' },
      { color: '#1D69B4', label: '水体' },
      { color: '#A5CEE2', label: '雪/冰' },
      { color: '#CEBDA3', label: '裸地' },
      { color: '#E24272', label: '不透水面' },
      { color: '#279BE8', label: '湿地' }
    ]
  }

  // 模拟土地利用分类 - 5类 (0-4)，0值为透明
  if (dataType === 'sim_landuse') {
    return [
      { color: '#D3A463', label: '商业城市用地' },
      { color: '#FFFFBF', label: '住宅用地' },
      { color: '#91BCA8', label: '工业城市用地' },
      { color: '#218292', label: '其他城市土地' }
    ]
  }

  return []
}
</script>

<style scoped>
.data-layer-panel {
  display: flex;
  flex-direction: column;
  background-color: #f8f9fa;
  border-right: 1px solid #d9d9d9;
  position: relative;
  min-width: 180px;
  max-width: 400px;
}

/* 图层列表 */
.layer-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.empty-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #999;
  font-size: 13px;
  padding: 20px;
  text-align: center;
}

.layer-item {
  margin-bottom: 8px;
  padding: 8px 10px;
  background-color: white;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  transition: all 0.2s;
}

.layer-item:hover {
  border-color: #2c6e9e;
  box-shadow: 0 2px 4px rgba(44, 110, 158, 0.1);
}

.layer-item.checked {
  background-color: #e8f4fc;
  border-color: #2c6e9e;
}

/* 图层头部 */
.layer-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 展开/收起按钮 */
.expand-btn {
  width: 18px;
  height: 18px;
  padding: 0;
  border: 1px solid #999;
  background-color: white;
  border-radius: 2px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.expand-btn:hover {
  border-color: #2c6e9e;
  background-color: #e8f4fc;
}

.expand-icon {
  font-size: 14px;
  font-weight: bold;
  color: #333;
  line-height: 1;
}

.layer-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}

.layer-label input[type="checkbox"] {
  display: none;
}

.checkmark {
  width: 16px;
  height: 16px;
  border: 2px solid #999;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.layer-label input[type="checkbox"]:checked + .checkmark {
  background-color: #2c6e9e;
  border-color: #2c6e9e;
}

.layer-label input[type="checkbox"]:checked + .checkmark::after {
  content: '\2713';
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.layer-name {
  font-size: 13px;
  color: #333;
  word-break: break-all;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 图例容器 */
.legend-container {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #ddd;
}

/* 分类图例 */
.categorical-legend {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color-box {
  width: 16px;
  height: 16px;
  border-radius: 2px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.legend-label {
  font-size: 12px;
  color: #666;
}

/* 调整条 */
.resizer {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: transparent;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.resizer:hover {
  background-color: #2c6e9e;
}

.resizer-handle {
  width: 4px;
  height: 30px;
  background-color: #ccc;
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.resizer:hover .resizer-handle {
  opacity: 1;
  background-color: white;
}

/* 滚动条样式 */
.layer-list::-webkit-scrollbar {
  width: 6px;
}

.layer-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.layer-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.layer-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
