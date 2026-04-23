<template>
  <main class="knowledge-page">
    <!-- 页面头部 -->
    <header class="page-header animate-fade-in-up">
      <div class="page-header__content">
        <div class="page-header__meta">
          <span class="status-indicator"></span>
          <span class="status-text">知识库</span>
        </div>
        <h1 class="page-header__title">我的知识库</h1>
        <p class="page-header__desc">管理和检索你的所有知识内容</p>
      </div>
      
      <!-- 操作区 -->
      <div class="page-header__actions">
        <!-- 搜索 -->
        <div class="search-box">
          <svg class="search-box__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <circle cx="11" cy="11" r="8"/>
            <path stroke-linecap="round" d="M21 21l-4.35-4.35"/>
          </svg>
          <input
            v-model="searchKeyword"
            type="text"
            class="search-box__input"
            placeholder="搜索知识库..."
            @input="handleSearch"
          />
          <button v-if="searchKeyword" class="search-box__clear" @click="clearSearch">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <!-- 导航按钮 -->
        <button class="btn btn-ghost" @click="$router.push('/square')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          广场
        </button>

        <!-- 新建按钮 -->
        <button class="btn btn-primary" @click="toggleCreateModal">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" d="M12 4v16m8-8H4"/>
          </svg>
          新建知识库
        </button>
      </div>
    </header>

    <!-- 内容区域 -->
    <div class="page-content">
      <!-- 搜索结果 -->
      <template v-if="isSearching">
        <section class="content-section animate-fade-in">
          <div class="section-header">
            <h2 class="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <circle cx="11" cy="11" r="8"/>
                <path stroke-linecap="round" d="M21 21l-4.35-4.35"/>
              </svg>
              搜索结果
            </h2>
            <span class="section-count">{{ filteredCards.length }}</span>
          </div>
          
          <div v-if="filteredCards.length > 0" class="card-grid">
            <KbCard
              v-for="(card, index) in filteredCards"
              :key="card.id"
              :card="card"
              :starred="starredIds.has(card.id)"
              :pinned="pinnedIds.has(card.id)"
              class="animate-fade-in-up"
              :style="{ animationDelay: `${index * 50}ms` }"
              @click="goToDetail(card.id)"
              @star="toggleStar(card.id)"
              @pin="togglePin(card.id)"
              @delete="deleteCard(card)"
            />
          </div>
          
          <div v-else class="empty-state">
            <div class="empty-state__icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="11" cy="11" r="8"/>
                <path stroke-linecap="round" d="M21 21l-4.35-4.35"/>
              </svg>
            </div>
            <p class="empty-state__title">未找到 "{{ searchKeyword }}" 相关知识库</p>
            <p class="empty-state__desc">尝试其他关键词</p>
          </div>
        </section>
      </template>

      <!-- 正常内容 -->
      <template v-else>
        <!-- 星标区域 -->
        <section v-if="starredCards.length > 0" class="content-section animate-fade-in">
          <div class="section-header">
            <h2 class="section-title">
              <svg viewBox="0 0 24 24" fill="#fbbf24" stroke="#fbbf24" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
              </svg>
              星标知识库
            </h2>
            <span class="section-count">{{ starredCards.length }}</span>
          </div>
          
          <div class="card-grid">
            <KbCard
              v-for="(card, index) in starredCards"
              :key="card.id"
              :card="card"
              :starred="true"
              :pinned="pinnedIds.has(card.id)"
              class="animate-fade-in-up"
              :style="{ animationDelay: `${index * 50}ms` }"
              @click="goToDetail(card.id)"
              @star="toggleStar(card.id)"
              @pin="togglePin(card.id)"
              @delete="deleteCard(card)"
            />
          </div>
        </section>

        <!-- 最近访问 -->
        <section v-if="recentCards.length > 0" class="content-section animate-fade-in">
          <div class="section-header">
            <h2 class="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              最近访问
            </h2>
            <span class="section-count">{{ recentCards.length }}</span>
          </div>
          
          <div class="card-grid card-grid--compact">
            <KbCard
              v-for="(card, index) in recentCards"
              :key="card.id"
              :card="card"
              :starred="starredIds.has(card.id)"
              :pinned="pinnedIds.has(card.id)"
              compact
              class="animate-fade-in-up"
              :style="{ animationDelay: `${index * 50}ms` }"
              @click="goToDetail(card.id)"
              @star="toggleStar(card.id)"
              @pin="togglePin(card.id)"
              @delete="deleteCard(card)"
            />
          </div>
        </section>

        <!-- 全部知识库 -->
        <section class="content-section animate-fade-in">
          <div class="section-header">
            <h2 class="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
              </svg>
              全部知识库
            </h2>
            <div class="section-actions">
              <button 
                class="btn btn-ghost btn-sm"
                :class="{ 'btn-ghost--active': isDragMode }"
                @click="isDragMode = !isDragMode"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 8h16M4 12h16M4 16h16"/>
                </svg>
                {{ isDragMode ? '完成排序' : '排序' }}
              </button>
              <span class="section-count">{{ sortableCards.length }}</span>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="cardDataStore.loading" class="loading-state">
            <div class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span>加载中...</span>
          </div>

          <!-- 卡片网格 -->
          <div 
            v-else-if="sortableCards.length > 0"
            class="card-grid"
            :class="{ 'card-grid--drag': isDragMode }"
          >
            <div
              v-for="(card, index) in sortableCards"
              :key="card.id"
              class="card-wrapper"
              :class="{
                'card-wrapper--dragging': dragIndex === index,
                'card-wrapper--over': dragOverIndex === index && dragIndex !== index
              }"
              :draggable="isDragMode"
              @dragstart="onDragStart($event, index)"
              @dragover.prevent="onDragOver($event, index)"
              @dragleave="onDragLeave"
              @drop="onDrop($event, index)"
              @dragend="onDragEnd"
            >
              <div v-if="isDragMode" class="drag-handle">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <circle cx="9" cy="5" r="1.5"/>
                  <circle cx="15" cy="5" r="1.5"/>
                  <circle cx="9" cy="12" r="1.5"/>
                  <circle cx="15" cy="12" r="1.5"/>
                  <circle cx="9" cy="19" r="1.5"/>
                  <circle cx="15" cy="19" r="1.5"/>
                </svg>
              </div>
              <KbCard
                :card="card"
                :starred="starredIds.has(card.id)"
                :pinned="pinnedIds.has(card.id)"
                class="animate-fade-in-up"
                :style="{ animationDelay: `${index * 30}ms` }"
                @click="isDragMode ? undefined : goToDetail(card.id)"
                @star="toggleStar(card.id)"
                @pin="togglePin(card.id)"
                @delete="deleteCard(card)"
              />
            </div>

            <!-- 结束占位 -->
            <div class="end-marker">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>已加载全部</span>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="empty-state">
            <div class="empty-state__icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
              </svg>
            </div>
            <p class="empty-state__title">还没有知识库</p>
            <p class="empty-state__desc">点击右上角「新建知识库」开始</p>
          </div>
        </section>
      </template>
    </div>

    <!-- 创建弹窗 -->
    <Teleport to="body">
      <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
        <div class="modal animate-spring-in">
          <div class="modal__header">
            <div class="modal__icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
              </svg>
            </div>
            <div class="modal__info">
              <h3 class="modal__title">新建知识库</h3>
              <p class="modal__desc">创建一个新的知识空间</p>
            </div>
            <button class="modal__close" @click="showCreateModal = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          
          <div class="modal__body">
            <label class="input-label">知识库名称</label>
            <input
              ref="nameInputRef"
              v-model="kbName"
              type="text"
              class="input"
              placeholder="输入知识库名称..."
              @keydown.enter="createKnowledgeBase"
            />
            <p class="input-hint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              名称将用于知识库的显示和搜索
            </p>
          </div>
          
          <div class="modal__footer">
            <button class="btn btn-secondary" @click="showCreateModal = false">取消</button>
            <button 
              class="btn btn-primary" 
              :disabled="!kbName.trim()"
              @click="createKnowledgeBase"
            >
              创建
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
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
const handleSearch = () => cardDataStore.filterCardData(searchKeyword.value)
const clearSearch = () => {
  searchKeyword.value = ''
  handleSearch()
}

