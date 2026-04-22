<template>
  <div id="nova-app">
    <!-- ═══ 粒子背景层 ═══ -->
    <div class="nova-particle-bg">
      <div class="nova-particle-orb" />
    </div>
    <div class="nova-grid-overlay" />

    <!-- 路由进度条 -->
    <transition name="progress">
      <div v-if="pageLoading" class="nova-progress-bar">
        <div class="nova-progress-bar__inner" />
      </div>
    </transition>

    <!-- 登录页：无侧边栏 -->
    <div v-if="!showSidebar" class="nova-fullscreen">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <!-- 主布局：侧边栏 + 内容区 -->
    <template v-else>
      <NovaSidebar ref="sidebarRef" />
      
      <main class="nova-main" ref="mainRef">
        <router-view v-slot="{ Component }">
          <transition name="page-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </template>

    <!-- 全局搜索 (Ctrl+K) -->
    <GlobalSearch :visible="searchVisible" @close="searchVisible = false" />

    <!-- 快速新建知识库 -->
    <teleport to="body">
      <transition name="modal-glow">
        <div
          v-if="quickCreateVisible"
          class="nova-modal-overlay"
          @click.self="quickCreateVisible = false"
        >
          <div class="nova-modal-card nova-animate-in">
            <!-- 发光装饰 -->
            <div class="nova-modal-card__glow" />
            
            <header class="nova-modal-header">
              <div class="nova-modal-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                  <line x1="12" y1="6" x2="12" y2="14"/>
                  <line x1="8" y1="10" x2="16" y2="10"/>
                </svg>
              </div>
              <h3>新建知识库</h3>
              <button class="nova-modal-close" @click="quickCreateVisible = false">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </header>

            <div class="nova-modal-body">
              <input
                ref="quickCreateInputRef"
                v-model="quickCreateName"
                type="text"
                class="nova-modal-input"
                placeholder="输入知识库名称..."
                @keydown.enter="doQuickCreate"
                @keydown.esc="quickCreateVisible = false"
              />
            </div>

            <footer class="nova-modal-footer">
              <NovaButton variant="ghost" size="sm" @click="quickCreateVisible = false">取消</NovaButton>
              <NovaButton 
                variant="primary" 
                size="sm" 
                :disabled="!quickCreateName.trim()" 
                @click="doQuickCreate"
              >
                创建知识库
              </NovaButton>
            </footer>
          </div>
        </div>
      </transition>
    </teleport>

    <!-- 评测浮层 -->
    <transition name="toast-up">
      <div v-if="evalStore.isRunning" class="nova-toast-bar" @click="goToEval">
        <span class="nova-toast-spinner" />
        <span>{{ evalStore.progress || `正在评测 ${evalStore.models}...` }}</span>
        <span class="nova-toast-action">查看详情 →</span>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

import NovaSidebar from './components/nova/NovaSidebar.vue'
import NovaButton from './components/nova/NovaButton.vue'
import GlobalSearch from './components/GlobalSearch.vue'
import { initInteractions } from './composables/useInteractions'
import { applyAllAppearance } from './composables/useTheme'
import { setLocale } from './i18n/index'
import { useEvalStore } from './store'

import './styles/nova.css'

const route = useRoute()
const router = useRouter()
const evalStore = useEvalStore()
const goToEval = () => router.push('/settings')

// ── 侧边栏控制 ──
const hideSidebarRoutes = ['/LogonOrRegister']
const showSidebar = computed(() => !hideSidebarRoutes.includes(route.path))

// ── 全局搜索 ──
const searchVisible = ref(false)
const openSearch = () => { searchVisible.value = true }

// ── 快速新建知识库 ──
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
    const userInfo = (() => {
      try { return JSON.parse(localStorage.getItem('user_info') || '{}') }
      catch { return {} }
    })()
    const ownerId = userInfo.id || userInfo.email || ''
    if (ownerId) formData.append('owner_id', ownerId)

    await axios.post('/api/create-knowledgebase/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    alert(`知识库「${name}」创建成功 🎉`)
    quickCreateVisible.value = false
    route.path === '/knowledge' ? router.go(0) : router.push('/knowledge')
  } catch (e: any) {
    alert(e.response?.status === 400 ? '知识库名称已存在' : '创建失败，请稍后重试')
  }
}

