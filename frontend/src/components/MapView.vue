<template>
  <div class="map-container">
    <div ref="mapRef" class="map"></div>
    <!-- 隐藏的 canvas 用于 plotty 渲染 -->
    <canvas ref="plottyCanvas" style="display: none;"></canvas>
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在加载地图数据...</div>
    </div>
    <div v-if="error" class="error-overlay">
      <div class="error-text">地图加载失败: {{ error }}</div>
      <button class="retry-btn" @click="retryLoad">重试</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import ImageLayer from 'ol/layer/Image'
import VectorLayer from 'ol/layer/Vector'
import XYZ from 'ol/source/XYZ'
import ImageStatic from 'ol/source/ImageStatic'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { defaults as defaultControls } from 'ol/control'
import { defaults as defaultInteractions } from 'ol/interaction'
import { fromLonLat, toLonLat } from 'ol/proj'
import proj4 from 'proj4'
import { register } from 'ol/proj/proj4'
import Style from 'ol/style/Style'
import Stroke from 'ol/style/Stroke'
import Fill from 'ol/style/Fill'

import * as GeoTIFF from 'geotiff'
import * as plotty from 'plotty'

// 注册 proj4 到 OpenLayers
register(proj4)

// 注册常用的 UTM 投影定义（WGS 84）
// UTM 北半球区域 1-60
for (let zone = 1; zone <= 60; zone++) {
  const epsgCode = 32600 + zone  // EPSG:32601 - EPSG:32660
  proj4.defs(`EPSG:${epsgCode}`, `+proj=utm +zone=${zone} +datum=WGS84 +units=m +no_defs`)
}
// UTM 南半球区域 1-60
for (let zone = 1; zone <= 60; zone++) {
  const epsgCode = 32700 + zone  // EPSG:32701 - EPSG:32760
  proj4.defs(`EPSG:${epsgCode}`, `+proj=utm +zone=${zone} +datum=WGS84 +units=m +no_defs +south`)
}

// 注册 Web Mercator（以防万一）
proj4.defs('EPSG:3857', '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs')

console.log('已注册 UTM 投影定义 (EPSG:32601-32660, EPSG:32701-32760)')

import 'ol/ol.css'

const props = defineProps({
  layerUrls: {
    type: Array,
    default: () => []
  },
  taskType: {
    type: Number,
    default: null
  },
  dataType: {
    type: String,
    default: null
  }
})


const mapRef = ref(null)
const plottyCanvas = ref(null)
const loading = ref(false)
const error = ref('')
// 存储所有图层，key为URL，value为OpenLayers图层对象
// 使用普通对象而非 Map，避免 Vue 响应式系统的问题
const layersMap = {}
let map = null

// 省级行政区划图层相关
const hasReceivedTif = ref(false)  // 标记是否已收到TIF
let provinceLayer = null           // 省级行政区划图层引用

// 事件处理函数
function handleZoomIn() {
  if (map) {
    const view = map.getView()
    view.setZoom(view.getZoom() + 1)
  }
}

function handleZoomOut() {
  if (map) {
    const view = map.getView()
    view.setZoom(view.getZoom() - 1)
  }
}

onMounted(() => {
  console.log('MapView onMounted 执行')

  map = new Map({
    target: mapRef.value,

    interactions: defaultInteractions(),

    controls: defaultControls({
      zoom: false,  // 禁用默认缩放控件，使用自定义控件
      rotate: false
    }),

    layers: [
      new TileLayer({
        source: new XYZ({
          url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
        })
      })
    ],

    view: new View({
      center: fromLonLat([105.0, 35.0]), // 中国中心点，适合显示全国
      zoom: 4
    })
  })

  // 监听来自 App.vue 的地图控制事件
  window.addEventListener('map-zoom-in', handleZoomIn)
  window.addEventListener('map-zoom-out', handleZoomOut)

  // 加载行政区划图层
  loadProvinceLayer()
})

onUnmounted(() => {
  // 清理事件监听
  window.removeEventListener('map-zoom-in', handleZoomIn)
  window.removeEventListener('map-zoom-out', handleZoomOut)

  // 清理所有图层
  removeAllLayers()

  // 清理行政区划图层
  if (provinceLayer && map) {
    map.removeLayer(provinceLayer)
    provinceLayer = null
  }

  if (map) {
    map.setTarget(null)
    map = null
  }
})

