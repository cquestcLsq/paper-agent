<template>
  <div class="py-3 border-b border-gray-200 last:border-0">
    <!-- 标题行 -->
    <div class="flex items-start gap-3">
      <!-- 确认模式下显示勾选框，否则显示编号 -->
      <input 
        v-if="isConfirming"
        type="checkbox"
        :checked="checked"
        @change="$emit('toggle')"
        class="mt-1 shrink-0 w-4 h-4 text-cyan-500 border-gray-300 rounded focus:ring-cyan-400"
      />
      <span 
        v-else
        class="text-xs font-mono font-semibold text-gray-700 bg-gray-100 px-2 py-1 rounded mt-0.5 shrink-0"
      >
        [{{ index + 1 }}]
      </span>
      
      <div class="flex-1 min-w-0">
        <a :href="paper.url" target="_blank" class="text-sm text-slate-800 hover:text-cyan-600 transition-colors leading-relaxed">
          {{ paper.title }}
        </a>
        <div class="flex items-center gap-3 mt-1">
          <span class="text-xs text-slate-400">📅 {{ paper.year || '未知' }}</span>
          <span class="text-xs text-slate-400 inline-flex items-center gap-1">
            📊 <span>引用 {{ paper.citations || 0 }}</span>
          </span>
          <!-- 展开/收起摘要 -->
          <button 
            v-if="paper.abstract && paper.abstract.length > 10"
            @click="showAbstract = !showAbstract"
            class="text-xs text-cyan-500 hover:text-cyan-600"
          >
            {{ showAbstract ? '收起摘要' : '中文摘要' }}
          </button>
          <span v-else class="text-xs text-gray-400 italic">暂无摘要</span>
        </div>
      </div>
    </div>
    <!-- 摘要展开区 -->
    <div v-if="showAbstract && paper.abstract" class="mt-2 ml-8 text-xs text-slate-500 leading-relaxed bg-gray-50 p-3 rounded-lg">
      {{ paper.abstract }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  paper: Object,
  index: Number,
  checked: Boolean,
  isConfirming: Boolean
})
defineEmits(['toggle'])

const showAbstract = ref(false)
</script>