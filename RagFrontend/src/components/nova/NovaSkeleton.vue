<template>
  <div :class="['nova-skeleton', `nova-skeleton--${variant}`]">
    <!-- 文本行 -->
    <div v-if="variant === 'text'" class="nova-skeleton__text">
      <div
        v-for="i in lines"
        :key="i"
        class="nova-skeleton__line"
        :style="{ width: i === lines ? lastLineWidth : '100%' }"
      />
    </div>

    <!-- 卡片骨架 -->
    <div v-else-if="variant === 'card'" class="nova-skeleton__card">
      <div class="nova-skeleton__thumb" />
      <div class="nova-skeleton__meta">
        <div class="nova-skeleton__title" />
        <div class="nova-skeleton__desc" />
        <div class="nova-skeleton__tags">
          <div class="nova-skeleton__tag" />
          <div class="nova-skeleton__tag nova-skeleton__tag--short" />
        </div>
      </div>
    </div>

    <!-- 头像 -->
    <div v-else-if="variant === 'avatar'" class="nova-skeleton__avatar" />

    <!-- 自定义 -->
    <slot v-else />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'text' | 'card' | 'avatar' | 'custom'
  lines?: number
  lastLineWidth?: string
}>(), {
  variant: 'text',
  lines: 3,
  lastLineWidth: '65%',
})
</script>

<style scoped>
.nova-skeleton {
  display: block;
}

/* ── 流光动画 ── */
.nova-skeleton__line,
.nova-skeleton__thumb,
.nova-skeleton__title,
.nova-skeleton__desc,
.nova-skeleton__tag,
.nova-skeleton__avatar {
  background: linear-gradient(
    90deg,
    rgba(30, 41, 59, 0.6) 25%,
    rgba(51, 65, 85, 0.8) 50%,
    rgba(30, 41, 59, 0.6) 75%
  );
  background-size: 400px 100%;
  animation: novaShimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-md);
}

/* ── Text ── */
.nova-skeleton__text { display: flex; flex-direction: column; gap: var(--nova-space-2); }
.nova-skeleton__line { height: 13px; border-radius: var(--radius-sm); }

/* ── Card ── */
.nova-skeleton__card {
  display: flex;
  flex-direction: column;
  gap: var(--nova-space-4);
  padding: var(--nova-space-5);
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid var(--nova-border);
  border-radius: var(--radius-2xl);
}

.nova-skeleton__thumb {
  height: 140px;
  width: 100%;
  border-radius: var(--radius-xl) var(--radius-xl) var(--radius-sm) var(--radius-sm);
}

.nova-skeleton__meta { display: flex; flex-direction: column; gap: var(--nova-space-3); }
.nova-skeleton__title { height: 18px; width: 70%; }
.nova-skeleton__desc { height: 12px; width: 95%; }
.nova-skeleton__tags { display: flex; gap: var(--nova-space-2); margin-top: var(--nova-space-1); }
.nova-skeleton__tag { height: 20px; width: 56px; border-radius: var(--radius-full); }
.nova-skeleton__tag--short { width: 40px; }

/* ── Avatar ── */
.nova-skeleton__avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-full);
}
</style>
