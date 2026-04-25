// file: apiClient.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios'

const getAuthHeader = (): string => {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('jwt') : ''
  return token ? `Bearer ${token}` : ''
}

const apiClient: AxiosInstance = axios.create({
  // baseURL: 'https://your-api.com/v1',
  timeout: 10000, // 请求超时时间
  headers: {
    'Content-Type': 'application/json', // 默认请求头
    Accept: 'application/json'
  }
})

// 每次请求动态注入最新的 JWT（解决模块加载时 token 为空的 401 问题）
apiClient.interceptors.request.use(config => {
  const auth = getAuthHeader()
  if (auth) config.headers.Authorization = auth
  return config
})

// ── 全局响应错误处理 ──────────────────────────────────────────────
// 统一处理 401/403 等状态码，避免每个组件单独处理

let _isRedirectingToLogin = false // 防止多个 401 并发时多次跳转

apiClient.interceptors.response.use(
  response => response,
  async (error: AxiosError) => {
    const status = error.response?.status
    const url = error.config?.url || ''

    // 401：未认证 → 清除 token，跳转登录页（只跳一次）
    if (status === 401 && !_isRedirectingToLogin) {
      _isRedirectingToLogin = true
      console.warn(`[API] 401 未授权 (${url})，即将跳转登录页`)
      localStorage.removeItem('jwt')
      // 延迟一小段时间，确保当前所有并发请求都已完成
      setTimeout(() => {
        _isRedirectingToLogin = false
        // 如果不在登录页才跳转，避免循环
        if (!window.location.pathname.includes('/LogonOrRegister')) {
          window.location.href = `/LogonOrRegister?redirect=${encodeURIComponent(window.location.pathname)}`
        }
      }, 300)
      return Promise.reject(error)
    }

    // 403：无权限 → 提示用户（不自动跳转，可能只是功能不可用）
    if (status === 403) {
      console.warn(`[API] 403 无权限 (${url})`)
      // 不阻断，让调用方决定如何展示
    }

    // 500+：服务端错误 → 打日志但不弹窗打扰用户
    if (status && status >= 500) {
      console.error(`[API] 服务端错误 ${status} (${url})`, error.response?.data)
    }

    // 网络错误 / 超时
    if (!status && error.message) {
      console.debug(`[API] 网络/超时错误: ${error.message}`)
    }

    return Promise.reject(error)
  }
)

const request = async <T>(config: AxiosRequestConfig): Promise<T> => {
  try {
    const response = await apiClient.request<T>(config)
    return response.data
  } catch (error) {
    const axiosError = error as AxiosError
    // 在这里可以进行更统一的错误处理，例如上报错误、根据状态码跳转等
    console.error(
      `API Error [${config.method?.toUpperCase()} ${config.url}]:`,
      axiosError.response?.data || axiosError.message
    )
    throw axiosError.response?.data || new Error('Network Error')
  }
}

export const get = <T>(url: string, params?: object): Promise<T> => {
  return request<T>({ method: 'get', url, params })
}

export const post = <T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'post', url, data, ...config })
}

export const postMultipart = <T>(url: string, formData: FormData): Promise<T> => {
  return request<T>({
    method: 'post',
    url,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const put = <T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'put', url, data, ...config })
}

export const del = <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'delete', url, ...config })
}

// 默认导出所有方法，方便统一引入
export default {
  get,
  post,
  put,
  del
}
