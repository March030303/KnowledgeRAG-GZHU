<template>
  <div
    :class="[
      'kb-card',
      { 'kb-card--compact': compact, 'kb-card--starred': starred, 'kb-card--pinned': pinned }
    ]"
    @click="$emit('click')"
  >
    <!-- 置顶徽章 -->
    <div v-if="pinned" class="kb-card__pin-badge">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
      </svg>
      置顶
    </div>
    <!-- 封面颜色条（基于title hash） -->
    <div class="kb-card__color-bar" :style="{ background: cardColor }"></div>
    <!-- 卡片主体 -->
    <div class="kb-card__body">
      <div class="kb-card__top">
        <!-- 图标 -->
        <div class="kb-card__icon" :style="{ background: cardColorSubtle, borderColor: cardColorSubtle }">
          <svg viewBox="0 0 24 24" fill="none" :stroke="cardColor" stroke-width="1.8">
            <path
              stroke-linecap="round"
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
            />
          </svg>
        </div>
        <!-- 操作按钮（悬浮显示） -->
        <div class="kb-card__actions" @click.stop>
          <!-- 置顶按钮 -->
          <button
            :class="['action-btn', 'pin-btn', { 'pin-btn--active': pinned }]"
            @click.stop="handlePin"
            @mousedown="ripple"
            :title="pinned ? '取消置顶' : '置顶'"
          >
            <svg
              :class="{ 'like-pop': pinAnimating }"
              viewBox="0 0 24 24"
              fill="none"
              :stroke="pinned ? 'var(--accent-indigo)' : 'currentColor'"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
              />
            </svg>
          </button>
          <!-- 星标按钮 -->
          <button
            :class="['action-btn', 'star-btn', { 'star-btn--active': starred }]"
            @click.stop="handleStar"
            @mousedown="ripple"
            :title="starred ? '取消星标' : '加入星标'"
          >
            <svg
              :class="{ 'like-pop': starAnimating }"
              viewBox="0 0 24 24"
              :fill="starred ? '#f59e0b' : 'none'"
              :stroke="starred ? '#f59e0b' : 'currentColor'"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
              />
            </svg>
          </button>
          <!-- 更多操作 -->
          <t-dropdown :options="dropdownOptions" trigger="click" @click="handleDropdown">
            <button class="action-btn" @click.stop title="更多操作">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="5" r="1.5" />
                <circle cx="12" cy="12" r="1.5" />
                <circle cx="12" cy="19" r="1.5" />
              </svg>
            </button>
          </t-dropdown>
        </div>
      </div>
      <!-- 标题 -->
      <h3 class="kb-card__title">{{ card.title }}</h3>
      <!-- 描述 -->
      <p v-if="!compact && card.description" class="kb-card__desc">{{ card.description }}</p>
      <!-- 底部信息 -->
      <div class="kb-card__footer">
        <span class="kb-card__time">{{ formattedTime }}</span>
        <div class="kb-card__tags" v-if="!compact">
          <span class="kb-card__tag">RAG</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, ref } from 'vue'
