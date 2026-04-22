<template>
  <main class="kb-page">
    <!-- ═══ 顶部 Hero 区域 ═══ -->
    <header class="kb-hero">
      <!-- 装饰光效 -->
      <div class="kb-hero__glow kb-hero__glow--1" />
      <div class="kb-hero__glow kb-hero__glow--2" />

      <div class="kb-hero__content">
        <div class="kb-hero__left">
          <!-- 标题组 -->
          <div class="kb-title-group nova-animate-in">
            <div class="kb-title-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#kbIconGrad)" stroke-width="2" stroke-linecap="round">
                <defs>
                  <linearGradient id="kbIconGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#3b82f6"/>
                    <stop offset="50%" stop-color="#8b5cf6"/>
                    <stop offset="100%" stop-color="#ec4899"/>
                  </linearGradient>
                </defs>
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
            </div>
            <div>
              <h1 class="kb-title">
                <span class="nova-gradient-text-animated">知识库</span>
              </h1>
              <p class="kb-subtitle">管理和检索你的所有知识内容</p>
            </div>
          </div>
        </div>

        <div class="kb-hero__actions nova-animate-in nova-animate-in--delay-2">
          <!-- 搜索框 -->
          <div class="kb-search">
            <svg class="kb-search__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <circle cx="11" cy="11" r="8"/><path stroke-linecap="round" d="M21 21l-4.35-4.35"/>
            </svg>
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索知识库..."
              class="kb-search__input"
              @input="handleSearch"
            />
            <button
              v-if="searchKeyword"
              class="kb-search__clear"
              @click="clearSearchKeyword"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
            <kbd class="kb-search__kbd">/</kbd>
          </div>

          <!-- 新建按钮 -->
          <NovaButton variant="primary" size="lg" @click="toggleUploadModal">
            <template #icon>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" d="M12 4v16m8-8H4"/></svg>
            </template>
            新建知识库
          </NovaButton>
        </div>
      </div>
    </header>

    <!-- ═══ 创建弹窗 ═══ -->
    <teleport to="body">
      <transition name="modal-glow">
        <div v-if="showCreateModal" class="nova-modal-overlay" @click.self="showCreateModal = false">
          <div class="nova-modal-card nova-animate-in">
            <header class="nova-modal-header">
              <div class="nova-modal-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                  <line x1="12" y1="6" x2="12" y2="14"/>
                  <line x1="8" y1="10" x2="16" y2="10"/>
                </svg>
              </div>
              <h3>新建知识库</h3>
              <button class="nova-modal-close" @click="showCreateModal = false">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </header>
            <div class="nova-modal-body">
              <label class="nova-label">知识库名称</label>
              <input
                v-model="kbName"
                type="text"
                class="nova-modal-input"
                placeholder="输入名称..."
                @keydown.enter="createKnowledgeBase"
              />
            </div>
            <footer class="nova-modal-footer">
              <NovaButton variant="ghost" size="sm" @click="showCreateModal = false">取消</NovaButton>
              <NovaButton variant="primary" size="sm" :disabled="!kbName.trim()" @click="createKnowledgeBase">创建</NovaButton>
            </footer>
          </div>
        </div>
      </transition>
    </teleport>

    <!-- ═══ 搜索结果 ═══ -->
    <section v-if="isSearching" class="kb-section nova-animate-in">
      <div class="kb-section-head">
        <h2 class="kb-section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--nova-info)" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path stroke-linecap="round" d="M21 21l-4.35-4.35"/></svg>
          搜索结果
        </h2>
        <NovaBadge type="primary">{{ filteredCards.length }} 个结果</NovaBadge>
      </div>

      <div v-if="filteredCards.length > 0" class="kb-grid nova-stagger-grid">
        <div v-for="card in filteredCards" :key="card.id" class="kb-grid-item">
          <NovaCard hoverable clickable accent="blue" @click="goToDetail(card.id)">
            <template #header>
              <div class="kb-card-header">
                <div class="kb-card-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                </div>
                <div class="kb-card-info">
                  <h4>{{ card.title }}</h4>
                  <span>知识库</span>
                </div>
              </div>
            </template>
            <p class="kb-card-desc">{{ card.description || '暂无描述' }}</p>
          </NovaCard>
        </div>
      </div>

      <div v-else class="kb-empty">
        <div class="kb-empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path stroke-linecap="round" d="M21 21l-4.35-4.35"/></svg>
        </div>
        <p>没有找到「{{ searchKeyword }}」相关内容</p>
      </div>
    </section>

    <!-- ═══ 主内容区 ═══ -->
    <template v-else>
      <!-- 星标区域 -->
      <section v-if="starredCards.length > 0" class="kb-section nova-animate-in">
        <div class="kb-section-head">
          <h2 class="kb-section-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="#f59e0b" stroke="#f59e0b" stroke-width="2"><path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/></svg>
            星标知识库
          </h2>
          <NovaBadge type="warning">{{ starredCards.length }}</NovaBadge>
        </div>
        <div class="kb-grid nova-stagger-grid">
          <div v-for="card in starredCards" :key="card.id" class="kb-grid-item">
            <NovaCard hoverable clickable accent="warning" @click="goToDetail(card.id)">
              <template #header>
                <div class="kb-card-header">
                  <div class="kb-card-icon kb-card-icon--warning">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                  </div>
                  <div class="kb-card-info">
                    <h4>{{ card.title }}</h4>
                    <span>知识库</span>
                  </div>
                </div>
              </template>
              <p class="kb-card-desc">{{ card.description || '暂无描述' }}</p>
            </NovaCard>
          </div>
        </div>
      </section>

      <!-- 全部知识库 -->
      <section class="kb-section nova-animate-in nova-animate-in--delay-1">
        <div class="kb-section-head">
          <h2 class="kb-section-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
            全部知识库
          </h2>
          <div class="kb-section-actions">
            <button
              class="kb-sort-btn"
              :class="{ active: isDragMode }"
              @click="isDragMode = !isDragMode"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
              {{ isDragMode ? '完成' : '排序' }}
            </button>
            <NovaBadge type="primary">{{ sortableCards.length }}</NovaBadge>
          </div>
        </div>

        <!-- 加载骨架屏 -->
        <div v-if="cardDataStore.loading" class="kb-loading nova-stagger-grid">
          <NovaSkeleton v-for="i in 6" :key="i" variant="card" />
        </div>

        <!-- 卡片网格 -->
        <div
          v-else-if="sortableCards.length > 0"
          class="kb-grid"
          :class="{ 'kb-grid--drag': isDragMode }"
        >
          <div
            v-for="(card, index) in sortableCards"
            :key="card.id"
            class="kb-grid-item"
            :class="{
              'kb-grid-item--draggable': isDragMode,
              'kb-grid-item--active': dragIndex === index,
            }"
            :draggable="isDragMode"
            @dragstart="onDragStart($event, index)"
            @dragover.prevent="onDragOver($event, index)"
            @dragleave="onDragLeave"
            @drop="onDrop($event, index)"
            @dragend="onDragEnd"
          >
            <NovaCard
              hoverable
              clickable
              :accent="starredIds.has(card.id) ? 'warning' : 'blue'"
              @click="isDragMode ? undefined : goToDetail(card.id)"
            >
              <template #header>
                <div class="kb-card-header">
                  <div class="kb-card-icon" :class="{ 'kb-card-icon--warning': starredIds.has(card.id) }">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                  </div>
                  <div class="kb-card-info">
                    <h4>{{ card.title }}</h4>
                    <span>知识库</span>
                  </div>
                  <div v-if="isDragMode" class="kb-drag-handle">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="9" cy="5" r="1.5" fill="currentColor"/><circle cx="15" cy="5" r="1.5" fill="currentColor"/><circle cx="9" cy="12" r="1.5" fill="currentColor"/><circle cx="15" cy="12" r="1.5" fill="currentColor"/><circle cx="9" cy="19" r="1.5" fill="currentColor"/><circle cx="15" cy="19" r="1.5" fill="currentColor"/></svg>
                  </div>
                </div>
              </template>
              <p class="kb-card-desc">{{ card.description || '暂无描述' }}</p>
            </NovaCard>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="kb-empty nova-animate-in">
          <div class="kb-empty-art">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          </div>
          <h3>还没有知识库</h3>
          <p>点击右上角「新建知识库」开始创建</p>
          <NovaButton variant="primary" @click="toggleUploadModal">
            <template #icon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" d="M12 4v16m8-8H4"/></svg>
            </template>
            创建第一个知识库
          </NovaButton>
        </div>
      </section>
    </template>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useCardDataStore } from '../../store'
