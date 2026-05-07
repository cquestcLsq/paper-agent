import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'  // 首页组件

// 路由配置：目前只有一个首页路由
export default createRouter({
  history: createWebHistory(),  // 使用 HTML5 History 模式
  routes: [
    { path: '/', component: Home }  // 根路径渲染首页
  ]
})