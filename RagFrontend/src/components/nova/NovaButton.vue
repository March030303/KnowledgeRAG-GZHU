<template>
  <div class="nova-btn" :class="btnClasses" @click="$emit('click', $event)">
    <!-- 发光底层 -->
    <span v-if="variant === 'primary'" class="nova-btn__glow" />
    
    <!-- 边框动画 -->
    <span class="nova-btn__border" />
    
    <!-- 内容 -->
    <span class="nova-btn__content">
      <slot name="icon" />
      <slot />
    </span>
    
    <!-- 扫光层 -->
    <span class="nova-btn__shine" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  block?: boolean
  disabled?: boolean
}>(), {
  variant: 'primary',
  size: 'md',
  block: false,
  disabled: false,
})

defineEmits<{ click: [e: MouseEvent] }>()

const btnClasses = computed(() => [
  `nova-btn--${props.variant}`,
  `nova-btn--${props.size}`,
  { 'nova-btn--block': props.block, 'nova-btn--disabled': props.disabled },
])
</script>

<style scoped>
.nova-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--nova-space-2);
  font-family: var(--nova-font-display);
  font-weight: var(--nova-font-semibold);
  letter-spacing: 0.01em;
  border: none;
  cursor: pointer;
  overflow: hidden;
  user-select: none;
  white-space: nowrap;
  outline: none;
  transition:
    transform var(--nova-duration-fast) var(--nova-ease-spring),
    box-shadow var(--nova-duration-fast) ease,
    background var(--nova-duration-fast) ease;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    opacity: 0;
    transition: opacity var(--nova-duration-fast) ease;
  }

  &:hover:not(.nova-btn--disabled) {
    transform: translateY(-2px) scale(1.02);
  }

  &:active:not(.nova-btn--disabled) {
    transform: translateY(0) scale(0.98);
    transition-duration: 60ms;
  }
}

/* ── 尺寸 ── */
.nova-btn--sm {
  padding: var(--nova-space-2) var(--nova-space-4);
  font-size: var(--nova-text-xs);
  border-radius: var(--nova-radius-md);
}

.nova-btn--md {
  padding: var(--nova-space-3) var(--nova-space-6);
  font-size: var(--nova-text-sm);
  border-radius: var(--nova-radius-lg);
}

.nova-btn--lg {
  padding: var(--nova-space-4) var(--nova-space-8);
  font-size: var(--nova-text-base);
  border-radius: var(--nova-radius-xl);
}

/* ── Primary：渐变发光 ── */
.nova-btn--primary {
  color: white;
  background: var(--nova-gradient-brand);
  background-size: 200% 200%;
  animation: novaGradientFlow 3s ease infinite;
  box-shadow: 
    0 4px 15px rgba(99, 102, 241, 0.35),
    inset 0 1px 0 rgba(255,255,255,0.15);

  &:hover {
    box-shadow:
      0 8px 30px rgba(99, 102, 241, 0.5),
      0 0 50px rgba(139, 92, 246, 0.2),
      inset 0 1px 0 rgba(255,255,255,0.2);
  }

  .nova-btn__glow {
    position: absolute;
    inset: -2px;
    border-radius: inherit;
    background: var(--nova-gradient-brand);
    filter: blur(12px);
    opacity: 0;
    z-index: -1;
    transition: opacity var(--nova-duration-normal) ease;
  }

  &:hover .nova-btn__glow { opacity: 0.5; }
}

/* ── Secondary：玻璃拟态 ── */
.nova-btn--secondary {
  color: var(--nova-text-primary);
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid var(--nova-border);

  &:hover {
    background: rgba(51, 65, 85, 0.8);
    border-color: var(--nova-border-hover);
    box-shadow: var(--nova-shadow-lg);
  }
}

/* ── Ghost：透明边框 ── */
.nova-btn--ghost {
  color: var(--nova-text-secondary);
  background: transparent;
  border: 1px solid transparent;

  &:hover {
    color: var(--nova-text-primary);
    background: rgba(99, 102, 241, 0.08);
    border-color: var(--nova-border-hover);
  }
}

/* ── Danger：红渐变 ── */
.nova-btn--danger {
  color: white;
  background: linear-gradient(135deg, #ef4444, #f43f5e);
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);

  &:hover {
    box-shadow:
      0 8px 30px rgba(239, 68, 68, 0.45),
      0 0 40px rgba(244, 63, 94, 0.15);
  }
}

/* ── Disabled ── */
.nova-btn--disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
  filter: grayscale(0.5);
}

.nova-btn--block {
  width: 100%;
}

/* ── 内部元素 ── */
.nova-btn__content {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--nova-space-2);
  z-index: 1;
}

.nova-btn__border {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

.nova-btn__shine {
  position: absolute;
  top: 0; left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.12),
    transparent
  );
  transform: skewX(-20deg);
  transition: left var(--nova-duration-slower) ease;
  pointer-events: none;
}

.nova-btn:hover .nova-btn__shine {
  left: 180%;
}
</style>