import { storeToRefs } from 'pinia'
import { NovaButton, NovaCard, NovaBadge, NovaSkeleton } from '@/components/nova'

const router = useRouter()
const cardDataStore = useCardDataStore()
const { allCards, filteredCards } = storeToRefs(cardDataStore)

// ── 搜索 ──
const searchKeyword = ref('')
const isSearching = computed(() => searchKeyword.value.trim() !== '')
const handleSearch = () => cardDataStore.filterCardData(searchKeyword.value)
const clearSearchKeyword = () => { searchKeyword.value = ''; handleSearch() }

// ── 导航 ──
const goToDetail = (id: string) => { recordRecent(id); router.push(`/knowledge/knowledgeDetail/${id}`) }

// ── 星标 / 最近 / 置顶 (localStorage) ──
const STAR_KEY = 'kb_starred_ids', RECENT_KEY = 'kb_recent_ids', PIN_KEY = 'kb_pinned_ids'
const starredIds = ref<Set<string>>(new Set())
const recentIds = ref<string[]>([])
const pinnedIds = ref<Set<string>>(new Set())

const loadStarred = () => { try { starredIds.value = new Set(JSON.parse(localStorage.getItem(STAR_KEY) || '')) } catch {} }
const saveStarred = () => localStorage.setItem(STAR_KEY, JSON.stringify([...starredIds.value]))
const toggleStar = (id: string) => { const s = starredIds.value; if (s.has(id)) s.delete(id); else s.add(id); starredIds.value = new Set(s); saveStarred() }

