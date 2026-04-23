<template>
  <aside :class="['sidebar', { 'sidebar--collapsed': isCollapsed }]">
    <!-- Logo区域 -->
    <div class="sidebar__logo">
      <div class="sidebar__logo-icon">
        <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="32" height="32" rx="8" fill="url(#grad)" />
          <path
            d="M8 10h10M8 16h14M8 22h10"
            stroke="white"
            stroke-width="2.2"
            stroke-linecap="round"
          />
          <defs>
            <linearGradient id="grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
              <stop stop-color="#4f7ef8" />
              <stop offset="1" stop-color="#8b5cf6" />
            </linearGradient>
          </defs>
        </svg>
      </div>
      <transition name="fade-text">
        <span v-if="!isCollapsed" class="sidebar__logo-text">RAGF-01</span>
      </transition>
      <!-- 折叠按钮 -->
      <button
        class="sidebar__collapse-btn"
        @click="toggleCollapse"
        :title="isCollapsed ? '展开侧边栏' : '折叠侧边栏'"
      >
        <svg
          :class="['collapse-icon', { 'rotate-180': isCollapsed }]"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
    </div>

    <!-- 快速新建按钮 -->
    <div class="sidebar__quick-action">
      <button
        class="quick-new-btn"
        @click="emit('quickCreate')"
        :title="isCollapsed ? '新建知识库' : ''"
      >
        <svg
          class="quick-new-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        <transition name="fade-text">
          <span v-if="!isCollapsed">快速新建</span>
        </transition>
      </button>
    </div>

    <!-- 主导航菜单 -->
    <nav class="sidebar__nav">
      <div class="sidebar__nav-section">
        <transition name="fade-text">
          <p v-if="!isCollapsed" class="sidebar__nav-label">主要功能</p>
        </transition>
        <ul class="sidebar__nav-list">
          <li v-for="item in mainNavItems" :key="item.path">
            <t-tooltip
              :content="isCollapsed ? item.label : ''"
              placement="right"
              :show-arrow="false"
            >
              <button
                :class="['nav-item', { 'nav-item--active': isActive(item.path) }]"
                @click="navigateTo(item.path)"
              >
                <span class="nav-item__icon" v-html="item.icon"></span>
                <transition name="fade-text">
                  <span v-if="!isCollapsed" class="nav-item__label">{{ item.label }}</span>
                </transition>
                <transition name="fade-text">
                  <span v-if="!isCollapsed && item.badge" class="nav-item__badge">{{
                    item.badge
                  }}</span>
                </transition>
              </button>
            </t-tooltip>
          </li>
        </ul>
      </div>

      <div class="sidebar__nav-section">
        <transition name="fade-text">
          <p v-if="!isCollapsed" class="sidebar__nav-label">工具</p>
        </transition>
        <ul class="sidebar__nav-list">
          <li v-for="item in toolNavItems" :key="item.path">
            <t-tooltip
              :content="isCollapsed ? item.label : ''"
              placement="right"
              :show-arrow="false"
            >
              <button
                :class="['nav-item', { 'nav-item--active': isActive(item.path) }]"
                @click="navigateTo(item.path)"
              >
                <span class="nav-item__icon" v-html="item.icon"></span>
                <transition name="fade-text">
                  <span v-if="!isCollapsed" class="nav-item__label">{{ item.label }}</span>
                </transition>
              </button>
            </t-tooltip>
          </li>
        </ul>
      </div>
    </nav>

    <!-- 底部区域 -->
    <div class="sidebar__footer">
      <!-- 快捷搜索提示 -->
      <transition name="fade-text">
        <button v-if="!isCollapsed" class="shortcut-hint" @click="emit('openSearch')">
          <svg
            class="shortcut-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="11" cy="11" r="8" />
            <path stroke-linecap="round" d="M21 21l-4.35-4.35" />
          </svg>
          <span>搜索</span>
          <kbd>Ctrl K</kbd>
        </button>
      </transition>
      <t-tooltip :content="isCollapsed ? '搜索 Ctrl+K' : ''" placement="right" :show-arrow="false">
        <button v-if="isCollapsed" class="nav-item" @click="emit('openSearch')">
          <span class="nav-item__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8" />
              <path stroke-linecap="round" d="M21 21l-4.35-4.35" />
            </svg>
          </span>
        </button>
      </t-tooltip>

      <!-- 语言切换 -->
      <t-tooltip
        :content="isCollapsed ? (locale === 'zh' ? 'Switch to English' : '切换中文') : ''"
        placement="right"
        :show-arrow="false"
      >
        <button
          class="nav-item"
          @click="handleToggleLocale"
          :title="locale === 'zh' ? 'Switch to English' : '切换中文'"
        >
          <span class="nav-item__icon" style="font-size: 15px">🌐</span>
          <transition name="fade-text">
            <span v-if="!isCollapsed" class="nav-item__label" style="font-size: 12px">{{
              locale === 'zh' ? 'EN' : '中文'
            }}</span>
          </transition>
        </button>
      </t-tooltip>

      <!-- GitHub链接 -->
      <t-tooltip :content="isCollapsed ? 'GitHub仓库' : ''" placement="right" :show-arrow="false">
        <button class="nav-item" @click="openGitHub" title="GitHub仓库">
          <span class="nav-item__icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
              />
            </svg>
          </span>
          <transition name="fade-text">
            <span v-if="!isCollapsed" class="nav-item__label">GitHub</span>
          </transition>
        </button>
      </t-tooltip>

      <!-- App下载 -->
      <t-tooltip
        :content="isCollapsed ? '下载移动端 App' : ''"
        placement="right"
        :show-arrow="false"
      >
        <button class="nav-item nav-item--download" @click="openAppDownload" title="下载移动端 App">
          <span class="nav-item__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
              <line x1="12" y1="18" x2="12" y2="18.01" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 11l4 4 4-4M12 7v8" />
            </svg>
          </span>
          <transition name="fade-text">
            <span v-if="!isCollapsed" class="nav-item__label">下载 App</span>
          </transition>
        </button>
      </t-tooltip>

      <!-- 用户信息 -->
      <t-dropdown :min-column-width="160" trigger="click" placement="right-bottom">
        <div :class="['user-info', { 'user-info--collapsed': isCollapsed }]">
          <t-avatar
            :image="userAvatar"
            :hide-on-load-failed="false"
            size="small"
            class="user-avatar"
          />
          <transition name="fade-text">
            <div v-if="!isCollapsed" class="user-meta">
              <span class="user-name">{{ userName }}</span>
              <span class="user-email">{{ userEmail }}</span>
            </div>
          </transition>
          <transition name="fade-text">
            <svg
              v-if="!isCollapsed"
              class="user-chevron"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </transition>
        </div>
        <template #dropdown>
          <t-dropdown-menu>
            <t-dropdown-item @click="navigateTo('/user/userInfo')">
              <t-icon name="user" />
              <span class="ml-2">个人中心</span>
            </t-dropdown-item>
            <t-dropdown-item @click="navigateTo('/devtools')">
              <t-icon name="code" />
              <span class="ml-2">开发者模式</span>
            </t-dropdown-item>
            <t-dropdown-item divided @click="logout" class="text-red-500">
              <t-icon name="logout" />
              <span class="ml-2">退出登录</span>
            </t-dropdown-item>
          </t-dropdown-menu>
        </template>
      </t-dropdown>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { useDataUserStore } from '@/store'
