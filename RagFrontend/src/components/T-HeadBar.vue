<template>
  <t-header class="t-header-dark">
    <t-head-menu theme="dark" :value="currentMenuItem" height="64px" class="flex items-center">
      <template #logo>
        <h2 class="logo-title">
          <span class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" fill="url(#logoGrad)" opacity="0.9"/>
              <path d="M2 17l10 5 10-5" stroke="url(#logoGrad)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.6"/>
              <path d="M2 12l10 5 10-5" stroke="url(#logoGrad)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.8"/>
              <defs>
                <linearGradient id="logoGrad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                  <stop stop-color="#818cf8"/>
                  <stop offset="1" stop-color="#6366f1"/>
                </linearGradient>
              </defs>
            </svg>
          </span>
          RAGF-01
        </h2>
      </template>
      <!-- 导航菜单 -->
      <t-menu-item
        value="item1"
        @click="navigateTo('/knowledge')"
        :class="['nav-item', { active: $route.path === '/knowledge' }]"
      >
        <t-icon name="book" class="nav-icon" />
        知识库
      </t-menu-item>
      <t-menu-item
        value="item2"
        @click="navigateTo('/chat')"
        :class="['nav-item', { active: $route.path === '/chat' }]"
      >
        <t-icon name="chat" class="nav-icon" />
        对话
      </t-menu-item>
      <t-menu-item
        value="itemacmd"
        @click="navigateTo('/acmd_search')"
        :class="['nav-item', { active: $route.path === '/acmd_search' }]"
      >
        <t-icon name="search" class="nav-icon" />
        学术检索
      </t-menu-item>
      <t-menu-item
        value="item3"
        @click="navigateTo('/service')"
        :class="['nav-item', { active: $route.path === '/service' }]"
      >
        <t-icon name="server" class="nav-icon" />
        模型管理
      </t-menu-item>
      <t-menu-item
        value="item5"
        @click="navigateTo('/files')"
        :class="['nav-item', { active: $route.path === '/files' }]"
      >
        <t-icon name="file" class="nav-icon" />
        文件管理
      </t-menu-item>
      <t-menu-item
        value="item4"
        @click="navigateTo('/user')"
        :class="['nav-item', { active: $route.path.startsWith('/user') }]"
      >
        <t-icon name="user" class="nav-icon" />
        个人主页
      </t-menu-item>
      <t-menu-item
        value="item6"
        @click="navigateTo('/DOC')"
        :class="['nav-item', { active: $route.path === '/DOC' }]"
      >
        <t-icon name="book-open" class="nav-icon" />
        开发文档
      </t-menu-item>
      <div class="header-spacer"></div>
      <template #operations>
        <div class="header-ops">
          <!-- 分隔线 -->
          <div class="header-divider"></div>
          <!-- 操作按钮组 -->
          <div class="header-btn-group">
            <t-tooltip content="GitHub仓库" placement="bottom">
              <t-button theme="default" shape="square" variant="text" @click="navToGitHub" class="header-icon-btn">
                <svg viewBox="0 0 24 24" fill="currentColor" class="github-icon">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                </svg>
              </t-button>
            </t-tooltip>
            <t-tooltip content="帮助文档" placement="bottom">
              <t-button theme="default" shape="square" variant="text" @click="navToHelper" class="header-icon-btn">
                <t-icon name="help-circle" class="header-ticon" />
              </t-button>
            </t-tooltip>
            <t-tooltip content="返回首页" placement="bottom">
              <t-button theme="default" shape="square" variant="text" @click="navigateTo('/knowledge')" class="header-icon-btn">
                <t-icon name="home" class="header-ticon" />
              </t-button>
            </t-tooltip>
          </div>
          <!-- 用户头像 -->
          <t-dropdown :min-column-width="140" trigger="click" placement="bottom-right">
            <div class="user-avatar-wrapper">
              <t-avatar
                :image="userAvatar"
                :hide-on-load-failed="false"
                size="medium"
                class="user-avatar"
              />
              <div class="avatar-glow"></div>
            </div>
            <template #dropdown>
              <t-dropdown-menu class="user-dropdown">
                <t-dropdown-item @click="goToProfile" class="dropdown-item">
                  <t-icon name="user" class="dropdown-icon dropdown-icon--blue" />
                  个人中心
                </t-dropdown-item>
                <t-dropdown-item divided @click="logout" class="dropdown-item dropdown-item--danger">
                  <t-icon name="logout" class="dropdown-icon dropdown-icon--red" />
                  退出登录
                </t-dropdown-item>
              </t-dropdown-menu>
            </template>
          </t-dropdown>
        </div>
      </template>
    </t-head-menu>
  </t-header>
  <!-- 设置抽屉（保留但暗色化） -->
  <t-drawer
    v-model:visible="drawerVisible"
    placement="bottom"
    :header="'设置面板'"
    :footer="null"
    size="400px"
  >
    <div class="drawer-empty">
      <div class="drawer-empty__icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-indigo)" stroke-width="1.5">
          <path stroke-linecap="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      </div>
      <h3 class="drawer-empty__title">功能即将上线</h3>
      <p class="drawer-empty__desc">我们正在努力开发中，请耐心等待！</p>
    </div>
  </t-drawer>
</template>
<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { useDataUserStore } from '@/store'
const userStore = useDataUserStore()
import API_ENDPOINTS from '@/utils/apiConfig'
const userAvatar = computed(() => {
  if (!userStore.userData) {
    return 'https://tdesign.gtimg.com/site/avatar.jpg'
  }
  const avatar = userStore.userData?.avatar || ''
  if (avatar && avatar.startsWith('/static/')) {
    return API_ENDPOINTS.USER.AVATAR(avatar)
  }
  return avatar || 'https://tdesign.gtimg.com/site/avatar.jpg'
})
const goToProfile = () => {
  router.push('/user/userInfo')
}
const logout = async () => {
  try {
    await router.push('/LogonOrRegister')
    MessagePlugin.success('已登出账号')
  } catch (error) {
    console.error('路由跳转失败:', error)
  }
}
onMounted(async () => {
  try {
    await userStore.fetchUserData()
    handleUserDropdownOpen()
  } catch (error) {
    console.error('获取用户数据失败:', error)
  }
})
const refreshUserAvatar = async () => {
  try {
    await userStore.fetchUserData()
  } catch (error) {
    console.error('刷新用户数据失败:', error)
  }
}
const handleUserDropdownOpen = () => {
  refreshUserAvatar()
}
const route = useRoute()
const router = useRouter()
const currentMenuItem = computed(() => {
  const path = route.path
  if (path.startsWith('/chat')) return 'item2'
  switch (path) {
    case '/knowledge': return 'item1'
    case '/service': return 'item3'
    case '/files': return 'item5'
    case '/DOC': return 'item6'
    case '/acmd_search': return 'itemacmd'
    default:
      if (path.startsWith('/user')) return 'item4'
      return ''
  }
})
const navigateTo = (path: string) => {
  router.push(path)
}
const navToGitHub = () => {
  window.open('https://github.com/Zhongye1')
}
const navToHelper = () => {
  window.open('https://tdesign.tencent.com/vue-next/overview')
}
const drawerVisible = ref(false)
const _toggleSettingPanel = () => {
  drawerVisible.value = !drawerVisible.value
}
</script>
<style scoped>
/* ===== 顶部导航 — Linear暗色风格 ===== */
.t-header-dark {
  background: var(--bg-surface) !important;
  border-bottom: 1px solid var(--border-base) !important;
  box-shadow: none !important;
  height: 64px !important;
  backdrop-filter: blur(12px);
}
/* 导航项 — Linear细竖条风格 */
:deep(.t-menu) {
  background: transparent !important;
  border: none !important;
}
:deep(.t-menu__logo) {
  background: transparent !important;
  border: none !important;
}
:deep(.t-menu-item) {
  color: var(--text-secondary) !important;
  border-radius: var(--radius-md) !important;
  transition: all var(--transition-normal) !important;
  position: relative;
}
:deep(.t-menu-item::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 2px;
  height: 0;
  background: var(--accent-indigo);
  border-radius: 2px;
  transition: height var(--transition-normal);
}
:deep(.t-menu-item:hover) {
  color: var(--text-primary) !important;
  background: var(--bg-hover) !important;
}
:deep(.t-menu-item.active) {
  color: var(--text-brand-strong) !important;
  background: var(--accent-indigo-subtle) !important;
  font-weight: 500;
}
:deep(.t-menu-item.active::before) {
  height: 60%;
}
/* Logo */
.logo-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  margin: 0;
  padding: 0 4px;
}
.logo-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-hover);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-base);
}
.logo-icon svg {
  width: 18px;
  height: 18px;
}
/* 导航图标 */
.nav-icon {
  font-size: 16px !important;
  margin-right: 6px !important;
  opacity: 0.8;
}
:deep(.t-menu-item.active) .nav-icon,
:deep(.t-menu-item:hover) .nav-icon {
  opacity: 1;
}
/* 右侧操作区 */
.header-spacer {
  flex: 1;
}
.header-ops {
  display: flex;
  align-items: center;
  gap: 4px;
}
.header-divider {
  width: 1px;
  height: 24px;
  background: var(--border-base);
  margin: 0 8px;
}
.header-btn-group {
  display: flex;
  align-items: center;
  gap: 2px;
}
/* 图标按钮 */
.header-icon-btn {
  width: 36px !important;
  height: 36px !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-secondary) !important;
  transition: all var(--transition-normal) !important;
}
.header-icon-btn:hover {
  background: var(--bg-hover) !important;
  color: var(--text-primary) !important;
}
.github-icon {
  width: 18px;
  height: 18px;
}
.header-ticon {
  font-size: 18px !important;
}
/* 用户头像 */
.user-avatar-wrapper {
  position: relative;
  margin-left: 4px;
  cursor: pointer;
}
.user-avatar {
  border: 2px solid var(--border-base) !important;
  transition: all var(--transition-normal) !important;
  border-radius: var(--radius-full) !important;
}
.user-avatar-wrapper:hover .user-avatar {
  border-color: var(--accent-indigo) !important;
  box-shadow: 0 0 0 3px var(--accent-indigo-subtle) !important;
}
.avatar-glow {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  background: var(--gradient-brand);
  opacity: 0;
  z-index: -1;
  filter: blur(8px);
  transition: opacity var(--transition-normal);
}
.user-avatar-wrapper:hover .avatar-glow {
  opacity: 0.3;
}
/* 下拉菜单 */
.user-dropdown {
  background: var(--bg-overlay) !important;
  border: 1px solid var(--border-base) !important;
  border-radius: var(--radius-lg) !important;
  box-shadow: var(--shadow-lg) !important;
  padding: 4px !important;
  min-width: 160px !important;
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px !important;
  border-radius: var(--radius-md) !important;
  font-size: 13.5px !important;
  color: var(--text-primary) !important;
  transition: all var(--transition-fast) !important;
}
.dropdown-item:hover {
  background: var(--bg-hover) !important;
}
.dropdown-item--danger {
  color: var(--text-danger) !important;
}
.dropdown-item--danger:hover {
  background: var(--accent-rose-subtle) !important;
}
.dropdown-icon {
  font-size: 15px !important;
  flex-shrink: 0;
}
.dropdown-icon--blue { color: var(--accent-indigo) !important; }
.dropdown-icon--red { color: var(--text-danger) !important; }
/* 抽屉空状态 */
.drawer-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 12px;
}
.drawer-empty__icon {
  width: 72px;
  height: 72px;
  border-radius: var(--radius-2xl);
  background: var(--accent-indigo-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}
.drawer-empty__icon svg {
  width: 36px;
  height: 36px;
}
.drawer-empty__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.drawer-empty__desc {
  font-size: 13.5px;
  color: var(--text-secondary);
  margin: 0;
  text-align: center;
}
</style>