const loadPinned = () => { try { pinnedIds.value = new Set(JSON.parse(localStorage.getItem(PIN_KEY) || '')) } catch {} }
const togglePin = (id: string) => { const p = pinnedIds.value; if (p.has(id)) p.delete(id); else p.add(id); pinnedIds.value = new Set(p); localStorage.setItem(PIN_KEY, JSON.stringify([...p])) }

const loadRecent = () => { try { recentIds.value = JSON.parse(localStorage.getItem(RECENT_KEY) || '') } catch {} }
const recordRecent = (id: string) => { recentIds.value = [id, ...recentIds.value.filter(i => i !== id)].slice(0, 10); localStorage.setItem(RECENT_KEY, JSON.stringify(recentIds.value)) }

const starredCards = computed(() => allCards.value.filter(c => starredIds.value.has(c.id)))
const sortableCards = computed(() => {
  const pinned = allCards.value.filter(c => pinnedIds.value.has(c.id))
  return [...pinned, ...allCards.value.filter(c => !pinnedIds.value.has(c.id))]
})

// ── 拖拽排序 ──
const isDragMode = ref(false), dragIndex = ref(-1), dragOverIndex = ref(-1)
const onDragStart = (e: DragEvent, i: number) => { dragIndex.value = i; e.dataTransfer && (e.dataTransfer.effectAllowed = 'move') }
const onDragOver = (_e: DragEvent, i: number) => { dragOverIndex.value = i }
const onDragLeave = () => {}
const onDrop = (_e: DragEvent, _targetIdx: number) => { dragIndex.value = -1; dragOverIndex.value = -1 }
const onDragEnd = () => { dragIndex.value = -1; dragOverIndex.value = -1 }

// ── 创建知识库 ──
const showCreateModal = ref(false), kbName = ref('')
const toggleUploadModal = () => { showCreateModal.value = !showCreateModal.value; if (!showCreateModal.value) kbName.value = '' }

const createKnowledgeBase = async () => {
  if (!kbName.value.trim()) return
  try {
    const fd = new FormData(); fd.append('kbName', kbName.value)
    let ui: any = {}
    try { ui = JSON.parse(localStorage.getItem('user_info') || '{}') } catch {}
    const oid = ui.id || ui.email || ''
    if (oid) fd.append('owner_id', oid)
    await axios.post('/api/create-knowledgebase/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    alert(`知识库「${kbName.value}」创建成功`)
    showCreateModal.value = false; kbName.value = ''
    await cardDataStore.fetchCards()
  } catch (e: any) { alert(e.response?.status === 400 ? '知识库名称已存在' : '创建失败，请稍后重试') }
}

const deleteCard = async (card: any) => {
  if (!confirm(`确定删除知识库「${card.title}」吗？`)) return
  await axios.delete(`/api/knowledgebases/${card.id}`)
  alert('删除成功')
  await cardDataStore.fetchCards()
}

onMounted(async () => { void loadStarred(); void loadPinned(); void loadRecent(); await cardDataStore.fetchCards() })
</script>

<style scoped>
/* ============================================
   KB Page — Game-Grade Knowledge Base Page v2.0
   ============================================ */

.kb-page {
  padding: var(--nova-space-8);
  max-width: var(--nova-content-max-width);
  margin: 0 auto;
  min-height: 100%;
}

/* ═══ Hero 区域 ═══ */
.kb-hero {
  position: relative;
  padding-bottom: var(--nova-space-10);
  margin-bottom: var(--nova-space-8);
  overflow: hidden;

  /* 底部分隔线 */
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--nova-border-hover), transparent);
  }
}

