import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import TDesign from 'tdesign-vue-next';
import './assets/tailwind.css';
import pinia from './store' // 导入 Pinia 实例
import TDesignChat from '@tdesign-vue-next/chat'; // 引入chat组件
import 'tdesign-vue-next/es/style/index.css'; // 引入少量全局样式变量

// ── 全局 axios JWT 拦截器（所有 import axios from 'axios' 的文件自动生效）──
import axios from 'axios';

// 动态读取最新 token（每次请求都读 localStorage，避免模块加载时 token 为空）
const getAuthToken = (): string => {
  try {
    if (typeof localStorage !== 'undefined' && localStorage.getItem) {
      const token = localStorage.getItem('jwt');
      if (token) return `Bearer ${token}`;
    }
  } catch {}
  return '';
};

// 请求拦截：注入 Authorization 头
axios.interceptors.request.use((config) => {
  const auth = getAuthToken();
  if (auth && config.headers) {
    config.headers.Authorization = auth;
  }
  return config;
});

// 响应拦截：统一处理 401
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      // Token 过期或无效时清除并跳转登录页
      try { localStorage.removeItem('jwt'); } catch {}
      const currentPath = window.location.pathname;
      if (!currentPath.includes('/login') && !currentPath.includes('/register')) {
        window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
      }
    }
    return Promise.reject(error);
  }
);



const app = createApp(App);

// 启用Devtools (在开发和生产环境中)
//app.config.devtools = true
app.config.performance = true

app.use(TDesignChat);
app.use(TDesign);
app.use(router);
app.use(pinia); // 使用 Pinia 实例
app.mount('#app');
