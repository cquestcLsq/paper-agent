import { defineConfig } from 'vite'    // Vite 配置函数
import vue from '@vitejs/plugin-vue'   // Vue 单文件组件编译插件

export default defineConfig({
  plugins: [vue()],  // 启用 Vue 插件

  // -------- 开发服务器 --------
  server: {
    port: 3000,  // 前端开发服务器端口
    proxy: {
      '/api': {                         // 所有 /api 开头的请求
        target: 'http://127.0.0.1:8000', // 转发到后端 FastAPI
        changeOrigin: true               // 修改请求头 origin
      }
    }
  }
})