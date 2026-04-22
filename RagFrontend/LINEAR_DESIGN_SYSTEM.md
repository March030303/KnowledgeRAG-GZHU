# Geist x Linear 设计系统 — KnowledgeRAG-GZHU 前端

> 本文档记录了项目中融合 **Geist (Vercel)** + **Linear** 设计语言的全面重构，
> 借鉴了 Geist 极简克制、网格系统 + Linear 暗色精致 + FreeFrontend 微交互动效。

---

## 1. 设计理念

### 1.1 核心原则

| 原则 | 说明 | 实践 |
|------|------|------|
| **极简克制** | 减少视觉噪音，让内容说话 | 极少装饰、精简组件、单色系点缀 |
| **网格系统** | 12列网格，8px基准间距 | 对齐一致、节奏清晰 |
| **线性引导** | 单向阅读路径，减少认知负荷 | 从上到下、从左到右 |
| **微交互驱动** | 每个操作都有视觉反馈 | hover/active/focus 状态明确 |
| **性能优先** | GPU加速动画、transform/opacity | 零重排、零卡顿 |

### 1.2 设计来源

- **Geist (Vercel)**：极简字体（Geist Sans/Mono）、高对比度、网格系统
- **Linear 趋势**：暗色主题、单色系品牌色、精简UI
- **FreeFrontend 动画**：霓虹边框、呼吸脉冲、波纹扩散、滚动触发动效
- **2025 Web UI**：微交互主导、无障碍优先、响应式设计

---

## 2. 文件清单

```
RagFrontend/src/
├── assets/styles/global.css     # 设计令牌 + 全局动效系统
├── styles/animations.css       # 微交互动效（独立模块）
├── composables/useTheme.ts     # 主题管理器
├── views/KnowledgePages/
│   ├── KnowledgeBase.vue        # 知识库主页（Geist网格布局）
│   └── KnowledgeDetail.vue     # 知识库详情
├── components/
│   ├── knowledge-unit/
│   │   └── KbCard.vue          # 知识卡片（Geist风格）
│   ├── T-HeadBar.vue           # 顶部导航（Linear风格）
│   └── SideBar.vue             # 侧边栏
├── App.vue                      # 根布局
└── views/Chat.vue              # 聊天界面
```

---

## 3. 设计令牌 (Design Tokens)

### 3.1 暗色背景层级（Geist 深黑）

```css
:root {
  /* 核心背景 — 近纯黑 */
  --bg-base: #000000;
  --bg-surface: #0a0a0a;
  --bg-elevated: #111111;
  --bg-overlay: #181818;
  --bg-overlay-hover: #222222;
  --bg-overlay-active: #2a2a2a;
  
  /* 状态背景 */
  --bg-hover: rgba(255, 255, 255, 0.04);
  --bg-active: rgba(255, 255, 255, 0.08);
  --bg-subtle: rgba(255, 255, 255, 0.02);
  
  /* 边框层级 */
  --border-subtle: rgba(255, 255, 255, 0.04);
  --border-default: rgba(255, 255, 255, 0.08);
  --border-strong: rgba(255, 255, 255, 0.16);
  --border-brand: rgba(124, 106, 255, 0.4);
}
```

### 3.2 文字层级（高对比度）

```css
:root {
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --text-tertiary: rgba(255, 255, 255, 0.5);
  --text-disabled: rgba(255, 255, 255, 0.3);
  --text-brand: #a78bfa;
  --text-brand-strong: #c4b5fd;
  
  /* 功能色 */
  --text-success: #4ade80;
  --text-warning: #fbbf24;
  --text-danger: #f87171;
  --text-info: #60a5fa;
}
```

### 3.3 品牌色系统（单色系 Indigo）

```css
:root {
  /* 主色 — Indigo/Violet */
  --accent-primary: #7c6aff;
  --accent-primary-hover: #9d8cff;
  --accent-primary-active: #6a58e0;
  --accent-primary-subtle: rgba(124, 106, 255, 0.1);
  --accent-primary-glow: rgba(124, 106, 255, 0.2);
  
  /* 功能色 */
  --accent-success: #4ade80;
  --accent-success-subtle: rgba(74, 222, 128, 0.1);
  --accent-warning: #fbbf24;
  --accent-warning-subtle: rgba(251, 191, 36, 0.1);
  --accent-danger: #f87171;
  --accent-danger-subtle: rgba(248, 113, 113, 0.1);
  --accent-info: #60a5fa;
  --accent-info-subtle: rgba(96, 165, 250, 0.1);
}
```