/**
 * 将NoData像素和指定值设置为透明
 * @param {HTMLCanvasElement} canvas - canvas元素
 * @param {TypedArray} pixelData - 像素数据
 * @param {number} noDataValue - NoData值
 * @param {number} width - 图像宽度
 * @param {number} height - 图像高度
 * @param {Array} transparentValues - 需要设为透明的额外值数组
 */
function makeNoDataTransparent(canvas, pixelData, noDataValue, width, height, transparentValues = []) {
  const ctx = canvas.getContext('2d')
  const imageData = ctx.getImageData(0, 0, width, height)
  const data = imageData.data

  let transparentCount = 0

  for (let i = 0; i < pixelData.length; i++) {
    const pixelValue = pixelData[i]
    // 检查是否为 NoData 或需要透明的特定值
    const isNoData = pixelValue === null || pixelValue === undefined || isNaN(pixelValue) ||
        pixelValue === noDataValue
    const isTransparentValue = transparentValues.includes(pixelValue)

    if (isNoData || isTransparentValue) {
      // 将对应像素的alpha通道设为0（透明）
      const idx = i * 4
      data[idx + 3] = 0
      transparentCount++
    }
  }

  ctx.putImageData(imageData, 0, 0)
  console.log(`已将 ${transparentCount} 个像素设为透明`)
}

/**
 * 移除指定的GeoTIFF图层
 * @param {string} url - 图层URL
 */
function removeLayer(url) {
  if (url in layersMap) {
    const layer = layersMap[url]
    if (map) {
      map.removeLayer(layer)
    }
    delete layersMap[url]
    console.log('移除图层:', url)
  }
}

/**
 * 加载省级行政区划图层
 */
function loadProvinceLayer() {
  if (!map) {
    console.warn('地图未初始化，无法加载行政区划图层')
    return
  }

  console.log('开始加载省级行政区划图层...')

  // 使用 fetch 手动加载 GeoJSON，以便更好地处理错误
  fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      console.log('GeoJSON 数据获取成功')
      return response.json()
    })
    .then(geojsonData => {
      console.log('GeoJSON 数据解析完成，开始创建图层...')

      const source = new VectorSource({
        features: new GeoJSON().readFeatures(geojsonData, {
          featureProjection: 'EPSG:3857'  // 将数据从 WGS84 投影到 Web Mercator
        })
      })

      console.log(`已读取 ${source.getFeatures().length} 个行政区划要素`)

      provinceLayer = new VectorLayer({
        source: source,
        style: new Style({
          stroke: new Stroke({
            color: '#666666',  // 灰色边界
            width: 1.5
          }),
          fill: new Fill({
            color: 'rgba(200, 200, 200, 0.1)'  // 淡灰色填充
          })
        }),
        zIndex: 1  // 在OSM之上，TIF之下
      })

      map.addLayer(provinceLayer)
      console.log('省级行政区划图层已添加到地图')

      // 调整视图以适应行政区划数据
      const extent = source.getExtent()
      console.log('行政区划范围:', extent)
      if (extent && extent[0] !== Infinity) {
        map.getView().fit(extent, { padding: [50, 50, 50, 50] })
        console.log('视图已调整以适应行政区划')
      }
    })
    .catch(error => {
      console.error('加载行政区划图层失败:', error)
    })
}

/**
 * 移除所有GeoTIFF图层
 */
function removeAllLayers() {
  Object.values(layersMap).forEach((layer) => {
    if (map) {
      map.removeLayer(layer)
    }
  })
  Object.keys(layersMap).forEach(key => delete layersMap[key])
  console.log('移除所有图层')
}

/**
 * 自定义颜色映射方案
 */
