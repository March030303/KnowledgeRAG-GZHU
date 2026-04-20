<template>
  <div class="chat-box">
    <t-chat
      ref="chatRef"
      :clear-history="chatList.length > 0 && !isStreamLoad"
      :data="chatList"
      :text-loading="loading"
      :is-stream-load="isStreamLoad"
      class="chat-inner p-5"
      @scroll="handleChatScroll"
      @clear="clearConfirm"
    >
      <template #default="{ item, index }">
        <t-chat-item :key="index" :role="item?.role">
          <template #default>
            <t-chat-reasoning v-if="item.reasoning?.length > 0" expand-icon-placement="right">
              <template #header>
                <t-chat-loading
                  v-if="isStreamLoad && item.content.length === 0"
                  text="思考中...按Ctrl+C停止"
                />
                <div v-else style="display: flex; align-items: center">
                  <CheckCircleIcon
                    style="color: var(--td-success-color-5); font-size: 20px; margin-right: 8px"
                  />
                  <span>已思考</span>
                </div>
              </template>
              <t-chat-content v-if="item.reasoning.length > 0" :content="item.reasoning" />
            </t-chat-reasoning>
            <t-chat-content
              v-if="item.content.length > 0"
              :content="item.content"
              class="custom-chat-dialog"
            />
            <!-- 引用溯源 -->
            <div v-if="item.sources && item.sources.length > 0" class="source-citations">
              <div class="source-citations__header" @click="toggleSources(item)">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="source-icon"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <span>{{ item.sources.length }} 个引用来源</span>
                <svg
                  :class="['chevron', { rotated: item._sourcesExpanded }]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
              <div v-if="item._sourcesExpanded" class="source-citations__list">
                <div v-for="(src, si) in item.sources" :key="si" class="source-item">
                  <div class="source-item__header">
                    <span class="source-num">{{ si + 1 }}</span>
                    <span class="source-filename">{{ src.filename }}</span>
                    <span v-if="src.score != null" class="source-score"
                      >{{ Math.round(src.score * 100) }}%</span
                    >
                  </div>
                  <div class="source-item__content">{{ src.content }}</div>
                </div>
              </div>
            </div>
          </template>
        </t-chat-item>
      </template>
      <template #actions="{ item }">
        <t-chat-action
          :content="item.content"
          :operation-btn="['good', 'bad', 'replay', 'copy']"
          :class="{
            'active-good': item.actionsState?.good,
            'active-bad': item.actionsState?.bad
          }"
          @operation="op => handleOperation(op, item)"
        />
      </template>
      <template #footer>
        <div v-if="imgDatas && imgDatas.length > 0" class="image-preview-container">
          <t-space :gap="10" class="image-preview-space">
            <div v-for="(item, index) in imgDatas" :key="index" class="image-wrapper">
              <t-image
                :src="item"
                alt="上传失败"
                :style="{ width: '60px', height: '60px' }"
                fit="cover"
              />
              <t-button
                class="remove-image-btn"
                shape="circle"
                size="small"
                variant="base"
                @click="useChatImg.clearImage(item)"
              >
                <template #icon>
                  <CloseIcon />
                </template>
              </t-button>
            </div>
          </t-space>
        </div>
        <t-chat-sender
          id="chatSender"
          ref="chatSenderRef"
          v-model="inputValue"
          class="chat-sender"
          :textarea-props="{
            placeholder: '请输入消息，Shift + Enter 换行'
          }"
          :loading="isStreamLoad"
          @send="inputEnter"
          @file-select="fileSelect"
          @stop="onStop"
        >
          <template #suffix="{ renderPresets }">
            <component
              :is="renderPresets([{ name: 'uploadImage' }, { name: 'uploadAttachment' }])"
            />
          </template>
          <template #prefix>
            <div class="sender-prefix-controls">
              <div class="model-badge" :title="selectedModelLabel">
                <span class="model-badge__dot" :class="{ 'is-cloud': isCloudModel }"></span>
                <span class="model-badge__text">{{ selectedModelLabel }}</span>
              </div>
              <t-tooltip content="开启后模型会进行更深度的思考，但响应会变慢">
                <t-button
                  class="deep-think-btn"
                  :class="{ 'is-active': isChecked }"
                  variant="text"
                  @click="checkClick"
                >
                  <SystemSumIcon />
                  <span>深度思考</span>
                </t-button>
              </t-tooltip>
              <!-- 语音输入 -->
              <t-tooltip content="语音输入（Whisper 本地识别）">
                <VoiceInput
                  :language="'zh'"
                  @transcribed="
                    text => {
                      inputValue = text
                    }
                  "
                  @error="msg => console.warn('[Voice]', msg)"
                />
              </t-tooltip>
            </div>
          </template>
        </t-chat-sender>
      </template>
    </t-chat>
    <t-button v-show="isShowToBottom" variant="text" class="bottomBtn" @click="backBottom">
      <div class="to-bottom">
        <ArrowDownIcon />
      </div>
    </t-button>
  </div>