### 3.4 阴影系统（极简）

```css
:root {
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.4);
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.5);
  --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.6);
  --shadow-lg: 0 16px 48px rgba(0, 0, 0, 0.7);
  
  /* 品牌辉光 */
  --shadow-glow: 0 0 20px rgba(124, 106, 255, 0.15);
  --shadow-glow-strong: 0 0 40px rgba(124, 106, 255, 0.25);
  
  /* 内阴影 */
  --shadow-inner: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}
```

### 3.5 圆角层级（Geist 精细）

```css
:root {
  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 20px;
  --radius-full: 9999px;
}
```

### 3.6 动画曲线（流畅自然）

```css
:root {
  /* 缓动函数 */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  
  /* 时长 */
  --duration-fast: 0.1s;
  --duration-normal: 0.2s;
  --duration-slow: 0.35s;
  --duration-slower: 0.5s;
  
  /* 过渡 shorthand */
  --transition-fast: var(--duration-fast) var(--ease-out-quart);
  --transition-normal: var(--duration-normal) var(--ease-out-quart);
  --transition-slow: var(--duration-slow) var(--ease-out-expo);
  --transition-spring: var(--duration-slower) var(--ease-spring);
}
```

### 3.7 字体系统（Geist）

```css
:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
  
  /* 字号 */
  --text-xs: 11px;
  --text-sm: 12px;
  --text-base: 13px;
  --text-md: 14px;
  --text-lg: 16px;
  --text-xl: 18px;
  --text-2xl: 24px;
  --text-3xl: 30px;
}
```

### 3.8 间距系统（8px 基准）

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
}
```

---

## 4. 动效系统

### 4.1 核心动效类型

| 类型 | 动效 | 时长 | 缓动 |
|------|------|------|------|
| **微交互** | hover/active 状态变化 | 0.1-0.2s | ease-out-quart |
| **入场动画** | fadeIn/slideUp | 0.3-0.5s | ease-out-expo |
| **弹簧反馈** | 点击压缩/弹跳 | 0.3-0.5s | ease-spring |
| **脉冲指示** | 状态点呼吸 | 2-3s infinite | ease-in-out |
| **霓虹边框** | 边框发光追踪 | 1-2s infinite | ease-in-out |

### 4.2 关键帧动画库

```css
/* ===== 微交互 ===== */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInScale {
  from { opacity: 0; transform: scale(0.96); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-8px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(8px); }
  to { opacity: 1; transform: translateX(0); }
}

/* ===== 弹簧动效 ===== */
@keyframes springIn {
  0% { transform: scale(0.9); opacity: 0; }
  60% { transform: scale(1.02); }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes springBounce {
  0%, 100% { transform: scale(1); }
  25% { transform: scale(1.15); }
  50% { transform: scale(0.95); }
  75% { transform: scale(1.05); }
}

/* ===== 脉冲/呼吸 ===== */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes breathe {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.05); opacity: 1; }
}