import { DropdownProps } from 'tdesign-vue-next'
import { useRipple } from '@/composables/useScrollReveal'
const { ripple } = useRipple()
interface Card {
  id: string
  title: string
  avatar?: string
  description?: string
  cover?: string
  createdTime?: string
}
const props = defineProps<{
  card: Card
  starred?: boolean
  pinned?: boolean
  compact?: boolean
}>()
const emit = defineEmits(['click', 'star', 'pin', 'delete'])
// 微交互状态
const starAnimating = ref(false)
const pinAnimating = ref(false)
const handleStar = () => {
  starAnimating.value = true
  setTimeout(() => {
    starAnimating.value = false
  }, 500)
  emit('star')
}
const handlePin = () => {
  pinAnimating.value = true
  setTimeout(() => {
    pinAnimating.value = false
  }, 400)
  emit('pin')
}
// 颜色方案基于title hash（暗色主题优化版）
const COLOR_SETS = [
  // Indigo系 — 与主题主色呼应
  { bar: 'linear-gradient(135deg, #6366f1, #818cf8)', subtle: 'rgba(99, 102, 241, 0.12)', glow: 'rgba(99, 102, 241, 0.3)' },
  // Emerald系 — 清新绿
  { bar: 'linear-gradient(135deg, #10b981, #34d399)', subtle: 'rgba(16, 185, 129, 0.12)', glow: 'rgba(16, 185, 129, 0.3)' },
  // Amber系 — 温暖金
  { bar: 'linear-gradient(135deg, #f59e0b, #fbbf24)', subtle: 'rgba(245, 158, 11, 0.12)', glow: 'rgba(245, 158, 11, 0.3)' },
  // Rose系 — 玫瑰粉
  { bar: 'linear-gradient(135deg, #ec4899, #f472b6)', subtle: 'rgba(236, 72, 153, 0.12)', glow: 'rgba(236, 72, 153, 0.3)' },
  // Violet系 — 紫罗兰
  { bar: 'linear-gradient(135deg, #8b5cf6, #a78bfa)', subtle: 'rgba(139, 92, 246, 0.12)', glow: 'rgba(139, 92, 246, 0.3)' },
  // Teal系 — 蓝绿
  { bar: 'linear-gradient(135deg, #14b8a6, #2dd4bf)', subtle: 'rgba(20, 184, 166, 0.12)', glow: 'rgba(20, 184, 166, 0.3)' },
  // Orange系 — 活力橙
  { bar: 'linear-gradient(135deg, #f97316, #fb923c)', subtle: 'rgba(249, 115, 22, 0.12)', glow: 'rgba(249, 115, 22, 0.3)' }
]
const colorIndex = computed(() => {
  let hash = 0
  for (let i = 0; i < props.card.title.length; i++) {
    hash = props.card.title.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash) % COLOR_SETS.length
})
const cardColor = computed(() => COLOR_SETS[colorIndex.value].bar.split(',')[0].replace('linear-gradient(135deg, ', '').trim())
const cardColorSubtle = computed(() => COLOR_SETS[colorIndex.value].subtle)
const cardGlow = computed(() => COLOR_SETS[colorIndex.value].glow)
const formattedTime = computed(() => {
  const t = props.card.createdTime
  if (!t) return ''
  try {
    const d = new Date(t)
    const now = new Date()
    const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000)
    if (diffDays === 0) return '今天'
    if (diffDays === 1) return '昨天'
    if (diffDays < 7) return `${diffDays} 天前`
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch {
    return t
  }
})
const dropdownOptions: DropdownProps['options'] = [
  { content: '打开', value: 'open' },
  { content: '置顶/取消置顶', value: 'pin' },
  { content: '删除', value: 'delete' }
]
const handleDropdown = (data: any) => {
  if (data.value === 'open') emit('click')
  if (data.value === 'pin') emit('pin')
  if (data.value === 'delete') emit('delete')
}
</script>
<style scoped>
/* ===== 卡片主体 — 暗色主题 ===== */
.kb-card {
  background: var(--bg-elevated);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-base);
  overflow: hidden;
  cursor: pointer;
  position: relative;
  /* Galaxy/Linear风格过渡 */
  transition:
    transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1),
    border-color 0.2s ease,
    background 0.2s ease;
  will-change: transform, box-shadow;
}
/* Hover：浮起 + Linear式Glow阴影 + 边框发光 */
.kb-card:hover {
  transform: translateY(-5px) scale(1.01);
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.5),
    0 8px 16px rgba(0, 0, 0, 0.3),
    0 0 0 1px var(--border-active);
  border-color: var(--border-active);
}
/* active：按下感（spring回弹） */
.kb-card:active {
  transform: translateY(-1px) scale(0.985) !important;
  transition-duration: 0.08s !important;
  box-shadow:
    0 6px 16px rgba(0, 0, 0, 0.4),
    0 2px 4px rgba(0, 0, 0, 0.3) !important;
}
/* 星标状态 */
.kb-card--starred {
  border-color: rgba(245, 158, 11, 0.25);
}
.kb-card--starred:hover {
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.5),
    0 0 24px rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.4);
}
/* 置顶状态 */
.kb-card--pinned {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.1);
}
.kb-card--pinned:hover {
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.5),
    0 0 28px rgba(99, 102, 241, 0.15),
    0 0 0 1px rgba(99, 102, 241, 0.3);
  border-color: rgba(99, 102, 241, 0.5);
}
/* 置顶徽章 */
.kb-card__pin-badge {
  position: absolute;
  top: 8px;
  left: 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  background: var(--gradient-brand);
  color: #fff;
  padding: 3px 8px 3px 5px;
  border-radius: var(--radius-full);
  z-index: 2;
  letter-spacing: 0.02em;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
  animation: pinBadgePop var(--transition-spring) ease-out both;
}
.kb-card__pin-badge svg {
  width: 11px;
  height: 11px;
  fill: #fff;
  stroke: #fff;
}
@keyframes pinBadgePop {
  0% { opacity: 0; transform: scale(0.6) translateY(-4px); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}
/* 顶部颜色条 */
.kb-card__color-bar {
  height: 3px;
  width: 100%;
  transition: height 0.25s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s ease;
}
.kb-card:hover .kb-card__color-bar {
  height: 4px;
  opacity: 0.85;
}
.kb-card__body {
  padding: 14px 14px 12px;
}
.kb-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 10px;
}
/* 图标 — Galaxy风格发光hover */
.kb-card__icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid transparent;
  transition:
    transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1),
    border-color 0.2s ease,
    box-shadow 0.25s ease;
}
.kb-card:hover .kb-card__icon {
  transform: scale(1.1) rotate(-3deg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
.kb-card__icon svg {
  width: 20px;
  height: 20px;
  transition: transform 0.25s ease;
}
/* 操作按钮：平时透明，卡片hover时显示 */
.kb-card__actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transform: translateY(-4px) scale(0.95);
  transition:
    opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1),
    transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.kb-card:hover .kb-card__actions {
  opacity: 1;
  transform: translateY(0) scale(1);
}
/* 星标始终亮着 */
.kb-card--starred .kb-card__actions,
.kb-card--starred .star-btn {
  opacity: 1;
  transform: translateY(0) scale(1);
}
.action-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: var(--bg-hover);
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition:
    background 0.15s ease,
    color 0.15s ease,
    transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  position: relative;
}
.action-btn:hover {
  background: var(--accent-indigo-subtle);
  color: var(--accent-indigo);
  transform: scale(1.12);
}
.action-btn:active {
  transform: scale(0.88) !important;
  transition-duration: 0.06s !important;
}
.action-btn svg {
  width: 15px;
  height: 15px;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
/* 星标激活 */
.star-btn--active {
  color: #f59e0b;
}
.star-btn--active:hover {
  background: var(--accent-amber-subtle) !important;
  color: #d97706 !important;
}
/* 置顶激活 */
.pin-btn--active {
  color: var(--accent-indigo);
}
.pin-btn--active:hover {
  background: var(--accent-indigo-subtle) !important;
}
/* ===== 文字 ===== */
.kb-card__title {
  font-size: 14.5px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
  transition: color 0.2s ease;
}
.kb-card:hover .kb-card__title {
  color: var(--text-brand-strong);
}
.kb-card__desc {
  font-size: 12.5px;
  color: var(--text-secondary);
  margin: 0 0 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
  transition: color 0.2s ease;
}
.kb-card:hover .kb-card__desc {
  color: var(--text-primary);
}
/* ===== 底部 ===== */
.kb-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
.kb-card__time {
  font-size: 11.5px;
  color: var(--text-tertiary);
  transition: color 0.2s ease;
}
.kb-card:hover .kb-card__time {
  color: var(--text-secondary);
}
.kb-card__tags {
  display: flex;
  gap: 4px;
}
.kb-card__tag {
  font-size: 10.5px;
  font-weight: 500;
  padding: 2px 8px;
  background: var(--bg-subtle);
  color: var(--text-tertiary);
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
  letter-spacing: 0.02em;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease;
}
.kb-card:hover .kb-card__tag {
  background: var(--accent-indigo-subtle);
  color: var(--text-brand);
  border-color: var(--border-brand);
}
/* ===== like-pop动画（Galaxy风格弹簧） ===== */
.like-pop {
  animation: likeSpring var(--transition-spring) both;
}
@keyframes likeSpring {
  0% { transform: scale(1); }
  30% { transform: scale(1.4) rotate(8deg); }
  60% { transform: scale(0.9) rotate(-4deg); }
  100% { transform: scale(1) rotate(0); }
}
/* ===== 紧凑模式 ===== */
.kb-card--compact .kb-card__body {
  padding: 10px 12px;
}
.kb-card--compact .kb-card__icon {
  width: 30px;
  height: 30px;
  border-radius: 7px;
}
.kb-card--compact .kb-card__icon svg {
  width: 16px;
  height: 16px;
}
.kb-card--compact .kb-card__title {
  font-size: 13.5px;
}
</style>