const colorSchemes = {
  // 土地覆盖分类 - task_type=1，9类 (1-9)，0为NoData/占位
  landCover: [
    '#000000',   // 0 - 占位/NoData（透明）
    '#FBE59C',   // 1 - 耕地 - 淡黄
    '#436F32',   // 2 - 森林 - 深绿
    '#33A02B',   // 3 - 灌木 - 亮绿
    '#ABD37B',   // 4 - 草地 - 淡绿
    '#1D69B4',   // 5 - 水体 - 深蓝
    '#A5CEE2',   // 6 - 雪/冰 - 灰白
    '#CEBDA3',   // 7 - 裸地 - 暖沙
    '#E24272',   // 8 - 不透水面 - 紫红
    '#279BE8'    // 9 - 湿地 - 浅蓝
  ],
  // 模拟土地利用分类 - task_type=2，5类 (0-4)
  simLandUse: [
    '#000000',  // 0 - 无 - 黑色（将设为透明）
    '#D3A463',  // 1 - 商业城市用地 - 橙黄
    '#FFFFBF',  // 2 - 住宅用地 - 淡黄
    '#91BCA8',  // 3 - 工业城市用地 - 淡绿
    '#218292'   // 4 - 其他城市土地 - 深绿
  ],
  // 连续数据 - 绿到红渐变 (人口/GDP)，从深绿 #0D6300 到深红 #FF2200
  greenRed: [
    '#0D6300',  // 深绿 (低值)
    '#2E7D32',
    '#4CAF50',
    '#81C784',
    '#AED581',
    '#FFD54F',  // 过渡黄
    '#FF9800',
    '#F57C00',
    '#E64A19',
    '#FF2200'   // 深红 (高值)
  ]
}

/**
 * 根据任务类型和数据类型获取颜色映射方案
 * @param {number} taskType - 任务类型 (1=数据展示, 2=模拟预测)
 * @param {string} dataType - 数据类型 ('landcover'|'population'|'gdp'|'sim_landuse'|'sim_population'|'sim_gdp')
 * @returns {Object} - 返回颜色方案配置 { colorScale, domain, transparentValues }
 */
function getColorSchemeConfig(taskType, dataType) {
  // 数据展示任务 (task_type = 1)
  if (taskType === 1) {
    if (dataType === 'landcover') {
      // 土地覆盖数据：9类分类 (1-9)，0为NoData
      return {
        colorScale: colorSchemes.landCover,
        domain: [0, 9],
        transparentValues: [0]
      }
    } else if (dataType === 'population' || dataType === 'gdp') {
      // 人口/GDP：连续数据，绿-红渐变
      return {
        colorScale: colorSchemes.greenRed,
        domain: null, // 使用数据实际范围
        transparentValues: []
      }
    }
  }

  // 模拟预测任务 (task_type = 2)
  if (taskType === 2) {
    if (dataType === 'landcover' || dataType === 'sim_landuse') {
      // 模拟土地利用：5类分类 (0-4)，0值为透明
      return {
        colorScale: colorSchemes.simLandUse,
        domain: [0, 4],
        transparentValues: [0]
      }
    } else if (dataType === 'population' || dataType === 'sim_population' || dataType === 'gdp' || dataType === 'sim_gdp') {
      // 模拟人口/GDP：连续数据，绿-红渐变，0值为透明
      return {
        colorScale: colorSchemes.greenRed,
        domain: null,
        transparentValues: [0]
      }
    }
  }

  // 默认配置
  return {
    colorScale: 'viridis',
    domain: null,
    transparentValues: []
  }
}

/**
 * 加载GeoTIFF图层（使用plotty渲染）
 */
/**
 * 从URL或文件名识别数据类型和任务类型
 * @param {string} url - TIF文件URL或名称
 * @returns {Object} - { dataType, taskType }
 */