import API_ENDPOINTS from '@/utils/apiConfig'
import { useI18n, locale as _locale } from '@/i18n'

const { toggleLocale } = useI18n()

// 使用原始 _locale ref 确保响应式
const locale = _locale

// 包装 toggleLocale，切换后强制刷新页面上依赖 locale 的文字
const handleToggleLocale = () => {
  toggleLocale()
  MessagePlugin.success(locale.value === 'en' ? 'Language: English' : '语言：中文')
}

const emit = defineEmits<{
  (event: 'openSearch'): void
  (event: 'quickCreate'): void
}>()

const router = useRouter()
const route = useRoute()
const userStore = useDataUserStore()
const isCollapsed = ref(false)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const isActive = (path: string) => {
  if (path === '/chat') return route.path.startsWith('/chat')
  if (path === '/user') return route.path.startsWith('/user')
  return route.path === path || route.path.startsWith(path + '/')
}

const navigateTo = (path: string) => router.push(path)
const openGitHub = () =>
  window.open('https://github.com/March030303/KnowledgeRAG-GZHU/tree/master', '_blank')
const openAppDownload = () => window.open('/download', '_blank')

const logout = async () => {
  await router.push('/LogonOrRegister')
  MessagePlugin.success('已登出账号')
}

const userAvatar = computed(() => {
  if (!userStore.userData) return 'https://tdesign.gtimg.com/site/avatar.jpg'
  const avatar = userStore.userData?.avatar || ''
  if (avatar && avatar.startsWith('/static/')) return API_ENDPOINTS.USER.AVATAR(avatar)
  return avatar || 'https://tdesign.gtimg.com/site/avatar.jpg'
})

