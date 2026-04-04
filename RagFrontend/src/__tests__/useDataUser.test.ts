import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { MessagePlugin } from 'tdesign-vue-next'
import { get, post } from '@/utils/ASFaxios'
import { useDataUserStore } from '@/store/modules/useDataUser'

vi.mock('@/utils/ASFaxios', () => ({
  get: vi.fn(),
  post: vi.fn()
}))

vi.mock('tdesign-vue-next', () => ({
  MessagePlugin: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('useDataUserStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.spyOn(console, 'log').mockImplementation(() => undefined)

    Object.defineProperty(globalThis, 'window', {
      value: {
        location: {
          reload: vi.fn()
        }
      },
      configurable: true,
      writable: true
    })
  })

  it('fetchUserData 成功时会写入最新用户资料', async () => {
    const payload = {
      name: '暖霜',
      avatar: 'avatar.png',
      signature: '保持学习',
      email: 'demo@example.com',
      social_media: '@demo'
    }
    vi.mocked(get).mockResolvedValueOnce({ data: payload })

    const store = useDataUserStore()
    await store.fetchUserData()

    expect(get).toHaveBeenCalledWith('/api/user/GetUserData')
    expect(store.userData).toEqual(payload)
    expect(MessagePlugin.error).not.toHaveBeenCalled()
  })

  it('fetchUserData 失败时会提示错误', async () => {
    vi.mocked(get).mockRejectedValueOnce(new Error('boom'))

    const store = useDataUserStore()
    await store.fetchUserData()

    expect(MessagePlugin.error).toHaveBeenCalledWith('获取用户数据失败！')
  })

  it('updateUserData 成功时会提交 FormData、更新状态并刷新页面', async () => {
    const store = useDataUserStore()
    store.userData.email = 'demo@example.com'
    store.userData.social_media = '@demo'

    const updated = {
      name: '新名字',
      avatar: 'new.png',
      signature: '新签名',
      email: 'demo@example.com',
      social_media: '@demo'
    }
    vi.mocked(post).mockResolvedValueOnce({ data: updated })

    await store.updateUserData('新名字', 'new.png', '新签名')

    expect(post).toHaveBeenCalledTimes(1)
    const [url, formData] = vi.mocked(post).mock.calls[0]
    expect(url).toBe('/api/UpdateUserData')
    expect(formData).toBeInstanceOf(FormData)
    expect((formData as FormData).get('name')).toBe('新名字')
    expect((formData as FormData).get('avatar')).toBe('new.png')
    expect((formData as FormData).get('signature')).toBe('新签名')
    expect((formData as FormData).get('email')).toBe('demo@example.com')
    expect((formData as FormData).get('social_media')).toBe('@demo')
    expect(store.userData).toEqual(updated)
    expect(MessagePlugin.success).toHaveBeenCalledWith('更新用户数据成功！')
    expect(window.location.reload).toHaveBeenCalledTimes(1)
  })

  it('updateUserData 失败时会提示错误且不刷新页面', async () => {
    vi.mocked(post).mockRejectedValueOnce(new Error('save failed'))

    const store = useDataUserStore()
    await store.updateUserData('名字', 'avatar', '签名')

    expect(MessagePlugin.error).toHaveBeenCalledWith('更新用户数据失败！')
    expect(window.location.reload).not.toHaveBeenCalled()
  })
})
