# KnowledgeRAG 全新设计系统 (NOVA Design)

> 基于 droitstock 视觉风格 + Galaxy 组件库，完全重构前端界面

---

## 一、设计理念

### 1.1 设计定位
- **产品类型**：AI 知识库智能问答系统
- **目标用户**：需要高效知识管理和问答的企业/个人用户
- **视觉调性**：专业、科技、简约、现代

### 1.2 核心设计原则
1. **科技感优先**：深蓝色调 + 渐变 + 玻璃拟态
2. **模块化布局**：卡片式设计，功能分区清晰
3. **动效驱动**：流畅的微交互动效增强体验
4. **暗色支持**：支持深色模式切换

---

## 二、色彩系统

### 2.1 主色调 (Primary Colors)
```css
:root {
  /* 主品牌色 - 深蓝科技 */
  --primary-900: #0f172a;    /* 深色背景 */
  --primary-800: #1e293b;    /* 卡片背景 */
  --primary-700: #334155;    /* 边框/分割线 */
  --primary-600: #475569;    /* 次要文字 */
  --primary-500: #64748b;    /* 占位符 */
  --primary-400: #94a3b8;    /* 辅助文字 */
  --primary-300: #cbd5e1;    /* 浅色文字 */
  --primary-200: #e2e8f0;    /* 亮色边框 */
  --primary-100: #f1f5f9;    /* 浅色背景 */
  --primary-50: #f8fafc;     /* 极浅背景 */
}

/* 强调色 - 渐变蓝紫 */
--accent-gradient: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
--accent-primary: #3b82f6;    /* 主蓝 */
--accent-secondary: #8b5cf6; /* 紫 */
--accent-cyan: #06b6d4;      /* 青 */
```

### 2.2 功能色 (Semantic Colors)
```css
/* 成功 */
--success-500: #22c55e;
--success-400: #4ade80;
--success-100: #dcfce7;

/* 警告 */
--warning-500: #f59e0b;
--warning-400: #fbbf24;
--warning-100: #fef3c7;

/* 错误 */
--error-500: #ef4444;
--error-400: #f87171;
--error-100: #fee2e2;

/* 信息 */
--info-500: #3b82f6;
--info-400: #60a5fa;
--info-100: #dbeafe;
```

### 2.3 暗色模式
```css
[data-theme="dark"] {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: #1e293b;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --border-color: #334155;
}
```

---

## 三、字体系统

### 3.1 字体选择
```css
/* 中文优先 */
--font-family-cn: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif;

/* 英文/数字 */
--font-family-en: 'Inter', 'SF Pro Display', -apple-system, sans-serif;

/* 等宽字体（代码） */
--font-family-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

/* 混合 */
--font-family: var(--font-family-cn), var(--font-family-en);
```

### 3.2 字体层级
```css
--text-xs: 0.75rem;      /* 12px - 辅助说明 */
--text-sm: 0.875rem;      /* 14px - 次要文字 */
--text-base: 1rem;        /* 16px - 正文 */
--text-lg: 1.125rem;      /* 18px - 小标题 */
--text-xl: 1.25rem;       /* 20px - 标题 */
--text-2xl: 1.5rem;       /* 24px - 页面标题 */
--text-3xl: 1.875rem;     /* 30px - 大标题 */
--text-4xl: 2.25rem;      /* 36px - 巨型标题 */

/* 字重 */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

---

## 四、间距系统

### 4.1 基础间距（8px 网格）
```css
--space-0: 0;
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;    /* 12px */
--space-4: 1rem;       /* 16px */
--space-5: 1.25rem;    /* 20px */
--space-6: 1.5rem;     /* 24px */
--space-8: 2rem;       /* 32px */
--space-10: 2.5rem;    /* 40px */
--space-12: 3rem;      /* 48px */
--space-16: 4rem;      /* 64px */
--space-20: 5rem;      /* 80px */
--space-24: 6rem;      /* 96px */
```

---

## 五、组件系统

### 5.1 按钮 (Buttons)

#### 主按钮
```css
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  border-radius: 12px;
  background: var(--accent-gradient);
  color: white;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.5);
}