function detectDataInfoFromUrl(url) {
  const lowerUrl = url.toLowerCase()
  let dataType = props.dataType
  let taskType = props.taskType

  // 检测数据类型
  if (lowerUrl.includes('人口') || lowerUrl.includes('pop')) {
    dataType = 'population'
  } else if (lowerUrl.includes('gdp')) {
    dataType = 'gdp'
  } else if (lowerUrl.includes('土地') || lowerUrl.includes('land') || lowerUrl.includes('覆盖')) {
    dataType = 'landcover'
  }

  // 检测任务类型：模拟/预测数据通常是 task_type=2
  // 判断依据：文件名包含年份且 >= 2025，或包含 sim/模拟/quick/预测等关键词
  const yearMatch = url.match(/(20\d{2})/)
  const year = yearMatch ? parseInt(yearMatch[1]) : null

  if (lowerUrl.includes('sim') ||
      lowerUrl.includes('模拟') ||
      lowerUrl.includes('预测') ||
      lowerUrl.includes('quick') ||
      lowerUrl.includes('future') ||
      (year && year >= 2025)) {
    taskType = 2  // 模拟预测任务
    // 模拟数据的 dataType 需要加前缀
    if (dataType === 'landcover') {
      dataType = 'sim_landuse'
    } else if (dataType === 'population') {
      dataType = 'sim_population'
    } else if (dataType === 'gdp') {
      dataType = 'sim_gdp'
    }
  } else if (year && year < 2025) {
    taskType = 1  // 历史数据展示任务
  }

  return { dataType, taskType }
}

/**
 * 从URL或文件名识别数据类型（兼容旧代码）
 * @param {string} url - TIF文件URL或名称
 * @returns {string} - 数据类型标识
 */
function detectDataTypeFromUrl(url) {
  return detectDataInfoFromUrl(url).dataType
}

/**
 * 加载单个GeoTIFF图层并返回图层对象
 * @param {string} url - TIF文件URL
 * @returns {Promise<ImageLayer>} - OpenLayers图层对象
 */
