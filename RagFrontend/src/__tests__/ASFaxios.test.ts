import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiClient = {
  request: vi.fn()
}

const axiosCreateMock = vi.fn(() => apiClient)

vi.mock('axios', () => ({
  default: {
    create: axiosCreateMock
  }
}))

function createLocalStorage(initial: Record<string, string> = {}) {
  const store = new Map(Object.entries(initial))
  return {
    getItem: vi.fn((key: string) => store.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store.set(key, value)
    }),
    removeItem: vi.fn((key: string) => {
      store.delete(key)
    })
  }
}

async function loadModule() {
  const mod = await import('@/utils/ASFaxios')
  expect(axiosCreateMock).toHaveBeenCalledTimes(1)
  return mod
}

describe('ASFaxios utils', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    apiClient.request.mockReset()

    Object.defineProperty(globalThis, 'localStorage', {
      value: createLocalStorage({ jwt: 'token-abc' }),
      configurable: true,
      writable: true
    })

    vi.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  it('初始化 axios 实例时会带上默认请求头和 JWT', async () => {
    await loadModule()

    expect(axiosCreateMock).toHaveBeenCalledWith({
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        Authorization: 'Bearer token-abc'
      }
    })
  })

  it('get/post/postMultipart/put/del 会透传配置并返回 response.data', async () => {
    const { default: asfAxios, del, get, post, postMultipart, put } = await loadModule()
    const formData = new FormData()
    formData.append('file', 'demo')

    apiClient.request
      .mockResolvedValueOnce({ data: { method: 'get' } })
      .mockResolvedValueOnce({ data: { method: 'post' } })
      .mockResolvedValueOnce({ data: { method: 'multipart' } })
      .mockResolvedValueOnce({ data: { method: 'put' } })
      .mockResolvedValueOnce({ data: { method: 'delete' } })

    await expect(get('/api/a', { page: 1 })).resolves.toEqual({ method: 'get' })
    await expect(post('/api/b', { name: 'alice' }, { timeout: 5000 })).resolves.toEqual({
      method: 'post'
    })
    await expect(postMultipart('/api/c', formData)).resolves.toEqual({ method: 'multipart' })
    await expect(put('/api/d', { enabled: true }, { headers: { 'X-Test': '1' } })).resolves.toEqual(
      { method: 'put' }
    )
    await expect(del('/api/e', { params: { force: true } })).resolves.toEqual({ method: 'delete' })

    expect(apiClient.request).toHaveBeenNthCalledWith(1, {
      method: 'get',
      url: '/api/a',
      params: { page: 1 }
    })
    expect(apiClient.request).toHaveBeenNthCalledWith(2, {
      method: 'post',
      url: '/api/b',
      data: { name: 'alice' },
      timeout: 5000
    })
    expect(apiClient.request).toHaveBeenNthCalledWith(3, {
      method: 'post',
      url: '/api/c',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    expect(apiClient.request).toHaveBeenNthCalledWith(4, {
      method: 'put',
      url: '/api/d',
      data: { enabled: true },
      headers: { 'X-Test': '1' }
    })
    expect(apiClient.request).toHaveBeenNthCalledWith(5, {
      method: 'delete',
      url: '/api/e',
      params: { force: true }
    })
    expect(asfAxios.get).toBe(get)
    expect(asfAxios.post).toBe(post)
    expect(asfAxios.put).toBe(put)
    expect(asfAxios.del).toBe(del)
  })

  it('当后端返回响应数据时会直接抛出该错误体', async () => {
    const { get } = await loadModule()
    const responseData = { detail: '权限不足' }
    apiClient.request.mockRejectedValueOnce({
      message: 'Request failed',
      response: { data: responseData }
    })

    await expect(get('/api/protected')).rejects.toEqual(responseData)
    expect(console.error).toHaveBeenCalled()
  })

  it('当没有响应体时会抛出 Network Error', async () => {
    const { post } = await loadModule()
    apiClient.request.mockRejectedValueOnce({
      message: 'socket hang up'
    })

    await expect(post('/api/demo')).rejects.toEqual(new Error('Network Error'))
    expect(console.error).toHaveBeenCalled()
  })
})
