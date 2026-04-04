import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useChatImgtore } from '@/store/modules/useChatImg'

describe('useChatImgtore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('addImage 会同步更新 uploadedImage 与 images 列表', () => {
    const store = useChatImgtore()

    store.addImage('data:image/png;base64,aaa')
    store.addImage('data:image/png;base64,bbb')

    expect(store.uploadedImage).toBe('data:image/png;base64,bbb')
    expect(store.images).toEqual(['data:image/png;base64,aaa', 'data:image/png;base64,bbb'])
  })

  it('clearImage 会只移除指定图片，clearAllImg 会清空全部', () => {
    const store = useChatImgtore()
    store.addImage('c')
    store.images = ['a', 'b', 'c']

    store.clearImage('b')

    expect(store.images).toEqual(['a', 'c'])

    store.clearAllImg()
    expect(store.images).toEqual([])
    expect(store.uploadedImage).toBe('c')
  })
})
