<template>
  <main class="kb-page">
    <!-- 顶部欢迎区域 — Linear风格 -->
    <div class="kb-header">
      <div class="kb-header__left">
        <div class="kb-header__meta">
          <div class="kb-header__dot"></div>
          <span class="kb-header__status">活跃</span>
        </div>
        <h1 class="kb-title">知识库</h1>
        <p class="kb-subtitle">管理和检索你的所有知识内容</p>
      </div>
      <div class="kb-header__right">
        <!-- 搜索框 — Linear风格 -->
        <div class="kb-search-wrapper">
          <svg class="kb-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" />
            <path stroke-linecap="round" d="M21 21l-4.35-4.35" />
          </svg>
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索知识库..."
            class="kb-search-input"
            @input="handleSearch"
          />
          <button v-if="searchKeyword" class="kb-search-clear" @click="clearSearchKeyword">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <!-- 去广场按钮 -->
        <button class="kb-btn kb-btn--ghost" @click="$router.push('/square')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          知识广场
        </button>
        <!-- 新建按钮 — Linear渐变 -->
        <button class="kb-btn kb-btn--primary" @click="toggleUploadModal">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" d="M12 4v16m8-8H4" />
          </svg>
          新建知识库
        </button>
      </div>
    </div>
    <!-- 创建知识库弹窗 — Linear毛玻璃风格 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-card animate-fade-in-scale">
        <div class="modal-header">
          <div class="modal-header__left">
            <div class="modal-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <div>
              <h3 class="modal-title">新建知识库</h3>
              <p class="modal-subtitle">创建一个新的知识空间，开始整理你的知识</p>
            </div>
          </div>
          <button class="modal-close" @click="showCreateModal = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <label class="modal-label">知识库名称</label>
          <input
            type="text"
            v-model="kbName"
            placeholder="例如：产品文档、设计规范、会议记录..."
            class="modal-input"
            @keydown.enter="createKnowledgeBase"
            ref="kbNameInput"
          />
          <div class="modal-hints">
            <span class="modal-hint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              名称将用于知识库的显示和搜索
            </span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="kb-btn kb-btn--ghost" @click="showCreateModal = false">取消</button>
          <button class="kb-btn kb-btn--primary" @click="createKnowledgeBase" :disabled="!kbName.trim()">
            创建知识库
          </button>
        </div>
      </div>
    </div>
    <!-- 搜索状态 -->
    <div v-if="isSearching" class="kb-section animate-fade-in">
      <div class="kb-section__header">
        <span class="kb-section__title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" />
            <path stroke-linecap="round" d="M21 21l-4.35-4.35" />
          </svg>
          搜索结果
        </span>
        <span class="kb-count">{{ filteredCards.length }} 个知识库</span>
      </div>
      <div v-if="filteredCards.length > 0" class="kb-grid">
        <KbCard
          v-for="card in filteredCards"
          :key="card.id"
          :card="card"
          :starred="starredIds.has(card.id)"
          :pinned="pinnedIds.has(card.id)"
          @click="goToDetail(card.id)"
          @star="toggleStar(card.id)"
          @pin="togglePin(card.id)"
          @delete="deleteCard(card)"
        />
      </div>
      <div v-else class="kb-empty">
        <div class="kb-empty__icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="11" cy="11" r="8" />
            <path stroke-linecap="round" d="M21 21l-4.35-4.35" />
          </svg>
        </div>
        <p class="kb-empty__title">没有找到 "{{ searchKeyword }}" 相关知识库</p>
        <p class="kb-empty__hint">尝试其他关键词，或创建新的知识库</p>
      </div>
    </div>
    <template v-else>
      <!-- 星标知识库 -->
      <div v-if="starredCards.length > 0" class="kb-section animate-fade-in">
        <div class="kb-section__header">
          <span class="kb-section__title">
            <svg viewBox="0 0 24 24" fill="#f59e0b" stroke="#f59e0b" stroke-width="1.5">
              <path stroke-linecap="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
            星标知识库
          </span>
          <span class="kb-count">{{ starredCards.length }}</span>
        </div>
        <div class="kb-grid">
          <KbCard
            v-for="card in starredCards"
            :key="card.id"
            :card="card"
            :starred="true"
            :pinned="pinnedIds.has(card.id)"
            @click="goToDetail(card.id)"
            @star="toggleStar(card.id)"
            @pin="togglePin(card.id)"
            @delete="deleteCard(card)"
          />
        </div>
      </div>
      <!-- 最近访问 -->
      <div v-if="recentCards.length > 0" class="kb-section animate-fade-in stagger-1">
        <div class="kb-section__header">
          <span class="kb-section__title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            最近访问
          </span>
          <span class="kb-count">{{ recentCards.length }}</span>
        </div>
        <div class="kb-grid kb-grid--compact">
          <KbCard
            v-for="card in recentCards"
            :key="card.id"
            :card="card"
            :starred="starredIds.has(card.id)"
            :pinned="pinnedIds.has(card.id)"
            compact
            @click="goToDetail(card.id)"
            @star="toggleStar(card.id)"
            @pin="togglePin(card.id)"
            @delete="deleteCard(card)"
          />
        </div>
      </div>
      <!-- 全部知识库 -->
      <div class="kb-section animate-fade-in stagger-2">
        <div class="kb-section__header">
          <span class="kb-section__title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
            全部知识库
          </span>
          <div class="kb-header__controls">
            <span v-if="isDragMode" class="drag-hint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" d="M5 9l4 4 4-4M5 15l4 4 4-4" />
              </svg>
              拖拽排序中
            </span>
            <button
              class="kb-btn kb-btn--ghost kb-btn--sm"
              :class="{ 'kb-btn--active': isDragMode }"
              @click="isDragMode = !isDragMode"
              :title="isDragMode ? '完成排序' : '拖拽排序'"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" d="M4 8h16M4 12h16M4 16h16" />
              </svg>
              {{ isDragMode ? '完成排序' : '排序' }}
            </button>
            <span class="kb-count">{{ sortableCards.length }}</span>
          </div>
        </div>
        <!-- 加载状态 -->
        <div v-if="cardDataStore.loading" class="kb-loading">
          <div class="loading-spinner">
            <div class="spinner-ring"></div>
          </div>
          <span>正在加载知识库...</span>
        </div>
        <!-- 知识库网格 -->
        <div
          v-else-if="sortableCards.length > 0"
          class="kb-grid"
          :class="{ 'kb-grid--drag': isDragMode }"
        >
          <div
            v-for="(card, index) in sortableCards"
            :key="card.id"
            class="kb-drag-wrapper"
            :class="{
              'kb-drag-wrapper--draggable': isDragMode,
              'kb-drag-wrapper--dragging': dragIndex === index,
              'kb-drag-wrapper--over': dragOverIndex === index && dragIndex !== index
            }"
            :draggable="isDragMode"
            @dragstart="onDragStart($event, index)"
            @dragover.prevent="onDragOver($event, index)"
            @dragleave="onDragLeave"
            @drop="onDrop($event, index)"
            @dragend="onDragEnd"
          >
            <!-- 拖拽抓手 -->
            <div v-if="isDragMode" class="kb-drag-handle">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <circle cx="9" cy="5" r="1.5" />
                <circle cx="15" cy="5" r="1.5" />
                <circle cx="9" cy="12" r="1.5" />
                <circle cx="15" cy="12" r="1.5" />
                <circle cx="9" cy="19" r="1.5" />
                <circle cx="15" cy="19" r="1.5" />
              </svg>
            </div>
            <KbCard
              :card="card"
              :starred="starredIds.has(card.id)"
              :pinned="pinnedIds.has(card.id)"
              @click="isDragMode ? undefined : goToDetail(card.id)"
              @star="toggleStar(card.id)"
              @pin="togglePin(card.id)"
              @delete="deleteCard(card)"
            />
          </div>
          <!-- 结束占位符 — Linear风格 -->
          <div class="kb-card-end">
            <div class="kb-card-end__icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p>Nothing more</p>
          </div>
        </div>
        <!-- 空状态 -->
        <div v-else class="kb-empty">
          <div class="kb-empty__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <p class="kb-empty__title">还没有知识库</p>
          <p class="kb-empty__hint">点击右上角「新建知识库」开始整理你的知识</p>
        </div>
      </div>
    </template>
  </main>
