<template>
  <!-- 报告展示面板：白色卡片，圆角，阴影，纵向弹性布局 -->
  <div class="bg-white/90 backdrop-blur rounded-2xl border border-gray-200 p-5 shadow-sm h-full flex flex-col">

    <!-- ===== 顶部标题栏：标题 + 中英文切换 + 复制按钮 ===== -->
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-base font-semibold text-slate-700 uppercase tracking-wider">
        📋 调研报告
      </h2>
      <div class="flex items-center gap-2">
        <!-- 中英文切换按钮组 -->
        <div class="flex items-center gap-0.5 bg-gray-100 rounded-lg p-0.5">
          <button 
            @click="toggleLang"
            :class="[
              'text-xs px-3 py-1.5 rounded-md transition-all font-medium',
              lang === 'zh' 
                ? 'bg-white text-cyan-600 shadow-sm' 
                : 'text-slate-500 hover:text-slate-700'
            ]"
          >
            中文
          </button>
          <button 
            @click="toggleLang"
            :class="[
              'text-xs px-3 py-1.5 rounded-md transition-all font-medium',
              lang === 'en' 
                ? 'bg-white text-cyan-600 shadow-sm' 
                : 'text-slate-500 hover:text-slate-700'
            ]"
          >
            English
          </button>
        </div>
        <!-- 复制按钮：报告生成后才显示 -->
        <button 
          @click="copyReport"
          class="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-slate-600"
        >
          📋 复制
        </button>
      </div>
    </div>

    <!-- ===== 报告正文：自动滚动，保留换行 ===== -->
    <div class="flex-1 text-slate-800 text-base leading-relaxed whitespace-pre-wrap overflow-y-auto">
      {{ displayReport }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useResearchStore } from '../stores/research'

const store = useResearchStore()

// 当前语言：zh 中文，en 英文
const lang = ref('zh')

// 根据语言切换显示内容
const displayReport = computed(() => {
  return lang.value === 'zh' 
    ? store.report                          // 中文 → 直接显示
    : (store.reportEn || 'Translating...')  // 英文 → 显示英文版，未加载时提示
})

// 切换中英文
function toggleLang() {
  lang.value = lang.value === 'zh' ? 'en' : 'zh'
}

// 复制当前显示的报告到剪贴板
function copyReport() {
  navigator.clipboard.writeText(displayReport.value)
}
</script>