const userName = computed(() => {
  return userStore.userData?.name || userStore.userData?.email?.split('@')[0] || '用户'
})

const userEmail = computed(() => {
  const email = userStore.userData?.email || ''
  if (email.length > 18) return email.substring(0, 15) + '...'
  return email
})

onMounted(async () => {
  try {
    await userStore.fetchUserData()
  } catch (error) {
    console.debug('[SideBar] fetchUserData skipped', error)
  }
})

interface NavItem {
  path: string
  label: string
  icon: string
  badge?: string
}

// 主导航项
const mainNavItems: NavItem[] = [
  {
    path: '/knowledge',
    label: '知识库',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
    </svg>`
  },
  {
    path: '/square',
    label: '知识广场',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>`
  },
  {
    path: '/chat',
    label: 'AI 对话',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
    </svg>`
  },
  {
    path: '/agent',
    label: '任务模式',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v3M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
    </svg>`,
    badge: 'Beta'
  }
]

const toolNavItems: NavItem[] = [
  {
    path: '/history',
    label: '历史记录',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>`
  },
  {
    path: '/creation',
    label: '文档创作',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
    </svg>`,
    badge: 'New'
  },
  {
    path: '/files',
    label: '文件管理',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
    </svg>`
  },
  {
    path: '/service',
    label: '模型管理',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"/>
    </svg>`
  },
  {
    path: '/settings',
    label: '系统设置',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><circle cx="12" cy="12" r="3"/>
    </svg>`
  },
  {
    path: '/architecture',
    label: '系统架构',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"/>
    </svg>`
  }
]
</script>

<style scoped>
.sidebar {
  width: 220px;
  height: 100vh;
  background: var(--bg-surface);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.25s var(--ease-out);
  overflow: hidden;
  position: relative;
  z-index: 100;
}
.sidebar::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(180deg, rgba(124, 106, 255, 0.08) 0%, transparent 30%, transparent 70%, rgba(34, 211, 238, 0.05) 100%);
  pointer-events: none;
}

.sidebar--collapsed {
  width: 56px;
}

.sidebar__logo {
  display: flex;
  align-items: center;
  padding: 12px 10px 10px;
  border-bottom: 1px solid var(--border-subtle);
  gap: 8px;
  min-height: 52px;
  position: relative;
}

.sidebar__logo-icon {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}

.sidebar__logo-icon svg {
  width: 100%;
  height: 100%;
}

.sidebar__logo-text {
  font-size: 14px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-violet-light), var(--accent-cyan));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  white-space: nowrap;
  flex: 1;
}

.sidebar__collapse-btn {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-quaternary);
  transition: all var(--transition-fast);
  flex-shrink: 0;
  margin-left: auto;
}

.sidebar__collapse-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.collapse-icon {
  width: 14px;
  height: 14px;
  transition: transform 0.25s var(--ease-out);
}

.rotate-180 {
  transform: rotate(180deg);
}

.sidebar--collapsed .sidebar__logo {
  justify-content: center;
  padding: 12px 6px;
}
.sidebar--collapsed .sidebar__collapse-btn {
  position: absolute;
  right: 2px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
}

.sidebar__quick-action {
  padding: 8px 8px 4px;
}

.quick-new-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  border: 1px dashed rgba(124, 106, 255, 0.2);
  background: var(--accent-violet-subtle);
  color: var(--accent-violet-light);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  overflow: hidden;
  position: relative;
  will-change: transform;
}

.quick-new-btn:hover {
  background: rgba(124, 106, 255, 0.12);
  border-color: rgba(124, 106, 255, 0.35);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(124, 106, 255, 0.12);
}

.quick-new-btn:active {
  transform: translateY(0) scale(0.97) !important;
  box-shadow: none !important;
  transition-duration: 0.06s !important;
}

.quick-new-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  transition: transform 0.25s var(--ease-spring);
}

.quick-new-btn:hover .quick-new-icon {
  transform: rotate(90deg) scale(1.1);
}