</template>
<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import axios from 'axios'
import { useCardDataStore } from '../../store'
import { storeToRefs } from 'pinia'
import KbCard from '@/components/knowledge-unit/KbCard.vue'
const router = useRouter()
const cardDataStore = useCardDataStore()
const { allCards, filteredCards } = storeToRefs(cardDataStore)
// 搜索
const searchKeyword = ref('')
const isSearching = computed(() => searchKeyword.value.trim() !== '')
const handleSearch = () => {
  cardDataStore.filterCardData(searchKeyword.value)
}
const clearSearchKeyword = () => {
  searchKeyword.value = ''
  handleSearch()
}
// 导航
const goToDetail = (id: string) => {
  recordRecent(id)
  router.push(`/knowledge/knowledgeDetail/${id}`)
}
// ======= 星标功能（localStorage持久化） =======
const STAR_KEY = 'kb_starred_ids'
const RECENT_KEY = 'kb_recent_ids'
const PIN_KEY = 'kb_pinned_ids'
const starredIds = ref<Set<string>>(new Set())
const recentIds = ref<string[]>([])
const pinnedIds = ref<Set<string>>(new Set())
const loadStarred = () => {
  try {
    const raw = localStorage.getItem(STAR_KEY)
    starredIds.value = new Set(raw ? JSON.parse(raw) : [])
  } catch {
    starredIds.value = new Set()
  }
}
const loadRecent = () => {
  try {
    const raw = localStorage.getItem(RECENT_KEY)
    recentIds.value = raw ? JSON.parse(raw) : []
  } catch {
    recentIds.value = []
  }
}
const loadPinned = () => {
  try {
    const raw = localStorage.getItem(PIN_KEY)
    pinnedIds.value = new Set(raw ? JSON.parse(raw) : [])
  } catch {
    pinnedIds.value = new Set()
  }
}
const toggleStar = (id: string) => {
  if (starredIds.value.has(id)) {
    starredIds.value.delete(id)
    MessagePlugin.info('已取消星标')
  } else {
    starredIds.value.add(id)
    MessagePlugin.success('已加入星标')
  }
  localStorage.setItem(STAR_KEY, JSON.stringify([...starredIds.value]))
}
const togglePin = (id: string) => {
  const s = new Set(pinnedIds.value)
  if (s.has(id)) {
    s.delete(id)
    MessagePlugin.info('已取消置顶')
  } else {
    s.add(id)
    MessagePlugin.success('已置顶')
  }
  pinnedIds.value = s
  localStorage.setItem(PIN_KEY, JSON.stringify([...s]))
}
const recordRecent = (id: string) => {
  const list = [id, ...recentIds.value.filter(i => i !== id)].slice(0, 6)
  recentIds.value = list
  localStorage.setItem(RECENT_KEY, JSON.stringify(list))
}
const starredCards = computed(() => allCards.value.filter(c => starredIds.value.has(c.id)))
const recentCards = computed(() => {
  const MAX = 6
  return recentIds.value
    .map(id => allCards.value.find(c => c.id === id))
    .filter(Boolean)
    .slice(0, MAX) as any[]
})
// ======= 创建知识库 =======
const showCreateModal = ref(false)
const kbName = ref('')
const kbNameInput = ref<HTMLInputElement | null>(null)
const toggleUploadModal = () => {
  showCreateModal.value = true
  kbName.value = ''
  nextTick(() => kbNameInput.value?.focus())
}
const createKnowledgeBase = async () => {
  if (!kbName.value.trim()) return
  try {
    const formData = new FormData()
    formData.append('kbName', kbName.value)
    const userInfo = (() => {
      try {
        return JSON.parse(localStorage.getItem('user_info') || '{}')
      } catch {
        return {}
      }
    })()
    const ownerId = userInfo.id || userInfo.email || ''
    if (ownerId) formData.append('owner_id', ownerId)
    await axios.post('/api/create-knowledgebase/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    MessagePlugin.success('知识库 "' + kbName.value + '" 创建成功')
    kbName.value = ''
    showCreateModal.value = false
    await cardDataStore.fetchCards()
  } catch (error: any) {
    if (error.response?.status === 400) {
      MessagePlugin.error('知识库已存在')
    } else {
      MessagePlugin.error('创建失败，请稍后重试')
    }
  }
}
// ======= 删除知识库 =======
const deleteCard = async (card: any) => {
  try {
    await axios.delete(`/api/delete-knowledgebase/${card.id}`)
    MessagePlugin.success(`知识库「${card.title}」已删除`)
    starredIds.value.delete(card.id)
    recentIds.value = recentIds.value.filter(id => id !== card.id)
    localStorage.setItem(STAR_KEY, JSON.stringify([...starredIds.value]))
    localStorage.setItem(RECENT_KEY, JSON.stringify(recentIds.value))
    await cardDataStore.fetchCards()
  } catch {
    MessagePlugin.error('删除失败')
  }
}
onMounted(async () => {
  loadStarred()
  loadRecent()
  loadPinned()
  await cardDataStore.fetchCards()
})
// ======= 拖拽排序 =======
const DRAG_ORDER_KEY = 'kb_card_order'
const isDragMode = ref(false)
const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
const customOrder = ref<string[]>([])
const loadOrder = () => {
  try {
    const raw = localStorage.getItem(DRAG_ORDER_KEY)
    customOrder.value = raw ? JSON.parse(raw) : []
  } catch {
    customOrder.value = []
  }
}
const saveOrder = () => {
  localStorage.setItem(DRAG_ORDER_KEY, JSON.stringify(customOrder.value.map(id => id)))
}
const sortableCards = computed(() => {
  const cards = [...allCards.value]
  if (customOrder.value.length === 0) {
    return cards.sort((a, b) => {
      const ap = pinnedIds.value.has(a.id) ? 1 : 0
      const bp = pinnedIds.value.has(b.id) ? 1 : 0
      return bp - ap
    })
  }
  const orderMap = new Map(customOrder.value.map((id, i) => [id, i]))
  return cards.sort((a, b) => {
    const ap = pinnedIds.value.has(a.id) ? 1 : 0
    const bp = pinnedIds.value.has(b.id) ? 1 : 0
    if (bp !== ap) return bp - ap
    const ai = orderMap.has(a.id) ? orderMap.get(a.id)! : 9999
    const bi = orderMap.has(b.id) ? orderMap.get(b.id)! : 9999
    return ai - bi
  })
})
watch(
  allCards,
  newCards => {
    const newIds = newCards.map(c => c.id)
    const existing = new Set(customOrder.value)
    const appended = newIds.filter(id => !existing.has(id))
    if (appended.length > 0) {
      customOrder.value = [...customOrder.value.filter(id => newIds.includes(id)), ...appended]
      saveOrder()
    }
  },
  { immediate: true }
)
const onDragStart = (_e: DragEvent, index: number) => { dragIndex.value = index }
const onDragOver = (_e: DragEvent, index: number) => { dragOverIndex.value = index }
const onDragLeave = () => { dragOverIndex.value = null }
const onDrop = (_e: DragEvent, dropIndex: number) => {
  if (dragIndex.value === null || dragIndex.value === dropIndex) return
  const cards = [...sortableCards.value]
  const [moved] = cards.splice(dragIndex.value, 1)
  cards.splice(dropIndex, 0, moved)
  customOrder.value = cards.map(c => c.id)
  saveOrder()
  dragIndex.value = null
  dragOverIndex.value = null
}
const onDragEnd = () => {
  dragIndex.value = null
  dragOverIndex.value = null
}
loadOrder()
</script>
<style scoped>
/* ===== 页面 — 暗色主题 ===== */
.kb-page {
  height: 100vh;
  overflow-y: auto;
  padding: 28px 32px 48px;
  background: var(--bg-base);
  /* 顶部微渐变光晕 */
  position: relative;
}
.kb-page::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 300px;
  background: radial-gradient(ellipse 60% 200px at 30% 0%, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}
/* ===== 顶部区域 ===== */
.kb-header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 16px;
}
.kb-header__left {}
.kb-header__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.kb-header__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-emerald);
  box-shadow: 0 0 6px var(--accent-emerald);
  animation: pulseDot 2.5s ease-in-out infinite;
}
@keyframes pulseDot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.85); }
}
.kb-header__status {
  font-size: 11px;
  font-weight: 500;
  color: var(--accent-emerald);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.kb-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px;
  letter-spacing: -0.03em;
}
.kb-subtitle {
  font-size: 13.5px;
  color: var(--text-tertiary);
  margin: 0;
  letter-spacing: -0.01em;
}
.kb-header__right {
  display: flex;
  align-items: center;
  gap: 10px;
}
/* ===== 按钮系统 — Linear风格 ===== */
.kb-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-normal);
  border: none;
  white-space: nowrap;
  font-family: inherit;
  letter-spacing: -0.01em;
}
.kb-btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}
/* 主按钮 — 渐变 */
.kb-btn--primary {
  background: var(--gradient-brand);
  color: #fff;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.35);
}
.kb-btn--primary:hover:not(:disabled) {
  filter: brightness(1.12);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.5);
  transform: translateY(-1px);
}
.kb-btn--primary:active:not(:disabled) {
  transform: translateY(0);
  filter: brightness(0.95);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}
