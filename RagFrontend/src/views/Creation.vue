<template>
  <div class="creation-page">
    <div class="creation-sidebar">
      <div class="cs-title">文档创作</div>
      <!-- 基础创作类型 -->
      <div class="cs-section-label">基础功能</div>
      <div
        v-for="t in types"
        :key="t.id"
        :class="['cs-item', activeType === t.id && !activeSkill ? 'cs-item--active' : '']"
        @click="selectCreationType(t.id)"
      >
        <span class="cs-icon">{{ t.icon }}</span>
        <div>
          <div class="cs-name">{{ t.name }}</div>
          <div class="cs-desc">{{ t.desc }}</div>
        </div>
      </div>
      <!-- Skill 预设模板 -->
      <div class="cs-section-label" style="margin-top: 12px">Skill 模板</div>
      <div
        v-for="s in skills"
        :key="s.id"
        :class="['cs-item', activeSkill === s.id ? 'cs-item--active' : '']"
        @click="selectSkill(s)"
      >
        <span class="cs-icon">{{ s.icon }}</span>
        <div>
          <div class="cs-name">{{ s.name }}</div>
          <div class="cs-desc">{{ s.desc }}</div>
        </div>
      </div>
    </div>
    <div class="creation-main">
      <!-- Skill 模式 -->
      <div v-if="activeSkill" class="creation-form">
        <h3>{{ currentSkill?.icon }} {{ currentSkill?.name }}</h3>
        <p class="cs-skill-desc">{{ currentSkill?.desc }}</p>
        <div class="cf-row">
          <label>{{ skillInputLabel }}</label>
          <textarea
            v-model="skillInput"
            rows="4"
            class="cf-textarea"
            :placeholder="skillInputPlaceholder"
          ></textarea>
        </div>
      </div>
      <!-- 大纲生成 -->
      <div v-if="!activeSkill && activeType === 'outline'" class="creation-form">
        <h3>大纲生成</h3>
        <div class="cf-row">
          <label>主题 / 标题</label>
          <input
            v-model="form.topic"
            placeholder="如：基于RAG的知识库问答系统设计与实现"
            class="cf-input"
          />
        </div>
        <div class="cf-row">
          <label>额外要求</label>
          <textarea
            v-model="form.requirements"
            rows="2"
            class="cf-textarea"
            placeholder="如：技术报告风格，约2000字，面向本科生读者"
          ></textarea>
        </div>
      </div>
      <!-- 摘要生成 -->
      <div v-if="!activeSkill && activeType === 'summary'" class="creation-form">
        <h3>摘要生成</h3>
        <div class="cf-row">
          <label>原文（支持粘贴长文本）</label>
          <textarea
            v-model="form.text"
            rows="6"
            class="cf-textarea"
            placeholder="粘贴需要摘要的文章内容..."
          ></textarea>
        </div>
        <div class="cf-row">
          <label>摘要长度（字）</label>
          <input
            v-model.number="form.summaryLength"
            type="number"
            min="50"
            max="1000"
            class="cf-input cf-input--short"
          />
        </div>
      </div>
      <!-- 翻译 -->
      <div v-if="!activeSkill && activeType === 'translate'" class="creation-form">
        <h3>文本翻译</h3>
        <div class="cf-row">
          <label>原文</label>
          <textarea
            v-model="form.text"
            rows="6"
            class="cf-textarea"
            placeholder="粘贴需要翻译的文本..."
          ></textarea>
        </div>
        <div class="cf-row">
          <label>目标语言</label>
          <select v-model="form.targetLang" class="cf-select">
            <option value="英文">英文</option>
            <option value="中文">中文</option>
            <option value="日语">日语</option>
            <option value="法语">法语</option>
            <option value="德语">德语</option>
          </select>
        </div>
      </div>
      <!-- 格式优化 -->
      <div v-if="!activeSkill && activeType === 'polish'" class="creation-form">
        <h3>格式优化</h3>
        <div class="cf-row">
          <label>原文</label>
          <textarea
            v-model="form.text"
            rows="6"
            class="cf-textarea"
            placeholder="粘贴需要优化的文本..."
          ></textarea>
        </div>
        <div class="cf-row">
          <label>优化风格</label>
          <select v-model="form.style" class="cf-select">
            <option value="正式学术风格">正式学术</option>
            <option value="商务正式风格">商务正式</option>
            <option value="通俗易懂风格">通俗易懂</option>
            <option value="简洁精炼风格">简洁精炼</option>
          </select>
        </div>
      </div>
      <!-- 内容扩写 -->
      <div v-if="!activeSkill && activeType === 'expand'" class="creation-form">
        <h3>内容扩写</h3>
        <div class="cf-row">
          <label>大纲 / 要点</label>
          <textarea
            v-model="form.outline"
            rows="6"
            class="cf-textarea"
            placeholder="输入大纲或关键要点，每行一条或使用 Markdown 格式..."
          ></textarea>
        </div>
        <div class="cf-row">
          <label>目标字数</label>
          <input
            v-model.number="form.expandLength"
            type="number"
            min="200"
            max="5000"
            class="cf-input cf-input--short"
          />
        </div>
      </div>
      <!-- 生成按钮 -->
      <div class="cf-actions">
        <button class="cf-btn-gen" @click="generate" :disabled="generating">
          {{ generating ? ' 生成中...' : ' 立即生成' }}
        </button>
        <!-- 模型选择 -->
        <div class="cf-model-selector">
          <label class="cf-model-label"> 模型</label>
          <select
            v-model="selectedModel"
            class="cf-model-select"
            @change="onModelChange"
            :disabled="generating"
          >
            <optgroup label=" 云端模型">
              <option
                v-for="m in availableModels.filter(m => m.provider !== 'ollama')"
                :key="m.id"
                :value="m.id"
                :disabled="!m.available"
              >
                {{ m.name }}{{ !m.available ? ' (需配置Key)' : '' }}
              </option>
            </optgroup>
            <optgroup label=" 本地模型">
              <option
                v-for="m in availableModels.filter(m => m.provider === 'ollama')"
                :key="m.id"
                :value="m.id"
                :disabled="!m.available"
              >
                {{ m.name }}{{ !m.available ? ' (未启动)' : '' }}
              </option>
            </optgroup>
          </select>
        </div>
        <button v-if="output" class="cf-btn-copy" @click="copyOutput">复制结果</button>
        <button v-if="output" class="cf-btn-clear" @click="output = ''">清空</button>
      </div>
      <!-- 输出区 -->
      <div v-if="output || generating" class="cf-output">
        <div class="cf-output-header">生成结果</div>
        <div class="cf-output-content" v-html="renderMd(output)"></div>
        <div v-if="generating" class="cf-cursor">▋</div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
