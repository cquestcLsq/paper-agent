<template>
  <!-- 搜索栏：输入框 + 按钮 水平排列 -->
  <div class="flex gap-3">
    <!-- 输入框：占满剩余空间 -->
    <div class="flex-1 relative">
      <input 
        v-model="query"
        @keyup.enter="$emit('search', query)"
        placeholder="输入研究方向，如：帮我调研近3年关于大语言模型 Agent 的 5 篇论文"
        class="w-full px-5 py-4 bg-white border border-gray-300 rounded-xl 
               text-slate-800 placeholder-slate-400 focus:outline-none focus:border-cyan-400 
               focus:ring-2 focus:ring-cyan-400/30 transition-all text-base shadow-sm"
      />
    </div>
    <!-- 开始调研按钮：loading 时显示旋转动画 -->
    <button 
      @click="$emit('search', query)"
      :disabled="store.isStreaming"
      class="px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl 
             font-semibold text-white hover:from-cyan-400 hover:to-blue-400 
             disabled:opacity-50 disabled:cursor-not-allowed transition-all text-base
             shadow-lg shadow-cyan-500/25"
    >
      <span v-if="store.isStreaming" class="flex items-center gap-2">
        <!-- SVG 旋转动画 -->
        <svg class="animate-spin w-5 h-5" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        调研中
      </span>
      <span v-else>🔬 开始调研</span>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useResearchStore } from '../stores/research'

const store = useResearchStore()
// 输入框默认值
const query = ref('')
</script>