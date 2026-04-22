<template>
  <aside class="nova-sidebar" :class="{ 'nova-sidebar--collapsed': isCollapsed }">
    <!-- 背景层 -->
    <div class="nova-sidebar__backdrop" />

    <!-- Logo 区域 -->
    <div class="nova-sidebar__brand">
      <transition name="logo-fade" mode="out-in">
        <div v-if="!isCollapsed" key="full" class="nova-sidebar__logo-full">
          <div class="nova-sidebar__logo-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#novaLogoGrad)" stroke-width="2" stroke-linecap="round">
              <defs>
                <linearGradient id="novaLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#3b82f6"/>
                  <stop offset="100%" stop-color="#8b5cf6"/>
                </linearGradient>
              </defs>
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </div>
          <span class="nova-sidebar__title">KnowledgeRAG</span>
        </div>
        <div v-else key="mini" class="nova-sidebar__logo-mini">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="url(#novaLogoGrad)" stroke="#818cf8" stroke-width="2.5" stroke-linecap="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
        </div>
      </transition>
    </div>

    <!-- 导航菜单 -->
    <nav class="nova-sidebar__nav">
      <ul class="nova-sidebar__menu">
        <li
          v-for="(item, index) in menuItems"
          :key="item.path"
          class="nova-sidebar__item"
          :class="{ 'nova-sidebar__item--active': isActive(item.path) }"
          :style="{ animationDelay: `${index * 50}ms` }"
        >
          <router-link :to="item.path" class="nova-sidebar__link">
            <span class="nova-sidebar__icon" v-html="item.icon" />
            <transition name="label-slide">
              <span v-if="!isCollapsed" class="nova-sidebar__label">{{ item.label }}</span>
            </transition>
            <!-- 活跃指示条 -->
            <span v-if="isActive(item.path)" class="nova-sidebar__indicator" />
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- 折叠按钮 -->
    <button class="nova-sidebar__toggle" @click="toggleCollapse" title="折叠/展开">
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        :style="{ transform: isCollapsed ? 'rotate(180deg)' : '' }"
      >
        <polyline points="15 18 9 12 15 6"/>
      </svg>
    </button>

    <!-- 底部用户区域 -->
    <div class="nova-sidebar__footer">
      <div v-if="!isCollapsed" class="nova-sidebar__user">
        <div class="nova-sidebar__avatar">U</div>
        <div class="nova-sidebar__userinfo">
          <span class="nova-sidebar__username">User</span>
          <span class="nova-sidebar__role">Admin</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isCollapsed = ref(false)

const menuItems = [
  { path: '/knowledge', label: '知识库', icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>' },
  { path: '/chat', label: '智能问答', icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>' },
  { path: '/settings', label: '设置', icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>' },
]

const isActive = (path: string) => route.path.startsWith(path)
const toggleCollapse = () => { isCollapsed.value = !isCollapsed.value }

defineExpose({ toggleCollapse })
</script>

<style scoped>
.nova-sidebar {
  position: relative;
  display: flex;
  flex-direction: column;
  width: var(--nova-sidebar-width);
  height: 100vh;
  background: rgba(10, 15, 30, 0.85);
  backdrop-filter: blur(24px) saturate(1.3);
  -webkit-backdrop-filter: blur(24px) saturate(1.3);
  border-right: 1px solid var(--nova-border);
  overflow: hidden;
  transition: width var(--nova-duration-slow) var(--nova-ease-out-expo);
  z-index: var(--nova-z-sticky);
  flex-shrink: 0;
}

.nova-sidebar--collapsed {
  width: 72px;
}

.nova-sidebar__backdrop {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 100% 0%, rgba(99, 102, 241, 0.08), transparent 50%),
    linear-gradient(180deg, transparent 70%, rgba(0, 0, 0, 0.2));
  pointer-events: none;
}

/* ── Logo ── */
.nova-sidebar__brand {
  display: flex;
  align-items: center;
  padding: var(--nova-space-6) var(--nova-space-5);
  min-height: 72px;
  border-bottom: 1px solid var(--nova-border);
  overflow: hidden;
  flex-shrink: 0;
}

.nova-sidebar__logo-full {
  display: flex;
  align-items: center;
  gap: var(--nova-space-3);
  animation: novaFadeInLeft var(--nova-duration-slower) var(--nova-ease-out-expo);
}

.nova-sidebar__logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--nova-gradient-brand);
  border-radius: var(--radius-lg);
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.nova-sidebar__title {
  font-size: var(--nova-text-lg);
  font-weight: var(--nova-font-bold);
  background: var(--nova-gradient-brand);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.01em;
}

.nova-sidebar__logo-mini {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(99, 102, 241, 0.12);
  border-radius: var(--radius-lg);
  margin: 0 auto;
  animation: novaFadeInScale var(--nova-duration-normal) ease;
}

/* ── 导航 ── */
.nova-sidebar__nav {
  flex: 1;
  padding: var(--nova-space-4) var(--nova-space-3);
  overflow-y: auto;
  overflow-x: hidden;
}

.nova-sidebar__menu {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--nova-space-1);
}