const types = [
  { id: 'outline', name: '大纲生成', desc: '主题→层次化大纲', icon: '' },
  { id: 'summary', name: '摘要生成', desc: '长文本→要点摘要', icon: '' },
  { id: 'translate', name: '文本翻译', desc: '中英互译', icon: '' },
  { id: 'polish', name: '格式优化', desc: '润色措辞格式', icon: '' },
  { id: 'expand', name: '内容扩写', desc: '大纲→完整文档', icon: '' }
]
const activeType = ref('outline')
const generating = ref(false)
const output = ref('')

// ── Skill 模板 ──────────────────────────────────────────────────
interface SkillItem {
  id: string
  name: string
  desc: string
  icon: string
  type: string
  preset: Record<string, string>
}
const skills = ref<SkillItem[]>([])
const activeSkill = ref<string>('')
const skillInput = ref('')
const currentSkill = computed(() => skills.value.find(s => s.id === activeSkill.value))
const skillInputLabel = computed(() => {
  const s = currentSkill.value
  if (!s) return '输入内容'
  if (s.type === 'outline') return '主题 / 标题'
  if (s.type === 'polish') return '原文内容'
  if (s.type === 'template') return '场景描述 / 补充说明'
  return '输入内容'
})
const skillInputPlaceholder = computed(() => {
  const s = currentSkill.value
  if (!s) return '请输入...'
  if (s.id === 'academic-paper') return '如：基于大语言模型的中文文本纠错方法研究'
  if (s.id === 'tech-report') return '如：RAGF 智能知识库系统'
  if (s.id === 'business-plan') return '如：AI + 教育赛道的创业项目'
  if (s.id === 'meeting-minutes') return '粘贴会议记录内容...'
  if (s.id === 'project-proposal') return '如：面向高校的知识库智能问答系统'
  if (s.id === 'weekly-report') return '描述本周工作内容和下周计划...'
  if (s.id === 'api-doc') return '描述你的 API 接口功能...'
  if (s.id === 'readme') return '描述你的项目功能和技术栈...'
  return '请输入...'
})

