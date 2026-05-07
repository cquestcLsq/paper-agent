<template>
  <div class="max-w-7xl mx-auto px-8 py-10">

    <!-- 顶部标题区 -->
    <header class="text-center mb-10 relative">
      <h1 class="text-5xl font-bold mb-3 bg-gradient-to-r from-cyan-500 to-blue-600 bg-clip-text text-transparent">
        📡 论文调研助手
      </h1>
      <p class="text-lg text-slate-500">输入研究方向，AI 自动搜索、阅读、分析、撰写调研报告</p>
      <button @click="openHistory" class="absolute top-0 right-0 text-base text-slate-400 hover:text-cyan-600 transition-colors">
        📋 历史记录
      </button>
    </header>

    <!-- 历史记录浮窗 -->
    <div v-if="showHistory" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div class="bg-white rounded-2xl p-6 max-w-2xl w-full max-h-[80vh] flex flex-col">
        <div class="flex justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-800">历史记录</h3>
          <button @click="showHistory = false" class="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        <!-- 报告详情 -->
        <div v-if="selectedHistory" class="flex-1 flex flex-col min-h-0">
          <button @click="selectedHistory = null" class="text-sm text-cyan-500 hover:text-cyan-600 mb-3 self-start shrink-0">← 返回列表</button>
          <div class="text-sm font-medium text-slate-700 mb-2 shrink-0">{{ selectedHistory.query }}</div>
          
          <!-- 论文列表 -->
          <div v-if="selectedHistory.papers && selectedHistory.papers.length > 0" class="mb-4 shrink-0">
            <div class="text-xs font-semibold text-slate-500 uppercase mb-2">📄 论文列表</div>
            <div v-for="(paper, i) in selectedHistory.papers" :key="i" class="text-xs text-slate-600 py-1 border-b border-gray-100 last:border-0">
              [{{ i + 1 }}] 
              <a v-if="paper.url" :href="paper.url" target="_blank" class="hover:text-cyan-600 transition-colors">
                {{ paper.title }}
              </a>
              <span v-else>{{ paper.title }}</span>
              <span v-if="paper.year" class="text-slate-400"> ({{ paper.year }})</span>
            </div>
          </div>
          
          <!-- 中英文标签切换 -->
          <div class="flex gap-2 mb-2 shrink-0">
            <button @click="historyLang = 'zh'" :class="historyLang === 'zh' ? 'bg-cyan-500 text-white' : 'bg-gray-100 text-slate-600'" class="text-xs px-2 py-1 rounded">中文</button>
            <button @click="historyLang = 'en'" :class="historyLang === 'en' ? 'bg-cyan-500 text-white' : 'bg-gray-100 text-slate-600'" class="text-xs px-2 py-1 rounded">English</button>
          </div>
          
          <!-- 报告内容（可滚动） -->
          <div class="flex-1 min-h-0 overflow-y-auto text-sm text-slate-600 leading-relaxed whitespace-pre-wrap bg-gray-50 rounded-lg p-4">
            {{ historyLang === 'zh' ? selectedHistory.report_zh : selectedHistory.report_en }}
          </div>
        </div>

        <!-- 记录列表（带删除按钮） -->
        <div v-else class="flex-1 overflow-y-auto">
          <div v-if="historyList.length === 0" class="text-gray-400 text-sm py-8 text-center">暂无历史记录</div>
          <div v-for="item in historyList" :key="item.id" 
              class="py-3 px-3 hover:bg-gray-50 rounded-lg cursor-pointer border-b border-gray-100 last:border-0 flex items-center gap-2">
            <div @click="viewHistoryItem(item.id)" class="flex-1 min-w-0">
              <div class="text-sm text-slate-700 truncate">{{ item.query }}</div>
              <div class="text-xs text-gray-400 mt-1">{{ item.created_at }}</div>
            </div>
            <button @click.stop="deleteHistoryItem(item.id)" class="text-xs text-red-400 hover:text-red-600 shrink-0 px-2 py-1">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索栏 -->
    <SearchBar @search="handleSearch" />

    <!-- 三栏布局 -->
    <div class="grid grid-cols-12 gap-8 mt-10">
      <aside class="col-span-3">
        <StatusTimeline />
      </aside>
      <main class="col-span-4">
        <div class="bg-white/90 backdrop-blur rounded-2xl border border-gray-200 p-5 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-base font-semibold text-slate-700 uppercase tracking-wider">📄 搜索到的论文</h2>
            <span v-if="store.isConfirming" class="text-xs text-cyan-600 font-medium">请勾选要分析的论文</span>
          </div>
          <div v-if="store.papers.length === 0" class="text-slate-400 text-sm py-10 text-center">暂无论文，开始调研后显示</div>
          <PaperCard 
            v-for="(paper, i) in store.papers" 
            :key="i" 
            :paper="paper" 
            :index="i"
            :checked="store.confirmedPapers.includes(paper.title)"
            :is-confirming="store.isConfirming"
            @toggle="store.togglePaper(paper.title)"
          />
          <div v-if="store.isConfirming && store.papers.length > 0" class="mt-4 pt-4 border-t border-gray-200">
            <button 
              @click="store.confirmSelection()"
              :disabled="store.confirmedPapers.length === 0"
              class="w-full py-2.5 bg-cyan-500 text-white rounded-lg font-medium hover:bg-cyan-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              确认选择（{{ store.confirmedPapers.length }} 篇）
            </button>
          </div>
        </div>
      </main>
      <section class="col-span-5">
        <ReportView />
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useResearchStore } from '../stores/research'
import SearchBar from '../components/SearchBar.vue'
import StatusTimeline from '../components/StatusTimeline.vue'
import PaperCard from '../components/PaperCard.vue'
import ReportView from '../components/ReportView.vue'

const store = useResearchStore()
const showHistory = ref(false)
const historyList = ref([])
const selectedHistory = ref(null)
const historyLang = ref('zh')

async function openHistory() {
  showHistory.value = true
  selectedHistory.value = null
  historyList.value = await store.fetchHistoryList()
}

async function viewHistoryItem(id) {
  const res = await fetch(`/api/history/${id}`)
  selectedHistory.value = await res.json()
}

async function deleteHistoryItem(id) {
  if (!confirm('确定删除这条历史记录吗？')) return
  await fetch(`/api/history/${id}`, { method: 'DELETE' })
  historyList.value = historyList.value.filter(item => item.id !== id)
}

function handleSearch(query) {
  store.startResearch(query)
}
</script>