.btn-primary:active {
  transform: translateY(0);
}
```

#### 次按钮
```css
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  border: 1.5px solid var(--primary-600);
  border-radius: 12px;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: var(--primary-700);
  border-color: var(--primary-500);
}
```

#### 图标按钮
```css
.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 10px;
  background: var(--primary-800);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-icon:hover {
  background: var(--primary-700);
  color: var(--accent-primary);
  transform: scale(1.05);
}
```

### 5.2 卡片 (Cards)

#### 基础卡片
```css
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  border-color: var(--accent-primary);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
  transform: translateY(-4px);
}
```

#### 玻璃拟态卡片
```css
.card-glass {
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
```

### 5.3 输入框 (Inputs)

```css
.input {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  background: var(--bg-primary);
  border: 1.5px solid var(--border-color);
  border-radius: 10px;
  color: var(--text-primary);
  outline: none;
  transition: all 0.3s ease;
}

.input:focus {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.input::placeholder {
  color: var(--text-secondary);
}
```

### 5.4 标签/徽章 (Badges)

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 6px;
}

.badge-primary {
  background: rgba(59, 130, 246, 0.15);
  color: var(--accent-primary);
}

.badge-success {
  background: rgba(34, 197, 94, 0.15);
  color: var(--success-500);
}

.badge-warning {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning-500);
}
```

---

## 六、动效系统

### 6.1 基础动效

```css
/* 过渡时长 */
--transition-fast: 150ms ease;
--transition-base: 300ms ease;
--transition-slow: 500ms ease;

/* 缓动曲线 */
--ease-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### 6.2 微交互动效

#### 悬浮发光效果
```css
.hover-glow {
  transition: all 0.3s var(--ease-out);
}

.hover-glow:hover {
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
  border-color: var(--accent-primary);
}
```

#### 弹性缩放
```css
.hover-scale {
  transition: transform 0.3s var(--ease-spring);
}

.hover-scale:hover {
  transform: scale(1.02);
}
```

### 6.3 页面过渡

```css
.page-enter-active {
  transition: all 0.4s var(--ease-out);
}

.page-leave-active {
  transition: all 0.25s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.page-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
```

### 6.4 骨架屏动画

```css
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--primary-800) 25%,
    var(--primary-700) 50%,
    var(--primary-800) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}
```

---

## 七、布局系统

### 7.1 页面结构
```
┌─────────────────────────────────────────────┐
│  顶部导航栏 (64px, 固定)                     │
├───────────┬─────────────────────────────────┤
│  侧边栏    │  主内容区                        │
│  (240px)  │  - 面包屑导航                     │
│  可折叠    │  - 页面标题                      │
│           │  - 内容区域                       │
│           │  - 响应式网格                     │
└───────────┴─────────────────────────────────┘
```

### 7.2 响应式断点
```css
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;
```

---

## 八、参考来源

### 8.1 网站模板参考
- **droitstock.com**：深蓝色调 + 模块化卡片 + 功能入口强调

### 8.2 组件库参考
- **Galaxy (Uiverse.io)**：3000+ CSS/Tailwind 组件
- https://uiverse.io/
- https://github.com/uiverse-io/galaxy

### 8.3 动效参考
- **006-jump-animation**：页面跳转动画实现
- https://github.com/JIEJOE-WEB-TUTORIAL/006-jump-animation

---

## 九、实施清单

### Phase 1: 基础系统
- [ ] CSS 变量定义
- [ ] 全局样式重置
- [ ] 字体加载配置
- [ ] 暗色模式支持

### Phase 2: 核心组件
- [ ] 按钮组件
- [ ] 卡片组件
- [ ] 输入框组件
- [ ] 标签/徽章组件
- [ ] 导航组件

### Phase 3: 页面重写
- [ ] App.vue 布局重构
- [ ] SideBar 全新设计
- [ ] 知识库页面重写
- [ ] 聊天页面优化

### Phase 4: 动效增强
- [ ] 页面过渡动效
- [ ] 悬浮交互动效
- [ ] 加载骨架屏
- [ ] 滚动动画

---

*最后更新: 2026-04-22*
