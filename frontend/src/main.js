import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 将 geotiff 暴露给 window，供 OpenLayers GeoTIFFSource 使用
import * as GeoTIFF from 'geotiff'
window.GeoTIFF = GeoTIFF

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')