.kb-btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}
/* 次要按钮 — 毛玻璃描边 */
.kb-btn--ghost {
  background: var(--bg-elevated);
  color: var(--text-secondary);
  border: 1px solid var(--border-base);
}
.kb-btn--ghost:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-active);
}
.kb-btn--ghost:active {
  transform: scale(0.97);
}
.kb-btn--sm {
  padding: 5px 12px;
  font-size: 12.5px;
}
.kb-btn--active {
  background: var(--accent-indigo-subtle) !important;
  color: var(--text-brand) !important;
  border-color: var(--border-brand) !important;
}
/* ===== 搜索框 ===== */
.kb-search-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  border-radius: var(--radius-md);
  padding: 7px 12px;
  width: 220px;
  transition: all var(--transition-normal);
}
.kb-search-wrapper:focus-within {
  border-color: var(--border-brand);
  box-shadow: 0 0 0 3px var(--accent-indigo-subtle);
  width: 280px;
}
.kb-search-icon {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
  flex-shrink: 0;
  transition: color var(--transition-fast);
}
.kb-search-wrapper:focus-within .kb-search-icon {
  color: var(--accent-indigo);
}
.kb-search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 13px;
  color: var(--text-primary);
  background: transparent;
  min-width: 0;
  font-family: inherit;
}
.kb-search-input::placeholder {
  color: var(--text-tertiary);
}
.kb-search-clear {
  width: 16px;
  height: 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--text-tertiary);
  padding: 0;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}
