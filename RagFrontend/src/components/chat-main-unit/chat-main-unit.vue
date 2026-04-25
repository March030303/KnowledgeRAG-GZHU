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
            <component :is="renderPresets([{ name: 'uploadAttachment' }])" />
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
// 支持的文件扩展名白名单
const SUPPORTED_EXTENSIONS = new Set([
  '.docx',
  '.doc',
  '.md',
  '.xls',
  '.xlsx',
  '.png',
  '.jpg',
  '.jpeg',
  '.webp',
  '.txt',
  '.pdf',
  '.ppt',
  '.pptx',
  '.pptm'
])

// 文件选择处理
/**
 * 处理文件选择的异步函数
 * - 图片文件（png/jpg/jpeg/webp）：生成预览并添加到图片列表，同时作为附件标记
 * - 文本文件（txt/md）：读取内容填充到输入框
 * - 其他支持文件（docx/doc/xls/xlsx/pdf/ppt/pptx/pptm）：作为附件上传到后端
 * - 不在白名单的文件类型则提示不支持
 */
const attachedFiles = ref<File[]>([]) // 附件文件列表

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
  const getExtension = (filename: string) => {
    const dotIdx = filename.lastIndexOf('.')
    return dotIdx >= 0 ? filename.slice(dotIdx).toLowerCase() : ''
  }
  try {
    if (!files || !files.files || files.files.length === 0) {
      console.warn('没有选择任何文件')
      return
    }
    const fileObj = files.files[0]
    const ext = getExtension(fileObj.name)

    if (!SUPPORTED_EXTENSIONS.has(ext)) {
      const message = `暂不支持处理此类型的文件: ${fileObj.name}，支持格式：docx/doc/md/xls/xlsx/png/jpg/webp/txt/pdf/ppt/pptx`
      console.warn(message)
      MessagePlugin.warning(message)
      return
    }

    if (fileObj.type.startsWith('image/')) {
      // 图片：生成预览
      console.log('检测到图片文件，正在处理...')
      const dataUrl = await getFileUrlByFileRaw(fileObj)
      useChatImg.addImage(dataUrl)
      attachedFiles.value.push(fileObj)
    } else if (fileObj.type === 'text/plain' || ext === '.txt' || ext === '.md') {
      // 文本/Markdown文件：读取内容填充到输入框
      console.log('检测到文本文件，正在读取内容...')
      const fileContent = await getTextByFileRaw(fileObj)
      const prefix = ext === '.md' ? 'Markdown' : '文本'
      const newText = `--- 从${prefix}文件 ${fileObj.name} 中读取的内容 ---\n\n${fileContent}`
      inputValue.value = newText
      document.querySelector('#chatSender textarea')?.focus()
    } else {
      // 其他支持的文件类型：作为附件标记
      console.log(`检测到附件文件: ${fileObj.name}，将作为附件发送`)
      attachedFiles.value.push(fileObj)
      MessagePlugin.success(`已添加附件: ${fileObj.name}`)
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
  let aiName = '助手'
  if (curModelVal.toLowerCase().includes('deepseek')) {
    aiName = ' DeepSeek'
  } else if (
    curModelVal.toLowerCase().includes('gpt') ||
    curModelVal.toLowerCase().includes('openai')
  ) {
    aiName = ' GPT'
  } else if (curModelVal.toLowerCase().includes('hunyuan')) {
    aiName = ' 混元'
  } else if (curModelVal) {
    aiName = ` ${curModelVal}`
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
  // 清空附件和图片预览（图片内容已包含在消息中，不再自动消失）
  useChatImg.clearAllImg()
  attachedFiles.value = []
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
            lastItem.content = ` ${data.error}`
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
            // 检测<think> 标签开始
            if (!thinkingStarted && accumulatedResponse.includes('<think>')) {
              isInThinking = true
              thinkingStarted = true
              console.log('开始思考过程')
              // 提取<think> 之前的内容作为正式回答
              const beforeThink = accumulatedResponse.split('<think>')[0]
              if (beforeThink.trim()) {
                lastItem.content = beforeThink
              }
              // 提取<think> 之后的内容作为思考过程开始
              const afterThink = accumulatedResponse.split('<think>')[1]
              if (afterThink) {
                lastItem.reasoning = afterThink
              }
            }
            // 检测</think> 标签结束
            else if (isInThinking && accumulatedResponse.includes('</think>')) {
              isInThinking = false
              console.log('结束思考过程')
              // 分割思考内容和后续回答
              const thinkContent = accumulatedResponse.split('<think>')[1].split('</think>')[0]
              const afterThink = accumulatedResponse.split('</think>')[1]
              // 更新思考内容（去掉标签）
              lastItem.reasoning = thinkContent
              // 添加</think> 后的内容到正式回答
              if (afterThink) {
                lastItem.content += afterThink
              }
            }
            // 在思考过程中
            else if (isInThinking) {
              // 更新思考内容（去掉<think> 标签）
              const currentThinking = accumulatedResponse.split('<think>')[1]
              if (currentThinking && !currentThinking.includes('</think>')) {
                lastItem.reasoning = currentThinking
              }
            }
            // 正常回答过程（不在思考中）
            else if (!isInThinking) {
              // 如果还没开始思考，或者思考已结束
              if (!thinkingStarted) {
                // 还没遇到<think> 标签，正常添加到内容
                lastItem.content += data.response
              } else {
                // 思考已结束，继续添加到内容（排除</think> 标签）
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
/* 应用滚动条样式 */
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
  /* 撑满父容器（chat-main-area）的全部高度 */
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  /* chat-inner 让 t-chat 内部自己处理滚动 */
  .chat-inner {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
  .bottomBtn {
    position: absolute;
    left: 50%;
    margin-left: -20px;
    bottom: 210px;
    padding: 0;
    border: 0;
    width: 40px;
    height: 40px;
    /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
    border-radius: 50%;
    box-shadow:
      0px 8px 10px -5px rgba(0, 0, 0, 0.08),
      0px 16px 24px 2px rgba(0, 0, 0, 0.04),
      0px 6px 30px 5px rgba(0, 0, 0, 0.05);
  }
  .to-bottom {
    width: 40px;
    height: 40px;
    /* eslint-disable-next-line no-useless-escape */
    /* eslint-disable-next-line no-useless-escape */
    border: 1px solid #dcdcdc;
    box-sizing: border-box;
    background: var(--td-bg-color-container);
    border-radius: 50%;
    font-size: 24px;
    line-height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    .t-icon {
      font-size: 24px;
    }
  }
}
.model-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 180px;
  padding: 0 10px;
  height: 32px;
  border-radius: 999px;
  background: var(--td-bg-color-secondarycontainer);
  border: 1px solid var(--td-border-level-1-color);
}
.model-badge__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  flex-shrink: 0;
}
.model-badge__dot.is-cloud {
  background: #3b82f6;
}
.model-badge__text {
  font-size: 12px;
  color: var(--td-text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.t-chat-input.position-absolute {
  position: absolute;
  bottom: 10px;
  /* 距离底部20px */
  left: 0;
  right: 0;
  margin: auto;
  /* 水平居中 */
  width: 100%;
  /* 可根据需要调整宽度 */
}
.custom-chat-dialog {
  /* 添加背景颜色 */
  background-color: #dbeafe59;
  /* 添加边框圆角 */
  border-radius: 8px;
  margin-top: 10px;
  padding-right: 20px !important;
}
.chat-sender {
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  border-top: 1px solid var(--td-border-level-1-color);
  padding: 16px;
  box-sizing: border-box;
}
/* 原有样式保持不变 */
.chat-box .t-chat {
  padding-bottom: 50px;
}
@media (max-width: 768px) {
  .chat-sender {
    padding: 12px;
  }
  .chat-box .t-chat {
    padding-bottom: 100px;
  }
}
.image-preview-container {
  padding: 8px 12px;
  background-color: var(--td-bg-color-secondarycontainer);
  border-bottom: 1px solid var(--td-border-level-1-color);
  max-height: 120px;
  overflow-y: auto;
  border-radius: 12px;
  border: 1px solid var(--td-border-level-1-color);
}
.image-wrapper {
  position: relative;
  display: inline-block;
  border-radius: var(--td-radius-medium);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
  &:hover {
    transform: translateY(-2px);
    .remove-image-btn {
      opacity: 1;
    }
  }
}
.remove-image-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  z-index: 2;
  opacity: 0;
  background-color: rgba(0, 0, 0, 0.5) !important;
  color: white !important;
  border: none;
  transition: opacity 0.2s ease-in-out;
}
.sender-prefix-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 12px;
}
.deep-think-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--td-text-color-placeholder);
  padding: 4px 8px;
  border-radius: var(--td-radius-medium);
  transition:
    color 0.2s ease,
    background-color 0.2s ease;
  &:hover {
    background-color: var(--td-bg-color-container-hover);
  }
  &.is-active {
    color: var(--td-brand-color);
    font-weight: bold;
  }
}
.chat-sender {
  :deep(.t-textarea__inner) {
    padding-left: 2px;
  }
}
/* 使用这个更精确和健壮的选择器 */
.t-chat-action.active-good :deep([aria-label='good']),
.t-chat-action.active-bad :deep([aria-label='bad']) {
  color: var(--td-brand-color) !important;
  background-color: var(--td-brand-color-light) !important;
  border-radius: var(--td-radius-default);
}
/* 如果想让踩的颜色不同 */
.t-chat-action.active-bad :deep([aria-label='bad']) {
  color: var(--td-error-color) !important;
  background-color: var(--td-error-color-1) !important;
}
/* 引用溯源样式 */
.source-citations {
  margin-top: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}
.source-citations__header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f8fafc;
  cursor: pointer;
  color: #4b5563;
  user-select: none;
  transition: background 0.15s;
  &:hover {
    background: #f1f5f9;
  }
}
.source-icon {
  width: 14px;
  height: 14px;
}
.chevron {
  width: 14px;
  height: 14px;
  margin-left: auto;
  transition: transform 0.2s;
  &.rotated {
    transform: rotate(180deg);
  }
}
.source-citations__list {
  border-top: 1px solid #e5e7eb;
  background: #fafafa;
}
.source-item {
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  &:last-child {
    border-bottom: none;
  }
}
.source-item__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.source-num {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #4f7ef8;
  color: white;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.source-filename {
  font-weight: 600;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.source-score {
  background: #dcfce7;
  color: #16a34a;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 600;
  white-space: nowrap;
}
.source-item__content {
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
