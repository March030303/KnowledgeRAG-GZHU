import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MessagePlugin } from 'tdesign-vue-next'

let requestHandler: ((config: Record<string, any>) => Record<string, any>) | undefined
let responseSuccessHandler: ((response: unknown) => unknown) | undefined
let responseErrorHandler: ((error: Record<string, any>) => Promise<unknown>) | undefined

const axiosInstance = Object.assign(vi.fn(), {
  post: vi.fn(),
  interceptors: {
    request: {
      use: vi.fn((handler: (config: Record<string, any>) => Record<string, any>) => {
        requestHandler = handler
        return 0
      })
    },
    response: {
      use: vi.fn(
        (
          success: (response: unknown) => unknown,
          error: (err: Record<string, any>) => Promise<unknown>
        ) => {
          responseSuccessHandler = success
          responseErrorHandler = error
          return 0
        }
      )
    }
  }
})

const axiosCreateMock = vi.fn(() => axiosInstance)

vi.mock('axios', () => ({
  default: {
    create: axiosCreateMock
  }
}))

vi.mock('tdesign-vue-next', () => ({
  MessagePlugin: {
    error: vi.fn(),
    success: vi.fn()
  }
}))

function createLocalStorage() {
  const store = new Map<string, string>()
  return {
    getItem: vi.fn((key: string) => store.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store.set(key, value)
    }),
    removeItem: vi.fn((key: string) => {
      store.delete(key)
    }),
    clear: vi.fn(() => {
      store.clear()
    })
  }
}

function resetAxiosMockState() {
  requestHandler = undefined
  responseSuccessHandler = undefined
  responseErrorHandler = undefined
  axiosCreateMock.mockClear()
  axiosInstance.mockReset()
  axiosInstance.post.mockReset()
  axiosInstance.interceptors.request.use.mockImplementation(
    (handler: (config: Record<string, any>) => Record<string, any>) => {
      requestHandler = handler
      return 0
    }
  )
  axiosInstance.interceptors.response.use.mockImplementation(
    (
      success: (response: unknown) => unknown,
      error: (err: Record<string, any>) => Promise<unknown>
    ) => {
      responseSuccessHandler = success
      responseErrorHandler = error
      return 0
    }
  )
}

async function loadRequestModule() {
  const mod = await import('@/utils/request')
  expect(axiosCreateMock).toHaveBeenCalledTimes(1)
  expect(requestHandler).toBeTypeOf('function')
  expect(responseSuccessHandler).toBeTypeOf('function')
  expect(responseErrorHandler).toBeTypeOf('function')
  return mod
}

