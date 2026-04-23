<template>
  <div class="chat-root">
    <aside class="sidebar">
      <div class="sidebar-head">
        <div class="sidebar-brand">
          <div class="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span class="brand-text">KnowledgeRAG</span>
        </div>
        <button class="icon-btn" @click="createNewSession" :disabled="loading" title="新对话">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        </button>
      </div>

      <div class="sidebar-search">
        <div class="search-input-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="search-icon"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          <input type="text" placeholder="搜索对话..." class="search-input" />
        </div>
      </div>

      <nav class="session-list" v-if="!loading || chatSessions.length > 0">
        <div
          v-for="(chat, idx) in chatSessions"
          :key="chat.id"
          @click="selectSession(idx)"
          :class="['session-item', 'shine-overlay', { 'session-item--active': currentSessionIndex === idx }]"
        >
          <div class="session-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
          </div>
          <div class="session-content">
            <div class="session-title">{{ chat.title || '新对话' }}</div>
            <div class="session-meta">{{ formatDateTime(chat.created_at) }}</div>
          </div>
          <button @click.stop="deleteSession(idx)" class="session-del" :disabled="chatSessions.length <= 1" title="删除">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
      </nav>

      <div v-else class="sidebar-loading">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>

      <div class="sidebar-footer">
        <div class="model-indicator" @click="router.push('/settings?tab=model-config')">
          <span class="model-dot"></span>
          <span class="model-name">{{ currentOllamaModel }}</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="model-arrow"><path d="m9 18 6-6-6-6"/></svg>
        </div>

        <div class="rag-section">
          <div class="rag-row">
            <div class="rag-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
              <span>知识库问答</span>
            </div>
            <t-switch v-model="ragMode" size="small" />
          </div>
          <div v-if="ragMode" class="rag-config animate-slide-up">
            <ModelSelector v-model="selectedModel" />
            <t-select v-model="selectedKbId" placeholder="选择知识库" size="small" clearable :options="kbSelectOptions" />
            <RetrievalConfig v-model="retrievalConfig" v-if="ragMode" />
          </div>
        </div>

        <div class="sidebar-actions">
          <button @click="createNewSession" :disabled="loading" class="action-btn action-btn--primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
            新对话
          </button>
          <button @click="showOllamaSettings" :disabled="loading" class="action-btn action-btn--ghost">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12.22 2h-.44a2 2 0 00-2 2v.18a2 2 0 01-1 1.73l-.43.25a2 2 0 01-2 0l-.15-.08a2 2 0 00-2.73.73l-.22.38a2 2 0 00.73 2.73l.15.1a2 2 0 011 1.72v.51a2 2 0 01-1 1.74l-.15.09a2 2 0 00-.73 2.73l.22.38a2 2 0 002.73.73l.15-.08a2 2 0 012 0l.43.25a2 2 0 011 1.73V20a2 2 0 002 2h.44a2 2 0 002-2v-.18a2 2 0 011-1.73l.43-.25a2 2 0 012 0l.15.08a2 2 0 002.73-.73l.22-.39a2 2 0 00-.73-2.73l-.15-.08a2 2 0 01-1-1.74v-.5a2 2 0 011-1.74l.15-.09a2 2 0 00.73-2.73l-.22-.38a2 2 0 00-2.73-.73l-.15.08a2 2 0 01-2 0l-.43-.25a2 2 0 01-1-1.73V4a2 2 0 00-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
            设置
          </button>
          <button @click="refreshSessions" :disabled="loading" class="action-btn action-btn--ghost">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'animate-spin': loading }"><path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9"/></svg>
          </button>
        </div>
      </div>
    </aside>

    <main class="chat-main">
      <div class="chat-main__bg">
        <div class="orb orb--violet" style="width:400px;height:400px;top:-100px;right:-100px;"></div>
        <div class="orb orb--cyan" style="width:300px;height:300px;bottom:-80px;left:-60px;"></div>
      </div>

      <div v-if="showStopHint" class="stop-toast animate-fade-in">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
        已停止生成
      </div>

      <chatMainUnit
        v-if="currentSession"
        :history="currentSession.history"
        :title="currentSession.title"
        :lastMessage="currentSession.lastMessage"
        :selectedModel="selectedModel"
        :key="currentSession.id"
        :loading="isStreamLoad"
        :ragMode="ragMode"
        :ragKbId="selectedKbId"
        @chat-updated="handleChatUpdated"
        @send-message="inputEnter"
      />

      <div v-else class="empty-state">
        <div class="empty-inner animate-fade-in-scale">
          <div class="empty-graphic">
            <div class="empty-ring"></div>
            <div class="empty-ring empty-ring--2"></div>
            <div class="empty-ring empty-ring--3"></div>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon-svg"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
          </div>
          <h3 class="empty-title">开始探索知识</h3>
          <p class="empty-desc">选择知识库，向 AI 提问，获取精准回答</p>
          <div class="empty-hints">
            <div class="empty-hint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
              <span>开启知识库模式</span>
            </div>
            <div class="empty-hint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
              <span>输入问题开始对话</span>
            </div>
          </div>
          <button @click="createNewSession" class="action-btn action-btn--primary" style="margin-top:24px">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
            新对话
          </button>
        </div>
      </div>
    </main>

    <t-drawer header="Ollama 设置" :visible="showSettingsDialog" placement="right" :onConfirm="confirmSettings" :onCancel="closeSettingsDialog" :onClose="closeSettingsDialog" size="500px">
      <div class="settings-form">
        <div class="form-field">
          <label>服务器地址</label>
          <t-input v-model="settings.serverUrl" placeholder="http://localhost:11434" />
          <span class="form-hint">本地模型: http://localhost:11434</span>
        </div>
        <div class="form-field">
          <label>连接超时（秒）</label>
          <t-input-number v-model="settings.timeout" :min="1" :max="300" />
        </div>
      </div>
    </t-drawer>
  </div>
