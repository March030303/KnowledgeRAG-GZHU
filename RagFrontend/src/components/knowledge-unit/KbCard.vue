<template>
  <div 
    class="kb-card" 
    :class="{ 'kb-card--compact': compact }"
    @click="$emit('click')"
  >
    <!-- 顶部渐变色条 -->
    <div class="kb-card__accent" :style="{ background: accentGradient }"></div>
    
    <!-- 主内容 -->
    <div class="kb-card__body">
      <!-- 头部：图标 + 标题 -->
      <div class="kb-card__header">
        <div class="kb-card__icon" :style="{ background: accentSubtle, color: accentColor }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
        <div class="kb-card__info">
          <h3 class="kb-card__title">{{ card.title }}</h3>
          <span class="kb-card__date">{{ formatDate(card.created_at) }}</span>
        </div>
      </div>

      <!-- 描述 -->
      <p v-if="card.description" class="kb-card__desc line-clamp-2">
        {{ card.description }}
      </p>

      <!-- 底部：标签 + 操作 -->
      <div class="kb-card__footer">
        <div class="kb-card__tags">
          <span class="badge badge-primary">
            <span class="badge__dot"></span>
            {{ card.document_count || 0 }} 文档
          </span>
        </div>
        <div class="kb-card__actions">
          <!-- 星标 -->
          <button 
            class="action-btn" 
            :class="{ 'action-btn--active': starred }"
            @click.stop="$emit('star')"
            :title="starred ? '取消星标' : '添加星标'"
          >
            <svg viewBox="0 0 24 24" :fill="starred ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </button>
          <!-- 置顶 -->
          <button 
            class="action-btn" 
            :class="{ 'action-btn--active': pinned }"
            @click.stop="$emit('pin')"
            :title="pinned ? '取消置顶' : '置顶'"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
          </button>
          <!-- 删除 -->
          <button 
            class="action-btn action-btn--danger"
            @click.stop="$emit('delete')"
            title="删除"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 悬浮层效果 -->
    <div class="kb-card__glow"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Card {
  id: string
  title: string
  description?: string
  created_at: string
  document_count?: number
}

const props = withDefaults(defineProps<{
  card: Card
  starred?: boolean
  pinned?: boolean
  compact?: boolean
}>(), {
  starred: false,
  pinned: false,
  compact: false
})

defineEmits<{
  click: []
  star: []
  pin: []
  delete: []
}>()

// 根据标题生成唯一渐变色
const accentGradient = computed(() => {
  const hash = props.card.title.split('').reduce((acc, char) => {
    return char.charCodeAt(0) + ((acc << 5) - acc)
  }, 0)
  
  const gradients = [
    'linear-gradient(135deg, #7c6aff 0%, #a78bfa 100%)',
    'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
    'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
    'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
    'linear-gradient(135deg, #f87171 0%, #ef4444 100%)',
    'linear-gradient(135deg, #22d3ee 0%, #06b6d4 100%)',
    'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)',
  ]
  
  return gradients[Math.abs(hash) % gradients.length]
})

const accentColor = computed(() => {
  return accentGradient.value.match(/#[a-fA-F0-9]{6}/)?.[0] || '#7c6aff'
})

const accentSubtle = computed(() => {
  const color = accentColor.value
  return `${color}15`
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days} 天前`
  if (days < 30) return `${Math.floor(days / 7)} 周前`
  
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
/* =====================================================
   知识卡片 — Geist x Linear 风格
   ===================================================== */

.kb-card {
  position: relative;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-normal);
  will-change: transform, box-shadow, border-color;
}

.kb-card:hover {
  border-color: var(--border-brand);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md), var(--shadow-glow);
}

/* 紧凑模式 */
.kb-card--compact .kb-card__body {
  padding: var(--space-3);
}

.kb-card--compact .kb-card__title {
  font-size: var(--text-sm);
}

.kb-card--compact .kb-card__desc {
  display: none;
}

/* 顶部渐变色条 */
.kb-card__accent {
  height: 3px;
  width: 100%;
  opacity: 0.8;
  transition: opacity var(--transition-normal);
}

.kb-card:hover .kb-card__accent {
  opacity: 1;
}

/* 发光效果 */
.kb-card__glow {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  opacity: 0;
  transition: opacity var(--transition-slow);
  pointer-events: none;
  background: radial-gradient(
    ellipse at 50% 0%,
    var(--accent-primary-subtle) 0%,
    transparent 70%
  );
}

.kb-card:hover .kb-card__glow {
  opacity: 1;
}

/* 主体内容 */
.kb-card__body {
  padding: var(--space-4);
  position: relative;
  z-index: 1;
}

/* 头部 */
.kb-card__header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.kb-card__icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform var(--transition-normal);
}

.kb-card:hover .kb-card__icon {
  transform: scale(1.05);
}

.kb-card__icon svg {
  width: 18px;
  height: 18px;
}

.kb-card__info {
  flex: 1;
  min-width: 0;
}

.kb-card__title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 2px;
  line-height: 1.4;
  letter-spacing: -0.01em;
}

.kb-card__date {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* 描述 */
.kb-card__desc {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-3);
  line-height: 1.5;
}

/* 底部 */
.kb-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.kb-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
}

/* 徽章 */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: 1.4;
  background: var(--accent-primary-subtle);
  color: var(--text-brand-strong);
}

.badge__dot {
  width: 5px;
  height: 5px;
  border-radius: var(--radius-full);
  background: currentColor;
  opacity: 0.7;
}

/* 操作按钮 */
.kb-card__actions {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  opacity: 0;
  transform: translateX(4px);
  transition: all var(--transition-normal);
}

.kb-card:hover .kb-card__actions {
  opacity: 1;
  transform: translateX(0);
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.action-btn:active {
  transform: scale(0.92);
}

.action-btn svg {
  width: 15px;
  height: 15px;
}

.action-btn--active {
  color: var(--accent-warning);
}

.action-btn--active:hover {
  color: var(--accent-warning);
  background: var(--accent-warning-subtle);
}

.action-btn--danger {
  opacity: 0;
  transition: all var(--transition-fast);
}

.kb-card:hover .action-btn--danger {
  opacity: 1;
}

.action-btn--danger:hover {
  background: var(--accent-danger-subtle);
  color: var(--accent-danger);
}

/* 响应式 */
@media (max-width: 640px) {
  .kb-card__actions {
    opacity: 1;
    transform: translateX(0);
  }
  
  .action-btn--danger {
    opacity: 1;
  }
}
</style>
