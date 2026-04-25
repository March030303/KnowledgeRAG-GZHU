/* eslint-disable @typescript-eslint/no-explicit-any */
import { defineStore } from 'pinia'
import { get, post } from '@/utils/ASFaxios'
import { MessagePlugin } from 'tdesign-vue-next'

// ── 用户数据缓存 TTL（5 分钟，与路由守卫一致）─────────────────
const USER_CACHE_TTL_MS = 5 * 60 * 1000
let _lastFetchTime = 0

export const useDataUserStore = defineStore('dataUser', {
  state: () => {
    return {
      userData: {
        name: '未知',
        avatar:
          'https://avatars.githubusercontent.com/u/145737758?s=400&u=90eecb2edb0caf7cea2cd073d75270cbaa155cdf&v=4',
        signature: '未知', // 修正字段名保持一致
        email: '', // 添加 email 字段
        social_media: '', // 添加 social_media 字段
        role: '' // 角色
      }
    }
  },
  actions: {
    /**
     * 获取用户数据（带去重缓存）。
     *
     * 策略：
     * 1. 如果 Pinia state 已有数据且在 TTL 内 → 直接返回，不发请求
     * 2. 如果 localStorage 有 user_info（登录时写入的）→ 先用它初始化 state，
     *    再后台刷新（避免 UI 闪烁）
     * 3. 否则 → 远程获取
     */
    async fetchUserData(forceRefresh = false) {
      // 去重：短时间内不重复请求（除非强制刷新）
      if (
        !forceRefresh &&
        this.userData.name !== '未知' &&
        Date.now() - _lastFetchTime < USER_CACHE_TTL_MS
      ) {
        return this.userData
      }

      // 尝试从 localStorage 读取（登录成功后写入的）
      const cachedInfo = localStorage.getItem('user_info')
      if (cachedInfo && this.userData.name === '未知') {
        try {
          const parsed = JSON.parse(cachedInfo)
          this.userData = {
            name: parsed.name || '未知',
            avatar: parsed.avatar || this.userData.avatar,
            signature: parsed.signature || '',
            email: parsed.email || '',
            social_media: parsed.social_media || '',
            role: parsed.role || ''
          }
          _lastFetchTime = Date.now()
          // 有缓存就先用着，不阻塞
        } catch {
          // JSON 解析失败，走远程
        }
      }

      // 远程获取最新数据
      try {
        const response = await get<any>('/api/user/GetUserData')
        this.userData = response.data
        _lastFetchTime = Date.now()

        // 同步到 localStorage，供其他组件/页面使用
        localStorage.setItem('user_info', JSON.stringify(response.data))
        if (response.data?.role) {
          localStorage.setItem('user_role', response.data.role)
        }

        console.log('API Response:', response.data)
        return response.data
      } catch (_error) {
        // 如果已有缓存数据（哪怕是旧的），静默失败不打扰用户
        if (this.userData.name !== '未知') {
          console.debug('[useDataUser] 远程获取失败，使用缓存数据')
          return this.userData
        }
        // 单用户模式下无缓存时静默使用默认数据，不弹出错误
        console.debug('[useDataUser] 获取用户数据失败，使用默认数据')
        return this.userData
      }
    },
    async updateUserData(name: string, avatar: string, signature: string) {
      // 修改参数名保持一致
      try {
        const data = new FormData()
        data.append('name', name)
        data.append('avatar', avatar)
        data.append('signature', signature) // 修改字段名保持一致
        data.append('email', this.userData.email) // 添加 email 字段
        data.append('social_media', this.userData.social_media) // 添加 social_media 字段
        console.log('FormData:', data) // 更好的方式来查看FormData内容
        const response = await post<any>('/api/UpdateUserData', data)
        MessagePlugin.success('更新用户数据成功！')
        this.userData = response.data

        console.log('API Response:', response.data)
        // 触发整个页面的刷新
        window.location.reload()
      } catch (_error) {
        MessagePlugin.error('更新用户数据失败！')
      }
    }
  }
})
