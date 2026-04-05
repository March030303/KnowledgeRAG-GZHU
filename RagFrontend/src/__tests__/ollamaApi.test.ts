import { beforeEach, describe, expect, it, vi } from 'vitest'
import API_ENDPOINTS from '@/utils/apiConfig'

function createLocalStorage(initial: Record<string, string> = {}) {
  const store = new Map(Object.entries(initial))
  return {
    getItem: vi.fn((key: string) => store.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store.set(key, value)
    })
  }
}

function createWindowMock() {
  const listeners = new Map<string, EventListener>()
  return {
    listeners,
    addEventListener: vi.fn((name: string, handler: EventListener) => {
      listeners.set(name, handler)
    })
  }
}

function createStreamBody(chunks: string[]) {
  const encoded = chunks.map(chunk => new TextEncoder().encode(chunk))
  return {
    getReader: () => ({
      read: vi
        .fn()
        .mockImplementationOnce(async () => ({ done: false, value: encoded[0] }))
        .mockImplementationOnce(async () => ({ done: true, value: undefined }))
    })
  }
}

async function loadService() {
  const mod = await import('@/utils/ollamaApi')
  return mod.default
}

describe('ollamaApi service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
    vi.spyOn(console, 'warn').mockImplementation(() => undefined)

    Object.defineProperty(globalThis, 'fetch', {
      value: vi.fn(),
      configurable: true,
      writable: true
    })
  })

  it('启动时会读取本地 serverUrl，并可响应设置更新事件', async () => {
    const windowMock = createWindowMock()
    Object.defineProperty(globalThis, 'window', {
      value: windowMock,
      configurable: true,
      writable: true
    })
    Object.defineProperty(globalThis, 'localStorage', {
      value: createLocalStorage({
        ollamaSettings: JSON.stringify({ serverUrl: 'http://127.0.0.1:22334' })
      }),
      configurable: true,
      writable: true
    })

    const service = await loadService()
    expect(service.getServerUrl()).toBe('http://127.0.0.1:22334')
    expect(windowMock.addEventListener).toHaveBeenCalledWith(
      'ollamaSettingsUpdated',
      expect.any(Function)
    )

    windowMock.listeners.get('ollamaSettingsUpdated')!({
      detail: { serverUrl: 'http://10.0.0.8:11434' }
    } as unknown as Event)
    expect(service.getServerUrl()).toBe('http://10.0.0.8:11434')

    service.updateServerUrl('http://manual-change:11434')
    expect(service.getServerUrl()).toBe('http://manual-change:11434')
  })

  it('本地设置损坏时会回退到默认地址', async () => {
    Object.defineProperty(globalThis, 'window', {
      value: createWindowMock(),
      configurable: true,
      writable: true
    })
    Object.defineProperty(globalThis, 'localStorage', {
      value: createLocalStorage({
        ollamaSettings: '{bad-json}'
      }),
      configurable: true,
      writable: true
    })

    const service = await loadService()

    expect(service.getServerUrl()).toBe(API_ENDPOINTS.OLLAMA.BASE)
    expect(console.error).toHaveBeenCalled()
  })

  it('getModels 成功时返回模型列表，失败时抛出包装后的错误', async () => {
    Object.defineProperty(globalThis, 'window', {
      value: createWindowMock(),
      configurable: true,
      writable: true
    })
    Object.defineProperty(globalThis, 'localStorage', {
      value: createLocalStorage(),
      configurable: true,
      writable: true
    })

    const service = await loadService()
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn(async () => ({ models: [{ name: 'llama3:8b' }] }))
      } as unknown as Response)
      .mockResolvedValueOnce({
        ok: false,
        status: 500
      } as Response)

    await expect(service.getModels()).resolves.toEqual([{ name: 'llama3:8b' }])
    expect(fetch).toHaveBeenCalledWith(`${API_ENDPOINTS.OLLAMA.BASE}${API_ENDPOINTS.OLLAMA.TAGS}`)

    await expect(service.getModels()).rejects.toThrow('获取模型列表失败: HTTP error! status: 500')
  })

  it('deleteModel 与 copyModel 会在异常时返回 false', async () => {
    Object.defineProperty(globalThis, 'window', {
      value: createWindowMock(),
      configurable: true,
      writable: true
    })
    Object.defineProperty(globalThis, 'localStorage', {
      value: createLocalStorage(),
      configurable: true,
      writable: true
    })

    const service = await loadService()
    vi.mocked(fetch)
      .mockResolvedValueOnce({ ok: true } as Response)
      .mockResolvedValueOnce({ ok: false, status: 400 } as Response)
      .mockRejectedValueOnce(new Error('network'))

    await expect(service.deleteModel('demo')).resolves.toBe(true)
    await expect(service.deleteModel('demo')).resolves.toBe(false)
    await expect(service.copyModel('a', 'b')).resolves.toBe(false)
  })

  it('downloadModel 会解析流式进度并忽略坏数据', async () => {
    Object.defineProperty(globalThis, 'window', {
      value: createWindowMock(),
      configurable: true,
      writable: true
    })
    Object.defineProperty(globalThis, 'localStorage', {
      value: createLocalStorage(),
      configurable: true,
      writable: true
    })

    const service = await loadService()
    const onProgress = vi.fn()

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      body: createStreamBody(['{"status":"pulling"}\nnot-json\n'])
    } as unknown as Response)

    await service.downloadModel('demo', onProgress)

    expect(onProgress).toHaveBeenCalledWith({ status: 'pulling' })
    expect(console.warn).toHaveBeenCalled()
  })

  it('downloadModel 遇到异常响应时会抛出友好错误', async () => {
    Object.defineProperty(globalThis, 'window', {
      value: createWindowMock(),
      configurable: true,
      writable: true
    })
    Object.defineProperty(globalThis, 'localStorage', {
      value: createLocalStorage(),
      configurable: true,
      writable: true
    })

    const service = await loadService()
    vi.mocked(fetch)
      .mockResolvedValueOnce({ ok: false, status: 503 } as Response)
      .mockResolvedValueOnce({ ok: true, body: null } as unknown as Response)

    await expect(service.downloadModel('demo')).rejects.toThrow(
      '下载模型失败: HTTP error! status: 503'
    )
    await expect(service.downloadModel('demo')).rejects.toThrow('下载模型失败: 响应体为空')
  })
})
