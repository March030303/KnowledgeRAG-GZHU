<template>
  <div class="tab-content">
    <div class="section-header">
      <h2>外观设置</h2>
      <p class="section-desc">自定义界面主题色、圆角、字体大小等全局样式，实时预览</p>
    </div>
    <!-- 主题色 -->
    <div class="card">
      <div class="card-title">主题色</div>
      <div class="color-row">
        <div
          v-for="c in themeColors"
          :key="c.primary"
          class="color-chip"
          :class="{ active: currentTheme.primary === c.primary }"
          :style="{ background: c.primary }"
          @click="applyTheme(c)"
          :title="c.name"
        >
          <span v-if="currentTheme.primary === c.primary" class="check">✓</span>
        </div>
      </div>
    </div>
    <!-- 圆角 -->
    <div class="card" style="margin-top: 16px">
      <div class="card-title">圆角风格</div>
      <div class="slider-row">
        <span class="slider-label">小</span>
        <input
          type="range"
          min="2"
          max="16"
          v-model.number="borderRadius"
          class="slider"
          @input="applyBorderRadius"
        />
        <span class="slider-label">大</span>
        <span class="slider-val">{{ borderRadius }}px</span>
      </div>
    </div>
    <!-- 字体大小 -->
    <div class="card" style="margin-top: 16px">
      <div class="card-title">字体大小</div>
      <div class="slider-row">
        <span class="slider-label">小</span>
        <input
          type="range"
          min="12"
          max="18"
          v-model.number="fontSize"
          class="slider"
          @input="applyFontSize"
        />
        <span class="slider-label">大</span>
        <span class="slider-val">{{ fontSize }}px</span>
      </div>
    </div>
    <!-- 重置 -->
    <div style="margin-top: 16px">
      <button class="btn-primary" @click="resetAll">重置为默认</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'

const themeColors = [
  { name: '默认蓝', primary: '#4f7ef8', secondary: '#8b5cf6' },
  { name: '翠绿', primary: '#22c55e', secondary: '#10b981' },
  { name: '热情红', primary: '#ef4444', secondary: '#f97316' },
  { name: '优雅紫', primary: '#8b5cf6', secondary: '#a855f7' },
  { name: '暖橙', primary: '#f59e0b', secondary: '#f97316' },
  { name: '青蓝', primary: '#06b6d4', secondary: '#3b82f6' },
  { name: '玫瑰粉', primary: '#ec4899', secondary: '#f43f5e' },
  { name: '石墨灰', primary: '#475569', secondary: '#64748b' }
]

const currentTheme = ref(themeColors[0])
const borderRadius = ref(8)
const fontSize = ref(14)

function applyTheme(theme: (typeof themeColors)[0]) {
  currentTheme.value = theme
  document.documentElement.style.setProperty('--ragf-primary', theme.primary)
  document.documentElement.style.setProperty('--ragf-primary-light', theme.primary + '20')
  document.documentElement.style.setProperty(
    '--ragf-primary-gradient',
    `linear-gradient(135deg, ${theme.primary}, ${theme.secondary})`
  )
  persist()
  MessagePlugin.success(`已切换为${theme.name}主题`)
}

function applyBorderRadius() {
  document.documentElement.style.setProperty('--ragf-radius', borderRadius.value + 'px')
  persist()
}

function applyFontSize() {
  document.documentElement.style.setProperty('--ragf-font-size', fontSize.value + 'px')
  document.documentElement.style.fontSize = fontSize.value + 'px'
  persist()
}

function resetAll() {
  currentTheme.value = themeColors[0]
  borderRadius.value = 8
  fontSize.value = 14
  document.documentElement.style.removeProperty('--ragf-primary')
  document.documentElement.style.removeProperty('--ragf-primary-light')
  document.documentElement.style.removeProperty('--ragf-primary-gradient')
  document.documentElement.style.removeProperty('--ragf-radius')
  document.documentElement.style.removeProperty('--ragf-font-size')
  document.documentElement.style.fontSize = ''
  localStorage.removeItem('ragf-appearance')
  MessagePlugin.success('已重置为默认外观')
}

function persist() {
  const config = {
    theme: currentTheme.value,
    borderRadius: borderRadius.value,
    fontSize: fontSize.value
  }
  localStorage.setItem('ragf-appearance', JSON.stringify(config))
}

onMounted(() => {
  try {
    const saved = localStorage.getItem('ragf-appearance')
    if (saved) {
      const config = JSON.parse(saved)
      if (config.theme) applyTheme(config.theme)
      if (config.borderRadius) {
        borderRadius.value = config.borderRadius
        applyBorderRadius()
      }
      if (config.fontSize) {
        fontSize.value = config.fontSize
        applyFontSize()
      }
    }
  } catch {}
})
</script>

<style scoped>
.card {
  background: var(--td-bg-color-container, #fff);
  border: 1px solid #e5e7eb;
  border-radius: var(--ragf-radius, 8px);
  padding: 16px;
}
.card-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}
.color-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.color-chip {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s;
  border: 2px solid transparent;
}
.color-chip:hover {
  transform: scale(1.15);
}
.color-chip.active {
  border-color: #111;
  box-shadow:
    0 0 0 2px #fff,
    0 0 0 4px currentColor;
}
.check {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}
.slider-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.slider-label {
  font-size: 12px;
  color: #9ca3af;
}
.slider {
  flex: 1;
  max-width: 300px;
}
.slider-val {
  font-size: 13px;
  font-weight: 600;
  color: var(--ragf-primary, #4f7ef8);
  min-width: 40px;
}
.btn-primary {
  padding: 8px 20px;
  background: var(--ragf-primary, #4f7ef8);
  color: #fff;
  border: none;
  border-radius: var(--ragf-radius, 6px);
  cursor: pointer;
  font-size: 13px;
}
.btn-primary:hover {
  opacity: 0.9;
}
</style>