// 导航
const goToDetail = (id: string) => {
  recordRecent(id)
  router.push(`/knowledge/knowledgeDetail/${id}`)
}

// 星标/置顶/最近
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
  } catch { starredIds.value = new Set() }
}

const loadRecent = () => {
  try {
    const raw = localStorage.getItem(RECENT_KEY)
    recentIds.value = raw ? JSON.parse(raw) : []
  } catch { recentIds.value = [] }
}

const loadPinned = () => {
  try {
    const raw = localStorage.getItem(PIN_KEY)
    pinnedIds.value = new Set(raw ? JSON.parse(raw) : [])
  } catch { pinnedIds.value = new Set() }
}

const toggleStar = (id: string) => {
  starredIds.value.has(id) 
    ? starredIds.value.delete(id)
    : starredIds.value.add(id)
  localStorage.setItem(STAR_KEY, JSON.stringify([...starredIds.value]))
}

const togglePin = (id: string) => {
  const s = new Set(pinnedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  pinnedIds.value = s
  localStorage.setItem(PIN_KEY, JSON.stringify([...s]))
}

const recordRecent = (id: string) => {
  recentIds.value = [id, ...recentIds.value.filter(i => i !== id)].slice(0, 6)
  localStorage.setItem(RECENT_KEY, JSON.stringify(recentIds.value))
}

const starredCards = computed(() => allCards.value.filter(c => starredIds.value.has(c.id)))

const recentCards = computed(() => 
  recentIds.value
    .map(id => allCards.value.find(c => c.id === id))
    .filter(Boolean)
    .slice(0, 6) as any[]
)

// 创建知识库
const showCreateModal = ref(false)
const kbName = ref('')
const nameInputRef = ref<HTMLInputElement | null>(null)

const toggleCreateModal = () => {
  showCreateModal.value = true
  kbName.value = ''
  nextTick(() => nameInputRef.value?.focus())
}

const createKnowledgeBase = async () => {
  if (!kbName.value.trim()) return
  try {
    const formData = new FormData()
    formData.append('kbName', kbName.value)
    const userInfo = (() => {
      try { return JSON.parse(localStorage.getItem('user_info') || '{}') }
      catch { return {} }
    })()
    if (userInfo.id || userInfo.email) formData.append('owner_id', userInfo.id || userInfo.email)
    
    await axios.post('/api/create-knowledgebase/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    MessagePlugin.success(`知识库 "${kbName.value}" 创建成功`)
    kbName.value = ''
    showCreateModal.value = false
    await cardDataStore.fetchCards()
  } catch (e: any) {
    MessagePlugin.error(e.response?.status === 400 ? '知识库已存在' : '创建失败')
  }
}

// 删除
const deleteCard = async (card: any) => {
  try {
    await axios.delete(`/api/delete-knowledgebase/${card.id}`)
    MessagePlugin.success(`「${card.title}」已删除`)
    starredIds.value.delete(card.id)
    recentIds.value = recentIds.value.filter(id => id !== card.id)
    localStorage.setItem(STAR_KEY, JSON.stringify([...starredIds.value]))
    localStorage.setItem(RECENT_KEY, JSON.stringify(recentIds.value))
    await cardDataStore.fetchCards()
  } catch { MessagePlugin.error('删除失败') }
}

// 拖拽排序
const DRAG_ORDER_KEY = 'kb_card_order'
const isDragMode = ref(false)
const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
const customOrder = ref<string[]>([])

const loadOrder = () => {
  try {
    const raw = localStorage.getItem(DRAG_ORDER_KEY)
    customOrder.value = raw ? JSON.parse(raw) : []
  } catch { customOrder.value = [] }
}

const saveOrder = () => {
  localStorage.setItem(DRAG_ORDER_KEY, JSON.stringify(customOrder.value))
}

const sortableCards = computed(() => {
  const cards = [...allCards.value]
  if (customOrder.value.length === 0) {
    return cards.sort((a, b) => (pinnedIds.value.has(b.id) ? 1 : 0) - (pinnedIds.value.has(a.id) ? 1 : 0))
  }
  const orderMap = new Map(customOrder.value.map((id, i) => [id, i]))
  return cards.sort((a, b) => {
    if (pinnedIds.value.has(b.id) !== pinnedIds.value.has(a.id)) 
      return (pinnedIds.value.has(b.id) ? 1 : 0) - (pinnedIds.value.has(a.id) ? 1 : 0))
    const ai = orderMap.has(a.id) ? orderMap.get(a.id)! : 9999
    const bi = orderMap.has(b.id) ? orderMap.get(b.id)! : 9999
    return ai - bi
  })
})

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
const onDragEnd = () => { dragIndex.value = null; dragOverIndex.value = null }

onMounted(async () => {
  loadStarred()
  loadRecent()
  loadPinned()
  loadOrder()
  await cardDataStore.fetchCards()
})
</script>

<style scoped>
/* =====================================================
   知识库页面 — Geist x Linear 风格
   ===================================================== */

/* 页面容器 */
.knowledge-page {
  min-height: 100vh;
  padding: calc(var(--header-height) + var(--space-6)) var(--space-6) var(--space-8);
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-6);
  margin-bottom: var(--space-8);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--border-subtle);
}

