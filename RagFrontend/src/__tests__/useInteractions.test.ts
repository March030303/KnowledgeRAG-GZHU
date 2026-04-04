import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

let watchedCallback: (() => void) | undefined
const observerInstances: MockIntersectionObserver[] = []

vi.mock('vue', () => ({
  watch: vi.fn((_source: () => string, callback: () => void) => {
    watchedCallback = callback
  })
}))

function createClassList(initial: string[] = []) {
  const classes = new Set(initial)
  return {
    add: vi.fn((name: string) => {
      classes.add(name)
    }),
    remove: vi.fn((name: string) => {
      classes.delete(name)
    }),
    contains: vi.fn((name: string) => classes.has(name)),
    toggle: vi.fn((name: string, enabled?: boolean) => {
      if (enabled) {
        classes.add(name)
      } else {
        classes.delete(name)
      }
    }),
    has: (name: string) => classes.has(name)
  }
}

function createInteractiveNode(initialClasses: string[] = [], rippleInited?: string) {
  let mousedownHandler: ((event: MouseEvent) => void) | undefined
  const node = {
    dataset: rippleInited ? { rippleInited } : {},
    classList: createClassList(initialClasses),
    addEventListener: vi.fn((name: string, handler: (event: MouseEvent) => void) => {
      if (name === 'mousedown') {
        mousedownHandler = handler
      }
    }),
    appendChild: vi.fn(),
    getBoundingClientRect: vi.fn(() => ({ left: 5, top: 10, width: 40, height: 20 }))
  }

  return {
    node,
    triggerRipple(event: Partial<MouseEvent> = {}) {
      mousedownHandler?.({ currentTarget: node, clientX: 20, clientY: 30, ...event } as MouseEvent)
    }
  }
}

class MockIntersectionObserver {
  callback: IntersectionObserverCallback
  options: IntersectionObserverInit
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()

  constructor(callback: IntersectionObserverCallback, options: IntersectionObserverInit) {
    this.callback = callback
    this.options = options
    observerInstances.push(this)
  }
}

async function loadModule() {
  return import('@/composables/useInteractions')
}

describe('useInteractions composable', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    vi.useFakeTimers()
    watchedCallback = undefined
    observerInstances.length = 0

    Object.defineProperty(globalThis, 'IntersectionObserver', {
      value: MockIntersectionObserver,
      configurable: true,
      writable: true
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('initInteractions 会初始化波纹、滚动显隐、吸顶导航，并在路由变化后重新扫描', async () => {
    const primaryButton = createInteractiveNode()
    const alreadyInited = createInteractiveNode([], '1')
    const revealHidden = { classList: createClassList(['reveal']) }
    const revealVisible = { classList: createClassList(['reveal', 'reveal--visible']) }
    const navbar = { classList: createClassList() }
    let scrollHandler: (() => void) | undefined
    const appMain = {
      scrollTop: 0,
      addEventListener: vi.fn((_name: string, handler: () => void) => {
        scrollHandler = handler
      })
    }
    const createdNodes: Array<{
      className: string
      style: { cssText: string }
      remove: ReturnType<typeof vi.fn>
      addEventListener: (name: string, handler: () => void) => void
    }> = []

    Object.defineProperty(globalThis, 'Window', {
      value: function WindowMock() {},
      configurable: true,
      writable: true
    })

    Object.defineProperty(globalThis, 'requestAnimationFrame', {
      value: vi.fn((callback: FrameRequestCallback) => {
        callback(0)
        return 1
      }),
      configurable: true,
      writable: true
    })

    Object.defineProperty(globalThis, 'document', {
      value: {
        querySelectorAll: vi.fn((selector: string) => {
          if (selector.includes('.t-button--theme-primary')) {
            return [primaryButton.node, alreadyInited.node]
          }
          if (selector.includes('.reveal')) {
            return [revealHidden, revealVisible]
          }
          return []
        }),
        querySelector: vi.fn((selector: string) => {
          if (selector === '.navbar-sticky') return navbar
          if (selector === '.app-main') return appMain
          return null
        }),
        createElement: vi.fn(() => {
          let animationEnd: (() => void) | undefined
          const created = {
            className: '',
            style: { cssText: '' },
            remove: vi.fn(),
            addEventListener: (_name: string, handler: () => void) => {
              animationEnd = handler
            }
          }
          createdNodes.push(created)
          if (animationEnd) animationEnd()
          return created
        }),
        body: {
          appendChild: vi.fn()
        }
      },
      configurable: true,
      writable: true
    })

    const { initInteractions } = await loadModule()
    const router = {
      currentRoute: {
        value: {
          fullPath: '/chat'
        }
      }
    }

    initInteractions(router as never)

    expect(primaryButton.node.dataset.rippleInited).toBe('1')
    expect(primaryButton.node.addEventListener).toHaveBeenCalledWith(
      'mousedown',
      expect.any(Function)
    )
    expect(alreadyInited.node.addEventListener).not.toHaveBeenCalled()
    expect(observerInstances[0].observe).toHaveBeenCalledWith(revealHidden)
    expect(observerInstances[0].observe).not.toHaveBeenCalledWith(revealVisible)
    expect(appMain.addEventListener).toHaveBeenCalledWith('scroll', expect.any(Function), {
      passive: true
    })

    observerInstances[0].callback(
      [{ isIntersecting: true, target: revealHidden } as unknown as IntersectionObserverEntry],
      observerInstances[0] as unknown as IntersectionObserver
    )

    expect(revealHidden.classList.add).toHaveBeenCalledWith('reveal--visible')
    expect(observerInstances[0].unobserve).toHaveBeenCalledWith(revealHidden)

    primaryButton.triggerRipple()
    expect(primaryButton.node.appendChild).toHaveBeenCalledTimes(1)
    expect(createdNodes[0].className).toBe('ripple-wave')
    expect(createdNodes[0].style.cssText).toContain('width:80px')

    appMain.scrollTop = 20
    scrollHandler?.()
    expect(navbar.classList.toggle).toHaveBeenCalledWith('scrolled', true)

    watchedCallback?.()
    await vi.advanceTimersByTimeAsync(80)
    expect(document.querySelectorAll).toHaveBeenCalledTimes(4)
  })

  it('showPageLoading/hidePageLoading 会避免重复创建并在动画后移除', async () => {
    const appended: any[] = []
    let latestNode: any

    Object.defineProperty(globalThis, 'document', {
      value: {
        body: {
          appendChild: vi.fn((node: any) => {
            appended.push(node)
          })
        },
        createElement: vi.fn(() => {
          latestNode = {
            className: '',
            style: {
              opacity: '',
              transition: ''
            },
            remove: vi.fn()
          }
          return latestNode
        })
      },
      configurable: true,
      writable: true
    })

    const { hidePageLoading, showPageLoading } = await loadModule()

    showPageLoading()
    showPageLoading()
    expect(appended).toHaveLength(1)
    expect(latestNode.className).toBe('page-loading-bar')

    hidePageLoading()
    expect(latestNode.style.opacity).toBe('0')
    expect(latestNode.style.transition).toBe('opacity 0.3s ease')
    await vi.advanceTimersByTimeAsync(350)
    expect(latestNode.remove).toHaveBeenCalledTimes(1)
  })
})
