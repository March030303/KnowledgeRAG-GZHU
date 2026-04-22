<template>
  <span class="nova-badge" :class="badgeClasses">
    <span class="nova-badge__dot" v-if="dot" />
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  type?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info'
  size?: 'sm' | 'md'
  dot?: boolean
  pulse?: boolean
}>(), {
  type: 'primary',
  size: 'md',
  dot: false,
  pulse: false,
})

const badgeClasses = computed(() => [
  `nova-badge--${props.type}`,
  `nova-badge--${props.size}`,
  { 'nova-badge--pulse': props.pulse },
])
</script>

<style scoped>
.nova-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--nova-space-1);
  font-family: var(--nova-font-display);
  font-weight: var(--nova-font-semibold);
  letter-spacing: 0.02em;
  white-space: nowrap;
  vertical-align: middle;
  line-height: 1;
  transition: all var(--nova-duration-fast) ease;
}

.nova-badge--sm {
  padding: 2px var(--nova-space-2);
  font-size: 10px;
  border-radius: var(--radius-full);
}

.nova-badge--md {
  padding: 4px var(--nova-space-3);
  font-size: var(--nova-text-xs);
  border-radius: var(--radius-full);
}

/* ── 类型 ── */
.nova-badge--primary {
  color: #c7d2fe;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.2);
}
.nova-badge--secondary {
  color: #cbd5e1;
  background: rgba(148, 163, 184, 0.15);
  border: 1px solid rgba(148, 163, 184, 0.15);
}
.nova-badge--success {
  color: #a7f3d0;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.2);
}
.nova-badge--warning {
  color: #fde68a;
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.2);
}
.nova-badge--error {
  color: #fecaca;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.2);
}
.nova-badge--info {
  color: #93c5fd;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.nova-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.nova-badge--pulse .nova-badge__dot {
  animation: novaPulse 1.5s ease-in-out infinite;
}
</style>
