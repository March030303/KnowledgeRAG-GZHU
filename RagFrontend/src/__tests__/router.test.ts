import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

let beforeEachGuard: ((to: any, from: any, next: (value?: unknown) => void) => void) | undefined

const routerMock = {
  beforeEach: vi.fn((guard: (to: any, from: any, next: (value?: unknown) => void) => void) => {
    beforeEachGuard = guard
  })
}

vi.mock('vue-router', () => ({
  createRouter: vi.fn(() => routerMock),
  createWebHistory: vi.fn(() => ({}))
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
    })
  }
}

async function assertEventually(assertion: () => void, attempts = 20) {
  let lastError: unknown

  for (let i = 0; i < attempts; i++) {
    try {
      assertion()
      return
    } catch (error) {
      lastError = error
      await new Promise(resolve => setTimeout(resolve, 0))
    }
  }

  throw lastError
}

async function loadRouterModule() {
  vi.resetModules()
  beforeEachGuard = undefined
  routerMock.beforeEach.mockImplementation(
    (guard: (to: any, from: any, next: (value?: unknown) => void) => void) => {
      beforeEachGuard = guard
    }
  )

  const mod = await import('@/router/index')
  expect(beforeEachGuard).toBeTypeOf('function')
  return mod
}

describe('router beforeEach guard', () => {
  beforeEach(() => {
    Object.defineProperty(globalThis, 'localStorage', {
      value: createLocalStorage(),
      configurable: true,
      writable: true
    })

    Object.defineProperty(globalThis, 'fetch', {
      value: vi.fn(),
      configurable: true,
      writable: true
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('公共路由直接放行', async () => {
    await loadRouterModule()
    const next = vi.fn()

    beforeEachGuard!({ path: '/LogonOrRegister', fullPath: '/LogonOrRegister' }, {}, next)

    expect(next).toHaveBeenCalledWith()
    expect(fetch).not.toHaveBeenCalled()
  })

  it('缺少 JWT 时会重定向到登录页并带 redirect 参数', async () => {
    await loadRouterModule()
    const next = vi.fn()

    beforeEachGuard!({ path: '/chat', fullPath: '/chat?id=1' }, {}, next)

    expect(next).toHaveBeenCalledWith('/LogonOrRegister?redirect=%2Fchat%3Fid%3D1')
  })

  it('刚登录后的首次跳转会跳过远程校验且仅生效一次', async () => {
    const { markJustAuthenticated } = await loadRouterModule()
    localStorage.setItem('jwt', 'fresh-token')
    const next = vi.fn()

    markJustAuthenticated()
    beforeEachGuard!({ path: '/knowledge', fullPath: '/knowledge' }, {}, next)

    expect(next).toHaveBeenCalledWith()
    expect(fetch).not.toHaveBeenCalled()

    vi.mocked(fetch).mockResolvedValueOnce({
      json: vi.fn(() => ({ status: 'success' }))
    } as unknown as Response)

    const nextAgain = vi.fn()

    beforeEachGuard!({ path: '/chat', fullPath: '/chat' }, {}, nextAgain)

    await assertEventually(() => {
      expect(fetch).toHaveBeenCalledTimes(1)
      expect(nextAgain).toHaveBeenCalledWith()
    })
  })

  it('JWT 远程校验成功时允许进入受保护页面', async () => {
    await loadRouterModule()
    localStorage.setItem('jwt', 'valid-token')
    vi.mocked(fetch).mockResolvedValueOnce({
      json: vi.fn(() => ({ status: 'success' }))
    } as unknown as Response)

    const next = vi.fn()

    beforeEachGuard!({ path: '/history', fullPath: '/history' }, {}, next)

    await assertEventually(() => {
      expect(fetch).toHaveBeenCalledWith('/api/users/me', {
        method: 'GET',
        headers: { Authorization: 'Bearer valid-token' }
      })
      expect(next).toHaveBeenCalledWith()
    })
  })

  it('JWT 远程校验失败时会清除 token 并跳回登录页', async () => {
    await loadRouterModule()
    localStorage.setItem('jwt', 'bad-token')
    vi.mocked(fetch).mockResolvedValueOnce({
      json: vi.fn(() => ({ status: 'error' }))
    } as unknown as Response)
    const next = vi.fn()

    beforeEachGuard!({ path: '/agent', fullPath: '/agent' }, {}, next)

    await assertEventually(() => {
      expect(localStorage.removeItem).toHaveBeenCalledWith('jwt')
      expect(next).toHaveBeenCalledWith('/LogonOrRegister?redirect=%2Fagent')
    })
  })

  it('JWT 远程校验遇到网络异常时保留 token 并放行', async () => {
    await loadRouterModule()
    localStorage.setItem('jwt', 'network-token')
    vi.mocked(fetch).mockRejectedValueOnce(new Error('network error'))
    const next = vi.fn()

    beforeEachGuard!({ path: '/files', fullPath: '/files' }, {}, next)

    await assertEventually(() => {
      expect(localStorage.removeItem).not.toHaveBeenCalled()
      expect(next).toHaveBeenCalledWith()
    })
  })
})