</template>
<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, watch, reactive, onMounted } from 'vue'
import chatMainUnit from '../components/chat-main-unit/chat-main-unit.vue'
import ModelSelector from '../components/ModelSelector.vue'
import RetrievalConfig from '../components/RetrievalConfig.vue'
import type { RetrievalConfig as RetrievalConfigType } from '../components/RetrievalConfig.vue'
import { useRouter, useRoute } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import axios from 'axios'
interface ChatMessage { avatar: string; name: string; datetime: string; content: string; role: 'user' | 'assistant'; reasoning?: string; duration?: number; sources?: SourceItem[] }
interface SourceItem { filename: string; content: string; score?: number }
interface ChatSession { id: string; title: string; lastMessage: string; history: ChatMessage[]; created_at: number; updated_at?: number }
const router = useRouter()
const route = useRoute()
const loading = ref(false)
const isStreamLoad = ref(false)
const currentSessionIndex = ref(0)
const showStopHint = ref(false)
const retryCount = ref(0)
const maxRetries = 3
const chatSessions = ref<ChatSession[]>([])
const ragMode = ref(false)
const selectedKbId = ref<string>('')
const kbList = ref<any[]>([])
const selectedModel = ref(localStorage.getItem('selected_model') || '')
const retrievalConfig = ref<RetrievalConfigType>({ strategy: 'rrf', topK: 6, scoreThreshold: 0.3, vectorWeight: 0.6, bm25Weight: 0.4, rerank: false, rerankTopN: 3 })
watch(selectedModel, v => { if (v) localStorage.setItem('selected_model', v) })
const currentOllamaModel = computed(() => selectedModel.value || '未选择模型')
async function syncCurrentOllamaModel() { if (selectedModel.value) return; try { const res = await import('axios').then(m => m.default.get('/api/user-model-config')); const model = res.data?.config?.llm_model; if (model) { selectedModel.value = model; localStorage.setItem('selected_model', model) } } catch { /* */ } }
const kbSelectOptions = computed(() => kbList.value.map((kb: any) => ({ label: kb.kbName || kb.title || kb.name, value: kb.kbId || kb.id })))
const loadKbList = async () => { try { const res = await axios.get('/api/get-knowledge-item/'); const data = res.data?.data || res.data || []; kbList.value = Array.isArray(data) ? data : [] } catch { kbList.value = [] } }
const currentSession = computed(() => chatSessions.value[currentSessionIndex.value])
const showSettingsDialog = ref(false)
const settings = reactive({ serverUrl: 'http://localhost:11434', timeout: 30 })
const showOllamaSettings = () => { loadSettings(); showSettingsDialog.value = true }
const closeSettingsDialog = () => { showSettingsDialog.value = false }
const confirmSettings = () => { saveSettings(); closeSettingsDialog() }
const saveSettings = () => { const s = { serverUrl: settings.serverUrl, timeout: settings.timeout }; localStorage.setItem('ollamaSettings', JSON.stringify(s)); MessagePlugin.success('设置已保存'); window.dispatchEvent(new CustomEvent('ollamaSettingsUpdated', { detail: s })); setTimeout(() => { window.location.reload() }, 100) }
const loadSettings = () => { const s = localStorage.getItem('ollamaSettings'); if (s) { try { const p = JSON.parse(s); settings.serverUrl = p.serverUrl || 'http://localhost:11434'; settings.timeout = p.timeout || 30 } catch (e) { console.error('加载设置失败:', e) } } }
onMounted(() => { loadSettings() })
const API_BASE = '/api/chat'
const API_ENDPOINTS = { SESSIONS: `${API_BASE}/chat-documents`, SAVE_SESSION: `${API_BASE}/save-session`, DELETE_SESSION: `${API_BASE}/delete-session`, DOWNLOAD: `${API_BASE}/download-chat-json`, SEND_MESSAGE: `${API_BASE}/send-message` }
const generateNumericUUID = (length = 16): string => { let r = ''; for (let i = 0; i < length; i++) r += Math.floor(Math.random() * 10); return r }
const formatDateTime = (timestamp: number): string => { if (!timestamp) return ''; const d = new Date(timestamp * 1000); const n = new Date(); const diff = Math.floor((n.getTime() - d.getTime()) / 86400000); if (diff === 0) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }); if (diff === 1) return '昨天'; if (diff < 7) return `${diff}天前`; return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }) }
const apiRequest = async (url: string, options: RequestInit = {}) => { const r = await fetch(url, { headers: { 'Content-Type': 'application/json', ...options.headers }, ...options }); if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`); return r.json() }
const fetchChatSessions = async (): Promise<boolean> => { try { loading.value = true; retryCount.value = 0; const data = await apiRequest(API_ENDPOINTS.SESSIONS); const sessions = Array.isArray(data) ? data : []; chatSessions.value = sessions.map(s => ({ ...s, id: s.id || generateNumericUUID(), title: s.history[1] ? s.history[1].content.slice(0, 5) + '...' : '新对话', lastMessage: s.history[s.history.length - 1] ? s.history[s.history.length - 1].content.slice(0, 10) + '...' : '空', history: s.history || [], created_at: s.created_at || Date.now() / 1000 })).sort((a, b) => (b.updated_at || b.created_at) - (a.updated_at || a.created_at)); return true } catch (e) { console.error('获取会话历史失败:', e); if (retryCount.value < maxRetries) { retryCount.value++; MessagePlugin.warning(`获取失败，正在重试 (${retryCount.value}/${maxRetries})...`); await new Promise(r => setTimeout(r, 1000 * retryCount.value)); return fetchChatSessions() } else { MessagePlugin.error('获取会话历史失败，请刷新页面重试'); await createDefaultSession(); return false } } finally { loading.value = false } }
const createDefaultSession = async () => { chatSessions.value = [{ id: generateNumericUUID(), title: '新对话', lastMessage: '', history: [], created_at: Date.now() / 1000 }]; currentSessionIndex.value = 0 }
const createNewSession = async () => { try { const s: ChatSession = { id: generateNumericUUID(), title: '新对话', lastMessage: '', history: [], created_at: Date.now() / 1000 }; await saveChatSession(s); chatSessions.value.unshift(s); currentSessionIndex.value = 0; await router.push(`/chat/${s.id}`); MessagePlugin.success('新对话已创建') } catch (e) { console.error('创建新会话失败:', e); MessagePlugin.error('创建新会话失败，请重试') } }
const deleteSession = async (index: number) => { if (chatSessions.value.length <= 1) { MessagePlugin.warning('至少需要保留一个会话'); return } const s = chatSessions.value[index]; try { await apiRequest(API_ENDPOINTS.DELETE_SESSION, { method: 'DELETE', body: JSON.stringify({ sessionId: s.id }) }); chatSessions.value.splice(index, 1); if (currentSessionIndex.value >= index) currentSessionIndex.value = Math.max(0, currentSessionIndex.value - 1); if (index === currentSessionIndex.value || currentSessionIndex.value >= chatSessions.value.length) { currentSessionIndex.value = Math.min(currentSessionIndex.value, chatSessions.value.length - 1); await router.push(`/chat/${chatSessions.value[currentSessionIndex.value].id}`) } MessagePlugin.success('会话已删除') } catch (e) { console.error('删除会话失败:', e); MessagePlugin.error('删除会话失败，请重试') } }
const selectSession = async (index: number) => { if (index < 0 || index >= chatSessions.value.length) return; currentSessionIndex.value = index; await router.push(`/chat/${chatSessions.value[index].id}`) }
const refreshSessions = async () => { await fetchChatSessions(); MessagePlugin.success('会话列表已刷新') }
const saveChatSession = async (session: ChatSession): Promise<boolean> => { try { await apiRequest(API_ENDPOINTS.SAVE_SESSION, { method: 'POST', body: JSON.stringify({ sessionId: session.id, session: { ...session, updated_at: Date.now() / 1000 } }) }); return true } catch (e) { console.error('保存对话失败:', e); MessagePlugin.error('保存失败，请检查网络连接'); return false } }
const handleChatUpdated = () => { if (currentSession.value) saveChatSession(currentSession.value) }
const inputEnter = async (inputValue: string) => { if (isStreamLoad.value || !inputValue.trim() || !currentSession.value) return; const idx = currentSessionIndex.value; const userMsg: ChatMessage = { avatar: 'https://tdesign.gtimg.com/site/avatar.jpg', name: '您', datetime: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }), content: inputValue.trim(), role: 'user', reasoning: '', duration: 0 }; chatSessions.value[idx].history.push(userMsg); chatSessions.value[idx].lastMessage = inputValue.trim(); if (!chatSessions.value[idx].title || chatSessions.value[idx].title === '新对话') chatSessions.value[idx].title = inputValue.length > 20 ? inputValue.substring(0, 20) + '...' : inputValue; await saveChatSession(chatSessions.value[idx]); isStreamLoad.value = true; loading.value = true; try { const cm = selectedModel.value || (() => { try { return JSON.parse(localStorage.getItem('user_model_config') || '{}').llm_model || '' } catch { return '' } })(); const resp = await apiRequest(API_ENDPOINTS.SEND_MESSAGE, { method: 'POST', body: JSON.stringify({ message: inputValue.trim(), sessionId: chatSessions.value[idx].id, history: chatSessions.value[idx].history, model: cm || undefined, rag_mode: ragMode.value, kb_id: ragMode.value ? selectedKbId.value : undefined, ollamaSettings: { serverUrl: settings.serverUrl, timeout: settings.timeout } }) }); await simulateStreamResponse(resp.reply || `这是对"${inputValue}"的回复`, idx, resp.sources || []) } catch (e) { console.error('发送消息失败:', e); chatSessions.value[idx].history.push({ avatar: 'https://tdesign.gtimg.com/site/chat-avatar.png', name: '系统', datetime: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }), content: '抱歉，消息发送失败，请检查网络连接后重试。', role: 'assistant', reasoning: '', duration: 0 }); MessagePlugin.error('消息发送失败') } finally { isStreamLoad.value = false; loading.value = false } }
const simulateStreamResponse = async (content: string, idx: number, sources: SourceItem[] = []) => { const msg: ChatMessage = { avatar: 'https://tdesign.gtimg.com/site/chat-avatar.png', name: 'RAG助手', datetime: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }), content: '', role: 'assistant', reasoning: '', duration: 0, sources }; chatSessions.value[idx].history.push(msg); const mi = chatSessions.value[idx].history.length - 1; for (let i = 0; i <= content.length; i++) { if (!isStreamLoad.value) break; chatSessions.value[idx].history[mi].content = content.substring(0, i); await new Promise(r => setTimeout(r, 18)) } await saveChatSession(chatSessions.value[idx]) }
const handleKeyDown = (event: KeyboardEvent) => { if (event.ctrlKey && event.key === 'c' && isStreamLoad.value) { event.preventDefault(); isStreamLoad.value = false; loading.value = false; showStopHint.value = true; setTimeout(() => { showStopHint.value = false }, 2000); MessagePlugin.info('已停止生成') } }
watch(() => route.params.id, async newId => { if (newId && typeof newId === 'string') { const si = chatSessions.value.findIndex(s => s.id === newId); if (si !== -1) currentSessionIndex.value = si } })
import { onMounted as onMountedHook, onUnmounted } from 'vue'
onMountedHook(async () => { document.addEventListener('keydown', handleKeyDown); await syncCurrentOllamaModel(); await loadKbList(); await fetchChatSessions(); const rid = route.params.id as string; if (rid && chatSessions.value.length > 0) { const si = chatSessions.value.findIndex(s => s.id === rid); if (si !== -1) currentSessionIndex.value = si; else { currentSessionIndex.value = 0; await router.replace(`/chat/${chatSessions.value[0].id}`) } } else if (chatSessions.value.length > 0) { currentSessionIndex.value = 0; await router.replace(`/chat/${chatSessions.value[0].id}`) } else { await createNewSession() } })
onUnmounted(() => { document.removeEventListener('keydown', handleKeyDown) })
</script>
<style scoped>
.chat-root { display: flex; width: 100%; height: 100vh; overflow: hidden; background: var(--bg-base); }

.sidebar { width: 256px; flex-shrink: 0; display: flex; flex-direction: column; height: 100%; background: var(--bg-surface); border-right: 1px solid var(--border-subtle); overflow: hidden; position: relative; }
.sidebar::after { content: ''; position: absolute; top: 0; right: 0; bottom: 0; width: 1px; background: linear-gradient(180deg, rgba(124, 106, 255, 0.1) 0%, transparent 30%, transparent 70%, rgba(34, 211, 238, 0.06) 100%); pointer-events: none; }

.sidebar-head { display: flex; align-items: center; justify-content: space-between; padding: 12px 12px 8px; }
.sidebar-brand { display: flex; align-items: center; gap: 8px; }
.brand-icon { width: 20px; height: 20px; color: var(--accent-violet-light); }
.brand-text { font-size: 13px; font-weight: 600; color: var(--text-primary); letter-spacing: -0.02em; }
.icon-btn { width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); background: transparent; color: var(--text-tertiary); cursor: pointer; transition: all var(--transition-fast); }
.icon-btn:hover { background: var(--bg-hover); color: var(--text-primary); border-color: var(--border-active); }
.icon-btn:disabled { opacity: 0.25; cursor: not-allowed; }
.icon-btn svg { width: 13px; height: 13px; }

.sidebar-search { padding: 0 10px 6px; }
.search-input-wrap { display: flex; align-items: center; gap: 5px; padding: 0 7px; height: 28px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); background: var(--bg-elevated); transition: border-color var(--transition-fast), box-shadow var(--transition-fast); }
.search-input-wrap:focus-within { border-color: var(--border-brand); box-shadow: 0 0 0 2px var(--accent-violet-subtle); }
.search-icon { width: 12px; height: 12px; color: var(--text-quaternary); flex-shrink: 0; }
.search-input { flex: 1; border: none; background: transparent; color: var(--text-primary); font-size: 11.5px; outline: none; }
.search-input::placeholder { color: var(--text-quaternary); }

.session-list { flex: 1; overflow-y: auto; padding: 2px 6px; display: flex; flex-direction: column; gap: 1px; }
.session-item { display: flex; align-items: center; padding: 7px 7px; border-radius: var(--radius-sm); cursor: pointer; transition: background var(--transition-fast), color var(--transition-fast); position: relative; }
.session-item:hover { background: var(--bg-hover); }
.session-item--active { background: var(--accent-violet-subtle); }
.session-item--active::before { content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%); width: 2px; height: 14px; border-radius: 0 2px 2px 0; background: var(--accent-violet); animation: navIndicatorIn 0.25s var(--ease-spring); }
@keyframes navIndicatorIn { from { transform: translateY(-50%) scaleY(0); } to { transform: translateY(-50%) scaleY(1); } }
.session-icon { width: 16px; height: 16px; color: var(--text-quaternary); margin-right: 7px; flex-shrink: 0; }
.session-item--active .session-icon { color: var(--accent-violet-light); }
.session-content { flex: 1; min-width: 0; }
.session-title { font-size: 12px; font-weight: 450; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-item--active .session-title { color: var(--text-brand-strong); }
.session-meta { font-size: 10px; color: var(--text-quaternary); margin-top: 1px; }
.session-del { opacity: 0; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-xs); border: none; background: transparent; color: var(--text-quaternary); cursor: pointer; transition: all var(--transition-fast); flex-shrink: 0; }
.session-del svg { width: 11px; height: 11px; }
.session-item:hover .session-del { opacity: 1; }
.session-del:hover { color: var(--accent-rose); background: var(--accent-rose-subtle); }
.session-del:disabled { opacity: 0; cursor: not-allowed; }

.sidebar-loading { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; color: var(--text-quaternary); font-size: 11px; }
.spinner { width: 18px; height: 18px; border: 1.5px solid var(--border-base); border-top-color: var(--accent-violet); border-radius: 50%; animation: spin 0.7s linear infinite; }

.sidebar-footer { padding: 6px 8px 10px; border-top: 1px solid var(--border-subtle); display: flex; flex-direction: column; gap: 5px; }
.model-indicator { display: flex; align-items: center; gap: 5px; padding: 5px 7px; border-radius: var(--radius-sm); background: var(--bg-elevated); border: 1px solid var(--border-subtle); cursor: pointer; transition: all var(--transition-fast); }
.model-indicator:hover { border-color: var(--border-active); }
.model-dot { width: 4px; height: 4px; border-radius: 50%; background: var(--accent-emerald); box-shadow: 0 0 6px rgba(52, 211, 153, 0.5); animation: pulseGlow 3s ease-in-out infinite; }
.model-name { flex: 1; font-size: 10.5px; font-family: var(--font-mono); color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.model-arrow { width: 11px; height: 11px; color: var(--text-quaternary); }
.rag-section { display: flex; flex-direction: column; gap: 3px; }
.rag-row { display: flex; align-items: center; justify-content: space-between; }
.rag-label { display: flex; align-items: center; gap: 4px; font-size: 11.5px; color: var(--text-secondary); }
.rag-label svg { width: 12px; height: 12px; color: var(--accent-violet-light); }
.rag-config { display: flex; flex-direction: column; gap: 3px; padding-top: 2px; }
.sidebar-actions { display: flex; gap: 3px; }
.action-btn { display: flex; align-items: center; justify-content: center; gap: 4px; padding: 5px 9px; font-size: 11.5px; font-weight: 500; border-radius: var(--radius-sm); border: none; cursor: pointer; transition: all var(--transition-fast); }
.action-btn:disabled { opacity: 0.25; cursor: not-allowed; }
.action-btn svg { width: 12px; height: 12px; }
.action-btn--primary { flex: 1; background: var(--gradient-brand); color: #fff; box-shadow: var(--shadow-glow); }
.action-btn--primary:hover:not(:disabled) { filter: brightness(1.12); box-shadow: var(--shadow-glow-strong); transform: translateY(-1px); }
.action-btn--ghost { background: transparent; color: var(--text-secondary); border: 1px solid var(--border-subtle); }
.action-btn--ghost:hover:not(:disabled) { background: var(--bg-hover); color: var(--text-primary); border-color: var(--border-base); }

.chat-main { flex: 1; display: flex; flex-direction: column; height: 100%; overflow: hidden; min-width: 0; position: relative; background: var(--bg-base); }
.chat-main__bg { position: absolute; inset: 0; pointer-events: none; overflow: hidden; z-index: 0; }
.stop-toast { position: absolute; top: 12px; right: 12px; z-index: 50; display: flex; align-items: center; gap: 5px; padding: 6px 10px; border-radius: var(--radius-md); background: var(--glass-bg); backdrop-filter: blur(16px); border: 1px solid var(--border-base); color: var(--text-brand-strong); font-size: 11.5px; box-shadow: var(--shadow-md); }
.stop-toast svg { width: 12px; height: 12px; }

.empty-state { flex: 1; display: flex; align-items: center; justify-content: center; position: relative; z-index: 1; }
.empty-inner { text-align: center; }
.empty-graphic { position: relative; width: 64px; height: 64px; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; }
.empty-ring { position: absolute; inset: 0; border-radius: 50%; border: 1px solid rgba(124, 106, 255, 0.15); animation: pulseGlow 3.5s ease-in-out infinite; }
.empty-ring--2 { inset: -7px; border-color: rgba(124, 106, 255, 0.08); animation-delay: 0.6s; }
.empty-ring--3 { inset: -14px; border-color: rgba(34, 211, 238, 0.05); animation-delay: 1.2s; }
.empty-icon-svg { width: 24px; height: 24px; color: var(--accent-violet-light); position: relative; z-index: 1; }
.empty-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.empty-desc { font-size: 12.5px; color: var(--text-tertiary); }
.empty-hints { display: flex; gap: 12px; justify-content: center; margin-top: 16px; }
.empty-hint { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--text-quaternary); }
.empty-hint svg { width: 13px; height: 13px; color: var(--text-tertiary); }

.settings-form { display: flex; flex-direction: column; gap: 14px; }
.form-field { display: flex; flex-direction: column; gap: 5px; }
.form-field label { font-size: 12.5px; font-weight: 500; color: var(--text-primary); }
.form-hint { font-size: 10.5px; color: var(--text-tertiary); }

:deep(.t-switch.t-is-checked .t-switch__handle) { background: var(--accent-violet) !important; }
:deep(.t-switch.t-is-checked) { background: rgba(124, 106, 255, 0.25) !important; }
:deep(.t-select-input) { background: var(--bg-elevated) !important; border-color: var(--border-base) !important; color: var(--text-primary) !important; }
</style>