async function loadGeoTiffLayer(url) {
  console.log('开始加载GeoTIFF:', url)

  // 根据URL识别该图层的数据类型和任务类型
  const { dataType: layerDataType, taskType: layerTaskType } = detectDataInfoFromUrl(url)
  console.log('图层数据类型:', layerDataType, '任务类型:', layerTaskType, 'URL:', url)

  // 使用geotiff.js读取TIF文件
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  const arrayBuffer = await response.arrayBuffer()
  console.log('文件下载完成，解析GeoTIFF...')

  // 解析GeoTIFF
  const tiff = await GeoTIFF.fromArrayBuffer(arrayBuffer)
  const image = await tiff.getImage()

  // ===== 提取坐标系信息 =====
  const geoKeys = image.getGeoKeys() || {}
  console.log('=== GeoTIFF 坐标系信息 ===')
  console.log('GeoKeys:', geoKeys)

  let epsgCode = null
  let crsType = null

  // 检查投影坐标系（如 Web Mercator、UTM 等）
  if (geoKeys.ProjectedCSTypeGeoKey && geoKeys.ProjectedCSTypeGeoKey !== 32767) {
    epsgCode = geoKeys.ProjectedCSTypeGeoKey
    crsType = 'projected'
    console.log(`坐标系类型: 投影坐标系 (Projected)`)
    console.log(`EPSG代码: ${epsgCode}`)
  }
  // 检查地理坐标系（如 WGS84）
  else if (geoKeys.GeographicTypeGeoKey && geoKeys.GeographicTypeGeoKey !== 32767) {
    epsgCode = geoKeys.GeographicTypeGeoKey
    crsType = 'geographic'
    console.log(`坐标系类型: 地理坐标系 (Geographic)`)
    console.log(`EPSG代码: ${epsgCode}`)
  }
  // 检查模型类型
  else if (geoKeys.GTModelTypeGeoKey) {
    const modelType = geoKeys.GTModelTypeGeoKey === 1 ? 'Projected' :
                      geoKeys.GTModelTypeGeoKey === 2 ? 'Geographic' : 'Unknown'
    console.log(`坐标系类型: ${modelType} (ModelType: ${geoKeys.GTModelTypeGeoKey})`)
    console.log('警告: 未找到具体EPSG代码')
  } else {
    console.log('警告: 未找到坐标系信息，假设为EPSG:4326')
  }

  // 输出额外信息
  if (geoKeys.GTRasterTypeGeoKey) {
    console.log(`栅格类型: ${geoKeys.GTRasterTypeGeoKey === 1 ? 'PixelIsArea' : 'PixelIsPoint'}`)
  }
  if (geoKeys.ProjLinearUnitsGeoKey) {
    console.log(`线性单位: ${geoKeys.ProjLinearUnitsGeoKey}`)
  }
  if (geoKeys.GeogAngularUnitsGeoKey) {
    console.log(`角度单位: ${geoKeys.GeogAngularUnitsGeoKey}`)
  }
  console.log('========================')

  // 获取图像信息
  const width = image.getWidth()
  const height = image.getHeight()
  const samplesPerPixel = image.getSamplesPerPixel()

  console.log(`图像尺寸: ${width} x ${height}, 波段数: ${samplesPerPixel}`)

  // 读取像素数据
  const rasterData = await image.readRasters()
  const pixelData = rasterData[0] // 使用第一个波段

  // 获取 NoData 值
  let noDataValue = null
  const fileDirectory = image.getFileDirectory ? image.getFileDirectory() : null
  if (fileDirectory && fileDirectory.GDAL_NODATA) {
    // GDAL_NODATA 是一个字符串数组
    noDataValue = parseFloat(fileDirectory.GDAL_NODATA[0])
    console.log(`检测到 NoData 值: ${noDataValue}`)
  }

  // 计算像素值范围（排除NoData值）
  let min = Infinity
  let max = -Infinity
  let hasNoData = false
  let validPixelCount = 0

  for (let i = 0; i < pixelData.length; i++) {
    const v = pixelData[i]
    // 检查是否为 NoData 或无效值
    if (v === null || v === undefined || isNaN(v) ||
        (noDataValue !== null && v === noDataValue)) {
      hasNoData = true
      continue
    }
    validPixelCount++
    if (v < min) min = v
    if (v > max) max = v
  }

  console.log(`像素值范围: ${min} ~ ${max} (有效像素: ${validPixelCount}/${pixelData.length})`)
  if (hasNoData) {
    console.log(`数据包含 NoData 值: ${noDataValue}`)
  }

  // 获取颜色方案配置（使用图层自己的任务类型和数据类型）
  const colorConfig = getColorSchemeConfig(layerTaskType, layerDataType)
  console.log('使用颜色方案:', colorConfig.colorScale, 'taskType:', layerTaskType, 'dataType:', layerDataType, 'URL:', url)

  // 获取canvas并设置尺寸
  const canvas = plottyCanvas.value
  canvas.width = width
  canvas.height = height

  // 使用plotty渲染
  // 根据配置或数据范围确定 domain
  let domain
  if (colorConfig.domain) {
    // 使用预定义的 domain（分类数据）
    domain = colorConfig.domain
  } else {
    // 使用数据实际范围（连续数据）
    domain = min === max ? [min - 1, max + 1] : [min, max]
  }

  // 确定颜色方案
  let colorScaleName
  if (Array.isArray(colorConfig.colorScale)) {
    // 如果是颜色数组，动态注册颜色方案（使用图层自己的任务类型和数据类型）
    colorScaleName = `custom_${layerTaskType}_${layerDataType}`
    const colors = colorConfig.colorScale
    // 生成均匀分布的位置数组 [0, 0.1, 0.2, ..., 1] 或根据颜色数量调整
    const positions = colors.map((_, i) => i / (colors.length - 1))
    try {
      plotty.addColorScale(colorScaleName, colors, positions)
      console.log('注册自定义颜色方案:', colorScaleName, colors.length, '色')
    } catch (e) {
      // 如果已存在，继续使用
      console.log('颜色方案已存在:', colorScaleName)
    }
  } else {
    // 使用内置颜色方案名称
    colorScaleName = colorConfig.colorScale
    console.log('使用内置颜色方案:', colorScaleName)
  }

  const plot = new plotty.plot({
    canvas: canvas,
    data: pixelData,
    width: width,
    height: height,
    domain: domain,
    colorScale: colorScaleName,
    clampLow: true,
    clampHigh: true,
    useWebGL: false
  })

  plot.render()
  console.log('plotty渲染完成')

  // 处理 NoData 透明化，同时处理需要透明的特定值
  const transparentValues = [...colorConfig.transparentValues]
  if (hasNoData && noDataValue !== null) {
    // NoData 已经通过 pixelData 检查处理，这里只需要传递 transparentValues
  }
  if (transparentValues.length > 0 || hasNoData) {
    makeNoDataTransparent(canvas, pixelData, noDataValue, width, height, transparentValues)
  }

  // 将canvas转换为dataURL
  const dataURL = canvas.toDataURL('image/png')

  // 获取地理范围
  // 尝试从TIF中获取地理参考信息
  let extent = null
  const tiePoints = image.getTiePoints ? image.getTiePoints() : null
  const geoTransform = image.getGeoTransform ? image.getGeoTransform() : null

  if (geoTransform && geoTransform.length >= 6) {
    // 使用地理变换计算范围
    const [originX, pixelWidth, skewX, originY, skewY, pixelHeight] = geoTransform
    const minX = originX
    const maxX = originX + width * pixelWidth
    const minY = originY + height * pixelHeight
    const maxY = originY
    extent = [minX, minY, maxX, maxY]
    console.log('从GeoTransform获取范围:', extent)
  } else if (tiePoints && tiePoints.length > 0) {
    // 使用tie points计算范围
    // tiePoints格式: [{i, j, x, y}, ...] 其中 (i,j) 是像素坐标，(x,y) 是地理坐标
    console.log('使用tie points:', tiePoints)

    // 通常有两个tie point：左上角和右下角，或者一个tie point + 分辨率
    if (tiePoints.length >= 2) {
      // 如果有两个tie points，直接使用它们的坐标
      const tp0 = tiePoints[0]
      const tp1 = tiePoints[1]
      extent = [Math.min(tp0.x, tp1.x), Math.min(tp0.y, tp1.y), Math.max(tp0.x, tp1.x), Math.max(tp0.y, tp1.y)]
    } else if (tiePoints.length === 1) {
      // 如果只有一个tie point，需要结合分辨率计算
      // 尝试从fileDirectory获取分辨率
      const tp = tiePoints[0]
      const resolution = fileDirectory && (fileDirectory.ModelPixelScale || fileDirectory.GDAL_NODATA) ? fileDirectory.ModelPixelScale : null

      if (resolution && resolution.length >= 2) {
        const [resX, resY] = resolution
        const minX = tp.x
        const maxY = tp.y
        const maxX = minX + width * resX
        const minY = maxY - height * resY
        extent = [minX, minY, maxX, maxY]
      } else {
        // 无法计算完整范围，使用单个点作为左上角
        console.warn('只有一个tie point且没有分辨率信息，无法计算完整范围')
        extent = [tp.x, tp.y - height, tp.x + width, tp.y]
      }
    }
    console.log('从tie points计算范围:', extent)
  }

  // 如果没有获取到有效范围，使用默认范围（北京附近）
  if (!extent) {
    // 默认范围：北京附近约1度范围
    extent = [116.0, 39.5, 116.8, 40.3] // [minX, minY, maxX, maxY] in EPSG:4326
    console.log('使用默认范围:', extent)
  }

  // 转换范围到EPSG:3857
  let extent3857

  // 判断 extent 的坐标系
  // 如果 extent 是从 GeoTransform 或 tie points 获取的，它使用 TIF 的坐标系
  // 如果 extent 是默认范围，它是 EPSG:4326 经纬度
  const isDefaultExtent = !geoTransform && (!tiePoints || tiePoints.length === 0)

  // 智能检测：检查 extent 值是否在经纬度范围内
  // 如果超出 -180~180, -90~90，说明是投影坐标（米），不是经纬度
  const isProjectedCoordinates = extent[0] < -180 || extent[0] > 180 ||
                                   extent[1] < -90 || extent[1] > 90 ||
                                   extent[2] < -180 || extent[2] > 180 ||
                                   extent[3] < -90 || extent[3] > 90

  if (isProjectedCoordinates && epsgCode === 4326) {
    console.warn('警告: TIF声明坐标系为EPSG:4326，但坐标值超出经纬度范围，可能是投影坐标')
    console.warn('坐标范围:', extent)
    console.warn('尝试按投影坐标处理...')
  }

  if (isDefaultExtent || (epsgCode === 4326 && !isProjectedCoordinates)) {
    // 使用默认范围或 TIF 是 EPSG:4326 且坐标在合理范围内，直接使用 fromLonLat 转换
    extent3857 = [
      ...fromLonLat([extent[0], extent[1]]),
      ...fromLonLat([extent[2], extent[3]])
    ]
  } else if (epsgCode && (epsgCode !== 4326 || isProjectedCoordinates)) {
    // TIF使用非EPSG:4326坐标系（如UTM），或声明为4326但实际是投影坐标
    let sourceCode = `EPSG:${epsgCode}`

    // 特殊情况：声明为EPSG:4326但实际是投影坐标，尝试从GeoKeys获取UTM Zone
    if (epsgCode === 4326 && isProjectedCoordinates) {
      let utmZone = null
      let isNorth = true

      // 方案B: 从GTCitationGeoKey解析Zone信息
      // 例如: "WGS 84 / UTM zone 49N" -> Zone 49, 北半球
      const citation = geoKeys.GTCitationGeoKey || geoKeys.GeogCitationGeoKey || ''
      const zoneMatch = citation.match(/zone\s*(\d+)([NS])/i)
      if (zoneMatch) {
        utmZone = parseInt(zoneMatch[1])
        isNorth = zoneMatch[2].toUpperCase() === 'N'
        console.log(`从GTCitationGeoKey解析到UTM Zone: ${utmZone}${isNorth ? 'N' : 'S'}`)
      }

      // 如果无法从citation解析，检查是否有ProjectedCSTypeGeoKey
      if (!utmZone && geoKeys.ProjectedCSTypeGeoKey && geoKeys.ProjectedCSTypeGeoKey !== 32767) {
        const pcsCode = geoKeys.ProjectedCSTypeGeoKey
        // 检查是否是UTM投影 (EPSG:32601-32660 或 32701-32760)
        if (pcsCode >= 32601 && pcsCode <= 32660) {
          utmZone = pcsCode - 32600
          isNorth = true
          console.log(`从ProjectedCSTypeGeoKey解析到UTM Zone: ${utmZone}N (EPSG:${pcsCode})`)
        } else if (pcsCode >= 32701 && pcsCode <= 32760) {
          utmZone = pcsCode - 32700
          isNorth = false
          console.log(`从ProjectedCSTypeGeoKey解析到UTM Zone: ${utmZone}S (EPSG:${pcsCode})`)
        }
      }

      // 如果仍然无法解析，尝试用Zone 49转换，然后检查结果是否合理
      if (!utmZone) {
        // 武汉位于114°E，通常在Zone 49 (108-114°E) 或 Zone 50 (114-120°E)
        // 但多数武汉数据使用Zone 49，优先尝试
        utmZone = 49
        isNorth = true
        console.warn(`无法从GeoKeys解析UTM Zone，默认使用Zone 49N (武汉常用)`)
        console.warn(`如果数据显示位置不正确，可能需要手动指定Zone`)
      }

      // 构建EPSG代码: 北半球 32601-32660, 南半球 32701-32760
      const epsgBase = isNorth ? 32600 : 32700
      const targetEpsg = epsgBase + utmZone
      sourceCode = `EPSG:${targetEpsg}`
      console.warn(`使用备用UTM投影 ${sourceCode} (Zone ${utmZone}${isNorth ? 'N' : 'S'}) 进行转换`)
    }

    console.log(`坐标转换: 从 ${sourceCode} 到 EPSG:3857`)

    try {
      // 检查投影是否已注册
      if (!proj4.defs(sourceCode)) {
        console.warn(`投影 ${sourceCode} 未注册，尝试使用 +init=epsg:${sourceCode.replace('EPSG:', '')}`)
        proj4.defs(sourceCode, `+init=epsg:${sourceCode.replace('EPSG:', '')}`)
      }

      // 使用 proj4 进行坐标转换
      const sw = proj4(sourceCode, 'EPSG:3857', [extent[0], extent[1]])
      const ne = proj4(sourceCode, 'EPSG:3857', [extent[2], extent[3]])
      extent3857 = [sw[0], sw[1], ne[0], ne[1]]

      console.log(`坐标转换完成: [${extent.join(', ')}] -> [${extent3857.join(', ')}]`)
    } catch (e) {
      console.error(`坐标转换失败 ${sourceCode}:`, e)
      console.warn('回退到假设数据为EPSG:4326')
      extent3857 = [
        ...fromLonLat([extent[0], extent[1]]),
        ...fromLonLat([extent[2], extent[3]])
      ]
    }
  } else {
    // 没有 EPSG 代码，假设是 EPSG:4326
    extent3857 = [
      ...fromLonLat([extent[0], extent[1]]),
      ...fromLonLat([extent[2], extent[3]])
    ]
  }

  // 创建OpenLayers图像图层
  const source = new ImageStatic({
    url: dataURL,
    imageExtent: extent3857,
    projection: 'EPSG:3857'
  })

  const layer = new ImageLayer({
    source: source,
    opacity: 0.8
  })

  console.log('GeoTIFF图层创建成功:', url)
  return layer
}