</template>
<script setup lang="tsx">
/* eslint-disable @typescript-eslint/no-explicit-any */
// @ts-nocheck
import {
  ref,
  reactive,
  toRefs,
  onMounted,
  onBeforeUnmount,
  nextTick,
  defineProps,
  computed
} from 'vue'
//import { MockSSEResponse } from './sseRequest-reasoning';
import { ArrowDownIcon, CheckCircleIcon, SystemSumIcon } from 'tdesign-icons-vue-next'
import VoiceInput from '@/components/VoiceInput.vue'
import {
  Chat as TChat,
  ChatAction as TChatAction,
  ChatContent as TChatContent,
  //ChatInput as TChatInput,
  ChatItem as TChatItem,
  ChatReasoning as TChatReasoning,
  ChatLoading as TChatLoading
} from '@tdesign-vue-next/chat'
import { fetchOllamaStream } from './sseRequest-reasoning'
import { MessagePlugin } from 'tdesign-vue-next'
import { useChatImgtore } from '@/store'
import { CloseIcon } from 'tdesign-icons-vue-next'
const useChatImg = useChatImgtore()
// 基础状态
const fetchCancel = ref(null)
const loading = ref(false)
const isStreamLoad = ref(false)
const chatRef = ref(null)
const chatSenderRef = ref(null)
const inputValue = ref('')
const isShowToBottom = ref(false)
//const allowToolTip = ref(false);
//定义props
// 定义 MessageRecord 类型
/** 
const MessageRecord = {
  avatar: String,
  name: String,
  datetime: String,
  content: String,
  role: String,
  reasoning: String,
  duration: Number,
};*/
// 定义 props
const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  lastMessage: {
    type: String,
    default: ''
  },
  history: {
    type: Array,
    default: () => []
  },
  selectedModel: {
    type: String,
    default: ''
  }
})
const isChecked = ref(false)
const selectedModelValue = computed(() => props.selectedModel || '')
const isCloudModel = computed(
  () => Boolean(selectedModelValue.value) && !selectedModelValue.value.includes(':')
)
const selectedModelLabel = computed(() => {
  if (!selectedModelValue.value) return '未选择模型'
  if (isCloudModel.value) {
    const providerLabel = (() => {
      const modelId = selectedModelValue.value.toLowerCase()
      if (modelId.includes('deepseek')) return 'DeepSeek'
      if (modelId.includes('gpt') || modelId.includes('openai')) return 'OpenAI'
      if (modelId.includes('hunyuan')) return '混元'
      return '云端模型'
    })()
    return `${providerLabel} · ${selectedModelValue.value}`
  }
  return `Ollama · ${selectedModelValue.value}`
})
// 深度思考开关
const checkClick = () => {
  isChecked.value = !isChecked.value
}
// 聊天数据
//[Vue warn] toRefs() expects a reactive object but received a plain one.
// 解决方法：这里要使用toRefs()将reactive对象转换为响应式对象
const state = reactive({
  chatList: props.history
})
const { chatList } = toRefs(state)
const nextMsg = ref('')
// 滚动相关
const backBottom = () => {
  chatRef.value.scrollToBottom({
    behavior: 'smooth'
  })
}
const handleChatScroll = function ({ e }) {
  const scrollTop = e.target.scrollTop
  isShowToBottom.value = scrollTop < 0
}
// 清空消息
const clearConfirm = function () {
  chatList.value = []
}
// 文件选择处理
/**
 * 处理文件选择的异步函数
 * - 如果是图片，则生成预览并添加到图片列表。
 * - 如果是文本文件，则读取内容并填充到输入框。
 * - 其他文件类型则提示不支持。
 */