.kb-hero__glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.25;
  pointer-events: none;
}
.kb-hero__glow--1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, rgba(99,102,241,0.4), transparent 70%);
  top: -200px; right: -100px;
  animation: heroGlow1 15s ease-in-out infinite alternate;
}
.kb-hero__glow--2 {
  width: 350px; height: 350px;
  background: radial-gradient(circle, rgba(139,92,246,0.3), transparent 70%);
  bottom: -150px; left: -80px;
  animation: heroGlow2 18s ease-in-out infinite alternate-reverse;
}

@keyframes heroGlow1 {
  0% { transform: translate(0, 0) scale(1); }
  100% { transform: translate(-40px, 30px) scale(1.15); }
}
@keyframes heroGlow2 {
  0% { transform: translate(0, 0) scale(1); }
  100% { transform: translate(30px, -40px) scale(1.1); }
}

.kb-hero__content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--nova-space-6);
  flex-wrap: wrap;
  position: relative;
}

/* 标题 */
.kb-title-group {
  display: flex;
  align-items: center;
  gap: var(--nova-space-4);
}

.kb-title-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px; height: 56px;
  border-radius: var(--radius-xl);
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.15);
  box-shadow:
    0 0 30px rgba(99, 102, 241, 0.1),
    inset 0 0 20px rgba(99, 102, 241, 0.05);

  /* 呼吸发光 */
  animation: titleIconBreath 4s ease-in-out infinite alternate;
}
@keyframes titleIconBreath {
  from { box-shadow: 0 0 30px rgba(99, 102, 241, 0.1), inset 0 0 20px rgba(99, 102, 241, 0.05); }
  to { box-shadow: 0 0 50px rgba(139, 92, 246, 0.2), inset 0 0 25px rgba(139, 92, 246, 0.08); }
}

.kb-title {
  font-size: var(--nova-text-4xl);
  font-weight: var(--nova-font-extrabold);
  line-height: var(--nova-leading-tight);
  margin: 0 0 var(--nova-space-1);
  letter-spacing: -0.02em;
}

.kb-subtitle {
  font-size: var(--nova-text-base);
  color: var(--nova-text-secondary);
  margin: 0;
}

/* Hero 操作区 */
.kb-hero__actions {
  display: flex;
  align-items: center;
  gap: var(--nova-space-4);
  flex-shrink: 0;
}

/* 搜索框 */
.kb-search {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(15, 23, 42, 0.65);
  border: 1.5px solid var(--nova-border);
  border-radius: var(--radius-xl);
  padding: 0 var(--nova-space-4);
  min-width: 300px;
  transition: all var(--nova-duration-fast) ease;

  &:focus-within {
    border-color: rgba(99, 102, 241, 0.45);
    box-shadow:
      0 0 0 3px rgba(99, 102, 241, 0.08),
      0 0 30px rgba(99, 102, 241, 0.06);
  }
}

.kb-search__icon {
  color: var(--nova-text-muted);
  flex-shrink: 0;
  transition: color var(--nova-duration-fast) ease;
}
.kb-search:focus-within .kb-search__icon { color: var(--nova-info); }

.kb-search__input {
  flex: 1;
  height: 48px;
  padding: 0 var(--nova-space-3);
  background: transparent;
  border: none;
  font-size: var(--nova-text-sm);
  font-family: var(--nova-font-display);
  color: var(--nova-text-primary);
  outline: none;
  &::placeholder { color: var(--nova-text-muted); }
}

.kb-search__clear {
  display: flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border: none; border-radius: var(--radius-full);
  background: rgba(239,68,68,0.08); color: var(--nova-text-muted); cursor: pointer;
  transition: all var(--nova-duration-fast) ease;
  &:hover { background: rgba(239,68,68,0.18); color: var(--nova-error); }
}

.kb-search__kbd {
  font-size: 11px;
  font-family: var(--nova-font-mono);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  background: rgba(148,163,184,0.08);
  color: var(--nova-text-muted);
  border: 1px solid var(--nova-border);
  margin-left: var(--nova-space-2);
  pointer-events: none;
}

/* ═══ Section ═══ */
.kb-section { margin-bottom: var(--nova-space-10); }

.kb-section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--nova-space-6);
  gap: var(--nova-space-4);
  flex-wrap: wrap;
}

.kb-section-title {
  display: flex;
  align-items: center;
  gap: var(--nova-space-3);
  font-size: var(--nova-text-lg);
  font-weight: var(--nova-font-semibold);
  color: var(--nova-text-primary);
  margin: 0;
}

