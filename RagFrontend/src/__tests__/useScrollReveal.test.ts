import { beforeEach, describe, expect, it, vi } from 'vitest'

const mountedCallbacks: Array<() => void> = []
const unmountedCallbacks: Array<() => void> = []
const observerInstances: MockIntersectionObserver[] = []

vi.mock('vue', () => ({
  onMounted: (callback: () => void) => {
    mountedCallbacks.push(callback)
  },
  onUnmounted: (callback: () => void) => {
    unmountedCallbacks.push(callback)
  }
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
    has: (name: string) => classes.has(name)
  }
}

function createNode(initialClasses: string[] = []) {
  return {
    classList: createClassList(initialClasses),
    querySelectorAll: vi.fn<() => unknown[]>(() => []),

    style: {
      position: '',
      overflow: ''
    },
    appendChild: vi.fn(),
    getBoundingClientRect: vi.fn(() => ({ left: 10, top: 20, width: 40, height: 20 }))
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
  return import('@/composables/useScrollReveal')
}

describe('useScrollReveal composable', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    mountedCallbacks.length = 0
    unmountedCallbacks.length = 0
    observerInstances.length = 0

    Object.defineProperty(globalThis, 'IntersectionObserver', {
      value: MockIntersectionObserver,
      configurable: true,
      writable: true
    })
  })

  it('useScrollReveal 会在 mounted 时观察 reveal-group 子元素与普通元素，并在 unmounted 时断开', async () => {
    const group = createNode(['reveal-group'])
    const child = createNode()
    const normal = createNode(['reveal'])
    group.querySelectorAll.mockReturnValue([child])

    Object.defineProperty(globalThis, 'document', {
      value: {
        querySelectorAll: vi.fn(() => [group, normal]),
        createElement: vi.fn()
      },
      configurable: true,
      writable: true
    })

    const { useScrollReveal } = await loadModule()
    const { refresh } = useScrollReveal({
      selector: '.target',
      rootMargin: '1px 0px',
      threshold: 0.5
    })

    mountedCallbacks[0]!()

    expect(observerInstances[0].options).toEqual({ rootMargin: '1px 0px', threshold: 0.5 })
    expect(group.querySelectorAll).toHaveBeenCalledWith('*')
    expect(child.classList.add).toHaveBeenCalledWith('reveal')
    expect(observerInstances[0].observe).toHaveBeenCalledWith(child)
    expect(observerInstances[0].observe).toHaveBeenCalledWith(normal)

    observerInstances[0].callback(
      [{ isIntersecting: true, target: child } as unknown as IntersectionObserverEntry],
      observerInstances[0] as unknown as IntersectionObserver
    )

    expect(child.classList.has('reveal--visible')).toBe(true)
    expect(observerInstances[0].unobserve).toHaveBeenCalledWith(child)

    refresh()
    expect(observerInstances).toHaveLength(2)

    unmountedCallbacks[0]!()
    expect(observerInstances[1].disconnect).toHaveBeenCalledTimes(1)
  })

  it('initScrollReveal 在 once=false 时会处理移出视口，并在没有 window 时直接返回', async () => {
    const target = createNode(['reveal'])
    Object.defineProperty(globalThis, 'document', {
      value: {
        querySelectorAll: vi.fn(() => [target])
      },
      configurable: true,
      writable: true
    })
    Object.defineProperty(globalThis, 'window', {
      value: {},
      configurable: true,
      writable: true
    })

    const { initScrollReveal } = await loadModule()

    const obs = initScrollReveal({ selector: '.init', once: false, threshold: 0.25 })
    expect(obs).toBe(observerInstances[0])
    expect(observerInstances[0].observe).toHaveBeenCalledWith(target)

    observerInstances[0].callback(
      [{ isIntersecting: false, target } as unknown as IntersectionObserverEntry],
      observerInstances[0] as unknown as IntersectionObserver
    )

    expect(target.classList.remove).toHaveBeenCalledWith('reveal--visible')

    delete (globalThis as any).window
    expect(initScrollReveal()).toBeUndefined()
  })

  it('useRipple 会创建波纹节点并在动画结束后移除', async () => {
    const wave = {
      className: '',
      style: { cssText: '' },
      remove: vi.fn(),
      addEventListener: vi.fn((name: string, handler: () => void) => {
        if (name === 'animationend') {
          handler()
        }
      })
    }
    const button = createNode()
    button.appendChild = vi.fn()

    Object.defineProperty(globalThis, 'document', {
      value: {
        createElement: vi.fn(() => wave),
        querySelectorAll: vi.fn(() => [])
      },
      configurable: true,
      writable: true
    })
    Object.defineProperty(globalThis, 'window', {
      value: {
        getComputedStyle: vi.fn(() => ({ position: 'static', overflow: 'visible' }))
      },
      configurable: true,
      writable: true
    })

    const { useRipple } = await loadModule()
    const { ripple } = useRipple()

    ripple({
      currentTarget: button,
      clientX: 20,
      clientY: 30
    } as unknown as MouseEvent)

    expect(button.style.position).toBe('relative')
    expect(button.style.overflow).toBe('hidden')
    expect(document.createElement).toHaveBeenCalledWith('span')
    expect(button.appendChild).toHaveBeenCalledWith(wave)
    expect(wave.className).toBe('ripple-wave')
    expect(wave.style.cssText).toContain('width:80px')
    expect(wave.remove).toHaveBeenCalledTimes(1)
  })
})