.page-header__content {
  flex: 1;
}

.page-header__meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--accent-success);
  box-shadow: 0 0 8px var(--accent-success);
  animation: breathe 2s ease-in-out infinite;
}

.status-text {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--accent-success);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.page-header__title {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-2);
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.page-header__desc {
  font-size: var(--text-md);
  color: var(--text-secondary);
  margin: 0;
}

.page-header__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

/* 搜索框 */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  width: 220px;
  background: var(--bg-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  gap: var(--space-2);
  transition: all var(--transition-normal);
}

.search-box:focus-within {
  width: 280px;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px var(--accent-primary-subtle);
}

.search-box__icon {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
  flex-shrink: 0;
  transition: color var(--transition-fast);
}

.search-box:focus-within .search-box__icon {
  color: var(--accent-primary);
}

.search-box__input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-family: inherit;
}

.search-box__input::placeholder {
  color: var(--text-tertiary);
}

.search-box__clear {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-xs);
  transition: all var(--transition-fast);
}

.search-box__clear:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.search-box__clear svg {
  width: 14px;
  height: 14px;
}

/* 内容区域 */
.page-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

/* 内容区块 */
.content-section {
  animation: fadeIn var(--transition-slow) var(--ease-out-expo) both;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.section-title svg {
  width: 16px;
  height: 16px;
}

.section-count {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--text-tertiary);
  background: var(--bg-overlay);
  border: 1px solid var(--border-subtle);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.section-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* 卡片网格 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.card-grid--compact {
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-3);
}

