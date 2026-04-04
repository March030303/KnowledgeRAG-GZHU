import { beforeEach, describe, expect, it, vi } from 'vitest'

type MatchMediaMock = {
  matches: boolean
  addEventListener: ReturnType<typeof vi.fn>
  removeEventListener: ReturnType<typeof vi.fn>
}

function createStorage(initial: Record<string, string> = {}) {
  const store = new Map(Object.entries(initial))
  return {
    getItem: vi.fn((key: string) => store.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store.set(key, value)
    })
  }
}

function createClassList() {
  const state = new Map<string, boolean>()
  return {
    toggle: vi.fn((name: string, enabled?: boolean) => {
      state.set(name, Boolean(enabled))
    }),
    has: (name: string) => state.get(name) ?? false
  }
}

function createStyle() {
  const values = new Map<string, string>()
  return {
    values,
    fontSize: '',
    backgroundColor: '',
    colorScheme: '',
    setProperty: vi.fn((key: string, value: string) => {
      values.set(key, value)
    })
  }
}

async function loadThemeModule() {
  return import('@/composables/useTheme')
}

describe('useTheme composable', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()

    const htmlStyle = createStyle()
    const bodyStyle = createStyle()
    const htmlClassList = createClassList()
    const attrMap = new Map<string, string>()
    let changeListener: ((event: { matches: boolean }) => void) | undefined

    const matchMediaMock: MatchMediaMock = {
      matches: true,
      addEventListener: vi.fn((_name: string, listener: (event: { matches: boolean }) => void) => {
        changeListener = listener
      }),
      removeEventListener: vi.fn()
    }

    Object.defineProperty(globalThis, 'localStorage', {
      value: createStorage(),
      configurable: true,
      writable: true
    })

    Object.defineProperty(globalThis, 'window', {
      value: {
        matchMedia: vi.fn(() => matchMediaMock)
      },
      configurable: true,
      writable: true
    })

    Object.defineProperty(globalThis, 'document', {
      value: {
        documentElement: {
          classList: htmlClassList,
          style: htmlStyle,
          setAttribute: vi.fn((key: string, value: string) => {
            attrMap.set(key, value)
          })
        },
        body: {
          style: bodyStyle,
          setAttribute: vi.fn((key: string, value: string) => {
            attrMap.set(`body:${key}`, value)
          })
        }
      },
      configurable: true,
      writable: true
    })

    Object.defineProperty(globalThis, '__themeTestContext', {
      value: {
        htmlStyle,
        bodyStyle,
        htmlClassList,
        attrMap,
        matchMediaMock,
        getChangeListener: () => changeListener
      },
      configurable: true,
      writable: true
    })
  })

  it('loadAppearance 会读取新配置并兼容旧配置迁移', async () => {
    const getItemMock = localStorage.getItem as unknown as {
      mockReturnValueOnce: (value: string | null) => void
    }

    getItemMock.mockReturnValueOnce(JSON.stringify({ theme: 'dark', color: 'rose' }))
    getItemMock.mockReturnValueOnce(null)
    getItemMock.mockReturnValueOnce('auto')
    getItemMock.mockReturnValueOnce('teal')
    getItemMock.mockReturnValueOnce('lg')

    const { loadAppearance } = await loadThemeModule()

    expect(loadAppearance()).toEqual({
      theme: 'dark',
      color: 'rose',
      fontSize: 'medium',
      layout: 'normal'
    })

    expect(loadAppearance()).toEqual({
      theme: 'auto',
      color: 'teal',
      fontSize: 'lg',
      layout: 'normal'
    })
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'app_appearance',
      JSON.stringify({
        theme: 'auto',
        color: 'teal',
        fontSize: 'lg',
        layout: 'normal'
      })
    )
  })

  it('saveAppearance 会同时写入新旧存储键', async () => {
    const { saveAppearance } = await loadThemeModule()

    saveAppearance({
      theme: 'dark',
      color: 'orange',
      fontSize: 'large',
      layout: 'compact'
    })

    expect(localStorage.setItem).toHaveBeenCalledWith(
      'app_appearance',
      JSON.stringify({
        theme: 'dark',
        color: 'orange',
        fontSize: 'large',
        layout: 'compact'
      })
    )
    expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'dark')
    expect(localStorage.setItem).toHaveBeenCalledWith('themeColor', 'orange')
    expect(localStorage.setItem).toHaveBeenCalledWith('fontSize', 'large')
  })

  it('applyTheme 支持 dark/light/auto，并会清理旧的媒体监听', async () => {
    const { applyTheme } = await loadThemeModule()
    const context = (globalThis as any).__themeTestContext

    applyTheme('dark')
    expect(context.htmlClassList.toggle).toHaveBeenCalledWith('dark', true)
    expect(context.attrMap.get('data-theme')).toBe('dark')
    expect(context.htmlStyle.backgroundColor).toBe('#1e1e2e')
    expect(context.bodyStyle.backgroundColor).toBe('#1e1e2e')
    expect(context.htmlStyle.colorScheme).toBe('dark')

    applyTheme('auto')
    expect(window.matchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)')
    expect(context.matchMediaMock.addEventListener).toHaveBeenCalledWith(
      'change',
      expect.any(Function)
    )
    context.getChangeListener()!({ matches: false })
    expect(context.htmlClassList.toggle).toHaveBeenCalledWith('dark', false)
    expect(context.attrMap.get('data-theme')).toBe('light')

    applyTheme('light')
    expect(context.matchMediaMock.removeEventListener).toHaveBeenCalledWith(
      'change',
      expect.any(Function)
    )
    expect(context.htmlStyle.colorScheme).toBe('light')
  })

  it('applyColor、applyFontSize、applyLayout 与 applyAllAppearance 会同步更新 DOM 变量', async () => {
    const { applyAllAppearance, applyColor, applyFontSize, applyLayout } = await loadThemeModule()
    const context = (globalThis as any).__themeTestContext

    applyColor('green')
    expect(context.htmlStyle.values.get('--color-primary')).toBe('#22c55e')
    expect(context.htmlStyle.values.get('--primary')).toBe('#22c55e')
    expect(context.htmlStyle.values.get('--color-primary-light')).toContain('rgba(')
    expect(context.htmlStyle.values.get('--shadow-hover-btn')).toContain('rgba(')

    applyFontSize('lg')
    expect(context.htmlStyle.fontSize).toBe('16px')
    expect(context.attrMap.get('body:data-font-size')).toBe('lg')
    expect(context.attrMap.get('data-font-size')).toBe('lg')

    applyLayout('compact')
    expect(context.attrMap.get('data-layout')).toBe('compact')
    expect(context.htmlStyle.values.get('--spacing-base')).toBe('12px')

    applyAllAppearance({
      theme: 'light',
      color: 'cyan',
      fontSize: 'small',
      layout: 'spacious'
    })
    expect(context.attrMap.get('data-theme')).toBe('light')
    expect(context.htmlStyle.values.get('--primary')).toBe('#06b6d4')
    expect(context.htmlStyle.fontSize).toBe('13px')
    expect(context.htmlStyle.values.get('--spacing-base')).toBe('20px')
  })
})
