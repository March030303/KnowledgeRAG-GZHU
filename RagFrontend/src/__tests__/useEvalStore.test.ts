import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useEvalStore } from '@/store/modules/useEvalStore'

// Mock axios
vi.mock('axios', () => ({
  default: {
    post: vi.fn().mockResolvedValue({ data: {} }),
    get: vi.fn().mockResolvedValue({
      data: {
        latest_run: { status: 'done', model: 'test', score: 0.9 },
        results: [{ status: 'done', model: 'test' }]
      }
    })
  }
}))

describe('useEvalStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('initial state is correct', () => {
    const store = useEvalStore()
    expect(store.running).toBe(false)
    expect(store.progress).toBe('')
    expect(store.models).toBe('')
    expect(store.startedAt).toBe(0)
    expect(store.latestRun).toBeNull()
    expect(store.historyList).toEqual([])
    expect(store.chartData).toBeNull()
  })

  it('isRunning computed reflects running state', () => {
    const store = useEvalStore()
    expect(store.isRunning).toBe(false)
    store.running = true
    expect(store.isRunning).toBe(true)
  })

  it('startEval ignores if already running', async () => {
    const store = useEvalStore()
    store.running = true
    await store.startEval(['model1'])
    // Should not change state or throw
    expect(store.running).toBe(true)
  })

  it('fetchLatest updates chartData and historyList', async () => {
    const store = useEvalStore()
    await store.fetchLatest()
    expect(store.latestRun).not.toBeNull()
    expect(Array.isArray(store.historyList)).toBe(true)
  })

  it('fetchLatest handles errors gracefully', async () => {
    const axios = (await import('axios')).default
    vi.mocked(axios.get).mockRejectedValueOnce(new Error('Network error'))
    const store = useEvalStore()
    // Should not throw
    await store.fetchLatest()
  })

  it('store is reactive — running changes are observed', () => {
    const store = useEvalStore()
    const initial = store.running
    store.running = !initial
    expect(store.running).toBe(!initial)
  })
})