async function loadSkills() {
  try {
    const res = await axios.get<{ skills: SkillItem[] }>('/api/creation/skills')
    if (Array.isArray(res.data?.skills) && res.data.skills.length > 0) {
      skills.value = res.data.skills
    } else {
      // API 返回空数据，使用内置 Skill 列表
      loadSkillsFallback()
    }
  } catch {
    // API 调用失败，使用内置 Skill 列表
    loadSkillsFallback()
  }
}
function loadSkillsFallback() {
  skills.value = [
    {
      id: 'academic-paper',
      name: '学术论文',
      desc: '完整学术论文结构，含摘要、引言、方法、实验、结论',
      icon: '🎓',
      type: 'outline',
      preset: { requirements: '学术论文风格，约5000字' }
    },
    {
      id: 'tech-report',
      name: '技术报告',
      desc: '项目技术报告，含背景、架构、实现、测试',
      icon: '🔧',
      type: 'outline',
      preset: { requirements: '技术报告风格，约3000字' }
    },
    {
      id: 'business-plan',
      name: '商业方案',
      desc: '商业计划书，含市场分析、产品策略、财务预测',
      icon: '💼',
      type: 'outline',
      preset: { requirements: '商业方案风格，约4000字' }
    },
    {
      id: 'meeting-minutes',
      name: '会议纪要',
      desc: '规范化会议纪要，含议题、决议、待办',
      icon: '📋',
      type: 'polish',
      preset: { text: '', style: '正式商务风格' }
    },
    {
      id: 'project-proposal',
      name: '项目申报书',
      desc: '项目申报/立项报告模板',
      icon: '📑',
      type: 'outline',
      preset: { requirements: '项目申报书风格，约3000字' }
    },
    {
      id: 'weekly-report',
      name: '周报/日报',
      desc: '工作周报/日报模板，含进展、问题、计划',
      icon: '📅',
      type: 'template',
      preset: { template_type: '工作周报', scenario: '技术研发团队周报' }
    },
    {
      id: 'api-doc',
      name: 'API 文档',
      desc: 'RESTful API 接口文档模板',
      icon: '🔌',
      type: 'template',
      preset: { template_type: 'API接口文档', scenario: 'RESTful API 接口文档' }
    },
    {
      id: 'readme',
      name: 'README',
      desc: 'GitHub 项目 README 文档',
      icon: '📖',
      type: 'template',
      preset: { template_type: '项目README', scenario: 'GitHub 开源项目 README' }
    }
  ]
}

function selectSkill(skill: SkillItem) {
  activeSkill.value = skill.id
  activeType.value = skill.type
  skillInput.value = ''
  output.value = ''
}

function selectCreationType(typeId: string) {
  activeSkill.value = ''
  activeType.value = typeId
  output.value = ''
}

