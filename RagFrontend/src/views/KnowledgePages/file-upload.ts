// 定义文件上传函数
import { Ref } from 'vue'
import axios from 'axios'
import { MessagePlugin } from 'tdesign-vue-next'

/** 允许的文件扩展名白名单（需与后端 ALLOWED_EXTENSIONS 保持同步） */
const ALLOWED_EXTENSIONS = new Set([
  // 文档格式
  '.pdf',
  '.docx',
  '.doc',
  '.xlsx',
  '.xls',
  '.csv',
  // 文本格式
  '.txt',
  '.md',
  // 图像格式
  '.png',
  '.jpg',
  '.jpeg',
  '.gif',
  '.bmp',
  // 音频格式
  '.mp3',
  '.wav',
  '.m4a',
  '.ogg',
  '.flac',
  '.aac',
  // 视频格式
  '.mp4',
  '.avi',
  '.mov',
  '.mkv',
  '.flv',
  '.wmv',
  '.webm'
])

/** 服务端最大文件大小限制（50MB） */
const MAX_FILE_SIZE = 50 * 1024 * 1024

/**
 * 并发限流执行器：最多同时运行 maxConcurrency 个 Promise
 * 避免大批量上传触发浏览器同源并发限制（Chrome 最多 6 个）
 */
async function runWithConcurrencyLimit<T>(
  tasks: (() => Promise<T>)[],
  maxConcurrency = 3
): Promise<T[]> {
  const results: T[] = []
  let index = 0

  async function worker() {
    while (index < tasks.length) {
      const taskIndex = index++
      results[taskIndex] = await tasks[taskIndex]()
    }
  }

  const workers = Array.from({ length: Math.min(maxConcurrency, tasks.length) }, () => worker())
  await Promise.all(workers)
  return results
}

/**
 * 校验文件类型和大小（上传前预检，快速失败）
 * @returns 错误信息字符串或空字符串（表示通过）
 */
function validateFileBeforeUpload(file: File): string {
  if (!file || !(file instanceof File)) return '无效的文件对象'
  if (!file.name || typeof file.name !== 'string') return '文件名无效'

  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  if (!ext || !ALLOWED_EXTENSIONS.has(ext)) {
    return `不支持的文件类型: ${ext ?? '(无扩展名)'}`
  }
  if (file.size > MAX_FILE_SIZE) {
    return `文件大小超过限制 (${(file.size / 1024 / 1024).toFixed(1)}MB / ${(MAX_FILE_SIZE / 1024 / 1024).toFixed(1)}MB)`
  }
  if (file.size === 0) {
    return '文件为空（0 字节）'
  }
  return ''
}

// 生成文件 hash，使用 SHA-256
const generateFileHash = async (file: File): Promise<string> => {
  // 检查文件参数是否有效
  if (!file) {
    throw new Error('文件对象为空')
  }

  if (!(file instanceof File)) {
    throw new Error('参数不是有效的File对象')
  }

  try {
    // 检查浏览器是否支持 crypto.subtle API
    if (window.crypto && window.crypto.subtle) {
      const buffer = await file.arrayBuffer()
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)

      // 检查 hashBuffer 是否有效
      if (!hashBuffer) {
        throw new Error('生成文件哈希失败')
      }

      const hashArray = Array.from(new Uint8Array(hashBuffer))
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
      return hashHex
    } else {
      // 备选方案：使用文件名、大小和最后修改时间生成标识符
      const identifier = `${file.name}-${file.size}-${file.lastModified}`
      let hash = 0
      for (let i = 0; i < identifier.length; i++) {
        const char = identifier.charCodeAt(i)
        hash = (hash << 5) - hash + char
        hash = hash & hash // 转换为32位整数
      }
      return Math.abs(hash).toString(16)
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    throw new Error(`生成文件哈希失败: ${errorMessage}`)
  }
}

// ... 已有代码 ...

export const uploadFiles = async (
  uploadedFiles: Ref<File[]>,
  isUploading: Ref<boolean>,
  uploadProgress: Ref<number>,
  KLB_id: string // 添加知识库ID参数
) => {
  // 参数校验
  if (!uploadedFiles || !uploadedFiles.value) {
    MessagePlugin.error('上传文件列表为空')
    return
  }

  if (!KLB_id || !KLB_id.trim()) {
    MessagePlugin.error('知识库ID为空')
    return
  }

  const validFiles = uploadedFiles.value.filter(f => f && f instanceof File)
  if (validFiles.length === 0) return

  // 上传前预检所有文件
  for (const file of validFiles) {
    const validationError = validateFileBeforeUpload(file)
    if (validationError) {
      MessagePlugin.error(`${file.name}: ${validationError}`)
      return // 快速失败：任一文件不合法即终止
    }
  }

  isUploading.value = true
  uploadProgress.value = 0

  // 存储每个文件的 fileName、fileHash 和 totalChunks
  const fileInfoList: { fileName: string; fileHash: string; totalChunks: number }[] = []

  try {
    for (const file of validFiles) {
      const chunkSize = 0.1 * 1024 * 1024 // 每个分块大小 100KB
      const totalChunks = Math.ceil(file.size / chunkSize)
      let uploadedChunks = 0

      // 生成文件唯一标识（基于内容 SHA-256）
      const fileHash = await generateFileHash(file)

      // 存储当前文件的信息，包含总块数
      fileInfoList.push({ fileName: file.name, fileHash, totalChunks })

      // 上传每个分块
      for (let i = 0; i < totalChunks; i++) {
        const start = i * chunkSize
        const end = Math.min(file.size, start + chunkSize)
        const chunk = file.slice(start, end)

        const formData = new FormData()
        formData.append('chunk', chunk)
        formData.append('fileHash', fileHash)
        formData.append('chunkIndex', i.toString())
        formData.append('totalChunks', totalChunks.toString())
        formData.append('fileName', file.name)
        formData.append('KLB_id', KLB_id)

        await axios.post('/api/upload-chunk', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: progressEvent => {
            const total = progressEvent.total || 0
            const chunkProgress = (progressEvent.loaded / total) * (100 / totalChunks)
            uploadProgress.value = Math.round(uploadedChunks * (100 / totalChunks) + chunkProgress)
          }
        })
        uploadedChunks++
      }
    }

    MessagePlugin.success(
      '文件上传完成：' + (fileInfoList.length > 0 ? fileInfoList[0].fileName : '所有文件')
    )

    // 遍历文件信息列表，逐个调用上传完成接口（最大3并发）
    const completeTasks = fileInfoList.map(fileInfo => async () => {
      return axios.post(
        '/api/upload-complete',
        {
          fileName: fileInfo.fileName,
          fileHash: fileInfo.fileHash,
          totalChunks: fileInfo.totalChunks || 1,
          KLB_id: KLB_id
        },
        { timeout: 60000 }
      )
    })
    await runWithConcurrencyLimit(completeTasks, 3)

    isUploading.value = false
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    MessagePlugin.error('文件上传失败:' + errorMessage)
    isUploading.value = false
  }
}
