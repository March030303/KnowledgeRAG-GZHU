// file: apiClient.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';

const getAuthHeader = (): string => {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('jwt') : '';
  return token ? `Bearer ${token}` : '';
};

const apiClient: AxiosInstance = axios.create({
  // baseURL: 'https://your-api.com/v1',
  timeout: 10000, // 请求超时时间
  headers: {
    'Content-Type': 'application/json', // 默认请求头
    'Accept': 'application/json'
  }
});

// 每次请求动态注入最新的 JWT（解决模块加载时 token 为空的 401 问题）
apiClient.interceptors.request.use((config) => {
  const auth = getAuthHeader();
  if (auth) config.headers.Authorization = auth;
  return config;
});

const request = async <T>(config: AxiosRequestConfig): Promise<T> => {
  try {
    const response = await apiClient.request<T>(config);
    return response.data;
  } catch (error) {
    const axiosError = error as AxiosError;
    // 在这里可以进行更统一的错误处理，例如上报错误、根据状态码跳转等
    console.error(`API Error [${config.method?.toUpperCase()} ${config.url}]:`, axiosError.response?.data || axiosError.message);
    throw axiosError.response?.data || new Error('Network Error');
  }
};



export const get = <T>(url: string, params?: object): Promise<T> => {
  return request<T>({ method: 'get', url, params });
};

export const post = <T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'post', url, data, ...config });
};

export const postMultipart = <T>(url: string, formData: FormData): Promise<T> => {
  return request<T>({
    method: 'post',
    url,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const put = <T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'put', url, data, ...config });
};


export const del = <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>({ method: 'delete', url, ...config });
};

// 默认导出所有方法，方便统一引入
export default {
  get,
  post,
  put,
  del,
};