/* ===== 霓虹边框追踪 ===== */
@keyframes borderTrace {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes neonGlow {
  0%, 100% { box-shadow: 0 0 4px var(--accent-primary-subtle); }
  50% { box-shadow: 0 0 16px var(--accent-primary-glow), 0 0 32px var(--accent-primary-subtle); }
}

/* ===== 加载动画 ===== */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes dotPulse {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* ===== 页面过渡 ===== */
@keyframes pageEnter {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pageLeave {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(-8px); }
}

/* ===== 弹窗 ===== */
@keyframes modalIn {
  0% { opacity: 0; transform: scale(0.95) translateY(8px); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}

@keyframes modalOut {
  from { opacity: 1; transform: scale(1); }
  to { opacity: 0; transform: scale(0.95); }
}

/* ===== 浮动 ===== */
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
```

### 4.3 交互状态矩阵

| 状态 | 按钮主 | 按钮次 | 卡片 | 输入框 |
|------|--------|--------|------|--------|
| Default | 渐变背景 | 透明+边框 | 暗色背景 | 暗色背景 |
| Hover | 亮度+10%、上移1px | 背景变亮 | 边框发光、轻微上移 | 边框变亮 |
| Active | 下压0.5px | 下压0.5px | 回弹 | 品牌色边框 |
| Focus | 辉光环 | 辉光环 | 辉光环 | 辉光环 |
| Disabled | 50%透明度 | 50%透明度 | 50%透明度 | 50%透明度 |

---

## 5. 组件规范

### 5.1 按钮系统

```css
/* 主按钮 */
.btn-primary {
  background: var(--accent-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 500;
  transition: all var(--transition-normal);
}
.btn-primary:hover {
  background: var(--accent-primary-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}
.btn-primary:active {
  transform: translateY(0) scale(0.98);
}

/* 次要按钮 */
.btn-secondary {
  background: var(--bg-overlay);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}
.btn-secondary:hover {
  background: var(--bg-overlay-hover);
  border-color: var(--border-strong);
}

/* 图标按钮 */
.btn-icon {
  background: transparent;
  color: var(--text-secondary);
  border: none;
  border-radius: var(--radius-sm);
  padding: 6px;
}
.btn-icon:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
```

### 5.2 卡片系统

```css
/* 基础卡片 */
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  transition: all var(--transition-normal);
}
.card:hover {
  border-color: var(--border-brand);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

/* 悬停时霓虹边框 */
.card-neon {
  position: relative;
}
.card-neon::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(90deg, 
    var(--accent-primary) 0%, 
    transparent 30%,
    transparent 70%,
    var(--accent-primary) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity var(--transition-normal);
}
.card-neon:hover::before {
  opacity: 1;
  animation: borderTrace 2s linear infinite;
}
```

### 5.3 输入框系统

```css
.input {
  background: var(--bg-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: 10px 14px;
  font-size: var(--text-base);
  transition: all var(--transition-normal);
}
.input::placeholder {
  color: var(--text-tertiary);
}
.input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px var(--accent-primary-subtle);
}
```

### 5.4 标签/徽章系统

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
}
.badge-primary {
  background: var(--accent-primary-subtle);
  color: var(--text-brand-strong);
}
.badge-success {
  background: var(--accent-success-subtle);
  color: var(--accent-success);
}
```

---

## 6. 布局系统

### 6.1 页面结构

```
┌─────────────────────────────────────────┐
│ Header (固定)                            │
│ ┌─────────┬─────────────────────────┐    │
│ │ Sidebar │ Content Area           │    │
│ │         │                        │    │
│ │ 导航    │ 主体内容                │    │
│ │         │                        │    │
│ └─────────┴─────────────────────────┘    │
└─────────────────────────────────────────┘
```

### 6.2 网格系统

```css
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--space-4);
}

.col-span-4 { grid-column: span 4; }
.col-span-6 { grid-column: span 6; }
.col-span-8 { grid-column: span 8; }
.col-span-12 { grid-column: span 12; }

@media (max-width: 1024px) {
  .col-span-4, .col-span-6 { grid-column: span 6; }
}
@media (max-width: 640px) {
  .grid { grid-template-columns: 1fr; }
  [class*="col-span-"] { grid-column: span 1; }
}
```

### 6.3 间距规范

| 名称 | 值 | 用途 |
|------|-----|------|
| xs | 4px | 紧凑元素 |
| sm | 8px | 小间距 |
| md | 16px | 常规间距 |
| lg | 24px | 大间距 |
| xl | 32px | 区块间距 |
| 2xl | 48px | 页面间距 |

---

## 7. 响应式断点

```css
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
}

/* 移动优先 */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
```

---

## 8. 无障碍设计

### 8.1 焦点状态

```css
:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}
```

### 8.2 减少动画

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 8.3 色彩对比

- 主要文字：#ffffff on #000000 = 21:1 ✓
- 次要文字：rgba(255,255,255,0.7) on #000000 = 10:1 ✓
- 辅助文字：rgba(255,255,255,0.5) on #000000 = 5.7:1 ✓

---

## 9. 性能优化

### 9.1 GPU 加速

```css
.gpu-accelerated {
  will-change: transform, opacity;
  transform: translateZ(0);
}
```

### 9.2 避免的属性

```css
/* ❌ 不推荐 */
.element {
  width: 100px;
  height: 100px;
  left: 50px;
  top: 50px;
  background-color: red;
}

/* ✅ 推荐 */
.element {
  transform: translate(50px, 50px);
  background: red;
}
```

---

## 10. 应用示例

```vue
<template>
  <div class="card card-neon gpu-accelerated animate-fade-in">
    <div class="card-header">
      <h3 class="text-lg">标题</h3>
      <span class="badge badge-primary">新</span>
    </div>
    <div class="card-body">
      <p class="text-secondary">内容描述...</p>
    </div>
    <div class="card-footer">
      <button class="btn btn-secondary">取消</button>
      <button class="btn btn-primary">确认</button>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  transition: all var(--transition-normal);
}

.card:hover {
  border-color: var(--border-brand);
  box-shadow: var(--shadow-glow);
}
</style>
```