// ── 页面切换进度条 ──
const pageLoading = ref(false)
router.beforeEach(() => { pageLoading.value = true })
router.afterEach(() => { setTimeout(() => { pageLoading.value = false }, 350) })

// ── Refs & 快捷键 ──
const mainRef = ref<HTMLElement | null>(null)
const sidebarRef = ref<InstanceType<typeof NovaSidebar> | null>(null)

const handleKeydown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    searchVisible.value = true
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  applyAllAppearance()
  const savedLocale = localStorage.getItem('locale') as 'zh' | 'en' | null
  if (savedLocale && (savedLocale === 'zh' || savedLocale === 'en')) setLocale(savedLocale)
  void initInteractions(router)
})

onUnmounted(() => document.removeEventListener('keydown', handleKeydown))

defineExpose({ openSearch, handleQuickCreate })
</script>

<style>
/* ============================================
   NOVA App — 全局应用样式 v2.0 Game-Grade
   ============================================ */

#nova-app {
  display: flex;
  min-height: 100vh;
  background: var(--nova-bg-deep);
  position: relative;
  overflow-x: hidden;
}

/* 登录页 */
.nova-fullscreen {
  height: 100vh;
  width: 100vw;
  overflow-y: auto;
}

/* 主内容区 */
.nova-main {
  flex: 1;
  height: 100vh;
  overflow: hidden auto;
  min-width: 0;
  position: relative;

  /* 滚动条隐藏但保留滚动功能（可选） */
  /* scrollbar-width: none; */
  /* &::-webkit-scrollbar { display: none; } */
}

/* ═══ 进度条 ═══ */
.nova-progress-bar {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 3px;
  z-index: var(--nova-z-maximum);
  background: rgba(99, 102, 241, 0.08);
}

.nova-progress-bar__inner {
  height: 100%;
  width: 30%;
  background: var(--nova-gradient-brand);
  border-radius: 0 var(--radius-full) var(--radius-full) 0;
  animation: progressSlide 0.8s ease-in-out infinite alternate;
  box-shadow: 0 0 14px rgba(99, 102, 241, 0.5), 0 0 28px rgba(139, 92, 246, 0.3);
}

@keyframes progressSlide {
  from { transform: translateX(-100%); }
  to { transform: translateX(350%); }
}

/* ═══ 页面过渡 ═══ */
.page-fade-enter-active,
.page-fade-leave-active,
.page-slide-enter-active,
.page-slide-leave-active {
  transition: all var(--nova-duration-page) var(--nova-ease-out-expo);
}
.page-fade-enter-from,
.page-fade-leave-to { opacity: 0; }

.page-slide-enter-from {
  opacity: 0;
  transform: translateX(24px) scale(0.98);
}
.page-slide-leave-to {
  opacity: 0;
  transform: translateX(-16px) scale(0.99);
}

/* 进度条过渡 */
.progress-enter-active,
.progress-leave-active { transition: opacity 0.25s ease; }
.progress-enter-from,
.progress-leave-to { opacity: 0; }

/* ═══ 弹窗样式 ═══ */
.nova-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--nova-z-modal);
  background: rgba(3, 7, 18, 0.75);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--nova-space-4);
}

.nova-modal-card {
  position: relative;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(28px) saturate(1.4);
  -webkit-backdrop-filter: blur(28px) saturate(1.4);
  border: 1px solid rgba(148, 163, 184, 0.1);
  border-radius: var(--radius-2xl);
  width: 100%;
  max-width: 420px;
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.5),
    0 0 60px rgba(99, 102, 241, 0.08),
    inset 0 1px 0 rgba(255,255,255,0.04);
  overflow: hidden;
}

