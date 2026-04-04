import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import axios from 'axios'
import { MessagePlugin } from 'tdesign-vue-next'
import { fetchCardData, useCardDataStore } from '@/store/modules/useCardData'

vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

vi.mock('tdesign-vue-next', () => ({
  MessagePlugin: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

const sampleCards = [
  {
    id: '1',
    title: '人工智能导论',
    avatar: 'avatar-1.png',
    description: '基础课程资料',
    createdTime: '2026-04-01',
    cover: 'cover-1.png'
  },
  {
    id: '2',
    title: '数据库系统',
    avatar: 'avatar-2.png',
    description: '期末复习重点',
    createdTime: '2026-04-02',
    cover: 'cover-2.png'
  }
]

describe('useCardDataStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.spyOn(console, 'log').mockImplementation(() => undefined)
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchCardData 在接口成功时返回卡片列表', async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({
      data: {
        code: 200,
        message: 'ok',
        data: sampleCards,
        total: sampleCards.length
      }
    })

    await expect(fetchCardData()).resolves.toEqual(sampleCards)
  })

  it('fetchCardData 在业务失败时返回空数组', async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({
      data: {
        code: 500,
        message: 'failed',
        data: sampleCards,
        total: sampleCards.length
      }
    })

    await expect(fetchCardData()).resolves.toEqual([])
  })

  it('fetchCardData 在请求异常时返回空数组', async () => {
    vi.mocked(axios.get).mockRejectedValueOnce(new Error('network error'))

    await expect(fetchCardData()).resolves.toEqual([])
  })

  it('fetchCards 成功后会写入列表、总数并提示成功', async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({
      data: {
        code: 200,
        message: 'ok',
        data: sampleCards,
        total: sampleCards.length
      }
    })

    const store = useCardDataStore()
    await store.fetchCards()

    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.allCards).toEqual(sampleCards)
    expect(store.total).toBe(2)
    expect(MessagePlugin.success).toHaveBeenCalledWith('已加载 2 个知识库')
  })

  it('fetchCards 在业务失败时记录错误信息', async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({
      data: {
        code: 403,
        message: '无权限访问',
        data: [],
        total: 0
      }
    })

    const store = useCardDataStore()
    await store.fetchCards()

    expect(store.loading).toBe(false)
    expect(store.error).toBe('无权限访问')
    expect(store.allCards).toEqual([])
    expect(store.total).toBe(0)
    expect(MessagePlugin.success).not.toHaveBeenCalled()
  })

  it('fetchCards 在网络异常时会重置列表并写入错误', async () => {
    vi.mocked(axios.get).mockRejectedValueOnce(new Error('网络断开'))

    const store = useCardDataStore()
    store.allCards = [...sampleCards]
    store.total = 99

    await store.fetchCards()

    expect(store.loading).toBe(false)
    expect(store.error).toBe('网络断开')
    expect(store.allCards).toEqual([])
    expect(store.total).toBe(0)
  })

  it('过滤、getter、按 ID 查询与清空逻辑正常', () => {
    const store = useCardDataStore()
    store.allCards = [...sampleCards]
    store.total = sampleCards.length

    expect(store.hasCards).toBe(true)
    expect(store.filteredCount).toBe(2)
    expect(store.getCardById('2')?.title).toBe('数据库系统')

    store.filterCardData('人工')
    expect(store.isSearching).toBe(true)
    expect(store.filteredCards.map(card => card.id)).toEqual(['1'])
    expect(store.filteredCount).toBe(1)

    store.resetFilters()
    expect(store.isSearching).toBe(false)
    expect(store.filteredCards).toEqual(sampleCards)

    store.clearCards()
    expect(store.allCards).toEqual([])
    expect(store.total).toBe(0)
    expect(store.error).toBeNull()
    expect(store.hasCards).toBe(false)
  })
})
