<template>
  <!-- 状态时间线面板 -->
  <div class="bg-white/90 backdrop-blur rounded-2xl border border-gray-200 p-5 shadow-sm">
    <h2 class="text-base font-semibold text-slate-700 uppercase tracking-wider mb-4">
      ⚡ 实时进度
    </h2>

    <!-- 四个步骤 -->
    <div class="space-y-1">
      <div 
        v-for="(step, i) in steps" 
        :key="step.key"
        class="flex items-center gap-3 py-2.5 px-3 rounded-lg transition-all"
        :class="getStepClass(step.key)"  <!-- 根据状态动态切换样式 -->
      >
        <!-- 图标 -->
        <span class="text-lg">{{ step.icon }}</span>
        <!-- 标签 + 描述 -->
        <div class="flex-1">
          <div class="text-sm font-medium text-slate-800">{{ step.label }}</div>
          <div v-if="currentStep === step.key" class="text-xs text-cyan-600">
            {{ step.description }}
          </div>
        </div>
        <!-- 已完成 ✓ / 进行中脉冲动画 / 等待中无标记 -->
        <span v-if="completedSteps.has(step.key)" class="text-green-600 text-sm">✓</span>
        <span v-else-if="currentStep === step.key" class="relative flex h-3 w-3">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"/>
          <span class="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"/>
        </span>
      </div>
    </div>

    <!-- 最新日志 -->
    <div class="mt-5 pt-4 border-t border-gray-200">
      <div class="text-xs font-medium text-slate-700 mb-2">最新日志</div>
      <div class="text-sm text-slate-600 leading-relaxed max-h-32 overflow-y-auto whitespace-pre-wrap">
        {{ store.logs[store.logs.length - 1]?.content || '等待中...' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useResearchStore } from '../stores/research'

const store = useResearchStore()
const currentStep = computed(() => store.currentStep)

// 四个步骤的定义
const steps = [
  { key: 'searching', icon: '🔍', label: '搜索论文', description: '分析意图，检索文献' },
  { key: 'reading',   icon: '📥', label: '下载全文', description: '提取摘要与结论' },
  { key: 'analysing', icon: '🧠', label: '智能分析', description: '提取框架、结果、局限' },
  { key: 'writing',   icon: '📝', label: '生成报告', description: '逐字输出调研报告' },
]

// 步骤顺序映射
const stepOrder = { searching: 0, reading: 1, analysing: 2, writing: 3 }
const currentStepIndex = computed(() => stepOrder[currentStep.value] ?? -1)

// 已完成步骤集合（序号 < 当前步骤序号）
const completedSteps = computed(() => {
  const set = new Set()
  for (const [key, idx] of Object.entries(stepOrder)) {
    if (idx < currentStepIndex.value) set.add(key)
  }
  return set
})

// 根据步骤状态返回不同 CSS 类
function getStepClass(stepKey) {
  if (currentStep.value === stepKey) return 'bg-cyan-50 border border-cyan-200'  // 当前：高亮
  if (completedSteps.value.has(stepKey)) return 'text-slate-500'                  // 已完成：灰色
  return 'text-slate-400'                                                          // 等待中：更浅灰
}
</script>