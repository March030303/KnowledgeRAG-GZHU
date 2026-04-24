<template>
  <div class="tab-content">
    <div class="section-header">
      <h2>模型评测面板</h2>
      <p class="section-desc">
        基于内置 20 条中文测试题，从准确率 / 响应速度 / 溯源准确率三维度评测，ECharts 可视化对比
      </p>
    </div>
    <!-- 操作区 -->
    <div class="eval-toolbar">
      <div class="eval-model-input">
        <label>评测模型（单选）</label>
        <select v-model="evalModels" class="eval-select">
          <optgroup label="本地模型">
            <option v-for="m in localModels" :key="m" :value="m">{{ m }}</option>
          </optgroup>
          <optgroup label="云端模型">
            <option v-for="m in cloudModels" :key="m" :value="m">{{ m }}</option>
          </optgroup>
        </select>
        <span v-if="modelLoading" class="eval-hint">检测中...</span>
      </div>
      <button class="eval-btn-run" @click="runEval" :disabled="running">
        {{ running ? ' 评测中...' : ' 开始评测' }}
      </button>
      <button class="eval-btn-refresh" @click="fetchLatest" :disabled="loadingChart">
        {{ loadingChart ? '加载中...' : ' 刷新图表' }}
      </button>
    </div>
    <!-- 进度提示 -->
    <div v-if="running" class="eval-progress">
      <div class="eval-spinner"></div>
      <span>{{
        evalStore.progress ||
        `正在评测 ${evalStore.models || evalModels} ... 每个模型约 20-60 秒，请稍候`
      }}</span>
    </div>
    <!-- 最近一次概览卡片 -->
    <div v-if="latestRun" class="eval-overview-cards">
      <div class="eval-ov-card" v-for="card in overviewCards" :key="card.key">
        <div class="eval-ov-icon">{{ card.icon }}</div>
        <div class="eval-ov-value" :style="{ color: card.color }">{{ card.value }}</div>
        <div class="eval-ov-label">{{ card.label }}</div>
      </div>
    </div>
    <!-- 高级指标卡片 -->
    <div class="eval-section-title">高级检索指标</div>
    <div class="eval-metrics-row">
      <div class="eval-metric-card" v-for="m in advancedMetrics" :key="m.key">
        <div class="eval-metric-value" :style="{ color: m.color }">{{ m.value }}</div>
        <div class="eval-metric-label">{{ m.label }}</div>
        <div class="eval-metric-desc">{{ m.desc }}</div>
      </div>
    </div>
    <button
      class="eval-btn-run"
      @click="computeAdvancedMetrics"
      :disabled="metricsLoading"
      style="margin-bottom: 16px"
    >
      {{ metricsLoading ? '计算中...' : '计算高级指标' }}
    </button>
    <!-- ECharts：三图并排 -->
    <div v-if="chartData" class="eval-charts-row">
      <!-- 雷达图：多模型三维度对比 -->
      <div class="eval-chart-box">
        <div class="eval-chart-title">多模型三维对比（雷达图）</div>
        <div ref="radarRef" style="width: 100%; height: 280px"></div>
      </div>
      <!-- 分类准确率柱状图 -->
      <div class="eval-chart-box">
        <div class="eval-chart-title">分类准确率（最新一次）</div>
        <div ref="catBarRef" style="width: 100%; height: 280px"></div>
      </div>
      <!-- 延迟分布直方图 -->
      <div class="eval-chart-box">
        <div class="eval-chart-title">响应时间分布</div>
        <div ref="latencyRef" style="width: 100%; height: 280px"></div>
      </div>
    </div>
    <!-- 指标趋势图 -->
    <div
      v-if="metricsTrend.length > 0"
      class="eval-charts-row"
      style="grid-template-columns: 1fr 1fr"
    >
      <div class="eval-chart-box">
        <div class="eval-chart-title">评分趋势（近30天）</div>
        <div ref="trendRatingRef" style="width: 100%; height: 260px"></div>
      </div>
      <div class="eval-chart-box">
        <div class="eval-chart-title">满意度趋势（近30天）</div>
        <div ref="trendSatisRef" style="width: 100%; height: 260px"></div>
      </div>
    </div>
    <!-- 历史评测列表 -->
    <div class="eval-history-card">
      <div class="eval-history-title">历史评测记录</div>
      <div v-if="!historyList.length" class="eval-empty">
        暂无评测记录，点击「开始评测」触发首次评测
      </div>
      <table v-else class="eval-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>模型</th>
            <th>时间</th>
            <th>准确率</th>
            <th>avg延迟</th>
            <th>溯源率</th>
            <th>综合分</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in historyList" :key="r.id" @click="viewDetail(r.id)" class="eval-tr">
            <td>
              <code>{{ r.id }}</code>
            </td>
            <td>{{ r.model_name }}</td>
            <td>{{ r.run_at?.slice(0, 16) }}</td>
            <td>
              <span :class="scoreClass(r.accuracy)">{{ pct(r.accuracy) }}</span>
            </td>
            <td>{{ r.avg_latency?.toFixed(0) }}ms</td>
            <td>{{ pct(r.source_acc) }}</td>
            <td>
              <b :class="scoreClass(r.overall)">{{ pct(r.overall) }}</b>
            </td>
            <td>
              <span
                :class="[
                  'eval-status',
                  r.status === 'done' ? 'eval-status--ok' : 'eval-status--run'
                ]"
              >
                {{ r.status === 'done' ? ' 完成' : ' 运行中' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!-- 题库预览 -->
    <div class="eval-qs-card">
      <div class="eval-history-title">内置测试题库（20条）</div>
      <div class="eval-qs-cats">
        <span v-for="(qs, cat) in questionsByCategory" :key="cat" class="eval-cat-chip">
          {{ catLabel(cat) }} {{ qs.length }}题
        </span>
      </div>
      <div class="eval-qs-list">
        <div v-for="q in allQuestions.slice(0, showAllQs ? 999 : 5)" :key="q.id" class="eval-q-row">
          <span class="eval-q-cat">{{ catLabel(q.category) }}</span>
          <span class="eval-q-text">{{ q.question }}</span>
        </div>
        <button
          v-if="allQuestions.length > 5"
          class="eval-btn-more"
          @click="showAllQs = !showAllQs"
        >
          {{ showAllQs ? '收起' : `展开全部 ${allQuestions.length} 条` }}
        </button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'
import { MessagePlugin } from 'tdesign-vue-next'
import { useEvalStore } from '@/store'
const evalStore = useEvalStore()
// ── 本地 UI 状态（非持久化） ─────────────────────────────────
const evalModels = ref(localStorage.getItem('selected_model') || '')
const loadingChart = ref(false)
const modelLoading = ref(false)
const localModels = ref<string[]>([])
const cloudModels = ref<string[]>([])

// 自动检测可用模型
async function detectModels() {
  modelLoading.value = true
  try {
    // 检测本地Ollama模型
    const ollamaSettings = localStorage.getItem('ollamaSettings')
    const ollamaUrl = ollamaSettings
      ? JSON.parse(ollamaSettings).serverUrl
      : 'http://localhost:11434'
    try {
      const res = await fetch(`${ollamaUrl}/api/tags`)
      const data = await res.json()
      localModels.value = (data.models || []).map((m: any) => m.name)
    } catch {
      localModels.value = []
    }
    // 检测云端模型配置
    try {
      const res = await fetch('/api/models/providers')
      if (res.ok) {
        const data = await res.json()
        cloudModels.value = (data.providers || [])
          .filter((p: any) => p.enabled && p.type !== 'local')
          .flatMap((p: any) => p.available_models || [p.config?.model].filter(Boolean))
      }
    } catch {
      // 降级：从localStorage读取已保存的模型
      const saved = localStorage.getItem('selected_model')
      if (saved) cloudModels.value = [saved]
    }
    // 默认选择第一个可用模型
    if (!evalModels.value) {
      if (localModels.value.length > 0) evalModels.value = localModels.value[0]
      else if (cloudModels.value.length > 0) evalModels.value = cloudModels.value[0]
    }
  } finally {
    modelLoading.value = false
  }
}
const questionsByCategory = ref<Record<string, any[]>>({})
const showAllQs = ref(false)
// ECharts DOM refs
const radarRef = ref<HTMLElement>()
const catBarRef = ref<HTMLElement>()
const latencyRef = ref<HTMLElement>()
const trendRatingRef = ref<HTMLElement>()
const trendSatisRef = ref<HTMLElement>()
// ── 高级指标 ────────────────────────────────────────────────────
const metricsLoading = ref(false)
const metricsData = ref<any>(null)
const metricsTrend = ref<any[]>([])

const advancedMetrics = computed(() => {
  const m = metricsData.value?.metrics
  if (!m) return []
  return [
    {
      key: 'recall',
      label: 'Recall@K',
      value: (m.recall_at_k * 100).toFixed(1) + '%',
      desc: '检索召回率',
      color: m.recall_at_k >= 0.7 ? '#22c55e' : m.recall_at_k >= 0.4 ? '#f59e0b' : '#ef4444'
    },
    {
      key: 'precision',
      label: 'Precision@K',
      value: (m.precision_at_k * 100).toFixed(1) + '%',
      desc: '检索精确率',
      color: m.precision_at_k >= 0.7 ? '#22c55e' : m.precision_at_k >= 0.4 ? '#f59e0b' : '#ef4444'
    },
    {
      key: 'mrr',
      label: 'MRR',
      value: m.mrr.toFixed(4),
      desc: '平均倒数排名',
      color: m.mrr >= 0.7 ? '#22c55e' : m.mrr >= 0.4 ? '#f59e0b' : '#ef4444'
    },
    {
      key: 'ndcg',
      label: 'NDCG@K',
      value: m.ndcg_at_k.toFixed(4),
      desc: '归一化折损累积增益',
      color: m.ndcg_at_k >= 0.7 ? '#22c55e' : m.ndcg_at_k >= 0.4 ? '#f59e0b' : '#ef4444'
    }
  ]
})

async function computeAdvancedMetrics() {
  metricsLoading.value = true
  try {
    const res = await axios.post('/api/rag-eval/advanced-metrics', {
      question: 'metrics-eval',
      top_k: 5,
      strategy: 'hybrid'
    })
    metricsData.value = res.data
    // 同时获取趋势数据
    const trendRes = await axios.get('/api/rag-eval/metrics-trend', { params: { days: 30 } })
    metricsTrend.value = trendRes.data?.trend || []
    await nextTick()
    renderTrendCharts()
  } catch {
    metricsData.value = {
      metrics: {
        recall_at_k: 0,
        precision_at_k: 0,
        mrr: 0,
        ndcg_at_k: 0,
        sample_count: 0,
        top_k: 5
      }
    }
  } finally {
    metricsLoading.value = false
  }
}
// ── 从 store 获取持久化状态 ──────────────────────────────────
const running = computed(() => evalStore.running)
const latestRun = computed(() => evalStore.latestRun)

const historyList = computed(() => evalStore.historyList)
const chartData = computed(() => evalStore.chartData)
// ── 计算属性 ─────────────────────────────────────────────────
const allQuestions = computed(() => Object.values(questionsByCategory.value).flat())
const overviewCards = computed(() => {
  if (!latestRun.value) return []
  const r = latestRun.value
  return [
    {
      key: 'acc',
      icon: '',
      label: '准确率',
      value: pct(r.accuracy),
      color: scoreColor(r.accuracy)
    },
    {
      key: 'lat',
      icon: '',
      label: '平均响应',
      value: `${r.avg_latency?.toFixed(0)}ms`,
      color: r.avg_latency < 2000 ? '#22c55e' : '#f59e0b'
    },
    {
      key: 'src',
      icon: '',
      label: '溯源准确率',
      value: pct(r.source_acc),
      color: scoreColor(r.source_acc)
    },
    {
      key: 'overall',
      icon: '',
      label: '综合评分',
      value: pct(r.overall),
      color: scoreColor(r.overall)
    },
    { key: 'qs', icon: '', label: '测试题数', value: `${r.total_q}题`, color: '#6366f1' },
    { key: 'pass', icon: '', label: '通过题数', value: `${r.passed_q}题`, color: '#22c55e' }
  ]
})
// ── 工具函数 ──────────────────────────────────────────────────
const pct = (v: number | undefined) => (v != null ? (v * 100).toFixed(1) + '%' : '-')
const scoreColor = (v: number) => (v >= 0.7 ? '#22c55e' : v >= 0.4 ? '#f59e0b' : '#ef4444')
const scoreClass = (v: number) =>
  v >= 0.7 ? 'score--good' : v >= 0.4 ? 'score--mid' : 'score--bad'
const catLabel = (cat: string) =>
  ({
    retrieval: ' 检索',
    summary: ' 摘要',
    reasoning: ' 推理',
    technical: ' 技术',
    general: ' 通用'
  })[cat] || cat
// ── API ───────────────────────────────────────────────────────
async function runEval() {
  const model = evalModels.value.trim()
  if (!model) {
    MessagePlugin.warning('请先选择评测模型')
    return
  }
  await evalStore.startEval([model])
  // 评测完成后重新渲染图表
  await nextTick()
  renderCharts()
}
async function fetchLatest() {
  loadingChart.value = true
  try {
    await evalStore.fetchLatest()
    await nextTick()
    renderCharts()
  } finally {
    loadingChart.value = false
  }
}
async function fetchQuestions() {
  try {
    const res = await axios.get('/api/eval/questions')
    questionsByCategory.value = res.data?.by_category || {}
  } catch {}
}
function viewDetail(runId: string) {
  window.open(`/api/eval/results/${runId}`, '_blank')
}
// ── ECharts 渲染 ──────────────────────────────────────────────
function renderCharts() {
  if (!chartData.value) return
  try {
    // @ts-ignore
    const echarts = (window as any).echarts
    if (!echarts) return
    renderRadar(echarts)
    renderCatBar(echarts)
    renderLatencyHist(echarts)
    renderTrendCharts()
  } catch {}
}

function renderTrendCharts() {
  // @ts-ignore
  const echarts = (window as any).echarts
  if (!echarts || metricsTrend.value.length === 0) return

  if (trendRatingRef.value) {
    const chart = echarts.init(trendRatingRef.value)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: metricsTrend.value.map(t => t.date?.slice(5) || '') },
      yAxis: { type: 'value', min: 0, max: 5, axisLabel: { formatter: '{value}' } },
      series: [
        {
          type: 'line',
          data: metricsTrend.value.map(t => t.avg_rating),
          smooth: true,
          itemStyle: { color: '#6366f1' },
          areaStyle: { color: 'rgba(99,102,241,0.1)' }
        }
      ]
    })
  }
  if (trendSatisRef.value) {
    const chart = echarts.init(trendSatisRef.value)
    chart.setOption({
      tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
      xAxis: { type: 'category', data: metricsTrend.value.map(t => t.date?.slice(5) || '') },
      yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%' } },
      series: [
        {
          type: 'line',
          data: metricsTrend.value.map(t => t.satisfaction_rate),
          smooth: true,
          itemStyle: { color: '#22c55e' },
          areaStyle: { color: 'rgba(34,197,94,0.1)' }
        }
      ]
    })
  }
}
function renderRadar(echarts: any) {
  // intentionally empty
  if (!radarRef.value) return
  const chart = echarts.init(radarRef.value)
  const d = chartData.value.radar
  chart.setOption({
    tooltip: {},
    radar: { indicator: d.indicators, radius: '65%' },
    series: [
      {
        type: 'radar',

        data: d.series.map((s: any) => ({ name: s.name, value: s.value }))
      }
    ]
  })
}
function renderCatBar(echarts: any) {
  if (!catBarRef.value) return
  const chart = echarts.init(catBarRef.value)
  const d = chartData.value.category_bar
  chart.setOption({
    // intentionally empty

    tooltip: {},
    xAxis: { type: 'category', data: d.categories.map((c: string) => catLabel(c)) },
    yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    series: [{ type: 'bar', data: d.scores, itemStyle: { color: '#6366f1' } }]
  })
}
function renderLatencyHist(echarts: any) {
  if (!latencyRef.value) return
  const chart = echarts.init(latencyRef.value)

  const d = chartData.value.latency_hist
  chart.setOption({
    tooltip: {},
    xAxis: { type: 'category', data: d.labels },
    yAxis: { type: 'value' },

    series: [
      {
        type: 'bar',
        data: d.counts,
        itemStyle: {
          color: (p: any) =>
            p.dataIndex <= 1 ? '#22c55e' : p.dataIndex <= 3 ? '#f59e0b' : '#ef4444'
        }
      }
    ]
  })
}
// ── 挂载 ECharts CDN 脚本 ─────────────────────────────────────
function ensureECharts(): Promise<void> {
  return new Promise(resolve => {
    if ((window as any).echarts) {
      resolve()
      return
    }
    const s = document.createElement('script')

    s.src = 'https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js'
    s.onload = () => resolve()
    document.head.appendChild(s)
  })
}
onMounted(async () => {
  await ensureECharts()
  await Promise.all([detectModels(), fetchLatest(), fetchQuestions()])
  // 如果 store 中已有数据（从其他页面带回来的），立即渲染图表
  if (chartData.value) {
    await nextTick()

    renderCharts()
  }
})
// 监听 store 中图表数据变化（如在其他页面评测完成），自动渲染
watch(chartData, async val => {
  if (val) {
    await nextTick()
    renderCharts()
  }
})
</script>
<style scoped>
.eval-toolbar {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}
.eval-model-input {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 220px;
}
.eval-model-input label {
  font-size: 12px;
  color: #6b7280;
}
.eval-input {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
  background: var(--td-bg-color-container, #fff);
  color: var(--td-text-color-primary, #111);
}
.eval-input:focus {
  border-color: #6366f1;
}
.eval-select {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
  background: var(--td-bg-color-container, #fff);
  color: var(--td-text-color-primary, #111);
  min-width: 200px;
}
.eval-select:focus {
  border-color: #6366f1;
}
.eval-hint {
  font-size: 11px;
  color: #9ca3af;
}
.eval-btn-run {
  padding: 8px 22px;
  background: #6366f1;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}
.eval-btn-run:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.eval-btn-run:hover:not(:disabled) {
  background: #4f46e5;
}
.eval-btn-refresh {
  padding: 8px 14px;
  background: #f9fafb;
  color: #374151;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}
.eval-btn-refresh:hover:not(:disabled) {
  background: #f3f4f6;
}
.eval-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  font-size: 13px;
  color: #1d4ed8;
  margin-bottom: 16px;
}
.eval-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #bfdbfe;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.eval-overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}
.eval-ov-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 8px;
  background: var(--td-bg-color-container, #fff);
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  gap: 4px;
}
.eval-ov-icon {
  font-size: 20px;
}
.eval-ov-value {
  font-size: 20px;
  font-weight: 700;
}
.eval-ov-label {
  font-size: 11px;
  color: #6b7280;
}
.eval-charts-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
@media (max-width: 900px) {
  .eval-charts-row {
    grid-template-columns: 1fr;
  }
}
.eval-chart-box {
  background: var(--td-bg-color-container, #fff);
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 14px;
}
.eval-chart-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--td-text-color-primary, #111);
}
.eval-history-card,
.eval-qs-card {
  background: var(--td-bg-color-container, #fff);
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}
.eval-history-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}
.eval-empty {
  font-size: 13px;
  color: #9ca3af;
  text-align: center;
  padding: 20px;
}
.eval-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.eval-table th {
  text-align: left;
  padding: 6px 10px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}
.eval-tr td {
  padding: 7px 10px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
}
.eval-tr:hover {
  background: #f9fafb;
}
.eval-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}
.eval-status--ok {
  background: #dcfce7;
  color: #166534;
}
.eval-status--run {
  background: #dbeafe;
  color: #1e40af;
}
.score--good {
  color: #22c55e;
  font-weight: 600;
}
.score--mid {
  color: #f59e0b;
  font-weight: 600;
}
.score--bad {
  color: #ef4444;
  font-weight: 600;
}
.eval-qs-cats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.eval-cat-chip {
  padding: 3px 10px;
  background: #eff6ff;
  color: #1d4ed8;
  border-radius: 12px;
  font-size: 12px;
}
.eval-qs-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.eval-q-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.eval-q-cat {
  min-width: 80px;
  font-size: 11px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
}
.eval-btn-more {
  background: none;
  border: none;
  color: #6366f1;
  font-size: 12px;
  cursor: pointer;
  padding: 4px 0;
  text-decoration: underline;
}
/* 高级指标 */
.eval-section-title {
  font-size: 14px;
  font-weight: 600;
  margin: 20px 0 12px;
  color: var(--td-text-color-primary, #111);
}
.eval-metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}
.eval-metric-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  background: var(--td-bg-color-container, #fff);
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  gap: 4px;
}
.eval-metric-value {
  font-size: 22px;
  font-weight: 700;
}
.eval-metric-label {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
}
.eval-metric-desc {
  font-size: 10px;
  color: #9ca3af;
}
</style>