const fileSelect = async function (files) {
  const getFileUrlByFileRaw = file => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = e => reject(new Error('图片读取失败: ' + e))
      reader.readAsDataURL(file)
    })
  }
  const getTextByFileRaw = file => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsText(file, 'UTF-8')
      reader.onload = () => resolve(reader.result)
      reader.onerror = e => reject(new Error('文本文件读取失败: ' + e))
    })
  }
  try {
    if (!files || !files.files || files.files.length === 0) {
      console.warn('没有选择任何文件')
      return
    }
    const fileObj = files.files[0]
    if (fileObj.type.startsWith('image/')) {
      console.log('检测到图片文件，正在处理...')
      const dataUrl = await getFileUrlByFileRaw(fileObj)
      useChatImg.addImage(dataUrl)
    } else if (fileObj.type === 'text/plain') {
      console.log('检测到文本文件，正在读取内容...')
      const fileContent = await getTextByFileRaw(fileObj)
      const newText = `--- 从文件 ${fileObj.name} 中读取的内容 ---\n\n${fileContent}`
      inputValue.value = newText
      document.querySelector('#chatSender textarea')?.focus()
    } else {
      const message = `暂不支持处理此类型的文件: ${fileObj.name} (${fileObj.type})`
      console.warn(message)
      MessagePlugin.warning(message)
    }
  } catch (error) {
    console.error('文件处理失败:', error)
    MessagePlugin.error(error.message || '文件处理失败，请重试')
  }
}
// 添加中断状态标识
const isUserAborted = ref(false)
const onStop = () => {
  if (fetchCancel.value?.controller) {
    // 标记为用户主动中断
    isUserAborted.value = true
    // 使用 abort() 中断请求
    fetchCancel.value.controller.abort()
    // 清理状态
    fetchCancel.value = null
    loading.value = false
    isStreamLoad.value = false
    console.log('用户主动停止流式响应')
    MessagePlugin.info('已停止生成')
  }
}
// 消息发送处理 - 修复后的版本
const inputEnter = function (messageContent) {
  // 防止重复发送
  if (isStreamLoad.value) {
    console.log('正在处理中，忽略重复发送')
    return
  }
  nextMsg.value = messageContent
  console.log('发送的消息:', messageContent)
  // 添加用户消息
  const userMessage = {
    avatar: 'https://tdesign.gtimg.com/site/avatar.jpg',
    name: '自己',
    datetime: new Date().toLocaleString(),
    content: messageContent,
    role: 'user',
    actionsState: { good: false, bad: false }
  }
  // 根据当前选中模型动态命名 AI
  const curModelVal = selectedModelValue.value
  let aiName = 'TDesignAI'
  if (curModelVal.toLowerCase().includes('deepseek')) {
    aiName = '🤖 DeepSeek'
  } else if (
    curModelVal.toLowerCase().includes('gpt') ||
    curModelVal.toLowerCase().includes('openai')
  ) {
    aiName = '🤖 GPT'
  } else if (curModelVal.toLowerCase().includes('hunyuan')) {
    aiName = '🤖 混元'
  } else if (curModelVal) {
    aiName = `🤖 ${curModelVal}`
  }
  // 添加AI占位消息
  const aiMessage = {
    avatar: 'https://tdesign.gtimg.com/site/chat-avatar.png',
    name: aiName,
    datetime: new Date().toLocaleString(),
    content: '',
    reasoning: '',
    role: 'assistant',
    actionsState: { good: false, bad: false }
  }
  chatList.value.unshift(userMessage)
  chatList.value.unshift(aiMessage)
  // 启动流式加载状态
  isStreamLoad.value = true
  //loading.value = true;
  // 清空输入框 - 正确的方式
  inputValue.value = ''
  useChatImg.clearAllImg()
  // 如果组件提供了清空方法，也调用一下
  nextTick(() => {
    if (chatSenderRef.value && typeof chatSenderRef.value.clear === 'function') {
      chatSenderRef.value.clear()
    }
  })
  // 开始处理数据
  handleData(messageContent)
}
// SSE 处理
/** 
const fetchSSE = async (fetchFn, options) => {
  try {
    const response = await fetchFn();
    const { success, fail, complete } = options;
    if (!response.ok) {
      complete?.(false, response.statusText);
      fail?.();
      return;
    }
    const reader = response?.body?.getReader();
    const decoder = new TextDecoder();
    if (!reader) {
      complete?.(false, "无法获取数据流");
      return;
    }
    const processText = async ({ done, value }) => {
      if (done) {
        complete?.(true);
        return;
      }
      try {
        const chunk = decoder.decode(value, { stream: true });
        const buffers = chunk.toString().split(/\r?\n/);
        const jsonData = JSON.parse(buffers);
        success(jsonData);
      } catch (error) {
        console.error("解析数据出错:", error);
      }
      return reader.read().then(processText);
    };
    reader.read().then(processText);
  } catch (error) {
    console.error("fetchSSE 出错:", error);
    options.complete?.(false, error.message);
  }
};*/
// 数据处理
// src/components/chat-main-unit/chat-main-unit.vue
// 修改数据处理函数
const emit = defineEmits(['chat-updated', 'send-message'])
// ── 云端模型 SSE 对话（走 /api/models/chat）──────────────────────
const handleCloudChat = async (messageContent: string, modelId: string, historyList: any[]) => {
  const lastItem = chatList.value[0]
  isUserAborted.value = false
  // 将 chatList 历史转换为 messages 格式（最多保留最近20条）
  const recentHistory = [...historyList].reverse().slice(-20)
  const messages = recentHistory
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .map(m => ({ role: m.role, content: m.content || '' }))
  // 最后一条就是本次用户输入
  if (!messages.length || messages[messages.length - 1]?.content !== messageContent) {
    messages.push({ role: 'user', content: messageContent })
  }
  const controller = new AbortController()
  fetchCancel.value = { controller }
  try {
    const response = await fetch('/api/models/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: modelId,
        messages,
        stream: true,
        temperature: 0.7,
        max_tokens: 4096
      }),
      signal: controller.signal
    })
    if (!response.ok) {
      const errText = await response.text()
      throw new Error(`云端 API 返回 ${response.status}: ${errText}`)
    }
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n').filter(l => l.trim())
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.error) {
            lastItem.role = 'error'
            lastItem.content = `❌ ${data.error}`
            lastItem.reasoning = ''
          } else if (data.content) {
            lastItem.content += data.content
          }
          if (data.done) {
            lastItem.duration = 0
            isStreamLoad.value = false
            loading.value = false
            fetchCancel.value = null
            emit('chat-updated')
          }
        } catch {
          /* skip bad JSON */
        }
      }
    }
  } catch (error: any) {
    if (isUserAborted.value || error.name === 'AbortError') {
      lastItem.content = lastItem.content || '响应已停止'
    } else {
      lastItem.role = 'error'
      lastItem.content = `云端模型请求失败: ${error.message}`
      lastItem.reasoning = ''
    }
  } finally {
    isStreamLoad.value = false
    loading.value = false
    fetchCancel.value = null
  }
}
// 修改数据处理函数
const handleData = async messageContent => {
  console.log('开始处理数据:', messageContent)
  isUserAborted.value = false
  const lastItem = chatList.value[0]
  const currentModel = selectedModelValue.value
  if (!currentModel) {
    lastItem.role = 'error'
    lastItem.content = '请先在左侧选择可用模型后再发送消息'
    lastItem.reasoning = ''
    isStreamLoad.value = false
    loading.value = false
    return
  }
  // ── 云端模型路由（原始 ID 不带 provider 前缀）───────────────
  if (!currentModel.includes(':')) {
    await handleCloudChat(messageContent, currentModel, chatList.value)
    return
  }
  // ── 本地 Ollama 模型（原有逻辑）─────────────────────────
  const localModel = currentModel.replace(/^local:/, '') || currentModel || 'llama2'
  // 获取 Ollama 配置
  let serverUrl = 'http://localhost:11434'
  try {
    const savedSettings = localStorage.getItem('ollamaSettings')
    if (savedSettings) {
      const settings = JSON.parse(savedSettings)
      serverUrl = settings.serverUrl || 'http://localhost:11434'
    }
  } catch (e) {
    console.error('加载 Ollama 设置失败:', e)
  }
  // 用于追踪思考过程状态
  let isInThinking = false
  let thinkingStarted = false
  let accumulatedResponse = '' // 累积所有响应内容
  try {
    const { response, controller } = await fetchOllamaStream(
      messageContent,
      localModel, // 使用本地模型名（已去掉 local: 前缀）
      serverUrl
    )
    fetchCancel.value = { controller }
    if (!response.ok) {
      throw new Error(`Ollama API responded with status: ${response.status}`)
    }
    const reader = response.body.getReader()

    const decoder = new TextDecoder()
    // 处理流式响应
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      try {
        const lines = chunk.trim().split('\n')
        for (const line of lines) {
          if (!line.trim()) continue
          const data = JSON.parse(line)
          if (data.response) {
            accumulatedResponse += data.response
            // 检测 <think> 标签开始
            if (!thinkingStarted && accumulatedResponse.includes('<think>')) {
              isInThinking = true
              thinkingStarted = true
              console.log('开始思考过程')
              // 提取 <think> 之前的内容作为正式回答
              const beforeThink = accumulatedResponse.split('<think>')[0]
              if (beforeThink.trim()) {
                lastItem.content = beforeThink
              }
              // 提取 <think> 之后的内容作为思考过程开始
              const afterThink = accumulatedResponse.split('<think>')[1]
              if (afterThink) {
                lastItem.reasoning = afterThink
              }
            }
            // 检测 </think> 标签结束
            else if (isInThinking && accumulatedResponse.includes('</think>')) {
              isInThinking = false
              console.log('结束思考过程')
              // 分割思考内容和后续回答
              const thinkContent = accumulatedResponse.split('<think>')[1].split('</think>')[0]
              const afterThink = accumulatedResponse.split('</think>')[1]
              // 更新思考内容（去掉标签）
              lastItem.reasoning = thinkContent
              // 添加 </think> 后的内容到正式回答
              if (afterThink) {
                lastItem.content += afterThink
              }
            }
            // 在思考过程中
            else if (isInThinking) {
              // 更新思考内容（去掉 <think> 标签）
              const currentThinking = accumulatedResponse.split('<think>')[1]
              if (currentThinking && !currentThinking.includes('</think>')) {
                lastItem.reasoning = currentThinking
              }
            }
            // 正常回答过程（不在思考中）
            else if (!isInThinking) {
              // 如果还没开始思考，或者思考已结束
              if (!thinkingStarted) {
                // 还没遇到 <think> 标签，正常添加到内容
                lastItem.content += data.response
              } else {
                // 思考已结束，继续添加到内容（排除 </think> 标签）
                const cleanResponse = data.response.replace('</think>', '')
                if (cleanResponse) {
                  lastItem.content += cleanResponse
                }
              }
            }
          }
          // 检查是否完成
          if (data.done) {
            // 最终清理：确保移除所有标签
            lastItem.content = lastItem.content.replace(/<\/?think>/g, '')
            lastItem.reasoning = lastItem.reasoning.replace(/<\/?think>/g, '')
            lastItem.duration = data.total_duration ? Math.round(data.total_duration / 1000000) : 20
            console.log('最终内容:', {
              reasoning: lastItem.reasoning,
              content: lastItem.content
            })
            // 完成处理
            isStreamLoad.value = false
            loading.value = false
            fetchCancel.value = null
            // **发送保存信号给父组件**
            emit('chat-updated')
          }
        }
      } catch (error) {
        console.error('解析数据出错:', error, chunk)
      }
    }
    // 完成处理
    isStreamLoad.value = false
    loading.value = false
    fetchCancel.value = null
  } catch (error) {
    console.log('用户主动中断:', error)
    // 区分用户主动中断和真正的连接错误
    if (isUserAborted.value || error.name === 'AbortError') {
      // 用户主动中断，不显示错误消息
      console.log('流式响应被用户中断')
      if (lastItem) {
        // 保持当前内容，不覆盖为错误消息
        lastItem.content = lastItem.content || '响应已停止'
      }
    } else {
      // 真正的连接或其他错误
      console.error('Ollama连接错误:', error)
      if (lastItem) {
        lastItem.role = 'error'
        lastItem.content = `连接Ollama服务失败，请检查API服务是否配置正确: ${error.message}`
        lastItem.reasoning = ''
      }
    }
    // 清理状态
    isStreamLoad.value = false
    loading.value = false
    fetchCancel.value = null
  }
}
// 键盘事件处理
const handleKeyDown = event => {
  if (event.ctrlKey && event.key === 'c') {
    event.preventDefault()
    onStop()
  }
}
//图片展示相关
const imgDatas = computed(() => {
  console.log(useChatImg.images)
  return useChatImg.images
})
const handleOperation = async (operation, item) => {
  if (!item.actionsState) {
    item.actionsState = { good: false, bad: false }
  }
  const state = item.actionsState
  switch (operation) {
    case 'good':
      state.good = !state.good
      if (state.good) state.bad = false
      MessagePlugin.success(state.good ? '已点赞' : '已取消赞')
      break
    case 'bad':
      state.bad = !state.bad
      if (state.bad) state.good = false
      MessagePlugin.info(state.bad ? '已点踩' : '已取消踩')
      break
    case 'copy':
      try {
        await navigator.clipboard.writeText(item.content)
        MessagePlugin.success('内容已复制到剪贴板')
      } catch (err) {
        MessagePlugin.error('复制失败' + err)
      }
      break
    case 'replay':
      MessagePlugin.info('“重新生成”')
      inputEnter(nextMsg.value)
      break
  }
}
// 生命周期
onMounted(() => {
  console.log(chatList.value)
  nextMsg.value = chatList.value[Object.keys(chatList.value)[0]]?.content || ''
  console.log(nextMsg.value)
  window.addEventListener('keydown', handleKeyDown)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown)
  if (fetchCancel.value?.controller) {
    fetchCancel.value.controller.abort()
  }
})
// 引用溯源展开/折叠
const toggleSources = item => {
  item._sourcesExpanded = !item._sourcesExpanded
}
</script>
<style lang="less">
::-webkit-scrollbar-thumb {
  background-color: var(--td-scrollbar-color);
}
::-webkit-scrollbar-thumb:horizontal:hover {
  background-color: var(--td-scrollbar-hover-color);
}
::-webkit-scrollbar-track {
  background-color: var(--td-scroll-track-color);
}
.chat-box {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  .chat-inner {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
  .bottomBtn {
    position: absolute;
    left: 50%;
    margin-left: -18px;
    bottom: 210px;
    padding: 0;
    border: 0;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--bg-overlay);
    border: 1px solid var(--border-base);
    box-shadow: var(--shadow-md);
    color: var(--text-secondary);
    transition: all var(--transition-fast);
    &:hover {
      background: var(--bg-hover);
      color: var(--text-primary);
      border-color: var(--border-active);
      transform: translateY(-1px);
      box-shadow: var(--shadow-lg);
    }
  }
  .to-bottom {
    width: 36px;
    height: 36px;
    border: none;
    background: transparent;
    border-radius: 50%;
    font-size: 20px;
    line-height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: inherit;
    .t-icon {
      font-size: 20px;
    }
  }
}
.model-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 160px;
  padding: 0 8px;
  height: 28px;
  border-radius: var(--radius-full);
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  transition: border-color var(--transition-fast);
  &:hover {
    border-color: var(--border-active);
  }
}
.model-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-emerald);
  flex-shrink: 0;
  box-shadow: 0 0 6px rgba(52, 211, 153, 0.4);
}
.model-badge__dot.is-cloud {
  background: var(--accent-cyan);
  box-shadow: 0 0 6px rgba(34, 211, 238, 0.4);
}
.model-badge__text {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.t-chat-input.position-absolute {
  position: absolute;
  bottom: 10px;
  left: 0;
  right: 0;
  margin: auto;
  width: 100%;
}
.custom-chat-dialog {
  background-color: rgba(124, 106, 255, 0.04);
  border: 1px solid rgba(124, 106, 255, 0.08);
  border-radius: var(--radius-md);
  margin-top: 8px;
  padding-right: 16px !important;
}
.chat-sender {
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  border-top: 1px solid var(--border-subtle);
  padding: 12px 16px;
  box-sizing: border-box;
  background: var(--bg-surface);
}
.chat-box .t-chat {
  padding-bottom: 50px;
}
@media (max-width: 768px) {
  .chat-sender {
    padding: 10px 12px;
  }
  .chat-box .t-chat {
    padding-bottom: 80px;
  }
}
.image-preview-container {
  padding: 6px 10px;
  background-color: var(--bg-elevated);
  border-bottom: 1px solid var(--border-subtle);
  max-height: 100px;
  overflow-y: auto;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}
.image-wrapper {
  position: relative;
  display: inline-block;
  border-radius: var(--radius-sm);
  overflow: hidden;
  box-shadow: var(--shadow-xs);
  transition: transform 0.2s var(--ease-out);
  &:hover {
    transform: translateY(-2px);
    .remove-image-btn {
      opacity: 1;
    }
  }
}
.remove-image-btn {
  position: absolute;
  top: 3px;
  right: 3px;
  z-index: 2;
  opacity: 0;
  background-color: rgba(0, 0, 0, 0.6) !important;
  color: white !important;
  border: none !important;
  transition: opacity 0.2s ease-in-out;
}
.sender-prefix-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-left: 10px;
}
.deep-think-btn {
  display: flex;
  align-items: center;
  gap: 3px;
  color: var(--text-tertiary);
  padding: 3px 6px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  transition: color 0.15s ease, background-color 0.15s ease;
  &:hover {
    background-color: var(--bg-hover);
  }
  &.is-active {
    color: var(--accent-violet);
    font-weight: 600;
  }
}
.chat-sender {
  :deep(.t-textarea__inner) {
    padding-left: 2px;
    background: var(--bg-elevated) !important;
    color: var(--text-primary) !important;
  }
}
.t-chat-action.active-good :deep([aria-label='good']),
.t-chat-action.active-bad :deep([aria-label='bad']) {
  color: var(--accent-violet) !important;
  background-color: var(--accent-violet-subtle) !important;
  border-radius: var(--radius-sm);
}
.t-chat-action.active-bad :deep([aria-label='bad']) {
  color: var(--accent-rose) !important;
  background-color: var(--accent-rose-subtle) !important;
}
.source-citations {
  margin-top: 6px;
  border: 1px solid var(--border-base);
  border-radius: var(--radius-md);
  overflow: hidden;
  font-size: 11.5px;
  background: var(--bg-elevated);
}
.source-citations__header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: var(--bg-overlay);
  cursor: pointer;
  color: var(--text-secondary);
  user-select: none;
  transition: background 0.12s ease;
  &:hover {
    background: var(--bg-hover);
  }
}
.source-icon {
  width: 13px;
  height: 13px;
  color: var(--accent-violet-light);
}
.chevron {
  width: 13px;
  height: 13px;
  margin-left: auto;
  color: var(--text-quaternary);
  transition: transform 0.2s var(--ease-out);
  &.rotated {
    transform: rotate(180deg);
  }
}
.source-citations__list {
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-surface);
}
.source-item {
  padding: 6px 10px;
  border-bottom: 1px solid var(--border-subtle);
  &:last-child {
    border-bottom: none;
  }
}
.source-item__header {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 3px;
}
.source-num {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent-violet);
  color: white;
  font-size: 9px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.source-filename {
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.source-score {
  background: var(--accent-emerald-subtle);
  color: var(--accent-emerald);
  padding: 1px 5px;
  border-radius: var(--radius-full);
  font-weight: 600;
  font-size: 10px;
  white-space: nowrap;
}
.source-item__content {
  color: var(--text-tertiary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 11px;
}
</style>
