<template>
  <div
    class="nova-card"
    :class="cardClasses"
    :style="tiltStyle"
    @mousemove="onMouseMove"
    @mouseleave="onMouseLeave"
    @click="$emit('click', $event)"
  >
    <!-- 背景光效 -->
    <div class="nova-card__bg-glow" />

    <!-- 边框发光 -->
    <div class="nova-card__border-ring" />

    <!-- 头部区域 -->
    <div v-if="hasHeaderSlot || title" class="nova-card__header">
      <slot name="header" />
    </div>

    <!-- 默认内容 -->
    <div class="nova-card__body">
      <slot />
    </div>

    <!-- 底部区域 -->
    <div v-if="hasFooterSlot" class="nova-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, useSlots } from 'vue'

const props = withDefaults(defineProps<{
  variant?: 'default' | 'elevated' | 'glass' | 'bordered' | 'glow'
  hoverable?: boolean
  clickable?: boolean
  accent?: 'blue' | 'purple' | 'pink' | 'cyan' | 'warning'
  title?: string
}>(), {
  variant: 'default',
  hoverable: true,
  clickable: false,
})

defineEmits<{ click: [e: MouseEvent] }>()
const slots = useSlots()
const hasHeaderSlot = computed(() => !!slots.header)
const hasFooterSlot = computed(() => !!slots.footer)

// 鼠标跟随 3D 倾斜
const tiltStyle = ref({ transform: '' })
const rotateX = ref(0)
const rotateY = ref(0)

const onMouseMove = (e: MouseEvent) => {
  if (!props.hoverable) return
  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  
  rotateX.value = ((y - centerY) / centerY) * -8
  rotateY.value = ((x - centerX) / centerX) * 8
  
  tiltStyle.value = {
    transform: `perspective(800px) rotateX(${rotateX.value}deg) rotateY(${rotateY.value}deg) translateZ(10px)`,
  }
}

const onMouseLeave = () => {
  tiltStyle.value = { transform: '' }
}

const cardClasses = computed(() => [
  `nova-card--${props.variant}`,
  { 'nova-card--hoverable': props.hoverable, 'nova-card--clickable': props.clickable },
  props.accent ? `nova-card--accent-${props.accent}` : '',
])
</script>

<style scoped>
.nova-card {
  position: relative;
  border-radius: var(--nova-radius-2xl);
  overflow: hidden;
  will-change: transform;
  transition:
    transform var(--nova-duration-normal) var(--nova-ease-out-expo),
    box-shadow var(--nova-duration-normal) ease;

  /* 光标样式 */
  &.nova-card--clickable { cursor: pointer; }
  &.nova-card--hoverable:not(.nova-card--clickable):not(:hover) { cursor: default; }
}

/* ── 变体：默认深色 ── */
.nova-card--default {
  background: var(--nova-bg-card);
  border: 1px solid var(--nova-border);
  box-shadow: var(--nova-shadow-md);
}

.nova-card--default:hover {
  box-shadow: var(--nova-shadow-xl), var(--nova-glow-blue);
  border-color: var(--nova-border-hover);
}

/* ── 变体：提升阴影 ── */
.nova-card--elevated {
  background: var(--nova-bg-card);
  border: 1px solid transparent;
  box-shadow: var(--nova-shadow-lg);
}

.nova-card--elevated:hover {
  box-shadow: var(--nova-shadow-xl);
  transform: translateY(-4px);
}

/* ── 变体：玻璃拟态 ── */
.nova-card--glass {
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid rgba(148, 163, 184, 0.08);
  box-shadow: var(--nova-shadow-md);
}

.nova-card--glass:hover {
  background: rgba(15, 23, 42, 0.7);
  border-color: rgba(148, 163, 184, 0.15);
  backdrop-filter: blur(28px) saturate(1.6);
}

/* ── 变体：边框发光 ── */
.nova-card--bordered {
  background: transparent;
  border: 1px solid var(--nova-border);
  box-shadow: none;
}

.nova-card--bordered:hover {
  border-color: var(--nova-info);
  box-shadow: var(--nova-glow-blue);
}

/* ── 变体：霓虹发光 ── */
.nova-card--glow {
  background: var(--nova-bg-card);
  border: 1px solid rgba(99, 102, 241, 0.25);
  box-shadow: var(--nova-shadow-glow-blue);
}

.nova-card--glow:hover {
  box-shadow: 
    0 0 40px rgba(99, 102, 241, 0.3),
    0 0 80px rgba(139, 92, 246, 0.15),
    inset 0 0 30px rgba(99, 102, 241, 0.05);
  border-color: rgba(99, 102, 241, 0.4);
}

/* ── 强调色 ── */
.nova-card--accent-blue .nova-card__bg-glow { background: radial-gradient(circle at 50% 0%, rgba(59,130,246,0.1), transparent 70%); }
.nova-card--accent-purple .nova-card__bg-glow { background: radial-gradient(circle at 50% 0%, rgba(139,92,246,0.1), transparent 70%); }
.nova-card--accent-pink .nova-card__bg-glow { background: radial-gradient(circle at 50% 0%, rgba(236,72,153,0.1), transparent 70%); }
.nova-card--accent-cyan .nova-card__bg-glow { background: radial-gradient(circle at 50% 0%, rgba(6,182,212,0.1), transparent 70%); }
.nova-card--accent-warning .nova-card__bg-glow { background: radial-gradient(circle at 50% 0%, rgba(245,158,11,0.1), transparent 70%); }

/* ── 内部元素 ── */
.nova-card__bg-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 120px;
  opacity: 0;
  transition: opacity var(--nova-duration-normal) ease;
  pointer-events: none;
}
.nova-card:hover .nova-card__bg-glow { opacity: 1; }

.nova-card__border-ring {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(
    135deg,
    transparent 40%,
    rgba(99, 102, 241, 0.2),
    rgba(139, 92, 246, 0.15),
    transparent 60%
  );
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  -webkit-mask-composite: xor;
  opacity: 0;
  transition: opacity var(--nova-duration-normal) ease;
  pointer-events: none;
}
.nova-card:hover .nova-card__border-ring { opacity: 1; }

.nova-card__header {
  padding: var(--nova-space-5) var(--nova-space-6) 0;
  position: relative;
  z-index: 1;
}

.nova-card__body {
  padding: var(--nova-space-6);
  position: relative;
  z-index: 1;
}

.nova-card__footer {
  padding: 0 var(--nova-space-6) var(--nova-space-5);
  position: relative;
  z-index: 1;
}
</style>
