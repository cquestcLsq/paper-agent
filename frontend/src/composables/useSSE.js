import { ref } from 'vue'

export function useSSE() {
  const isStreaming = ref(false)
  const currentStep = ref('')

  async function start(query, callbacks = {}) {
    if (isStreaming.value) return
    isStreaming.value = true

    callbacks.onLog?.('正在连接服务器...')

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
              handleMessage(msg, callbacks)
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (e) {
      callbacks.onError?.(e.message)
    } finally {
      isStreaming.value = false
      currentStep.value = ''
    }
  }

  function handleMessage(msg, callbacks) {
    const { step, state, data } = msg

    if (step) currentStep.value = step

    if (step === 'writing' && state === 'streaming') {
      callbacks.onReport?.(data)
    } else if (data) {
      callbacks.onLog?.(data)
    }
  }

  return { start, isStreaming, currentStep }
}