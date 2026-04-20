<template>
  <t-config-provider :global-config="{ classPrefix: 't' }">
    <ErrorBoundary>
      <!-- 路由切换顶部进度条 -->
      <div v-if="pageLoading" class="page-loading-bar" />
      <!-- 登录页：不显示侧边栏 -->
      <div v-if="!showSidebar" class="app-fullpage">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
      <!-- 主应用布局：左侧导航 + 右侧内容 -->
      <div v-else class="app-layout">
        <SideBar @openSearch="openSearch" @quickCreate="handleQuickCreate" />
        <main class="app-main" ref="mainRef">
          <router-view v-slot="{ Component }">
            <transition
              name="page"
              mode="out-in"
              @before-enter="onPageBeforeEnter"
              @after-enter="onPageAfterEnter"
            >
              <component :is="Component" />
            </transition>
          </router-view>
        </main>
      </div>
    </ErrorBoundary>
    <!-- 全局快捷搜索 -->
    <GlobalSearch :visible="searchVisible" @close="searchVisible = false" />
    <!-- 右侧智能助理（登录后显示） -->
    <SmartAssistant v-if="showSidebar" />
    <!-- 回到顶部 FAB -->
    <BackToTop v-if="showSidebar" />
    <!-- 全局评测进度浮层（评测运行时始终可见） -->
    <div v-if="showSidebar && evalStore.isRunning" class="eval-toast-bar" @click="goToEval">
      <span class="eval-toast-spinner"></span>
      <span class="eval-toast-text">{{
        evalStore.progress || `正在评测 ${evalStore.models}...`
      }}</span>
      <span class="eval-toast-link">查看详情 →</span>
    </div>
    <!-- 全局快速新建知识库弹窗 -->
    <teleport to="body">
      <div v-if="quickCreateVisible" class="qc-overlay" @click.self="quickCreateVisible = false">
        <div class="qc-card">
          <div class="qc-header">
            <span class="qc-icon">📚</span>
            <h3>新建知识库</h3>
            <button class="qc-close" @click="quickCreateVisible = false">✕</button>
          </div>
          <input
            v-model="quickCreateName"
            class="qc-input"
            placeholder="输入知识库名称..."
            @keydown.enter="doQuickCreate"
            @keydown.esc="quickCreateVisible = false"
            ref="quickCreateInputRef"
          />
          <div class="qc-footer">
            <button class="qc-btn-cancel" @click="quickCreateVisible = false">取消</button>
            <button
              class="qc-btn-confirm"
              @click="doQuickCreate"
              :disabled="!quickCreateName.trim()"
            >
              创建知识库
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </t-config-provider>
</template>
<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, ref, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import SideBar from './components/SideBar.vue'
import GlobalSearch from './components/GlobalSearch.vue'
import ErrorBoundary from './components/ErrorBoundary.vue'
import SmartAssistant from './components/SmartAssistant.vue'
import BackToTop from './components/BackToTop.vue'
import { initInteractions } from './composables/useInteractions'
import { applyAllAppearance } from './composables/useTheme'
import { setLocale } from './i18n/index'
import { useEvalStore } from './store'
import { MessagePlugin } from 'tdesign-vue-next'
import '@/assets/scroll.css'
import '@/styles/animations.css'
const route = useRoute()
const router = useRouter()
// 评测全局状态
const evalStore = useEvalStore()
const goToEval = () => router.push('/settings')
// 不需要显示侧边栏的路由（登录/注册页）
const hideSidebarRoutes = ['/LogonOrRegister']
const showSidebar = computed(() => !hideSidebarRoutes.includes(route.path))
// 全局搜索开关
const searchVisible = ref(false)
const openSearch = () => {
  searchVisible.value = true
}
// ── 全局快速新建知识库 ─────────────────────────────────────
const quickCreateVisible = ref(false)
const quickCreateName = ref('')
const quickCreateInputRef = ref<HTMLInputElement | null>(null)
async function handleQuickCreate() {
  quickCreateName.value = ''
  quickCreateVisible.value = true
  await nextTick()
  quickCreateInputRef.value?.focus()
}
async function doQuickCreate() {
  const name = quickCreateName.value.trim()
  if (!name) return
  try {
    const formData = new FormData()
    formData.append('kbName', name)
    // 绑定 owner_id
    const userInfo = (() => {
      try {
        return JSON.parse(localStorage.getItem('user_info') || '{}')
      } catch {
        return {}
      }
    })()
    const ownerId = userInfo.id || userInfo.email || ''
    if (ownerId) formData.append('owner_id', ownerId)
    await axios.post('/api/create-knowledgebase/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    MessagePlugin.success(`知识库「${name}」创建成功 🎉`)
    quickCreateVisible.value = false
    // 若当前在知识库页面，刷新列表
    if (route.path === '/knowledge') {
      router.go(0)
    } else {
      router.push('/knowledge')
    }
  } catch (e: any) {
    if (e.response?.status === 400) {
      MessagePlugin.error('知识库名称已存在')
    } else {
      MessagePlugin.error('创建失败，请稍后重试')
    }
  }
}
// 页面切换顶部进度条
const pageLoading = ref(false)
router.beforeEach(() => {
  pageLoading.value = true
})

router.afterEach(() => {
  setTimeout(() => {
    pageLoading.value = false
  }, 350)
})
// 路由切换后触发动效初始化
const onPageBeforeEnter = () => {
  /* 页面开始进入 */
}
const onPageAfterEnter = () => {
  // DOM 就绪后重新扫描 reveal 元素 & 注入 ripple
  setTimeout(() => initInteractions(), 50)
}
// 主内容区 ref（用于 BackToTop 的滚动监听）
const mainRef = ref<HTMLElement | null>(null)
// 全局 Ctrl+K 快捷键
const handleKeydown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    searchVisible.value = true
  }
}
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  // ── 恢复外观设置（统一由 useTheme 管理，单一数据源）──
  applyAllAppearance()
  // ── 初始化语言设置（确保默认语言在每次启动时生效）──
  const savedLocale = localStorage.getItem('locale') as 'zh' | 'en' | null
  if (savedLocale && (savedLocale === 'zh' || savedLocale === 'en')) {
    setLocale(savedLocale)
  }
  // ── 初始化全局交互动效 ──
  initInteractions(router)
})
onUnmounted(() => document.removeEventListener('keydown', handleKeydown))
</script>
<style>
* {
  box-sizing: border-box;
}
html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
}
#app {
  height: 100vh;
  width: 100vw;
}
.app-fullpage {
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-base);
}
.qc-overlay {
  position: fixed;
  inset: 0;
  z-index: 9000;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: qc-fade-in 0.12s ease;
}
@keyframes qc-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
.qc-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  border-radius: var(--radius-xl);
  padding: 24px;
  width: 400px;
  box-shadow: var(--shadow-lg);
  animation: qc-slide-up 0.2s var(--ease-spring);
}
@keyframes qc-slide-up {
  from {
    transform: translateY(16px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
.qc-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.qc-icon {
  font-size: 20px;
}
.qc-header h3 {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}
.qc-close {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-quaternary);
  width: 26px;
  height: 26px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}
.qc-close:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}
.qc-input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--border-base);
  border-radius: var(--radius-md);
  font-size: 13.5px;
  outline: none;
  box-sizing: border-box;
  background: var(--bg-elevated);
  color: var(--text-primary);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.qc-input:focus {
  border-color: var(--border-brand);
  box-shadow: 0 0 0 2px var(--accent-violet-subtle);
}
.qc-input::placeholder {
  color: var(--text-quaternary);
}
.qc-footer {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 16px;
}
.qc-btn-cancel {
  padding: 7px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-base);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  transition: all var(--transition-fast);
}
.qc-btn-cancel:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.qc-btn-confirm {
  padding: 7px 18px;
  border-radius: var(--radius-sm);
  border: none;
  background: var(--gradient-brand);
  color: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-glow);
}
.qc-btn-confirm:hover:not(:disabled) {
  filter: brightness(1.12);
  box-shadow: var(--shadow-glow-strong);
  transform: translateY(-1px);
}
.qc-btn-confirm:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-base);
  overflow: hidden;
}
.app-main {
  flex: 1;
  height: 100vh;
  overflow: hidden;
  min-width: 0;
}
.page-enter-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s var(--ease-out);
}
.page-leave-active {
  transition:
    opacity 0.14s ease,
    transform 0.14s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
.eval-toast-bar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-overlay);
  border: 1px solid var(--border-base);
  color: var(--text-primary);
  padding: 8px 16px;
  border-radius: var(--radius-full);
  font-size: 12px;
  z-index: 9999;
  cursor: pointer;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(16px);
  animation: toastIn 0.25s var(--ease-spring);
}
.eval-toast-bar:hover {
  background: var(--bg-hover);
  border-color: var(--border-active);
}
@keyframes toastIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}
.eval-toast-spinner {
  width: 12px;
  height: 12px;
  border: 1.5px solid var(--border-base);
  border-top-color: var(--accent-violet-light);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.eval-toast-text {
  flex: 1;
  white-space: nowrap;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.eval-toast-link {
  color: var(--accent-violet-light);
  font-weight: 550;
  flex-shrink: 0;
}
.page-loading-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-brand);
  z-index: 10000;
  animation: loadingBar 0.8s ease-out forwards;
}
@keyframes loadingBar {
  from { width: 0; }
  to { width: 100%; }
}
</style>