/**
 * 更新地图图层，根据layerUrls数组增删图层
 * @param {Array} newUrls - 新的图层URL数组
 */
async function updateLayers(newUrls) {
  if (!map) {
    console.log('地图尚未初始化，延迟更新图层')
    setTimeout(() => updateLayers(newUrls), 100)
    return
  }

  // 检测是否首次收到TIF，控制行政区划图层显示/隐藏
  if (newUrls.length > 0 && !hasReceivedTif.value) {
    hasReceivedTif.value = true
    // 隐藏行政区划图层
    if (provinceLayer) {
      provinceLayer.setVisible(false)
      console.log('收到TIF数据，隐藏行政区划图层')
    }
  }

  loading.value = true
  error.value = ''

  try {
    console.log('更新图层列表:', newUrls)

    // 1. 移除不在新列表中的图层
    const urlsToRemove = []
    Object.keys(layersMap).forEach(url => {
      if (!newUrls.includes(url)) {
        urlsToRemove.push(url)
      }
    })
    urlsToRemove.forEach(url => removeLayer(url))

    // 2. 加载并添加新图层（按顺序，先加载的显示在下层）
    for (let i = 0; i < newUrls.length; i++) {
      const url = newUrls[i]

      // 如果图层已存在，不需要重新加载
      if (url in layersMap) {
        // 调整图层顺序：数据框中靠前的（数组前面）显示在地图上层
        const layer = layersMap[url]
        layer.setZIndex(newUrls.length - i) // z-index越大越在上层
        continue
      }

      // 加载新图层
      try {
        const layer = await loadGeoTiffLayer(url)
        // 设置z-index，数据框中靠前的显示在上层
        layer.setZIndex(newUrls.length - i)
        map.addLayer(layer)
        layersMap[url] = layer
      } catch (err) {
        console.error('加载图层失败:', url, err)
      }
    }

    // 3. 调整视图以适应所有图层
    if (newUrls.length > 0) {
      const lastUrl = newUrls[newUrls.length - 1]
      const lastLayer = layersMap[lastUrl]
      if (lastLayer) {
        const source = lastLayer.getSource()
        const extent = source.getImageExtent()
        map.getView().fit(extent, { padding: [50, 50, 50, 50], maxZoom: 15 })
      }
    }

    console.log('图层更新完成，当前图层数:', Object.keys(layersMap).length)

  } catch (err) {
    console.error('更新图层失败:', err)
    error.value = err.message || '未知错误'
  } finally {
    loading.value = false
  }
}

/**
 * 重试加载
 */
function retryLoad() {
  if (props.layerUrls.length > 0) {
    updateLayers(props.layerUrls)
  }
}

/**
 * 监听 layerUrls 数组变化
 */
watch(
  () => props.layerUrls,
  (newUrls) => {
    // 更新图层列表
    updateLayers(newUrls)
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.map {
  width: 100%;
  height: 100%;
  border: 1px solid #d9d9d9;
  box-shadow: inset 0 0 8px rgba(0,0,0,0.05);
}

.loading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #2c6e9e;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 16px;
  color: #333;
}

.error-text {
  font-size: 16px;
  color: #f56c6c;
  margin-bottom: 16px;
  text-align: center;
  padding: 0 20px;
}

.retry-btn {
  padding: 8px 16px;
  background: #2c6e9e;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background: #255a82;
}
</style>