.card-grid--drag {
  cursor: default;
}

/* 拖拽 */
.card-wrapper {
  position: relative;
}

.card-wrapper--draggable {
  cursor: grab;
}

.card-wrapper--draggable:active {
  cursor: grabbing;
}

.card-wrapper--dragging {
  opacity: 0.3;
  transform: scale(0.96);
}

.card-wrapper--over::before {
  content: '';
  position: absolute;
  inset: -4px;
  border: 2px dashed var(--accent-primary);
  border-radius: var(--radius-lg);
  background: var(--accent-primary-subtle);
  z-index: 10;
  pointer-events: none;
}

.drag-handle {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  z-index: 20;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  cursor: grab;
  box-shadow: var(--shadow-sm);
}

.drag-handle:hover {
  background: var(--bg-overlay-hover);
  color: var(--text-secondary);
}

.drag-handle svg {
  width: 14px;
  height: 14px;
}

/* 结束标记 */
.end-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-8) var(--space-4);
  border: 1.5px dashed var(--border-subtle);
  border-radius: var(--radius-lg);
  color: var(--text-disabled);
  font-size: var(--text-sm);
  min-height: 140px;
}

.end-marker svg {
  width: 24px;
  height: 24px;
  opacity: 0.5;
}

/* 加载状态 */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-10);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) var(--space-4);
  text-align: center;
}

.empty-state__icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  margin-bottom: var(--space-4);
  color: var(--text-tertiary);
}

.empty-state__icon svg {
  width: 28px;
  height: 28px;
}

.empty-state__title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 var(--space-2);
}

.empty-state__desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin: 0;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
}

.modal {
  width: 100%;
  max-width: 420px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modal__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5);
  border-bottom: 1px solid var(--border-subtle);
}

.modal__icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-primary-subtle);
  border: 1px solid var(--border-brand);
  border-radius: var(--radius-lg);
  color: var(--accent-primary);
  flex-shrink: 0;
}

.modal__icon svg {
  width: 20px;
  height: 20px;
}

.modal__info {
  flex: 1;
}

.modal__title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 2px;
}

.modal__desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin: 0;
}

.modal__close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-hover);
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.modal__close:hover {
  background: var(--bg-overlay-hover);
  color: var(--text-primary);
}

.modal__close svg {
  width: 16px;
  height: 16px;
}

.modal__body {
  padding: var(--space-5);
}

.input-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
}

.input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-family: inherit;
  color: var(--text-primary);
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

.input-hint {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: var(--space-2) 0 0;
}

.input-hint svg {
  width: 14px;
  height: 14px;
}

.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-surface);
}

/* 动画 */
@keyframes breathe {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.9); }
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .page-header__actions {
    flex-wrap: wrap;
  }
  
  .search-box {
    width: 100%;
  }
  
  .search-box:focus-within {
    width: 100%;
  }
  
  .card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
