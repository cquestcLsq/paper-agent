import { createApp } from 'vue'       // Vue 3 核心
import { createPinia } from 'pinia'   // Pinia 状态管理
import App from './App.vue'           // 根组件
import router from './router'         // 路由
import './style.css'                  // 全局样式

const app = createApp(App)  // 创建 Vue 应用
app.use(createPinia())       // 挂载状态管理
app.use(router)              // 挂载路由
app.mount('#app')            // 挂载到 #app 元素