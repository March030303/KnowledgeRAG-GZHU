<div align="center">

# RAG-F · 智能知识管理平台

**基于检索增强生成（RAG）的私有知识库问答系统**

[![Vue3](https://img.shields.io/badge/Vue-3.x-42b883?logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6?logo=typescript)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Version](https://img.shields.io/badge/commit-6c71d6e-brightgreen)](https://github.com/March030303/KnowledgeRAG-GZHU/commits/main)

[快速启动](#-快速启动) · [功能模块](#4-核心功能模块) · [API 文档](http://localhost:8000/docs) · [移动端 App](#8-移动端-app) · [部署方案](#9-部署方案)

</div>

---

## 📖 项目简介

**RAG-F** 是一套面向个人与团队的智能知识管理平台，通过将私有文档与本地/云端大语言模型深度结合，实现**检索增强生成（RAG）**问答，显著降低 AI 幻觉、提升领域知识回答的准确性。

**核心价值：**

- 🧠 **防幻觉问答** — 答案严格基于你的文档，来源可追溯
- 📚 **统一知识管理** — 多格式文档、分块上传、权限分级（URL 批量导入前端已预留，后端待补齐）
- 🤖 **Agent 任务模式** — ReAct 框架，自然语言驱动多步骤任务
- ✍️ **文档创作** — 5 种文本创作 / 处理能力，按独立接口提供
- 🔗 **办公联动** — Obsidian / 飞书 / 钉钉 / 企微已接入；Notion / GitHub 当前为配置占位
- 📱 **双端支持** — Web + React Native 移动端 App
- 🗺️ **系统架构图** — 可视化 4-Tab 架构展示（技术栈/数据流/部署/模块）
- 🚀 **本地部署** — 数据不离本地，一键 Docker 启动

---

## 目录

1. [项目简介](#-项目简介)
2. [技术架构](#-技术架构)
3. [快速启动](#-快速启动)
4. [核心功能模块](#4-核心功能模块)
   - 4.1 [用户认证系统](#41-用户认证系统)
   - 4.2 [知识库管理](#42-知识库管理)
   - 4.3 [RAG 智能问答](#43-rag-智能问答)
   - 4.4 [Agent 任务模式](#44-agent-任务模式)
   - 4.5 [多模型适配](#45-多模型适配)
   - 4.6 [检索策略配置](#46-检索策略配置)
   - 4.7 [语音交互](#47-语音交互)
   - 4.8 [联网搜索](#48-联网搜索)
   - 4.9 [文档创作](#49-文档创作)
   - 4.10 [RAG 评测](#410-rag-评测)
5. [扩展功能模块](#5-扩展功能模块)
   - 5.1 [个人主页与设置](#51-个人主页与设置)
   - 5.2 [外观与主题](#52-外观与主题)
   - 5.3 [第三方账号绑定](#53-第三方账号绑定)
   - 5.4 [反馈与建议](#54-反馈与建议)
   - 5.5 [历史记录](#55-历史记录)
   - 5.6 [全局搜索](#56-全局搜索)
   - 5.7 [置顶功能](#57-置顶功能)
   - 5.8 [全局交互动效](#58-全局交互动效)
   - 5.9 [系统设置（Win11 风格）](#59-系统设置win11-风格)
   - 5.10 [系统架构图](#510-系统架构图)
6. [集成与联动](#6-集成与联动)
   - 6.1 [Obsidian 笔记同步](#61-obsidian-笔记同步)
   - 6.2 [飞书机器人](#62-飞书机器人)
   - 6.3 [钉钉 / 企微 / Notion / GitHub](#63-钉钉--企微--notion--github)
   - 6.4 [多数据源接入](#64-多数据源接入)
7. [系统管理](#7-系统管理)
   - 7.1 [开放 API](#71-开放-api)
   - 7.2 [审计日志](#72-审计日志)
   - 7.3 [增量向量化](#73-增量向量化)
   - 7.4 [RBAC 权限管理](#74-rbac-权限管理)
   - 7.5 [OCR 文档解析](#75-ocr-文档解析)
   - 7.6 [系统监控](#76-系统监控)
8. [移动端 App](#8-移动端-app)
9. [部署方案](#9-部署方案)
10. [目录结构](#10-目录结构)
11. [环境变量说明](#11-环境变量说明)
12. [常见问题 FAQ](#12-常见问题-faq)
13. [Contributors](#13-contributors)
14. [后续规划](#14-后续规划)

---

## 🏗️ 技术架构

```
┌──────────────────────────────────────────────────────┐
│                    客户端层                           │
│  Web 前端 (Vue3 + Vite + TDesign)                    │
│  移动端 App (React Native + Expo)                    │
└────────────────────┬─────────────────────────────────┘
                     │ HTTP / SSE
┌────────────────────▼─────────────────────────────────┐
│                   服务层                              │
│  FastAPI 后端 (Python 3.10+)                         │
│  ├── 用户认证 (JWT + MySQL)                          │
│  ├── 知识库管理 (文档解析 + 向量化)                  │
│  ├── RAG Pipeline (LangChain + 多策略检索 + 轻量重排)│
│  ├── Agent (ReAct + 工具链)                          │
│  ├── 多模型路由 (Ollama/OpenAI/DeepSeek/混元)        │
│  ├── 语音 ASR (Whisper)                              │
│  ├── 文档创作 (5 类文本处理接口)                     │
│  ├── 评测面板 (轻量问答评测 + 可视化)                │
│  ├── Prometheus 监控中间件                            │
│  ├── 联网搜索 (DuckDuckGo)                           │
│  └── 集成服务 (Obsidian/飞书/钉钉/企微/占位扩展)     │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│                   存储层                              │
│  MySQL (用户数据)  │  向量数据库  │  SQLite (审计日志) │
│  OSS/S3 (文件存储)│  本地文件系统                     │
└──────────────────────────────────────────────────────┘
```

| 层级       | 技术选型                                                    |
| ---------- | ----------------------------------------------------------- |
| 前端框架   | Vue 3 + TypeScript + Vite 5                                 |
| UI 组件库  | TDesign Vue Next                                            |
| 状态管理   | Pinia（跨路由持久化）                                       |
| 后端框架   | FastAPI + uvicorn                                           |
| LLM 框架   | LangChain                                                   |
| 本地模型   | Ollama（支持本地模型动态发现，低配友好）                    |
| 关系数据库 | MySQL 8.0（Docker 默认编排）                                |
| 重排能力   | 主链路 lightweight rerank + 独立 Cross-Encoder 接口（可选） |
| 移动端     | React Native + Expo SDK 52 + zustand                        |

| 容器化 | Docker + Docker Compose |
| 语音识别 | OpenAI Whisper（本地） |
| 监控 | Prometheus 中间件 + ECharts |

---

## 🚀 快速启动

### 环境前置要求

1. **安装 Ollama**：[https://ollama.com](https://ollama.com)
2. **拉取本地模型**（可选，低配机器推荐小参数模型）：
   ```bash
   ollama pull llama3.2:1b    # ~1GB，低配友好；也可使用其他已安装的 Ollama 模型
   ```
3. **硬件最低要求**（运行小参数本地模型）：

   | 组件        | 最低要求                   |
   | ----------- | -------------------------- |
   | 内存（RAM） | 4GB                        |
   | 存储空间    | 5GB                        |
   | GPU         | 可选（CPU 也可运行小模型） |

---

### 方式一：Docker Compose（推荐生产/演示）

```bash
# 克隆仓库
git clone https://github.com/March030303/KnowledgeRAG-GZHU.git
cd KnowledgeRAG-GZHU

# 配置环境变量
cp RagBackend/.env.example RagBackend/.env
# 编辑 .env，填写 DB_PASSWORD / JWT_SECRET 等

# 一键启动（前端 + 后端 + MySQL + Ollama）
docker compose up -d

# 访问
# 前端：    http://localhost:8089
# API 文档：http://localhost:8000/docs
# Ollama：  http://localhost:11435
```

---

### 方式二：一键开发脚本（推荐本地开发）

```powershell
# 启动所有服务（MySQL 用 Docker 托管，后端 + 前端本地运行）
powershell -ExecutionPolicy Bypass -File .\dev.ps1

# 查看状态
powershell -ExecutionPolicy Bypass -File .\dev.ps1 -Status

# 停止所有
powershell -ExecutionPolicy Bypass -File .\dev.ps1 -Stop

# 访问
# 前端（Vite）：http://localhost:5173
# 后端 API：    http://localhost:8000
# API 文档：    http://localhost:8000/docs
```

> **智能跳过**：脚本自动检测已运行的服务，二次调用几乎瞬间完成。

---

### 方式三：手动启动

```bash
# 1. 启动 MySQL（Docker）
docker run -d --name ragf-mysql -e MYSQL_ROOT_PASSWORD=yourpw -e MYSQL_DATABASE=rag_user_db -p 3307:3306 mysql:8.0


# 2. 后端
cd RagBackend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 3. 前端
cd RagFrontend
npm install
npm run dev   # → http://localhost:5173
```

---

## 4. 核心功能模块

### 4.1 用户认证系统

**功能描述：** 完整的账号生命周期管理，支持邮箱注册/登录。

| 功能     | 说明                                                             |
| -------- | ---------------------------------------------------------------- |
| 邮箱注册 | 输入邮箱+密码创建账户，后端当前使用 **SHA256** 哈希存储          |
| 邮箱登录 | JWT Token 鉴权，默认 **24 小时过期**                             |
| 忘记密码 | 邮箱验证码找回流程                                               |
| 个人资料 | 头像、昵称、签名、社交信息可更新；邮箱当前仅读取，不支持直接修改 |
| 语言设置 | 中文 / English 切换，前端 localStorage 持久化                    |

**数据库表：**

```sql
user (id, email, password, created_at, qq_openid)
user_profile (user_id, nickname, avatar, ...)
```

**API 端点：**

```
POST /api/register                 -- 注册
POST /api/login                    -- 登录（Token）
POST /api/login/json               -- 登录（JSON）
GET  /api/users/me                 -- 当前用户信息
GET  /api/user/GetUserData         -- 获取资料
POST /api/UpdateUserData           -- 更新资料
POST /api/user/UpdateAvatar        -- 更新头像
GET  /api/qq/authorize             -- QQ OAuth 授权
GET  /api/qq/callback              -- QQ OAuth 回调
POST /api/reset/send-email-code    -- 发送重置验证码
POST /api/reset/password           -- 重置密码
```

---

### 4.2 知识库管理

**功能描述：** 以"知识库"为单位组织文档；多格式上传与基础 CRUD 已实现，URL 批量导入和备份入口目前存在前后端不完全对齐的情况。

#### 知识库列表页

- ⭐ **星标置顶**：重要知识库一键收藏，星标分区展示
- 📌 **置顶固定**：重要知识库 / 文件 / 模型可置顶，localStorage 持久化
- 🕐 **最近访问**：自动记录访问历史，快速找回
- 🔍 **搜索过滤**：实时搜索知识库名称
- ↕️ **拖拽排序**：原生 HTML5 拖拽，localStorage 持久化排序
- 📦 **备份能力**：后端已提供备份 API，但当前 `KnowledgeBase.vue` 未见备份按钮入口

#### 知识库详情页

- 📄 **文档管理**：列表展示所有文档，支持删除、重命名
- 📤 **文件上传**：支持 PDF、Word、TXT、Markdown、Excel、图片等格式，采用分块上传
- 🔗 **URL 批量导入**：前端弹窗与调用已存在，但后端 `/api/url-import/` 当前未实现
- 📝 **笔记模块**：在详情页直接记录笔记，关联到知识库
- ⚙️ **知识库设置**：支持名称、描述与配置项更新

#### 权限体系（当前状态）

```text
前端已提供 个人 / 共享 / 广场 三档配置 UI
后端存在知识库配置更新接口，但三级可见性字段尚未形成完全统一的后端 schema 落地
```

**已实现 API 端点：**

```
POST   /api/create-knowledgebase/              -- 创建知识库
DELETE /api/delete-knowledgebase/{id}          -- 删除知识库
GET    /api/get-knowledge-item/                -- 知识库列表/详情聚合
GET    /api/list-knowledge-bases/              -- 简化列表接口
GET    /api/get-knowledge-item/{id}            -- 单个知识库详情
POST   /api/update-knowledgebase-config/{id}   -- 更新知识库配置
POST   /api/upload-chunk/                      -- 上传文件分块
POST   /api/upload-complete/                   -- 合并分块并入库
GET    /api/documents-list/{id}/               -- 文档列表
```

**实现缺口：**

- 前端当前调用 `POST /api/url-import/`，但后端未找到对应实现
- 后端已实现 `POST /api/backup/create` 等备份接口，但前端入口未接入

---

### 4.3 RAG 智能问答

**功能描述：** 基于 LangChain 的 RAG Pipeline，将用户问题与知识库文档结合，生成有据可查的回答。

#### 对话界面

- 💬 **流式输出**：SSE（Server-Sent Events）实时打字机效果
- 📚 **RAG 模式开关**：可切换纯 LLM 对话 vs 知识库增强对话
- 🗂️ **知识库选择器**：侧边栏面板，勾选参与问答的知识库
- 🔍 **引用溯源气泡**：AI 回答标注来源，点击展开原文段落
- 📋 **多轮对话**：保持上下文，支持追问

#### RAG Pipeline（当前真实链路）

```
用户问题
  → 问题向量化（embedding）
  → 检索策略执行（见4.6）
  → 召回相关段落（Top-K）
  → 可选轻量重排（token overlap，本地 lightweight rerank）
  → Prompt 构建（问题 + 上下文）
  → LLM 生成回答（流式 / 同步）
  → 引用来源标注
```

> 说明：项目中**存在**独立的 Cross-Encoder 实现（`rag_enhancement/reranker.py`，`POST /api/rerank`），但**默认 RAG 主链路未接入**；当前主链路使用的是本地轻量重排逻辑。

**核心 API 端点：**

```
POST /api/RAG/RAG_query            -- RAG 问答（流式）
POST /api/RAG/RAG_query_sync       -- RAG 问答（同步）
POST /api/RAG/native_query         -- 本地问答入口
POST /api/chat/send-message        -- 前端会话页发送消息
GET  /api/chat/chat-documents      -- 会话列表
DELETE /api/chat/delete-session    -- 删除会话
```

---

### 4.4 Agent 任务模式

**功能描述：** 基于 ReAct（Reasoning + Acting）框架的智能 Agent，能够分解复杂任务、调用工具链自主完成目标。

#### 执行可视化

```
任务输入
  → 🤔 Thought（推理步骤）
  → 🔧 Action（工具调用）
  → 👁️ Observation（执行结果）
  → 循环直到任务完成
  → ✅ Final Answer
```

#### 工具链

| 工具       | 说明                              |
| ---------- | --------------------------------- |
| 知识库检索 | 在指定知识库中语义搜索            |
| 联网搜索   | DuckDuckGo 实时搜索（零 API Key） |
| 文档读取   | 读取并分析指定文档内容            |
| 代码执行   | 运行 Python 代码片段              |

- 任务历史当前主要保存在前端 `localStorage.agent_task_history`
- 离线降级模板存在，Ollama 不可用时仍可演示基本流程

**API 端点：**

```
POST /api/agent/task               -- 启动 Agent 任务（SSE）
POST /api/RAG/agent_query          -- Agent 问答入口
POST /api/RAG/agent_query_sync     -- Agent 同步入口
GET  /api/agent/web-search         -- 联网搜索工具
```

---

### 4.5 多模型适配

**功能描述：** 统一的多模型路由层，支持本地和云端多种 LLM，按需切换。

| 类型 | 模型                   | 说明                                     |
| ---- | ---------------------- | ---------------------------------------- |
| 本地 | Ollama（任意本地模型） | 通过用户配置动态切换，低配可选小参数模型 |
| 云端 | OpenAI                 | 需配置 API Key                           |
| 云端 | DeepSeek               | 需配置 API Key                           |
| 云端 | 腾讯混元               | 需配置 API Key                           |

#### 用户自定义模型配置

- 设置页「模型配置」Tab 可自定义 Ollama 地址、模型名称、请求超时时长
- 后端不可用时，前端仍会先写入 localStorage 做离线兜底
- 多模型路由支持 provider 状态检测与统一聊天入口

```
GET  /api/user-model-config            -- 获取用户模型配置
POST /api/user-model-config            -- 保存用户模型配置
GET  /api/user-model-config/local-models
POST /api/user-model-config/test
GET  /api/models/list                  -- 可用模型列表
POST /api/models/chat                  -- 多模型统一对话
POST /api/models/configure             -- 配置模型 provider
POST /api/models/test                  -- 测试模型连通性
GET  /api/models/providers/status      -- provider 状态
```

---

### 4.6 检索策略配置

| 策略       | 说明                                   | 适用场景         |
| ---------- | -------------------------------------- | ---------------- |
| **Vector** | 纯向量语义相似度检索                   | 语义理解要求高   |
| **BM25**   | 关键词稀疏检索                         | 精确词匹配场景   |
| **Hybrid** | 向量 + BM25 线性加权融合               | 通用场景推荐     |
| **RRF**    | 倒数排名融合（Reciprocal Rank Fusion） | 多路召回重排     |
| **MMR**    | 最大边际相关性（减少冗余）             | 需要多样性的场景 |

前端 `RetrievalConfig.vue` 组件提供滑块、选择器等直观配置界面，参数透传至 RAG Pipeline。

> 当前默认策略为 **RRF**；`rerank` 选项调用的是本地 token overlap 轻量重排，而不是默认接入真实 Cross-Encoder 模型。该模块没有独立 REST 路由，由 RAG 请求参数直接驱动。

---

### 4.7 语音交互

```
点击麦克风按钮
  → MediaRecorder 开始录音（WebM 格式）
  → 波形动画实时显示（8 条动态柱）
  → 再次点击停止录音
  → POST /api/voice/transcribe（Whisper 后端）
  → 转录文字填入输入框
  → 可继续调用 /api/voice/ask 发起语音问答
```

> 当前 `VoiceInput.vue` 主链路依赖后端 Whisper。项目内另有 Web Speech API 试验性示例，但**未接入当前语音输入主流程**，因此不是自动降级链路。

```
POST /api/voice/transcribe   -- 音频转文字
POST /api/voice/ask          -- 语音问答
GET  /api/voice/models       -- 可用 Whisper 模型
POST /api/voice/load-model   -- 加载指定模型
GET  /api/voice/health       -- 服务健康状态
```

---

### 4.8 联网搜索

集成 DuckDuckGo 联网搜索，无需 API Key，Agent 可调用实时获取最新信息。当前实现采用 **Instant Answer API → HTML 搜索页解析** 的双层降级机制，默认超时 10 秒。

```
GET /api/agent/web-search?q=搜索关键词&max_results=5
```

---

### 4.9 文档创作

**功能描述：** 当前实现为 5 类文本创作 / 处理接口，而不是单一 `mode` 聚合接口。

| 模式         | 说明                         | 输出特点         |
| ------------ | ---------------------------- | ---------------- |
| **大纲生成** | 根据主题与要求生成多级结构   | 层次化标题与要点 |
| **摘要生成** | 对长文本进行压缩总结         | 关键信息提炼     |
| **文本翻译** | 将文本翻译到目标语言         | 保留术语与语义   |
| **格式优化** | 润色措辞、统一格式、修正表达 | 更适合直接发布   |
| **内容扩写** | 根据大纲或要点扩展正文       | 生成更完整的文档 |

```
POST /api/creation/outline
POST /api/creation/summary
POST /api/creation/translate
POST /api/creation/polish
POST /api/creation/expand
GET  /api/creation/templates
```

**前端入口：** SideBar「文档创作」→ `/creation`，`Creation.vue` 页面。

---

### 4.10 RAG 评测

**功能描述：** 当前实现为**轻量问答评测面板**，支持题库、模型对比、结果持久化与可视化；但严格来说，它还不是完全接入真实 RAG 主链路的端到端评测系统。

| 指标           | 说明                                         |
| -------------- | -------------------------------------------- |
| **准确率**     | 基于 expected 文本与关键词覆盖率的启发式打分 |
| **溯源准确率** | 回答中是否包含来源/参考等引用标记            |
| **延迟**       | 端到端响应时间分布                           |

- 📡 **雷达图**：3 维指标对比（准确率 / 响应速度 / 溯源准确率）
- 📊 **柱状图**：按题目分类聚合的平均得分对比
- 📈 **直方图**：响应延迟分布分析
- **Pinia Store** 跨路由持久化，切换页面不丢评测进度
- **全局进度浮层**：`App.vue` 底部 toast，任意页面均可感知评测进度

> 说明：`eval_panel.py` 当前优先请求 `POST /api/chat/ask`，但本仓库未找到该路由；失败时会回退到 Ollama 直接生成。因此它更接近“轻量模型问答评测面板”，而不是严格的真实 RAG 闭环评测。

```
POST /api/eval/run
GET  /api/eval/results
GET  /api/eval/latest
GET  /api/eval/results/{run_id}
GET  /api/eval/questions
POST /api/eval/questions/add
DELETE /api/eval/questions/{q_id}
```

---

## 5. 扩展功能模块

### 5.1 个人主页与设置

| 设置项   | 说明                                                         |
| -------- | ------------------------------------------------------------ |
| 基本信息 | 头像、姓名/昵称、个人简介可更新；公开邮箱当前以读取/回填为主 |
| 偏好设置 | 开发模式（当前仅默认项）、语言切换，前端立即生效             |
| 账号操作 | 登出账号、账号注销确认弹窗                                   |

> 说明：当前用户页未提供独立“修改密码”表单；密码重置流程仍走 4.1 中的忘记密码接口。

---

### 5.2 外观与主题

完整的个性化外观系统，所有设置 **localStorage 持久化**：

| 功能         | 选项                                                |
| ------------ | --------------------------------------------------- |
| **主题模式** | 亮色 / 暗色 / 跟随系统（`light` / `dark` / `auto`） |
| **主题色**   | 8 种预设色（蓝/紫/绿/红/橙/青/粉/灰）               |
| **界面布局** | 默认 / 紧凑 / 宽松                                  |
| **字体大小** | 小 / 中 / 大，实时调整根字体大小                    |

---

### 5.3 第三方账号绑定

当前用户中心中的「第三方账号绑定」入口实际位于 `/user/coming-soon/2`，属于**前端演示/待上线页面**，尚未形成真实后端绑定闭环。

| 项目                   | 当前状态                                                               |
| ---------------------- | ---------------------------------------------------------------------- |
| 用户中心绑定页         | 可展示绑定/解绑交互，但当前为本地演示逻辑                              |
| QQ                     | 已实现 **QQ OAuth 登录**（见 4.1），但属于登录流程，不是用户中心绑定页 |
| GitHub / 微信 / 飞书等 | 用户中心未找到真实绑定 API；Settings 中部分仅为平台配置或占位实现      |

---

### 5.4 反馈与建议

多字段反馈表单，主路径：`POST /api/feedback/submit`。

- 后端已接入 `smtplib` 发送邮件
- 若 SMTP 未配置，后端返回 `feedback_received_no_smtp`
- 前端存在 `mailto:` 本地邮件客户端降级逻辑

---

### 5.5 历史记录

聚合展示多类历史活动，并按日期分组：

| 类型        | 实际来源                          |
| ----------- | --------------------------------- |
| 💬 对话历史 | `GET /api/chat/chat-documents`    |
| 🤖 任务历史 | `localStorage.agent_task_history` |
| 📝 笔记历史 | `localStorage.kb_notes_*`         |

> 当前代码中**未看到独立的“搜索历史”聚合来源**。

---

### 5.6 全局搜索

快捷键：`Ctrl + K`

- 浮窗覆盖式搜索界面
- 当前实际搜索范围：**知识库名称 + 对话会话标题**
- 键盘导航（↑↓ 选择，Enter 跳转，Esc 关闭）
- 提供快捷入口列表（知识库 / AI 对话 / 文件管理 / 学术检索）

> 当前 `GlobalSearch.vue` 未实现独立“搜索历史”功能，也**未看到真正接入文档标题/全文搜索结果**。

---

### 5.7 置顶功能

全平台统一的置顶机制，**localStorage 持久化**，重启后保持状态。

| 模块       | 置顶对象      |
| ---------- | ------------- |
| 知识库列表 | 知识库卡片    |
| 文件管理   | 单个文件      |
| 模型管理   | Ollama 模型   |
| 历史记录   | 对话/任务条目 |

---

### 5.8 全局交互动效

文件：`src/styles/animations.css`

| 动效类型     | 说明                        |
| ------------ | --------------------------- |
| **页面过渡** | 路由切换淡入淡出 + 轻微位移 |
| **按钮光晕** | hover 时发光扩散效果        |
| **卡片悬浮** | hover 上移 + 阴影加深       |
| **骨架屏**   | 灰色条流光扫过动画          |
| **列表浮入** | 列表项逐一延迟出现          |
| **毛玻璃**   | backdrop-filter 磨砂效果    |

所有动效支持 `prefers-reduced-motion` 媒体查询，用户开启“减少动态效果”时自动关闭。

---

### 5.9 系统设置（Win11 风格）

路径：`/settings`，左侧分组导航栏 + 右侧内容区。

**当前源码为 6 大分组 / 16 个 Tab：**

| 分组          | Tab                                     |
| ------------- | --------------------------------------- |
| 🔐 账号与安全 | API Key / 角色权限 / 合规中心           |
| 🗄️ 数据与存储 | 多数据源 / 版本管理 / OCR 解析          |
| 🤖 AI 与模型  | 模型配置 / 多模型 / RAG 评估 / 企业工具 |
| 🔗 集成与联动 | 办公联动 / 审计日志                     |
| 🎨 个性化     | 外观设置                                |
| 📡 系统       | 使用统计 / 系统监控 / 工单管理          |

**办公联动面板当前包含 6 平台：** Obsidian / 飞书 / 钉钉 / 企微 / Notion / GitHub。

> 说明：
>
> - Notion / GitHub 后端当前仅为“保存配置 + 测试占位”
> - 系统监控当前为**手动刷新**，未见 30 秒自动刷新逻辑
> - OCR 设置页当前前端仍带有演示态接口调用（见 7.5）

---

### 5.10 系统架构图

路径：`/architecture`，独立可视化页面。

| Tab             | 内容                                                    |
| --------------- | ------------------------------------------------------- |
| 🗺️ **全局架构** | 客户端层 / 网关层 / 业务服务层 / AI 模型层 / 存储层总览 |
| 🔄 **数据流**   | RAG 问答流与文件上传向量化流程图                        |
| 📦 **技术栈**   | 前后端、AI、存储等技术栈卡片展示                        |
| 🚀 **部署方案** | 本地开发、Docker 部署与端口总览                         |

> 当前该页面属于说明性可视化页面；其中数据流文案仍有个别示意描述，需继续与真实实现保持同步。

**入口：** SideBar 工具栏「系统架构」图标 → 路由 `/architecture`。

---

## 6. 集成与联动

### 6.1 Obsidian 笔记同步

将 Obsidian Vault 中的 Markdown 笔记增量同步到知识库目录。

```
POST /api/integrations/obsidian/configure   -- 配置 Vault 路径、目标知识库、排除规则
POST /api/integrations/obsidian/sync        -- 手动触发同步
GET  /api/integrations/obsidian/status      -- 查看同步状态
GET  /api/integrations/obsidian/files       -- 查看已同步文件列表
```

当前配置项以源码为准：`vault_path`、`kb_id`、`auto_sync`（布尔）、`exclude_patterns`。

> 当前并**未**实现 README 旧描述中的“每小时/每天”定时频率配置；增量检测采用文件内容哈希。

---

### 6.2 飞书机器人

当前实现的是**飞书机器人/事件订阅问答链路**，而不是简单的 webhook 发送接口。

```
POST /api/integrations/feishu/webhook      -- 飞书事件订阅入口
POST /api/integrations/feishu/configure    -- 动态配置 App ID / App Secret
GET  /api/integrations/feishu/status       -- 查看配置状态
GET  /api/integrations/feishu/setup-guide  -- 返回接入步骤说明
POST /api/integrations/feishu/test         -- 发送测试消息
```

配置方式：支持环境变量初始化，也支持在 Settings 页运行时配置 `app_id` / `app_secret` / `verification_token` / `encrypt_key` / `default_kb_id`。

---

### 6.3 钉钉 / 企微 / Notion / GitHub

```
POST /api/integrations/dingtalk/configure  -- 保存钉钉配置
POST /api/integrations/dingtalk/test       -- 发送钉钉测试消息
POST /api/integrations/dingtalk/send       -- 钉钉发送
POST /api/integrations/wecom/configure     -- 保存企微配置
POST /api/integrations/wecom/test          -- 发送企微测试消息
POST /api/integrations/wecom/send          -- 企微发送
POST /api/integrations/notion/configure    -- 保存 Notion 配置（占位）
POST /api/integrations/notion/test         -- Notion 测试（占位）
POST /api/integrations/github/configure    -- 保存 GitHub 配置（占位）
POST /api/integrations/github/test         -- GitHub 测试（占位）
```

- **钉钉 / 企微**：真实可发测试消息与正式消息
- **Notion / GitHub**：当前仅有“保存配置 + 测试占位返回”，**未实现真实同步链路**

---

### 6.4 多数据源接入

| 数据源             | 当前状态                       |
| ------------------ | ------------------------------ |
| **阿里云 OSS**     | 已支持                         |
| **AWS S3 / MinIO** | 已支持                         |
| **MySQL**          | 已支持                         |
| **PostgreSQL**     | 已支持                         |
| **SQLite**         | 已支持                         |
| **WebDAV**         | `types` 接口中标记为 `planned` |

```
GET    /api/datasources/list         -- 数据源列表
GET    /api/datasources/types        -- 支持类型说明
POST   /api/datasources/create       -- 创建数据源
DELETE /api/datasources/{ds_id}      -- 删除数据源
POST   /api/datasources/{ds_id}/test -- 测试连通性
POST   /api/datasources/{ds_id}/sync -- 触发同步
```

> 当前源码中未看到旧 README 所写的 `HTTP URL` 数据源类型；前端 Settings 页调用的也是上述 `datasources` 复数路由。

---

## 7. 系统管理

### 7.1 开放 API

当前已实现的是 **API Key 管理与验证能力**：

```
POST   /api/apikeys/create            -- 创建 API Key（仅首次返回明文）
GET    /api/apikeys/list              -- 查看 Key 列表
PATCH  /api/apikeys/{id}/toggle       -- 启用/禁用 Key
DELETE /api/apikeys/{id}              -- 删除 Key
POST   /api/apikeys/verify            -- 用 X-API-Key 验证可用性
```

```bash
curl -X POST http://localhost:8000/api/apikeys/verify \
     -H "X-API-Key: ragf_xxxx"
```

> 当前源码中**尚未看到**业务接口统一接入 API Key 鉴权依赖，因此 README 不再把 `/api/chat/send` 这类业务路由写成已完成的开放 API 调用示例。

---

### 7.2 审计日志

ASGI 中间件会自动记录请求时间、用户、路径、IP、状态码、耗时等信息，存储于 SQLite：`metadata/audit_log.db`。

```
GET    /api/audit/logs         -- 查询审计日志（分页+过滤）
GET    /api/audit/stats        -- 审计统计摘要
DELETE /api/audit/logs/clean   -- 清理旧日志
```

---

### 7.3 增量向量化

```
POST   /api/vectorize/ingest          -- 单文件增量向量化（异步）
POST   /api/vectorize/batch           -- 批量增量向量化（异步）
DELETE /api/vectorize/remove          -- 从向量库移除文档
GET    /api/vectorize/stats/{kb_id}   -- 查看向量库统计
GET    /api/vectorize/index/{kb_id}   -- 查看哈希索引
GET    /api/vectorize/status/{task_id} -- 查询任务状态
GET    /api/vectorize/queue           -- 查看当前队列长度
```

原理：计算文件哈希与索引记录对比，内容未变更则跳过，减少重复向量化计算。

---

### 7.4 RBAC 权限管理

| 内置角色      | 权限范围                              |
| ------------- | ------------------------------------- |
| `super_admin` | 全部权限                              |
| `admin`       | `kb:*` / `user:read` / `audit:read`   |
| `editor`      | `kb:write` / `kb:read` / `kb:comment` |
| `viewer`      | `kb:read` / `kb:comment`              |
| `guest`       | `kb:read`                             |

```
GET    /api/rbac/roles                    -- 角色列表
POST   /api/rbac/roles/assign            -- 为用户分配角色
GET    /api/rbac/users/{user_id}/roles   -- 查询用户角色
POST   /api/rbac/kb/grant                -- 授权知识库权限
DELETE /api/rbac/kb/{kb_id}/revoke       -- 撤销知识库权限
GET    /api/rbac/kb/{kb_id}/permissions  -- 查看知识库权限
GET    /api/rbac/check                   -- 检查权限
```

> 说明：`DELETE /api/rbac/kb/{kb_id}/revoke` 还需要通过查询参数传入 `subject_type` 与 `subject_id`；另有部门相关接口：`/api/rbac/dept/create`、`/api/rbac/dept/list`。

---

### 7.5 OCR 文档解析

后端 OCR 模块的能力范围比旧文档描述更广：除图片、扫描版 PDF 外，还能处理音频/视频转写。

```
POST /api/ocr/extract         -- 上传文件解析
POST /api/ocr/extract-base64  -- Base64 文件内容解析
```

- 图片优先走 PaddleOCR，缺失时降级 pytesseract
- PDF 支持逐页 OCR
- 音频/视频支持 Whisper 转写

> 当前前端 Settings「OCR 解析」Tab 仍调用 `/api/ocr/parse` 与 `/api/ocr/configure`，并在失败时回退到本地演示数据；这与后端真实接口**尚未完全对齐**。

---

### 7.6 系统监控

集成请求监控中间件，并提供 JSON / Prometheus 两类指标输出。

| 指标         | 说明                        |
| ------------ | --------------------------- |
| 请求计数     | 按 `method + path` 聚合统计 |
| 平均延迟     | 每个接口的平均响应时长      |
| P99 延迟     | Top 接口的 P99 响应时间     |
| 错误计数     | 4xx/5xx 累积错误数          |
| 模型调用     | 按模型名称统计调用次数      |
| 知识库上传量 | 上传相关请求计数            |
| 运行时长     | 服务启动以来 uptime         |

```
GET /api/metrics          -- JSON 概览数据
GET /api/metrics/echarts  -- ECharts 专用 JSON
GET /metrics              -- Prometheus 文本指标
```

**前端展示：** Settings「📡 系统监控」Tab，当前为 ECharts 面板 + **手动刷新**，未见 30 秒自动刷新逻辑。

---

## 8. 移动端 App

**位置：** `KnowledgeRAG-GZHU/RagMobile/`  
**技术栈：** React Native + Expo SDK 52 + TypeScript + zustand

| 屏幕                  | 功能                                                                             |
| --------------------- | -------------------------------------------------------------------------------- |
| LoginScreen           | 邮箱登录/注册，JWT 安全存储                                                      |
| KnowledgeBaseScreen   | 知识库列表、创建、删除                                                           |
| SquareScreen          | 知识广场、共享内容浏览                                                           |
| KnowledgeDetailScreen | 文档管理、文件上传、URL 导入                                                     |
| ChatScreen            | RAG 对话，SSE 流式，引用溯源                                                     |
| AgentScreen           | Agent 任务模式，步骤可视化                                                       |
| SettingsScreen        | 3 个标签：模型切换、办公联动（Obsidian / 飞书）、账号操作；云端 API Key 本地保存 |

```bash
# 本地开发
cd RagMobile
npm install
npx expo start

# 打包 APK（EAS Cloud Build）
npm install -g eas-cli
eas login              # 账号: gzlns
eas build -p android --profile preview   # 输出 APK

# 打包 AAB（Google Play）
eas build -p android --profile production
```

> **注意：** 打包前将 `EXPO_PUBLIC_API_URL` 改为服务器真实 IP/域名。

---

## 9. 部署方案

### Docker Compose（完整栈）

```yaml
# docker-compose.yml 包含以下 7 个服务：
services:
  redis: # Redis Stream 事件总线，端口 6380 -> 6379
  mysql: # MySQL 8.0，端口 3307 -> 3306
  ollama: # Ollama，端口 11435 -> 11434
  ollama-init: # 一次性模型预拉取任务（无对外端口）
  backend: # FastAPI 主服务，端口 8000
  worker: # 文档解析 / 向量化 Worker（无对外端口）
  frontend: # Vue3 + Nginx，端口 8089
```

```bash
docker compose up -d               # 启动完整栈
docker compose logs -f backend     # 查看后端日志
docker compose logs -f worker      # 查看向量化 Worker 日志
docker compose down                # 停止
```

### Docker Compose 轻量版（云端 API）

```yaml
# docker-compose.lite.yml：frontend + backend
# 使用 SQLite；无独立 MySQL / Ollama / Redis 容器
# 默认示例为 DeepSeek，可改成 DashScope / 宿主机 Ollama
services:
  backend: # FastAPI，端口 8000
  frontend: # Vue3 + Nginx，端口 8089
```

```bash
docker compose -f docker-compose.lite.yml up -d
```

> 说明：轻量版不是“只有后端”；它仍会同时启动前端，只是把数据库切到 SQLite，并依赖云端模型 API 或宿主机已有 Ollama。

### 前端独立构建

```bash
cd RagFrontend
npm run build    # 输出 dist/，可部署到 Nginx、Vercel、CDN 等
```

---

## 10. 目录结构

```
KnowledgeRAG-GZHU/
├── RagFrontend/                         # Vue3 前端
│   ├── src/
│   │   ├── App.vue                     # 根组件（含全局评测进度浮层）
│   │   ├── views/
│   │   │   ├── KnowledgePages/         # 知识库列表 / 详情 / 设置 / 广场
│   │   │   ├── SettingsTabs/           # 独立设置子 Tab（当前已拆分 8 个）
│   │   │   ├── Chat.vue                # RAG 智能问答
│   │   │   ├── Agent.vue               # Agent 任务模式
│   │   │   ├── History.vue             # 历史记录聚合
│   │   │   ├── Settings.vue            # Win11 风格设置页（6 组 / 16 Tab）
│   │   │   ├── Creation.vue            # 文档创作（5 类文本处理接口）
│   │   │   ├── Architecture.vue        # 系统架构图（4 Tab 可视化）
│   │   │   └── LogonOrRegister/        # 登录注册
│   │   ├── components/
│   │   │   ├── SideBar.vue             # 左侧导航（含架构图 / 文档创作入口）
│   │   │   ├── GlobalSearch.vue        # Ctrl+K 全局搜索
│   │   │   ├── ModelSelector.vue       # 模型切换
│   │   │   ├── RetrievalConfig.vue     # 检索策略配置
│   │   │   ├── VoiceInput.vue          # 语音输入
│   │   │   ├── SmartAssistant.vue      # 右侧智能助手
│   │   │   └── ShareModal.vue          # 分享链接 + 二维码
│   │   ├── store/                      # Pinia 状态管理
│   │   ├── composables/useTheme.ts     # 主题 / 字体 / 深色模式
│   │   ├── styles/animations.css       # 全局交互动效
│   │   ├── utils/request.ts            # Axios 封装（分块上传 + 重试）
│   │   └── router/index.ts             # 路由配置（含 /creation /architecture）
│   ├── Dockerfile
│   └── nginx.conf
│
├── RagBackend/                          # FastAPI 后端
│   ├── main.py                         # 应用入口
│   ├── RAGF_User_Management/           # 注册 / 登录 / QQ OAuth / 重置密码
│   ├── RAG_M/src/
│   │   ├── rag/rag_pipeline.py         # RAG 主流水线
│   │   └── agent/react_agent.py        # ReAct Agent
│   ├── document_processing/
│   │   ├── doc_upload.py               # 分块上传与文档入库
│   │   ├── incremental_vectorizer.py   # 增量向量化
│   │   └── retrieval_strategy.py       # 五策略检索
│   ├── creation/doc_creation.py        # 文档创作接口
│   ├── monitoring/metrics.py           # 指标聚合与监控接口
│   ├── multi_model/model_router.py     # 多模型路由
│   ├── multimodal/whisper_asr.py       # 语音识别
│   ├── integrations/
│   │   ├── obsidian_sync.py            # Obsidian 同步
│   │   ├── feishu_bot.py               # 飞书机器人 / 事件订阅
│   │   └── dingtalk_wecom.py           # 钉钉 / 企微 / WPS 联动
│   ├── data_sources/datasource_manager.py # 多数据源接入
│   ├── open_api/api_key_manager.py     # API Key 管理
│   ├── audit/audit_log.py              # ASGI 审计日志
│   ├── knowledge/
│   │   ├── rbac_manager.py             # RBAC 权限管理
│   │   ├── ocr_parser.py               # OCR / 音视频转写解析
│   │   ├── doc_version_manager.py      # 文档版本管理
│   │   ├── doc_tag_manager.py          # 文档标签
│   │   └── doc_comment_manager.py      # 评论 / AI 批注
│   ├── feedback/feedback_router.py     # 反馈邮件
│   ├── enterprise/kb_backup.py         # 知识库备份
│   └── .env.example                    # 环境变量模板
│
├── RagMobile/                           # React Native 移动端
│   ├── App.tsx
│   ├── src/
│   │   ├── navigation/Navigation.tsx   # 底部导航 + Stack 路由
│   │   ├── screens/                    # 7 个核心页面（含 SquareScreen）
│   │   ├── utils/api.ts                # API 层（AsyncStorage 缓存 + SSE 工具）
│   │   └── store/useKbStore.ts         # 知识库 Store（5 分钟列表缓存）
│   └── eas.json
│
├── dev.ps1                              # 一键开发启动脚本
├── docker-compose.yml                   # 完整栈（Redis + MySQL + Ollama + Worker）
└── docker-compose.lite.yml              # 轻量版（frontend + backend + SQLite）
```

---

## 11. 环境变量说明

创建 `RagBackend/.env`。如果你是“本地后端 + Docker MySQL”开发模式，`DB_PORT` 建议填 `3307`；如果是完整 Docker 容器内互联，`docker-compose.yml` 已固定使用容器内 `3306`。

```env
ENV_MODE=development

# 存储与上传
KB_STORAGE_PATH=./local-KLB-files
MAX_FILE_SIZE=52428800
CHUNK_SIZE=102400

# 日志
LOG_LEVEL=INFO
LOG_DIR=./logs

# 数据库（本地开发 + Docker MySQL 场景建议 DB_PORT=3307）
DB_HOST=127.0.0.1
DB_PORT=3307
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=rag_user_db
DB_CHARSET=utf8mb4

# JWT（推荐主名；旧名仍兼容）
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRATION_HOURS=24
# JWT_SECRET_KEY=your-secret-key-change-in-production
# JWT_EXPIRE_HOURS=24

# Ollama / 默认模型
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=300
MODEL=deepseek-chat
# DEFAULT_LLM_MODEL=deepseek-chat

# 向量 / 重排 / 知识图谱
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
RERANK_MODEL=bge-large
KG_MODEL=qwen3:0.6b

# Redis（完整 Docker 栈默认会注入；本地单进程可保持关闭）
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=false

# 知识库默认参数
KB_DEFAULT_CHUNK_SIZE=1000
KB_DEFAULT_CHUNK_OVERLAP=200
KB_DEFAULT_SIMILARITY_THRESHOLD=0.7

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8089

# 云端模型（可选）
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
DEEPSEEK_API_KEY=sk-xxx
HUNYUAN_SECRET_ID=xxx
HUNYUAN_SECRET_KEY=xxx
DASHSCOPE_API_KEY=sk-xxx
XFYUN_APP_ID=xxx
XFYUN_API_KEY=xxx
XFYUN_API_SECRET=xxx

# 语音识别（可选）
WHISPER_MODEL=base

# 飞书集成（可选）
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_VERIFICATION_TOKEN=xxx
FEISHU_ENCRYPT_KEY=xxx
FEISHU_DEFAULT_KB_ID=

# QQ 登录（可选；当前代码仍有默认值，生产环境建议显式覆盖）
QQ_APP_ID=your_qq_app_id
QQ_APP_KEY=your_qq_app_key
QQ_REDIRECT_URI=http://localhost:8000/api/qq/callback
FRONTEND_URL=http://localhost:5173

# 邮件（可选）
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your_email@163.com
SMTP_PASS=your_smtp_password
SMTP_FROM=your_email@163.com
# SMTP_PASSWORD=your_smtp_password
```

补充说明：

- **钉钉 / 企微**：当前主要由 Settings 页或请求体传入 `webhook_url` / `secret`，后端未固定读取 `DINGTALK_*` / `WECOM_*` 环境变量。
- **Notion / GitHub**：当前为“保存配置 + 测试占位”接口，代码中未固定读取 `NOTION_*` / `GITHUB_*` 启动环境变量。
- **OSS / S3 / MinIO / MySQL / PostgreSQL 数据源**：当前通过多数据源配置接口提交连接参数，而不是后端启动时的固定 `.env` 字段。

---

## 12. 常见问题 FAQ

**Q: Ollama 内存不足 / 超时 / 500 错误？**  
A: 优先切换更小的模型（如 `llama3.2:1b`）；同时把 `.env` 中 `MODEL=你的模型名`、`OLLAMA_TIMEOUT=300`。Docker 场景访问的是宿主机 `11435 -> 11434` 映射端口，本地直连通常仍用 `11434`。

**Q: 本地后端连不上 Docker MySQL？**  
A: 当前 `docker-compose.yml` 把 MySQL 映射为 **宿主机 3307 -> 容器 3306**。如果你是本地运行 `uvicorn`，`.env` 里的 `DB_PORT` 应写 `3307`；如果是容器内服务互联，则保持 `3306`。

**Q: 访问 localhost:8000 显示 502？**  
A: 常见原因是 VPN / 代理拦截 `localhost`。把 `localhost;127.0.0.1` 加进代理排除列表再试。

**Q: 端口 8000 被占用？**  
A: `taskkill /F /IM python.exe`，或更精确一点：`Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process`。

**Q: 改了 `RagBackend/.env` 但后端配置没生效？**  
A: `uvicorn --reload` 不会自动重新读取 `.env`。如果你改了 `DB_PORT`、模型配置或其他连接项，需要把旧的后端进程彻底重启，再重新启动服务。

**Q: 向量化时报 `Cannot send a request, as the client has been closed.`？**  
A: 最新版本会优先探测本机 HuggingFace 缓存中的 `sentence-transformers/all-MiniLM-L6-v2`，命中后自动启用 `local_files_only`，避免因为进程没有正确读取 `HF_HOME/.env` 而走到异常网络请求。如果仍复现，优先检查是否还有旧的 uvicorn 进程占着 `8000`，杀掉后整进程重启再试。

**Q: 为什么设置了云端模型 Key 仍提示未配置？**  
A: 当前多模型优先级是 **`models_config.json` > `.env` > 友好提示**。如果你曾在 Settings「多模型」里保存过配置，运行时会优先读取那份配置。

**Q: 如何打包移动端 APK？**  
A: 参考 [第8节](#8-移动端-app)，使用 EAS Cloud Build：`eas build -p android --profile preview`。打包前记得把 `EXPO_PUBLIC_API_URL` 指向真实后端地址。

---

## 13. Contributors

以下为当前仓库基于 `git shortlog -sne HEAD` 核对得到的提交身份统计：

| 身份（git shortlog）                                      | 提交数 | 备注                                 |
| --------------------------------------------------------- | -----: | ------------------------------------ |
| GZLns `<13425121993@163.com>`                             |     90 | 当前主要提交者                       |
| Zhongye1 `<2760913192@qq.com>`                            |      6 | 贡献者                               |
| mmk `<145737758+Zhongye1@users.noreply.github.com>`       |      4 | 与同一 GitHub 账号相关的另一提交身份 |
| Rosmontis `<145737758+Zhongye1@users.noreply.github.com>` |      3 | 与同一 GitHub 账号相关的另一提交身份 |
| xingjiu `<992254616@qq.com>`                              |      2 | 贡献者                               |
| 小海 `<3277975910@qq.com>`                                |      1 | 贡献者                               |

> 说明：仓库当前未配置 `.mailmap`，同一贡献者若使用多个昵称 / 邮箱提交，`git shortlog` 会拆分为多条身份。

---

## 14. 后续规划

- [x] 用户认证与权限管理
- [x] 多模型支持与参数配置
- [x] 用户自定义模型配置（Ollama 地址/模型名/超时）
- [x] 多格式文档处理（PDF/Word/Excel/图片）
- [x] 知识库 CRUD + 多维检索
- [x] 独立 Cross-Encoder 重排接口（二次精排，默认主链路未接入）
- [x] Docker 一键部署（完整栈 + 轻量版）
- [x] Agent 任务模式（ReAct）
- [x] 移动端 App（React Native）
- [x] 语音输入（Whisper ASR）
- [x] 置顶 / 拖拽排序 / 全局动效
- [x] Win11 风格系统设置
- [x] 办公联动（Obsidian/飞书/钉钉/企微已接入；Notion/GitHub 为配置占位）
- [x] 文档创作（5 类文本处理接口）
- [x] 轻量评测面板（ECharts 可视化 + Pinia 持久化）
- [x] 系统架构图页面（4 Tab 可视化）
- [x] Prometheus 监控 + ECharts 系统监控 Tab（当前手动刷新）
- [x] 知识库 ZIP 备份后端接口（前端入口待补）
- [ ] 文档协作（多人实时编辑）
- [ ] 知识图谱可视化增强
- [ ] 企业 SSO 登录（LDAP/SAML）

> 已评估但当前不推进的优化项，统一归档在 [第15节](#15-未实现更新)。

---

## 15. 未实现更新

> 本节记录经过评估后**暂不实现**的优化方案，保留原始设计思路供参考。

### 15.1 ~~Redis Stream 消息队列~~ ✅ 已于 `be97fe5` 后续版本实现

**解释：** 用 Redis Stream 替代内存队列，实现任务持久化、重试机制和死信队列，服务重启后任务不丢失。

**实现状态：** 已在 commit `ca18a43` 之后版本中实现——`task_queue.py` 已升级为 Redis Stream 持久化队列（含内存队列降级），`docker-compose.yml` 新增 Redis Alpine 服务。

---

### 15.2 独立子进程文件隔离处理

**解释：** 每个文件的解析和向量化在独立子进程中执行，完成后销毁进程释放内存，实现内存完全隔离。

**原本应用方向：** 防止单个大文件的解析/向量化内存泄漏积累导致 OOM，特别是多文件批量处理时。

**跳过原因：** docker-compose 已新增独立 `worker` 服务（与 `backend` 完全资源隔离），架构层面已解决内存隔离问题，无需进程级 multiprocessing。子进程 IPC 开销反而会拖慢整体吞吐，ROI 不高。

---

### 15.3 断点续传（分块 MD5 校验）

**解释：** 大文件上传时记录已上传分块的 MD5，断线重连后只上传未完成的分块，不从头开始。

**原本应用方向：** 防止大文件（>50MB）上传中途断网时需要重头传，提升用户体验。

**跳过原因：** 项目当前限制单文件最大 50MB（`doc_upload.py` `MAX_FILE_SIZE`），且文档类文件通常远小于此限制。现有分块上传机制（0.1MB/块）本身已经拆分了请求，实际发生断网重传的概率极低。断点续传需要后端持久化分块状态、前端增加重传逻辑，复杂度增加明显，ROI 不高。

---

### 15.4 ~~全链路超时统一（Nginx 600s 配置）~~ ✅ 已实现

**实现状态：** 已在本轮更新中实现——`nginx.conf` 为上传专用 location 配置 600s 超时，并开启 `proxy_request_buffering off` 避免 nginx 内存缓冲大文件。

---

### 15.5 所有异常返回 HTTP 200

**解释：** 业务异常和系统异常统一返回 HTTP 200，用业务 code 字段区分成功/失败。

**原本应用方向：** 防止前端因 4xx/5xx 状态码触发网络错误捕获，统一错误处理逻辑。

**跳过原因：** 这是反模式。HTTP 状态码是 REST 协议的核心语义，错误返回 200 会导致：监控告警失效（Prometheus 无法区分成功/失败）、日志排查困难、调试工具无法快速定位问题。正确做法是前端统一捕获 axios 的 error 响应，而不是让后端伪装成功。

---

### 15.6 向量化全局跨请求并发 Semaphore

**解释：** 在 FastAPI 进程级别维护一个全局 `asyncio.Semaphore`，限制同时运行的向量化请求总数（例如最多 2 个 `/ingest` 同时跑），超出的请求在 semaphore 处等待而不是直接执行。

**原本应用方向：** 防止多用户同时点击"向量化"时，多个 `/ingest` 并发占用 Embedding 模型导致内存溢出。

**跳过原因：** `/ingest` 和 `/native_ingest` 已改为 `asyncio.to_thread`，向量化在线程池中执行，本身不占用 event loop。项目是单用户/小团队场景，并发触发多个向量化的概率极低，且向量化耗时较长（几秒到几分钟），加全局 semaphore 反而可能导致前端长时间等待响应（semaphore 阻塞 `generate()` 入口）。当前方案已足够稳定，不引入额外的等待逻辑。

---

### 15.7 MySQL 水平分表

**解释：** 用 SQLAlchemy 实现文件元数据表、任务状态表按用户ID水平分表，支撑千万级元数据存储，无单表容量瓶颈。

**原本应用方向：** 海量文档元数据的高性能查询，长期运行无查询性能衰减。

**跳过原因：** 项目为校园/小团队场景，用户量和文档量均处于千级以内。MySQL 单表在百万行级别查询依然毫秒响应。分表会大幅增加 SQLAlchemy ORM 复杂度和维护成本，与项目规模严重不匹配，典型过度工程。

---

### 15.8 Redis 分布式读写锁（FAISS 并发写）

**解释：** 用 Redis 实现 FAISS 索引的分布式读写锁，保证同一时间只有一个写入操作，同时不阻塞读请求。

**原本应用方向：** 多进程/多容器场景下 FAISS 索引文件的并发写入保护。

**跳过原因：** 项目为单机 Docker 部署，向量化已在独立 `worker` 容器中单实例运行。`worker` 内部已有 `asyncio.Semaphore(_MAX_CONCURRENCY=2)` 限制并发写入数，单进程内无需分布式锁。引入 Redis 分布式锁会增加 lock/unlock 的网络开销和死锁风险，对单机场景是负优化。

---

### 15.9 Prometheus + Grafana 监控大盘（新增）

**解释：** 用 Alpine 版 Prometheus+Grafana 搭建上传全链路监控大盘，包含 QPS、响应时间、队列长度、系统资源等指标。

**原本应用方向：** 7×24 无人值守运维，问题秒级告警。

**跳过原因：** 项目 README 已有 Prometheus 监控能力（`monitoring.py` 中间件 + `/metrics` 端点），已能满足基础监控需求。Grafana 容器虽然只有 ~40MB，但需要额外配置 dashboard JSON + Alertmanager 告警规则，运维成本较高。在校园部署场景下，直接看 `/metrics` 原始指标 + 日志定位问题，效率已足够。

---

### 15.10 URL 批量导入接口

**解释：** 知识库详情页已有 URL 批量导入弹窗，前端会调用 `POST /api/url-import/`，但当前后端未实现对应路由。

**原本应用方向：** 批量抓取网页正文并直接写入知识库，减少手动复制粘贴成本。

**跳过原因：** URL 导入需要额外处理网页抓取、反爬、正文抽取、编码兼容和失败重试。当前项目已经有文件上传、Obsidian 同步、手动笔记等多种入库方式，URL 导入优先级较低，暂不引入额外维护负担。

---

### 15.11 知识库备份前端入口

**解释：** 后端已实现 `POST /api/backup/create`、`GET /api/backup/list`、下载与删除等备份接口，但前端知识库页面尚未接入备份按钮。

**原本应用方向：** 让普通用户在界面中直接导出知识库 ZIP 备份，无需手动调用接口。

**跳过原因：** 备份属于低频管理动作，当前可通过接口或服务器文件系统完成。若贸然加入前端入口，会带来权限控制、下载状态管理和空间提示等额外复杂度，暂缓处理。

---

### 15.12 API Key 业务路由统一鉴权

**解释：** 当前后端已实现 API Key 创建、列表、启停、删除、验证，但业务接口尚未统一接入 `X-API-Key` 鉴权依赖。

**原本应用方向：** 为第三方系统开放稳定的无界面调用方式，例如 RAG 问答、Agent 任务、文档创作等。

**跳过原因：** 现阶段项目主要仍以 JWT 用户态使用为主。若要真正开放业务 API，需要为大量路由补齐依赖、权限边界、配额统计和调用审计，工作量较大，暂不推进为默认能力。

---

### 15.13 OCR 配置页接口前后端对齐

**解释：** 后端真实 OCR 接口是 `/api/ocr/extract` 与 `/api/ocr/extract-base64`，而前端 Settings 的 OCR 页当前仍调用 `/api/ocr/configure` 与 `/api/ocr/parse`，失败时回退到本地演示数据。

**原本应用方向：** 在设置页统一配置 OCR 引擎并立即做在线测试，作为文档上传 OCR 的控制台。

**跳过原因：** 当前上传链路里的 OCR 解析能力已经可用，真正影响主流程的是上传时自动抽取文本，而不是设置页的演示控制台。为了避免继续扩大 UI/后端协议面，先保留为待对齐项。

---

### 15.14 系统监控自动刷新

**解释：** 系统监控页当前为手动刷新模式，尚未实现旧文档中提到的 30 秒自动刷新。

**原本应用方向：** 在设置页中持续展示系统 QPS、延迟和错误趋势，接近轻量监控大盘体验。

**跳过原因：** 该项目主要面向校园/小团队低并发使用，持续轮询的收益有限，反而会带来额外请求噪音。当前保留手动刷新，足够支撑排障与演示场景。

---

### 15.15 第三方账号真实绑定闭环

**解释：** 用户中心里的第三方账号绑定页目前仍是前端演示逻辑，状态保存在 localStorage；QQ OAuth 已实现的是登录流程，而不是绑定页闭环。

**原本应用方向：** 支持 GitHub / 微信 / QQ / 飞书等账号与当前用户绑定，实现多身份登录和账户合并。

**跳过原因：** 真实绑定功能涉及开放平台资质申请、回调校验、解绑安全校验、同邮箱合并策略等一整套账户体系改造。现阶段 QQ 登录已满足主要展示需求，其余平台先不扩展。

---

### 15.16 全局搜索文档标题 / 全文接入

**解释：** 当前 Ctrl + K 全局搜索主要用于知识库名称和会话标题跳转，尚未接入文档标题或正文全文检索。

**原本应用方向：** 在一个统一浮窗里直接搜到知识库、聊天记录、文档标题、正文片段与相关页面入口。

**跳过原因：** 全局搜索和知识库深度检索属于两类不同场景。若把全文检索强行塞进全局跳转浮窗，需要新增额外索引、分页、结果高亮与权限过滤，复杂度明显上升，暂不推进。

---

### 15.17 评测面板接入真实 RAG 链路

**解释：** 当前评测面板虽有完整题库、结果入库和图表展示，但后台优先调用的 `POST /api/chat/ask` 路由在仓库中未找到，因此失败时会回退为 Ollama 直接生成，尚未形成真实 RAG 端到端闭环评测。

**原本应用方向：** 评测检索 + 生成的完整 RAG 表现，并进一步扩展召回率、F1、忠实度等更严格指标。

**跳过原因：** 要做成真正的 RAG 评测，需要先统一评测入口、补齐真实检索链路调用、定义 gold retrieval 数据集并重构评分逻辑。这已经超出“轻量评测面板”的范围，当前版本先保持可演示的轻量实现。

---

## 16. 工程化治理（2026-04）

### 16.1 本地统一入口

在仓库根目录执行：

```bash
npm run frontend:lint
npm run frontend:typecheck
npm run mobile:lint
npm run backend:lint
npm run backend:coverage
npm run docs:build
```

或使用 Makefile：

```bash
make lint
make coverage
make docs-build
```

### 16.2 Git Hook 与提交规范

- `prepare` / `hooks:install`：自动安装本地 Git Hook 桥接脚本
- `pre-commit`：执行 `lint-staged`，对暂存区文件做格式化与前端 ESLint 修复
- `commit-msg`：执行 `commitlint`，要求 Conventional Commits 风格提交信息

### 16.3 后端质量门禁范围说明

当前后端静态检查默认对**核心可观测性链路**执行强校验：

- `trace_logging.py`
- `audit/`
- `exception/`
- `tests/test_tooling_smoke.py`

这样做是为了先把正在维护、已接入 CI、直接影响请求链路排障的部分稳定下来。`RAG_M`、旧用户管理、知识图谱等历史模块仍保留在仓库中，但暂不作为默认 CI 阻塞项，后续按专题逐步纳入治理。

### 16.4 当前已验证通过的基线

- 前端 ESLint：通过（保留 warning，不阻塞）
- 前端 TypeScript 类型检查：通过
- 移动端 ESLint：通过（保留 warning，不阻塞）
- 后端核心 Ruff + Black + mypy：通过
- 后端 smoke test + coverage：通过
- VitePress 文档构建：通过
- `/api/RAG/ingest` 与 `/api/RAG/native_ingest`：在重启后的本地环境已实测通过（含本地 HuggingFace 缓存探测修复）

<div align="center">

_最后核对基线：2026-04-05 | 工程化治理基线与 RAG 向量化链路已恢复为可验证通过状态_

**仓库：[https://github.com/March030303/KnowledgeRAG-GZHU](https://github.com/March030303/KnowledgeRAG-GZHU)**

</div>