.kb-section-actions {
  display: flex;
  align-items: center;
  gap: var(--nova-space-3);
}

.kb-sort-btn {
  display: inline-flex; align-items: center; gap: var(--nova-space-2);
  padding: var(--nova-space-2) var(--nova-space-3);
  font-size: var(--nova-text-xs);
  font-weight: var(--nova-font-medium);
  background: rgba(15,23,42,0.5);
  border: 1px solid var(--nova-border);
  border-radius: var(--radius-md);
  color: var(--nova-text-secondary);
  cursor: pointer;
  transition: all var(--nova-duration-fast) ease;

  &:hover, &.active {
    background: rgba(99,102,241,0.12);
    border-color: rgba(99,102,241,0.3);
    color: #a5b4fc;
  }
}

/* ═══ Grid ═══ */
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--nova-space-6);
}

.kb-grid--drag { gap: var(--nova-space-8); }

.kb-grid-item {
  transition: all var(--nova-duration-normal) var(--nova-ease-out-expo);
}

.kb-grid-item--draggable { cursor: grab; }
.kb-grid-item--draggable:active { cursor: grabbing; }
.kb-grid-item--active {
  opacity: 0.55;
  transform: scale(0.97);
}

/* ═══ Card Header ═══ */
.kb-card-header {
  display: flex;
  align-items: center;
  gap: var(--nova-space-3);
}

.kb-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px; height: 40px;
  border-radius: var(--radius-lg);
  background: rgba(59,130,246,0.1);
  color: var(--nova-info);
  flex-shrink: 0;
}
.kb-card-icon--warning {
  background: rgba(245,158,11,0.1);
  color: var(--nova-warning);
}

.kb-card-info { flex: 1; min-width: 0; }

.kb-card-info h4 {
  font-size: var(--nova-text-base);
  font-weight: var(--nova-font-semibold);
  margin: 0 0 2px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.kb-card-info span {
  font-size: var(--nova-text-xs);
  color: var(--nova-text-muted);
}

.kb-card-desc {
  font-size: var(--nova-text-sm);
  color: var(--nova-text-secondary);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.6;
}

.kb-drag-handle {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; color: var(--nova-text-muted); cursor: grab;
}

/* ═══ Loading ═══ */
.kb-loading {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--nova-space-6);
}

/* ═══ Empty State ═══ */
.kb-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--nova-space-20) var(--nova-space-8);
  text-align: center;
  background: rgba(15,23,42,0.3);
  border: 1.5px dashed var(--nova-border);
  border-radius: var(--radius-3xl);
}

.kb-empty-art {
  color: var(--nova-text-muted);
  margin-bottom: var(--nova-space-6);
  opacity: 0.5;
}

.kb-empty h3 {
  font-size: var(--nova-text-xl);
  font-weight: var(--nova-font-semibold);
  margin: 0 0 var(--nova-space-2);
  color: var(--nova-text-primary);
}

.kb-empty p {
  color: var(--nova-text-muted);
  margin: 0 0 var(--nova-space-6);
}

/* ═══ 弹窗辅助样式 ═══ */
.nova-label {
  display: block;
  font-size: var(--nova-text-xs);
  font-weight: var(--nova-font-medium);
  color: var(--nova-text-secondary);
  margin-bottom: var(--nova-space-2);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.nova-modal-input {
  width: 100%;
  padding: var(--nova-space-4);
  font-size: var(--nova-text-base);
  font-family: var(--nova-font-display);
  color: var(--nova-text-primary);
  background: rgba(3,7,18,0.5);
  border: 1.5px solid rgba(148,163,184,0.1);
  border-radius: var(--radius-xl);
  outline: none;
  transition: all var(--nova-duration-fast) ease;
  &::placeholder { color: var(--nova-text-muted); }
  &:focus {
    border-color: rgba(99,102,241,0.45);
    box-shadow: 0 0 0 3px rgba(99,102,241,0.08), 0 0 20px rgba(99,102,241,0.06);
  }
}

/* ═══ Responsive ═══ */
@media (max-width: 767px) {
  .kb-page { padding: var(--nova-space-4); }
  .kb-hero__content { flex-direction: column; }
  .kb-hero__actions { flex-direction: column; width: 100%; }
  .kb-search { min-width: auto; width: 100%; }
  .kb-grid { grid-template-columns: 1fr; }
  .kb-title { font-size: var(--nova-text-2xl); }
  .kb-title-group { gap: var(--nova-space-3); }
  .kb-title-icon { width: 44px; height: 44px; }
}
</style>