.nova-sidebar__item {
  animation: novaFadeInUp var(--nova-duration-slow) var(--nova-ease-out-expo) both;
}

.nova-sidebar__link {
  display: flex;
  align-items: center;
  gap: var(--nova-space-3);
  padding: var(--nova-space-3) var(--nova-space-4);
  color: var(--nova-text-secondary);
  text-decoration: none;
  border-radius: var(--radius-lg);
  font-size: var(--nova-text-sm);
  font-weight: var(--nova-font-medium);
  position: relative;
  transition:
    color var(--nova-duration-fast) ease,
    background var(--nova-duration-fast) ease,
    transform var(--nova-duration-fast) ease;

  &:hover {
    color: var(--nova-text-primary);
    background: rgba(99, 102, 241, 0.08);
    transform: translateX(3px);
  }
}

.nova-sidebar__item--active > .nova-sidebar__link {
  color: #a5b4fc;
  background: rgba(99, 102, 241, 0.12);
  font-weight: var(--nova-font-semibold);
  transform: none;
}

.nova-sidebar__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  transition: transform var(--nova-duration-fast) ease;
}

.nova-sidebar__item--active .nova-sidebar__icon {
  transform: scale(1.05);
}

.nova-sidebar__indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--nova-gradient-brand);
  border-radius: 0 var(--radius-full) var(--radius-full) 0;
  box-shadow: var(--nova-glow-blue);
}

.nova-sidebar__label {
  white-space: nowrap;
  overflow: hidden;
}

/* ── 折叠按钮 ── */
.nova-sidebar__toggle {
  position: absolute;
  right: -14px;
  top: 84px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--nova-border);
  border-radius: 50%;
  background: var(--nova-bg-secondary);
  color: var(--nova-text-muted);
  cursor: pointer;
  z-index: 10;
  transition: all var(--nova-duration-fast) ease;
  box-shadow: var(--nova-shadow-md);

  &:hover {
    background: rgba(99, 102, 241, 0.15);
    color: var(--nova-info);
    border-color: rgba(99, 102, 241, 0.3);
  }

  svg {
    transition: transform var(--nova-duration-normal) var(--nova-ease-out-expo);
  }
}

/* ── 底部 ── */
.nova-sidebar__footer {
  padding: var(--nova-space-4) var(--nova-space-5);
  border-top: 1px solid var(--nova-border);
}

.nova-sidebar__user {
  display: flex;
  align-items: center;
  gap: var(--nova-space-3);
}

.nova-sidebar__avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--nova-gradient-cyber);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--nova-text-sm);
  font-weight: var(--nova-font-bold);
  color: white;
  flex-shrink: 0;
}

.nova-sidebar__username {
  font-size: var(--nova-text-sm);
  font-weight: var(--nova-font-medium);
  color: var(--nova-text-primary);
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

.nova-sidebar__role {
  font-size: 11px;
  color: var(--nova-text-muted);
  display: block;
}

/* ── 过渡 ── */
.logo-fade-enter-active,
.logo-fade-leave-active { transition: opacity var(--nova-duration-fast) ease; }
.logo-fade-enter-from,
.logo-fade-leave-to { opacity: 0; }

.label-slide-enter-active,
.label-slide-leave-active { 
  transition: opacity var(--nova-duration-instant) ease, 
              width var(--nova-duration-normal) var(--nova-ease-out-expo); }
.label-slide-enter-from,
.label-slide-leave-to { 
  opacity: 0; 
  width: 0; 
}
</style>