.kb-search-clear:hover {
  color: var(--text-secondary);
  background: var(--bg-hover);
}
.kb-search-clear svg {
  width: 14px;
  height: 14px;
}
/* ===== 区块 ===== */
.kb-section {
  position: relative;
  z-index: 1;
  margin-bottom: 36px;
}
.kb-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.kb-section__title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: -0.01em;
}
.kb-section__title svg {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}
.kb-count {
  font-size: 11.5px;
  font-weight: 500;
  color: var(--text-tertiary);
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}
.kb-header__controls {
  display: flex;
  align-items: center;
  gap: 8px;
}
.drag-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--accent-indigo);
  background: var(--accent-indigo-subtle);
  padding: 3px 8px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-brand);
  animation: pulse-hint 1.5s ease-in-out infinite;
}
.drag-hint svg {
  width: 12px;
  height: 12px;
}
@keyframes pulse-hint {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
/* ===== 网格 ===== */
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.kb-grid--compact {
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.kb-grid--drag { cursor: default; }
/* ===== 拖拽排序 ===== */
.kb-drag-wrapper {
  position: relative;
}
.kb-drag-wrapper--draggable {
  cursor: grab;
  transition: transform var(--transition-normal), box-shadow var(--transition-normal);
}
.kb-drag-wrapper--draggable:hover {
  transform: translateY(-2px);
}
.kb-drag-wrapper--draggable:active { cursor: grabbing; }
.kb-drag-wrapper--dragging {
  opacity: 0.35;
  transform: scale(0.96);
}
.kb-drag-wrapper--over::before {
  content: '';
  position: absolute;
  inset: -3px;
  border: 2px dashed var(--accent-indigo);
  border-radius: var(--radius-xl);
  z-index: 1;
  pointer-events: none;
  background: var(--accent-indigo-subtle);
}
.kb-drag-handle {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-overlay);
  border: 1px solid var(--border-base);
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  box-shadow: var(--shadow-md);
  cursor: grab;
  transition: all var(--transition-fast);
}
.kb-drag-handle:hover {
  color: var(--text-secondary);
  background: var(--bg-hover);
  border-color: var(--border-active);
}
.kb-drag-handle svg { width: 14px; height: 14px; }
/* ===== 结束占位符 ===== */
.kb-card-end {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  border: 1.5px dashed var(--border-base);
  border-radius: var(--radius-xl);
  color: var(--text-quaternary);
  gap: 8px;
  min-height: 160px;
}
.kb-card-end__icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  background: var(--bg-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}
.kb-card-end__icon svg {
  width: 20px;
  height: 20px;
  opacity: 0.6;
}
.kb-card-end p {
  font-size: 12px;
  margin: 0;
}
/* ===== 空状态 ===== */
.kb-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 20px;
  gap: 10px;
}
.kb-empty__icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-2xl);
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}
.kb-empty__icon svg {
  width: 30px;
  height: 30px;
  color: var(--text-tertiary);
  opacity: 0.7;
}
.kb-empty__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0;
}
.kb-empty__hint {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
  text-align: center;
}
/* ===== 加载 ===== */
.kb-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 48px;
  color: var(--text-secondary);
  font-size: 14px;
}
.loading-spinner {
  width: 22px;
  height: 22px;
}
.spinner-ring {
  width: 100%;
  height: 100%;
  border: 2px solid var(--border-base);
  border-top-color: var(--accent-indigo);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
/* ===== 弹窗 — 毛玻璃暗色 ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(6px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  border-radius: var(--radius-2xl);
  width: 440px;
  max-width: 92vw;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 24px 24px 20px;
  border-bottom: 1px solid var(--border-subtle);
}
.modal-header__left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.modal-icon {
  width: 42px;
  height: 42px;
  border-radius: var(--radius-lg);
  background: var(--accent-indigo-subtle);
  border: 1px solid var(--border-brand);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.modal-icon svg {
  width: 22px;
  height: 22px;
  stroke: var(--accent-indigo);
}
.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 3px;
  letter-spacing: -0.02em;
}
.modal-subtitle {
  font-size: 12.5px;
  color: var(--text-tertiary);
  margin: 0;
}
.modal-close {
  width: 30px;
  height: 30px;
  border: none;
  background: var(--bg-hover);
  cursor: pointer;
  color: var(--text-tertiary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}
.modal-close:hover {
  background: var(--bg-active);
  color: var(--text-secondary);
}
.modal-close svg {
  width: 16px;
  height: 16px;
}
.modal-body {
  padding: 20px 24px;
}
.modal-label {
  display: block;
  font-size: 12.5px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
  letter-spacing: -0.01em;
}
.modal-input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-overlay);
  border: 1px solid var(--border-base);
  border-radius: var(--radius-md);
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
  transition: all var(--transition-normal);
  font-family: inherit;
  box-sizing: border-box;
}
.modal-input::placeholder {
  color: var(--text-tertiary);
}
.modal-input:focus {
  border-color: var(--border-brand);
  box-shadow: 0 0 0 3px var(--accent-indigo-subtle);
}
.modal-hints {
  margin-top: 10px;
}
.modal-hint {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  color: var(--text-tertiary);
}
.modal-hint svg {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 24px 24px;
}
/* ===== 响应式 ===== */
@media (max-width: 640px) {
  .kb-page { padding: 16px; }
  .kb-grid { grid-template-columns: 1fr; }
  .kb-search-wrapper { width: 160px; }
  .kb-search-wrapper:focus-within { width: 190px; }
}
</style>