.nova-modal-card__glow {
  position: absolute;
  top: -120px; left: 50%;
  transform: translateX(-50%);
  width: 300px; height: 200px;
  background: radial-gradient(ellipse, rgba(99,102,241,0.15), transparent 70%);
  pointer-events: none;
}

.nova-modal-header {
  display: flex;
  align-items: center;
  gap: var(--nova-space-3);
  padding: var(--nova-space-6) var(--nova-space-6) 0;
  position: relative;
}

.nova-modal-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px; height: 44px;
  background: var(--nova-gradient-brand);
  border-radius: var(--radius-lg);
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.nova-modal-header h3 {
  flex: 1;
  font-size: var(--nova-text-lg);
  font-weight: var(--nova-font-semibold);
  color: var(--nova-text-primary);
  margin: 0;
}

.nova-modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px; height: 32px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--nova-text-muted);
  cursor: pointer;
  transition: all var(--nova-duration-fast) ease;

  &:hover {
    background: rgba(239, 68, 68, 0.12);
    color: var(--nova-error);
  }
}

.nova-modal-body {
  padding: var(--nova-space-6);
}

.nova-modal-input {
  width: 100%;
  padding: var(--nova-space-4) var(--nova-space-4);
  font-size: var(--nova-text-base);
  font-family: var(--nova-font-display);
  color: var(--nova-text-primary);
  background: rgba(3, 7, 18, 0.5);
  border: 1.5px solid rgba(148, 163, 184, 0.12);
  border-radius: var(--radius-xl);
  outline: none;
  transition: all var(--nova-duration-fast) ease;

  &::placeholder { color: var(--nova-text-muted); }

  &:focus {
    border-color: rgba(99, 102, 241, 0.5);
    box-shadow: 
      0 0 0 3px rgba(99, 102, 241, 0.08),
      0 0 20px rgba(99, 102, 241, 0.06);
  }
}

.nova-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--nova-space-3);
  padding: 0 var(--nova-space-6) var(--nova-space-6);
  background: rgba(3, 7, 18, 0.3);
}

/* 弹窗过渡 */
.modal-glow-enter-active .nova-modal-card {
  animation: novaBounceIn var(--nova-duration-slower) var(--nova-ease-spring);
}
.modal-glow-leave-active .nova-modal-card {
  animation: modalFadeOut var(--nova-duration-normal) ease forwards;
}
.modal-glow-enter-active,
.modal-glow-leave-active {
  transition: opacity var(--nova-duration-normal) ease;
}
.modal-glow-enter-from,
.modal-glow-leave-to { opacity: 0; }
@keyframes modalFadeOut {
  to { opacity: 0; transform: scale(0.95) translateY(10px); }
}

/* ═══ Toast 浮层 ═══ */
.nova-toast-bar {
  position: fixed;
  bottom: var(--nova-space-8);
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--nova-z-toast);
  display: flex;
  align-items: center;
  gap: var(--nova-space-3);
  padding: var(--nova-space-3) var(--nova-space-6);
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: var(--radius-full);
  font-size: var(--nova-text-sm);
  color: var(--nova-info);
  cursor: pointer;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(99, 102, 241, 0.1);

  &:hover {
    border-color: rgba(99, 102, 241, 0.4);
    box-shadow:
      0 12px 40px rgba(0, 0, 0, 0.45),
      0 0 50px rgba(99, 102, 241, 0.15);
  }
}

.nova-toast-spinner {
  width: 16px; height: 16px;
  border: 2px solid transparent;
  border-top-color: var(--nova-info);
  border-right-color: var(--nova-info);
  border-radius: 50%;
  animation: novaSpin 0.75s linear infinite;
  flex-shrink: 0;
}

.nova-toast-action {
  color: #a5b4fc;
  font-weight: var(--nova-font-semibold);
  flex-shrink: 0;
}

/* Toast 过渡 */
.toast-up-enter-active,
.toast-up-leave-active {
  transition: all var(--nova-duration-slow) var(--nova-ease-out-expo);
}
.toast-up-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
.toast-up-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px) scale(0.96);
}
</style>