// ── 模型选择 ─────────────────────────────────────────────────
interface ModelOption {
  id: string
  name: string
  provider: string
  available: boolean
}
const availableModels = ref<ModelOption[]>([])
const selectedModel = ref('')
async function loadModels() {
  try {
    const res = await axios.get<{ models: ModelOption[] }>('/api/models/list')
    if (Array.isArray(res.data?.models) && res.data.models.length > 0) {
      availableModels.value = res.data.models
      // 优先选已配置的云端模型
      const saved = localStorage.getItem('creation_selected_model')
      const cloud = res.data.models.find((m: ModelOption) => m.provider !== 'ollama' && m.available)
      const local = res.data.models.find((m: ModelOption) => m.provider === 'ollama' && m.available)
      if (saved && res.data.models.find((m: ModelOption) => m.id === saved)) {
        selectedModel.value = saved
      } else if (cloud) {
        selectedModel.value = cloud.id
      } else if (local) {
        selectedModel.value = local.id
      } else {
        selectedModel.value = res.data.models[0]?.id || 'deepseek-chat'
      }
    } else {
      // API 返回空数据，使用本地缓存
      loadModelsFromCache()
    }
  } catch {
    // API 调用失败，使用本地缓存
    loadModelsFromCache()
  }
}
function loadModelsFromCache() {
  const persistedModel =
    localStorage.getItem('creation_selected_model') ||
    localStorage.getItem('selected_model') ||
    localStorage.getItem('default_model') ||
    'deepseek-chat'
  // 提供完整的默认模型列表，确保前端不会因空数据报错
  availableModels.value = [
    { id: 'deepseek-chat', name: 'DeepSeek Chat', provider: 'deepseek', available: false },
    { id: 'deepseek-reasoner', name: 'DeepSeek Reasoner', provider: 'deepseek', available: false },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai', available: false },
    { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai', available: false },
    { id: 'hunyuan-lite', name: '混元 Lite', provider: 'hunyuan', available: false },
    { id: 'qwen-plus', name: '通义千问 Plus', provider: 'dashscope', available: false },
    { id: 'llama3:8b', name: 'Llama3 8B（本地）', provider: 'ollama', available: false }
  ]
  // 如果有历史选择的模型，标记为可用
  const savedModel = availableModels.value.find(m => m.id === persistedModel)
  if (savedModel) {
    savedModel.available = true
    selectedModel.value = persistedModel
  } else {
    selectedModel.value = 'deepseek-chat'
  }
}
function onModelChange() {
  localStorage.setItem('creation_selected_model', selectedModel.value)
}
const form = reactive({
  topic: '',
  requirements: '技术报告风格，约2000字',
  text: '',
  summaryLength: 300,
  targetLang: '英文',
  style: '正式学术风格',
  outline: '',
  expandLength: 1500
})
async function generate() {
  generating.value = true
  output.value = ''
  const model = selectedModel.value

  // Skill 模式走 /api/creation/skill-execute
  if (activeSkill.value) {
    try {
      const resp = await fetch('/api/creation/skill-execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_id: activeSkill.value, user_input: skillInput.value, model })
      })
      if (!resp.ok) {
        output.value = `[错误] 服务器返回 ${resp.status}，请检查后端是否正常运行`
        return
      }
      const reader = resp.body!.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      let finished = false
      while (!finished) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop() ?? ''
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data: ')) continue
          const token = trimmed.slice(6)
          if (token === '[DONE]') {
            finished = true
            break
          }
          if (token.startsWith('[ERROR]')) {
            output.value += `\n\n${token.slice(8)}`
            finished = true
            break
          }
          if (token) {
            output.value += token
          }
        }
      }
    } catch (e: any) {
      output.value = `[错误] ${e?.message || e}`
    } finally {
      generating.value = false
    }
    return
  }

  // 原有基础创作模式
  const endpointMap: Record<string, { url: string; body: any }> = {
    outline: {
      url: '/api/creation/outline',
      body: { topic: form.topic, requirements: form.requirements, model }
    },
    summary: {
      url: '/api/creation/summary',
      body: { text: form.text, length: form.summaryLength, model }
    },
    translate: {
      url: '/api/creation/translate',
      body: { text: form.text, target_lang: form.targetLang, model }
    },
    polish: { url: '/api/creation/polish', body: { text: form.text, style: form.style, model } },
    expand: {
      url: '/api/creation/expand',
      body: { outline: form.outline, target_length: form.expandLength, model }
    }
  }
  const { url, body } = endpointMap[activeType.value]
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    if (!resp.ok) {
      output.value = `[错误] 服务器返回 ${resp.status}，请检查后端是否正常运行`
      return
    }
    const reader = resp.body!.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    let finished = false
    while (!finished) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      // 按行处理，避免 chunk 不完整导致 JSON 截断
      const lines = buf.split('\n')
      buf = lines.pop() ?? '' // 最后一行可能不完整，留待下次
      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data: ')) continue
        const token = trimmed.slice(6)
        if (token === '[DONE]') {
          finished = true
          break
        }
        if (token.startsWith('[ERROR]')) {
          output.value += `\n\n ${token.slice(8)}`
          finished = true
          break
        }
        if (token) {
          output.value += token
        }
      }
    }
  } catch (e: any) {
    output.value = `[错误] ${e?.message || e}`
  } finally {
    generating.value = false
  }
}
function copyOutput() {
  navigator.clipboard.writeText(output.value)
}
function renderMd(text: string): string {
  // 简单 Markdown 渲染（标题 + 粗体 + 代码块）
  return text
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/\n/g, '<br>')
}
onMounted(() => {
  loadModels()
  loadSkills()
})
</script>
<style scoped>
/* eslint-disable-next-line @typescript-eslint/no-explicit-any */
.creation-page {
  display: flex;
  gap: 0;
  height: calc(100vh - 120px);
  min-height: 500px;
}
.creation-sidebar {
  width: 200px;
  flex-shrink: 0;
  border-right: 1px solid #e5e7eb;
  padding: 16px 8px;
  background: var(--td-bg-color-secondarycontainer, #f9fafb);
}
.cs-title {
  font-size: 14px;
  font-weight: 700;
  padding: 0 8px 12px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 10px;
}
.cs-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 2px;
}
.cs-item:hover {
  background: #f3f4f6;
}
.cs-item--active {
  background: #eff6ff;
}
.cs-icon {
  font-size: 18px;
}
.cs-name {
  font-size: 13px;
  font-weight: 600;
}
.cs-desc {
  font-size: 11px;
  color: #9ca3af;
}
.cs-section-label {
  font-size: 10px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 8px 8px 4px;
  font-weight: 600;
}
.cs-skill-desc {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 16px;
}
.creation-main {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}
.creation-form h3 {
  margin: 0 0 16px;
  font-size: 16px;
}
.cf-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 14px;
}
.cf-row label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}
.cf-input,
.cf-textarea,
.cf-select {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  background: var(--td-bg-color-container, #fff);
  color: var(--td-text-color-primary, #111);
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
}
.cf-input:focus,
.cf-textarea:focus {
  border-color: #6366f1;
}
.cf-input--short {
  max-width: 120px;
}
.cf-select {
  appearance: auto;
}
.cf-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.cf-btn-gen {
  padding: 9px 26px;
  background: #6366f1;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.cf-btn-gen:hover:not(:disabled) {
  background: #4f46e5;
}
.cf-btn-gen:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.cf-btn-copy,
.cf-btn-clear {
  padding: 9px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  background: #f9fafb;
}
.cf-btn-copy:hover {
  background: #f3f4f6;
}
.cf-btn-clear:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
}
.cf-output {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}
.cf-output-header {
  padding: 8px 14px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
}
.cf-output-content {
  padding: 14px;
  font-size: 14px;
  line-height: 1.7;
  max-height: 500px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.cf-output-content :deep(h1),
.cf-output-content :deep(h2),
.cf-output-content :deep(h3) {
  margin: 10px 0 6px;
}
.cf-output-content :deep(pre) {
  background: #f3f4f6;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}
.cf-cursor {
  display: inline-block;
  animation: blink 1s step-end infinite;
  color: #6366f1;
  padding: 0 14px 10px;
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}
/* 模型选择器 */
.cf-model-selector {
  display: flex;
  align-items: center;
  gap: 6px;
}
.cf-model-label {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
}
.cf-model-select {
  font-size: 12px;
  padding: 5px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: var(--td-bg-color-container, #fff);
  color: var(--td-text-color-primary, #111);
  cursor: pointer;
  max-width: 200px;
  outline: none;
  transition: border-color 0.15s;
}
.cf-model-select:hover:not(:disabled),
.cf-model-select:focus:not(:disabled) {
  border-color: #6366f1;
}
.cf-model-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