.sidebar--collapsed .quick-new-btn {
  justify-content: center;
  padding: 6px;
}

.sidebar__nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 4px 0;
  scrollbar-width: none;
}
.sidebar__nav::-webkit-scrollbar {
  display: none;
}

.sidebar__nav-section {
  margin-bottom: 2px;
  padding: 0 6px;
}

.sidebar__nav-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-quaternary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 6px 8px 3px;
  white-space: nowrap;
  overflow: hidden;
}

.sidebar__nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 8px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12.5px;
  font-weight: 450;
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease, transform 0.12s ease;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  position: relative;
}

.nav-item:hover:not(.nav-item--active) {
  background: var(--bg-hover);
  color: var(--text-primary);
  transform: translateX(2px);
}

.nav-item:active {
  transform: translateX(0) scale(0.97) !important;
  transition-duration: 0.05s !important;
}

.nav-item--active {
  background: var(--accent-violet-subtle);
  color: var(--text-brand-strong);
  font-weight: 550;
}

.nav-item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(1);
  width: 2px;
  height: 55%;
  background: var(--accent-violet);
  border-radius: 0 2px 2px 0;
  animation: navIndicatorIn 0.25s var(--ease-spring);
}

@keyframes navIndicatorIn {
  from {
    transform: translateY(-50%) scaleY(0);
  }
  to {
    transform: translateY(-50%) scaleY(1);
  }
}

.nav-item__icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s var(--ease-spring);
}

.nav-item:hover .nav-item__icon {
  transform: scale(1.1);
}

.nav-item--active .nav-item__icon {
  transform: scale(1.05);
  color: var(--accent-violet-light);
}

.nav-item__icon svg {
  width: 16px;
  height: 16px;
}

.nav-item__label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-item--download .nav-item__icon {
  color: var(--accent-emerald);
}
.nav-item--download:hover {
  background: var(--accent-emerald-subtle) !important;
  color: var(--accent-emerald) !important;
}

.nav-item__badge {
  background: var(--accent-rose);
  color: white;
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
  transition: transform 0.2s var(--ease-spring);
}

.nav-item:hover .nav-item__badge {
  transform: scale(1.08);
}

.sidebar--collapsed .nav-item {
  justify-content: center;
  padding: 7px;
}

.sidebar--collapsed .nav-item:hover {
  transform: scale(1.06);
}

.sidebar__footer {
  padding: 6px 6px 8px;
  border-top: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.shortcut-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-elevated);
  color: var(--text-quaternary);
  font-size: 11.5px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.shortcut-hint:hover {
  background: var(--bg-hover);
  color: var(--text-tertiary);
  border-color: var(--border-base);
  transform: translateY(-1px);
}

.shortcut-hint:active {
  transform: translateY(0) scale(0.98) !important;
  transition-duration: 0.05s !important;
}

.shortcut-icon {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
}

kbd {
  margin-left: auto;
  background: var(--bg-overlay);
  border-radius: var(--radius-xs);
  padding: 1px 5px;
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text-quaternary);
  border: 1px solid var(--border-subtle);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.12s ease, transform 0.12s ease;
  overflow: hidden;
  margin-top: 1px;
}

.user-info:hover {
  background: var(--bg-hover);
  transform: translateX(1px);
}

.user-info:active {
  transform: translateX(0) scale(0.98) !important;
  transition-duration: 0.05s !important;
}

.user-info--collapsed {
  justify-content: center;
  padding: 6px;
}

.user-info--collapsed:hover {
  transform: scale(1.05);
}

.user-avatar {
  flex-shrink: 0;
  transition: transform 0.2s var(--ease-spring);
}

.user-info:hover .user-avatar {
  transform: scale(1.06);
}

.user-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 12px;
  font-weight: 550;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email {
  font-size: 10px;
  color: var(--text-quaternary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-chevron {
  width: 12px;
  height: 12px;
  color: var(--text-quaternary);
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.user-info:hover .user-chevron {
  transform: rotate(90deg);
}

.fade-text-enter-active,
.fade-text-leave-active {
  transition:
    opacity 0.12s ease,
    max-width 0.2s ease;
  overflow: hidden;
}

.fade-text-enter-from,
.fade-text-leave-to {
  opacity: 0;
  max-width: 0;
}

.fade-text-enter-to,
.fade-text-leave-from {
  opacity: 1;
  max-width: 180px;
}
</style>