describe('request utils', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.useFakeTimers()
    resetAxiosMockState()

    Object.defineProperty(globalThis, 'localStorage', {
      value: createLocalStorage(),
      configurable: true,
      writable: true
    })

    Object.defineProperty(globalThis, 'window', {
      value: { location: { href: '' } },
      configurable: true,
      writable: true
    })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('请求拦截器会自动附加 JWT', async () => {
    await loadRequestModule()
    localStorage.setItem('jwt', 'token-123')

    const config = requestHandler!({ headers: {} })

    expect(config.headers.Authorization).toBe('Bearer token-123')
  })

  it('响应成功时直接返回原响应', async () => {
    await loadRequestModule()
    const response = { data: { ok: true } }

    expect(responseSuccessHandler!(response)).toBe(response)
  })

  it('401 会清理 JWT、提示并跳转登录页', async () => {
    await loadRequestModule()
    localStorage.setItem('jwt', 'expired-token')

    const error = {
      message: 'Unauthorized',
      config: { headers: {} },
      response: { status: 401, data: { detail: 'expired' } }
    }

    const promise = responseErrorHandler!(error)

    await expect(promise).rejects.toBe(error)
    await vi.runAllTimersAsync()

    expect(localStorage.removeItem).toHaveBeenCalledWith('jwt')
    expect(MessagePlugin.error).toHaveBeenCalledWith('登录已过期，请重新登录')
    expect(window.location.href).toBe('/LogonOrRegister')
  })

  it('500/503 会按次数退避重试', async () => {
    await loadRequestModule()
    const config: { url: string; headers: Record<string, never>; _retryCount?: number } = {
      url: '/api/demo',
      headers: {}
    }

    const retriedResponse = { data: { ok: true } }
    axiosInstance.mockResolvedValueOnce(retriedResponse)

    const promise = responseErrorHandler!({
      message: 'server error',
      config,
      response: { status: 503, data: { detail: 'busy' } }
    })

    await vi.advanceTimersByTimeAsync(1000)
    await expect(promise).resolves.toEqual(retriedResponse)
    expect(config._retryCount).toBe(1)
    expect(axiosInstance).toHaveBeenCalledWith(config)
  })

  it('网络错误会提示连接失败', async () => {
    await loadRequestModule()

    const error = {
      message: 'Network Error',
      config: { headers: {} }
    }

    await expect(responseErrorHandler!(error)).rejects.toBe(error)
    expect(MessagePlugin.error).toHaveBeenCalledWith({
      content: '网络连接失败，请检查网络或后端服务',
      duration: 4000
    })
  })

  it('404 错误不会弹出 toast', async () => {
    await loadRequestModule()

    const error = {
      message: 'not found',
      config: { headers: {} },
      response: { status: 404, data: { detail: 'missing' } }
    }

    await expect(responseErrorHandler!(error)).rejects.toBe(error)
    expect(MessagePlugin.error).not.toHaveBeenCalled()
  })

  it('其他响应错误会展示服务端 detail', async () => {
    await loadRequestModule()

    const error = {
      message: 'bad request',
      config: { headers: {} },
      response: { status: 400, data: { detail: '参数不合法' } }
    }

    await expect(responseErrorHandler!(error)).rejects.toBe(error)
    expect(MessagePlugin.error).toHaveBeenCalledWith({
      content: '错误 400：参数不合法',
      duration: 4000
    })
  })

  it('小文件上传会透传 formData 并回调上传进度', async () => {
    const { uploadFileWithProgress } = await loadRequestModule()
    const progress = vi.fn()
    const response = { data: { ok: true } }

    axiosInstance.post.mockImplementationOnce(
      async (_url: string, _formData: FormData, config: Record<string, any>) => {
        config.onUploadProgress?.({ loaded: 5, total: 10 })
        return response
      }
    )

    const file = new File([new Uint8Array(10)], 'tiny.txt', { type: 'text/plain' })
    const result = await uploadFileWithProgress('/api/upload', file, { kb_id: 'demo' }, progress)

    expect(result).toBe(response)
    expect(axiosInstance.post).toHaveBeenCalledTimes(1)

    const [, formData, config] = axiosInstance.post.mock.calls[0]
    expect(formData.get('kb_id')).toBe('demo')
    expect((formData.get('file') as File).name).toBe('tiny.txt')
    expect(config.headers['Content-Type']).toBe('multipart/form-data')
    expect(progress).toHaveBeenCalledWith({ loaded: 5, total: 10, percent: 50 })
  })

  it('大文件上传会按分片重试并累计进度', async () => {
    const { uploadFileWithProgress } = await loadRequestModule()
    const progress = vi.fn()
    const largeFile = new File([new Uint8Array(6 * 1024 * 1024)], 'large.bin')

    axiosInstance.post
      .mockRejectedValueOnce(new Error('temporary error'))
      .mockResolvedValueOnce({ data: { chunk: 1 } })
      .mockResolvedValueOnce({ data: { done: true } })

    const promise = uploadFileWithProgress('/api/upload', largeFile, { kb_id: 'demo' }, progress)

    await vi.advanceTimersByTimeAsync(1000)
    const result = await promise

    expect(result).toEqual({ data: { done: true } })
    expect(axiosInstance.post).toHaveBeenCalledTimes(3)
    expect(progress).toHaveBeenLastCalledWith({
      loaded: largeFile.size,
      total: largeFile.size,
      percent: 100
    })

    const [, firstChunkFormData] = axiosInstance.post.mock.calls[0]
    const [, secondChunkFormData] = axiosInstance.post.mock.calls[2]
    expect(firstChunkFormData.get('chunk_index')).toBe('0')
    expect(secondChunkFormData.get('chunk_index')).toBe('1')
  })

  it('withLoading 在异常场景也会正确收起 loading', async () => {
    const { globalLoading, withLoading } = await loadRequestModule()

    await expect(
      withLoading(async () => {
        expect(globalLoading.value).toBe(true)
        throw new Error('boom')
      })
    ).rejects.toThrow('boom')

    expect(globalLoading.value).toBe(false)
  })
})
