/* ==============================================================
 * 入口文件 —— 整个应用的"启动开关"
 *
 * 通俗理解：就像 Flask 的 app.py，它是所有代码的起点。
 * 在这件事注册 Vue 本身、路由、UI 组件库、全局样式。
 * ============================================================== */

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

// 注册 Element Plus 组件库
app.use(ElementPlus)

// 全局注册所有 Element Plus 图标
// 这样在模板里可以直接用 <el-icon><Search /></el-icon>
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册路由
app.use(router)

// 挂载到 #app（对应 index.html 里的 <div id="app">）
app.mount('#app')
