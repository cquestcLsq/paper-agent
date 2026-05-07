import { defineStore } from 'pinia'
import { ref } from 'vue'

// Pinia Store：管理整个调研流程的所有状态
export const useResearchStore = defineStore('research', () => {

  // ===== 状态 =====
  const isStreaming = ref(false)       // 是否正在流式传输中
  const currentStep = ref('')         // 当前步骤（searching/reading/analysing/writing）
  const logs = ref([])                // 日志消息列表
  const papers = ref([])              // 搜索到的论文列表
  const report = ref('')              // 中文报告
  const reportEn = ref('')            // 英文报告（Ollama 翻译）
  const isTranslating = ref(false)    // 是否正在接收英文翻译
  const confirmedPapers = ref([])     // 用户勾选的论文标题列表
  const isConfirming = ref(false)     // 是否正在等待人工确认

  // -------- 添加一条日志 --------
  function addLog(msg) {
    logs.value.push({ time: new Date(), content: msg })
  }

  // -------- 添加一篇论文（存在则更新，不存在则追加）--------
  function addPaper(paper) {
  const key = `${paper.title}_${paper.year}`
  const existing = papers.value.find(p => `${p.title}_${p.year}` === key)

  if (existing) {
    if (paper.citations) existing.citations = paper.citations
    if (paper.url) existing.url = paper.url
    if (paper.abstract) existing.abstract = paper.abstract
  } else {
    papers.value.push(paper)
  }
}

  // -------- 切换勾选论文 --------
  function togglePaper(title) {
    const idx = confirmedPapers.value.indexOf(title)
    if (idx === -1) {
      confirmedPapers.value.push(title)
    } else {
      confirmedPapers.value.splice(idx, 1)
    }
  }

  // -------- 确认选择，触发后续流程 --------
  async function confirmSelection() {
    if (confirmedPapers.value.length === 0) return
    
    const response = await fetch('/api/confirm_papers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ titles: confirmedPapers.value })
    })
    const result = await response.json()
    
    if (result.status === 'ok') {
      // 只保留被勾选的论文
      papers.value = papers.value.filter(p => confirmedPapers.value.includes(p.title))
      confirmedPapers.value = []
      isConfirming.value = false
      // 重新建立 SSE 连接，接收后续流程
      startResearchContinuation()
    }
  }

  // -------- 追加报告文字（根据 isTranslating 切换中英文）--------
  function appendReport(text) {
    if (!isTranslating.value) {
      report.value += text
    } else {
      reportEn.value += text
    }
  }

  // -------- 重置所有状态 --------
  function reset() {
    logs.value = []
    papers.value = []
    report.value = ''
    reportEn.value = ''
    isTranslating.value = false
    confirmedPapers.value = []
    isConfirming.value = false
    currentStep.value = ''
  }

  // ===== 核心：发起 SSE 请求，监听后端推送 =====
  async function startResearch(query) {
    if (isStreaming.value) return
    isStreaming.value = true
    reset()
    addLog('🚀 正在连接服务器...')

    try {
      const response = await fetch(`/api/research?query=${encodeURIComponent(query)}`)
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const msg = JSON.parse(line.slice(6))
              handleMessage(msg)
            } catch (e) { /* 忽略解析错误 */ }
          }
        }
      }

    } catch (e) {
      addLog('❌ 连接失败: ' + e.message)
    } finally {
      isStreaming.value = false
      currentStep.value = ''
    }
  }

  // -------- 确认后继续接收 SSE --------
  async function startResearchContinuation() {
    isStreaming.value = true
    addLog('✅ 论文已确认，开始下载和分析...')

    try {
      const response = await fetch('/api/research/continue')
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const msg = JSON.parse(line.slice(6))
              handleMessage(msg)
            } catch (e) { /* 忽略解析错误 */ }
          }
        }
      }

    } catch (e) {
      addLog('❌ 连接失败: ' + e.message)
    } finally {
      isStreaming.value = false
      currentStep.value = ''
    }
  }

  // -------- 解析每条 SSE 消息 --------
 function handleMessage(msg) {
  const { step, state, data } = msg
  if (step) currentStep.value = step

  if (state === 'error') {
  isStreaming.value = false
  addLog(data)
  return
}

  // 搜索结果 → 进入确认模式
  if (step === 'searching' && state === 'result') {
    isConfirming.value = true
  }

  // 分隔线 → 切换翻译
  if (step === 'writing' && state === 'separator' && data === '---') {
    isTranslating.value = true
    addLog('[Writing Agent] 中文报告生成完毕，开始本地翻译...')
    return
  }

  // 流式报告
  if (step === 'writing' && state === 'streaming') {
    appendReport(data)
    return
  }

  // ===== 论文数据（JSON 字符串）=====
  if (state === 'result' && typeof data === 'string') {
     console.log('[DEBUG] 收到 result, data 前100字:', data.slice(0, 100))
    try {
      const payload = JSON.parse(data)
      if (payload.type === 'papers' && Array.isArray(payload.papers)) {
        payload.papers.forEach(p => {
          addPaper({
            title: p.title,
            year: p.year,
            citations: p.citations,
            url: p.url,
            abstract: p.abstract
          })
        })
        return
      }
    } catch (e) {}
  }

  // ===== 日志流 =====
  if (typeof data === 'string') {
    addLog(data)
  }
}
    // 获取历史记录列表
  async function fetchHistoryList() {
    const res = await fetch('/api/history')
    return await res.json()
  }

  // 加载某条历史记录
  async function loadHistory(historyId) {
    const res = await fetch(`/api/history/${historyId}`)
    const data = await res.json()
    papers.value = data.papers
    report.value = data.report_zh
    reportEn.value = data.report_en
    return data
  }
  return {
    isStreaming, currentStep, logs, papers, report, reportEn,
    confirmedPapers, isConfirming,
    startResearch, addLog, togglePaper, confirmSelection,
    fetchHistoryList,loadHistory
  }
})
