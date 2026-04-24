# ASF-RAG (RAG-F) 智能知识管理平台

> **项目全称**：Adaptive Semantic Fusion - Retrieval Augmented Generation
> **中文名称**：RAG-F 智能知识管理平台
> **项目定位**：面向个人与团队的私有化知识库管理检索解决方案
> **核心目标**：通过「外部知识检索 + 大模型生成」的组合范式，解决 LLM 固有幻觉、知识截断、领域知识缺失、回答缺乏透明度等痛点问题

---

## 目录

1. [项目简介](#1-项目简介)
2. [技术架构](#2-技术架构)
3. [快速启动](#3-快速启动)
4. [核心功能模块](#4-核心功能模块)
5. [扩展功能模块](#5-扩展功能模块)
6. [集成与联动](#6-集成与联动)
7. [系统管理](#7-系统管理)
8. [移动端 App](#8-移动端-app)
9. [部署方案](#9-部署方案)
10. [目录结构](#10-目录结构)
11. [环境变量说明](#11-环境变量说明)

---

## 1. 项目简介

### 1.1 创意来源与背景

ASF-RAG（RAG-F）受 RAG（Retrieval-Augmented Generation，检索增强生成）技术启发，核心设计思想是通过「外部知识检索 + 大模型生成」的组合范式，解决 LLM 固有幻觉、知识截断、领域知识缺失、回答缺乏透明度等问题，开创性地将检索技术和生成式人工智能模型相结合。

项目还引入 **ReAct Agent** 作为整个系统的控制中枢，旨在将人工智能代理（AI Agent）引入检索增强生成（RAG）流程来进行任务拆解、解决复杂业务问题。

### 1.2 项目定位

本项目设计并实现了 **RAG-F 智能知识管理平台** —— 一套面向个人与团队的私有知识库管理检索解决方案。用户可上传 PDF、Word 等多格式文档，系统自动完成文档解析、文本分块、向量化编码与持久化存储；当用户发起提问时，通过向量检索与重排序策略从知识库中精准召回相关内容片段，并将其作为上下文提供给大语言模型，生成有据可查、来源可追溯的高质量回答。

本平台在功能层面进行了全方位拓展：

- 支持本地离线部署以确保数据完全私密
- 兼容 Ollama 本地部署模型服务、OpenAI、DeepSeek 等多种在线模型 API 服务
- 集成基于 ReAct 框架的 Agent 任务模式，支持自然语言驱动的多步骤自动任务执行
- 内置多模式智能文档创作引擎，覆盖报告、摘要、大纲、博客、论文等典型写作场景
- 提供 Web 与移动端双端访问能力
- 可与飞书、钉钉、企业微信、Obsidian、Notion 等主流办公工具实现联动集成

### 1.3 核心痛点与解决思路

| 痛点             | 解决方案                                        |
| ---------------- | ----------------------------------------------- |
| LLM 幻觉问题     | 强制答案基于外部可信知识库，每条信息可追溯原文  |
| 知识时效性截断   | 更新知识库即可刷新模型知识，无需重训练          |
| 领域知识缺失     | 支持用户上传垂直领域文档，构建专属知识库        |
| 回答缺乏透明度   | 答案附带引用来源，用户可追溯验证                |
| 单次检索精度不足 | 支持 5 种检索策略（Vector/BM25/Hybrid/RRF/MMR） |
| 复杂任务处理     | ReAct Agent 自动拆解任务、多步推理执行          |

---

## 2. 技术架构

### 2.1 总体架构

系统采用经典的前后端分离架构，以实现关注点分离、独立部署与团队协作高效。

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层 (Client)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Web SPA    │  │  移动端 App  │  │   第三方集成客户端    │  │
│  │  (Vue3+Vite) │  │  (Uni-app)   │  │ (飞书/钉钉/企微Bot)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ RESTful API / SSE
┌───────────────────────────▼─────────────────────────────────────┐
│                        服务层 (Service)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FastAPI 主服务 (Python 3.11+)                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │  │
│  │  │ RAG问答  │ │ Agent任务│ │ 文档处理 │ │ 用户管理     │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Worker 进程 (Redis Stream 消费者)               │  │
│  │              文档解析 → 分块 → 向量化 → 索引构建            │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                        存储层 (Storage)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  MySQL   │  │  Redis   │  │  FAISS   │  │   SQLite       │  │
│  │(结构化数 │  │(Stream  │  │(向量检索 │  │(审计日志/      │  │
│  │ 据/元数据)│  │  队列)   │  │  索引)   │  │  API Key)      │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级             | 技术选型                          | 版本     | 说明                       |
| ---------------- | --------------------------------- | -------- | -------------------------- |
| **前端框架**     | Vue                               | 3.4.21   | 组合式 API，响应式系统     |
| **前端构建**     | Vite                              | 5.2.8    | 极速冷启动与 HMR           |
| **前端语言**     | TypeScript                        | 5.4.4    | 全项目静态类型检查         |
| **UI 组件库**    | TDesign Vue Next                  | latest   | 腾讯设计体系组件库         |
| **状态管理**     | Pinia                             | 3.0.3    | Vue 官方状态管理           |
| **路由管理**     | Vue Router                        | 4.5.1    | 嵌套路由、路由守卫         |
| **样式工具**     | TailwindCSS                       | 3.4.17   | 原子化 CSS                 |
| **后端框架**     | FastAPI                           | 0.116.1  | 高性能异步 Python Web 框架 |
| **ASGI 服务器**  | Uvicorn                           | 0.35.0   | 异步网关接口               |
| **RAG 框架**     | LangChain                         | 0.3.27   | RAG Pipeline 构建          |
| **向量数据库**   | FAISS                             | >=1.12.0 | Facebook AI 相似度搜索     |
| **结构化数据库** | MySQL                             | 8.0      | 主元数据存储               |
| **消息队列**     | Redis Stream                      | 7-alpine | 异步任务队列               |
| **本地 LLM**     | Ollama                            | latest   | 本地大模型服务             |
| **嵌入模型**     | sentence-transformers             | >=5.1.0  | 文本向量化                 |
| **文档解析**     | PyPDF2 / pdfplumber / python-docx | -        | 多格式文档读取             |
| **OCR 引擎**     | Tesseract + PaddleOCR             | -        | 双引擎交叉验证             |
| **容器化**       | Docker + Docker Compose           | -        | 完整容器化编排             |

### 2.3 核心依赖

**后端核心依赖**（requirements.txt）：

- `fastapi==0.116.1` —— 高性能异步 Web 框架
- `langchain==0.3.27` —— RAG Pipeline 核心框架
- `langchain_community==0.3.27` —— LangChain 社区组件
- `langchain_ollama==0.3.6` —— Ollama 本地模型集成
- `faiss-cpu>=1.12.0` —— 向量相似度搜索
- `sentence-transformers>=5.1.0` —— 句子嵌入模型
- `redis[hiredis]>=5.0.0` —— Redis 异步客户端
- `PyJWT==2.10.1` —— JWT 认证
- `PyMySQL==1.1.1` —— MySQL 数据库驱动
- `python-docx==1.1.2` —— Word 文档解析
- `pdfplumber==0.11.7` —— PDF 高级解析
- `pytesseract==0.3.13` —— OCR 文字识别
- `beautifulsoup4==4.13.4` —— HTML/XML 解析

**前端核心依赖**（package.json）：

- `vue@^3.4.21` —— 渐进式 JavaScript 框架
- `vue-router@^4.5.1` —— 官方路由管理器
- `pinia@^3.0.3` —— 状态管理库
- `tdesign-vue-next@latest` —— 腾讯 UI 组件库
- `axios@^1.11.0` —— HTTP 客户端
- `marked@^16.1.1` —— Markdown 解析器
- `highlight.js@^11.11.1` —— 代码语法高亮
- `tailwindcss@^3.4.17` —— 原子化 CSS 框架
- `graphology@^0.26.0` + `sigma@^3.0.2` —— 知识图谱可视化

---

## 3. 快速启动

### 3.1 Docker Compose 一键部署（推荐用于生产/演示）

```bash
# 1. 克隆项目并配置环境变量
git clone https://github.com/March030303/KnowledgeRAG-GZHU.git
cd KnowledgeRAG-GZHU
cp RagBackend/.env.example RagBackend/.env
# 编辑 .env 文件，填写数据库密码、JWT 密钥等

# 2. 一键启动所有服务
docker compose up -d
```

此命令将启动包含 **MySQL、Redis、Ollama、FastAPI 后端、异步 Worker 及 Nginx 前端** 在内的完整服务栈。访问前端（通常为 http://localhost:8089）即可使用。

### 3.2 一键开发脚本（推荐用于本地开发）

```powershell
# 启动所有服务（MySQL 用 Docker，前后端本地运行）
powershell -ExecutionPolicy Bypass -File .\dev.ps1
```

脚本智能检测已运行服务，实现快速启动。前端通过 Vite 运行在 http://localhost:5173，便于热重载调试。

### 3.3 手动分步启动

```bash
# 1. 启动 MySQL 和 Redis（Docker）
docker run -d --name ragf-mysql -p 3307:3306 -e MYSQL_ROOT_PASSWORD=your_password mysql:8.0
docker run -d --name ragf-redis -p 6380:6379 redis:7-alpine

# 2. 启动 Ollama（本地模型服务）
docker run -d --name ragf-ollama -p 11435:11434 -v ollama_data:/root/.ollama ollama/ollama:latest

# 3. 安装后端依赖并启动
cd RagBackend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 4. 安装前端依赖并启动（新终端）
cd RagFrontend
npm install
npm run dev
```

---

## 4. 核心功能模块

### 4.1 用户认证系统

#### 功能说明

用户认证系统提供完整的身份验证与授权机制，支持多种登录方式，确保系统安全访问。

#### 技术实现

**文件位置**：`RagBackend/RAGF_User_Management/`

| 模块     | 文件                 | 功能                         |
| -------- | -------------------- | ---------------------------- |
| 注册登录 | `LogonAndLogin.py`   | 用户注册、登录、密码加密存储 |
| 用户管理 | `User_Management.py` | 用户信息 CRUD、权限控制      |
| 密码重置 | `Reset_Password.py`  | 邮箱验证码密码重置           |
| QQ 登录  | `QQ_Login.py`        | OAuth2.0 第三方登录集成      |
| 用户设置 | `User_settings.py`   | 个人资料、偏好设置           |

**认证机制**：

- **JWT Token 认证**：使用 PyJWT 生成和验证令牌，支持 `JWT_SECRET` 和 `JWT_SECRET_KEY` 别名兼容
- **密码安全**：用户密码采用哈希加密存储
- **Token 有效期**：默认 24 小时，可通过 `JWT_EXPIRATION_HOURS` 配置
- **数据库**：MySQL `rag_user_db` 数据库，用户表包含用户名、密码哈希、邮箱、角色等字段

**API 端点**：

- `POST /api/auth/register` —— 用户注册
- `POST /api/auth/login` —— 用户登录（返回 JWT）
- `POST /api/auth/reset-password` —— 密码重置
- `GET /api/auth/qq/login` —— QQ OAuth 登录跳转
- `GET /api/auth/qq/callback` —— QQ 登录回调

### 4.2 知识库管理

#### 功能说明

知识库管理是系统的核心数据组织单元，采用「用户-知识库-文档」三层核心实体模型，支持多对多共享关系，为协作共享奠定基础。

#### 技术实现

**文件位置**：`RagBackend/knowledge_base/`

| 模块        | 文件                                                 | 功能               |
| ----------- | ---------------------------------------------------- | ------------------ |
| 知识库 CRUD | `knowledgeBASE4CURD.py` / `knowledgeBASE4CURD_v2.py` | 知识库增删改查     |
| 知识库封面  | `knowledgebase_cover.py`                             | 封面图片生成与管理 |

**数据模型设计**：

```
用户 (User) ←──多对多──→ 知识库 (KnowledgeBase) ←──一对多──→ 文档 (Document)
         ↓
    关联表 (UserKB) —— 包含角色字段（owner/editor/viewer）
```

**权限系统**：

- **RBAC（基于角色的访问控制）**：系统层面定义管理员、普通用户角色
- **ACL（访问控制列表）**：三级权限设置 —— 「个人」「共享」「广场」
- 文件位置：`RagBackend/knowledge/rbac_manager.py`

**文档处理流程**：

1. **上传接收**：前端分块上传大文件（支持 5MB 分片），后端合并
2. **任务入队**：生成处理任务推入 Redis Stream 消息队列
3. **异步处理**：Worker 进程消费队列，执行解析、分块、向量化
4. **索引构建**：文本块向量化后存入 FAISS 索引

**支持的文档格式**：

| 格式           | 解析方式                         |
| -------------- | -------------------------------- |
| PDF            | PyPDF2 / pdfplumber 提取文本     |
| Word (.docx)   | python-docx 解析                 |
| Excel (.xlsx)  | 表格数据提取                     |
| TXT / Markdown | 直接读取                         |
| 图片 (JPG/PNG) | Tesseract + PaddleOCR 双引擎识别 |
| 扫描件         | OCR 文字提取                     |

**Chunking 与向量化策略**：

- **递归分块**（默认）：按字符递归分割，适合结构不清晰文档
- **语义分块**：对 Markdown 等结构清晰文档，使用 `SemanticChunker` 按主题分割
- **嵌入模型**：默认 `sentence-transformers/all-MiniLM-L6-v2`（384 维向量）
- **向量存储**：FAISS 本地索引，支持 L2 距离和余弦相似度

### 4.3 RAG 智能问答

#### 功能说明

RAG 智能问答是系统的核心功能，通过检索增强生成技术，让 LLM 基于用户上传的文档生成有据可查的回答。

#### 技术实现

**文件位置**：`RagBackend/RAG_M/src/rag/`

| 模块          | 文件                  | 功能                        |
| ------------- | --------------------- | --------------------------- |
| RAG 流水线 v3 | `rag_pipeline.py`     | 核心检索生成流程            |
| 原生 RAG      | `native_rag.py`       | 不依赖 LangChain 的轻量实现 |
| 混合检索器    | `hybrid_retriever.py` | BM25 + 向量融合检索         |

**RAG Pipeline v3 架构**：

```
用户提问
    ↓
[检索策略选择] → Vector / BM25 / Hybrid / RRF / MMR
    ↓
[混合检索] → FAISS 向量检索 + BM25 关键词检索
    ↓
[重排序] → 轻量重排 / Cross-Encoder 精排（可选）
    ↓
[上下文组装] → 按相关度排序的文档片段 + 来源标注
    ↓
[LLM 生成] → 流式 / 非流式输出
    ↓
[答案返回] → 带引用溯源的回答
```

**Prompt 模板设计**：

```
你是知识管理助手，专门回答基于文档的问题。

规则：
1. 优先基于"参考文档"中的内容回答
2. 如果文档信息不足，在回答末尾注明"（以上部分内容基于通用知识补充）"
3. 回答时自然引用来源，例如："根据《文件名》中的内容，..."
4. 用户未指定语言时默认使用中文
5. 回答要完整、清晰，如涉及代码/公式/表格则给出对应示例
6. 与上下文完全无关的问题，说明无关并给出通用参考信息

参考文档（已按相关度排序）：
{context}

用户问题：{question}

回答：
```

**引用溯源机制**：

- 每个检索结果包含 `source_info`：排名、得分、文件名、页码、块索引
- 答案中自然嵌入来源引用，如「根据《系统架构说明书》第 3 页的内容...」
- 前端点击引用气泡可展开查看原文段落

**流式输出**：

- 后端使用 SSE（Server-Sent Events）推送生成内容
- 前端实现「打字机」效果，逐字显示回答
- API：`POST /api/RAG/RAG_query`（SSE 流式）

**模式切换**：

- **LangChain 模式**：完整 RAG Pipeline，功能丰富
- **原生模式**：轻量实现，响应更快，适合简单场景

### 4.4 Agent 任务模式

#### 功能说明

Agent 任务模式引入 ReAct（Reasoning + Acting）智能体，让 LLM 具备任务拆解和自主决策能力，实现复杂业务问题的自动化处理。

#### 技术实现

**文件位置**：`RagBackend/RAG_M/src/agent/react_agent.py`

**ReAct Agent 架构**：

```
用户任务
    ↓
[Thought] LLM 思考：是否需要检索？使用什么工具？
    ↓
[Action] 调用工具（知识库检索 / 联网搜索 / 其他）
    ↓
[Observation] 获取工具返回结果
    ↓
  （循环直到获得 Final Answer 或达到最大步数）
    ↓
[Final Answer] 生成最终回答
```

**循环引擎核心**：

- `while` 循环持续运行，终止条件：
  1. LLM 输出 `Final Answer`
  2. 达到最大步数（防止无限循环）
- 每轮循环包含三个固定阶段：
  1. **Thought（推理）**：组合任务目标、历史步骤、上一步观察，提交 LLM
  2. **Action（行动）**：解析 LLM 输出，调用对应工具（如 `search_kb(keywords="政策", kb_id="A")`）
  3. **Observation（观察）**：工具返回结构化结果，追加到历史记录

**标准化工具链**：

| 工具                    | 功能           | 实现              |
| ----------------------- | -------------- | ----------------- |
| `search_knowledge_base` | 知识库语义检索 | 调用 RAG 核心能力 |
| `web_search`            | 联网搜索       | DuckDuckGo API    |
| `rbac_check`            | 权限校验       | RBAC 管理器       |

**任务执行可视化**：

- Agent 启动接口采用 SSE 响应
- 后端推送每个阶段（Thought → Action → Observation）到前端
- 前端渲染流式数据，显示逐步思考的视觉效果

### 4.5 多模型适配

#### 功能说明

系统支持多种大语言模型的灵活接入与热切换，实现模型与业务逻辑的完全解耦。

#### 技术实现

**文件位置**：`RagBackend/multi_model/`

| 模块     | 文件                       | 功能             |
| -------- | -------------------------- | ---------------- |
| 模型路由 | `model_router.py`          | 统一模型调用接口 |
| 扩展路由 | `extended_model_router.py` | 额外模型适配器   |

**支持的模型类型**：

| 类型     | 提供商         | 配置方式                                              |
| -------- | -------------- | ----------------------------------------------------- |
| 本地模型 | Ollama         | `OLLAMA_BASE_URL` + `MODEL`                           |
| 云端 API | OpenAI         | `OPENAI_API_KEY` + `OPENAI_BASE_URL`                  |
| 云端 API | DeepSeek       | `DEEPSEEK_API_KEY`                                    |
| 云端 API | 腾讯混元       | `HUNYUAN_SECRET_ID` + `HUNYUAN_SECRET_KEY`            |
| 云端 API | 阿里 DashScope | `DASHSCOPE_API_KEY`                                   |
| 云端 API | 讯飞星火       | `XFYUN_APP_ID` + `XFYUN_API_KEY` + `XFYUN_API_SECRET` |

**模型配置管理**：

- 文件位置：`RagBackend/models/model_config.py`
- 支持运行时热切换模型，无需重启服务
- 前端「模型管理」界面提供添加、测试、切换功能

### 4.6 检索策略配置

#### 功能说明

系统提供 5 种可配置检索策略，适应不同查询场景和精度要求，用户可在前端动态配置。

#### 技术实现

**文件位置**：`RagBackend/document_processing/retrieval_strategy.py`

**支持的检索策略**：

| 策略       | 说明                           | 适用场景         |
| ---------- | ------------------------------ | ---------------- |
| **Vector** | 纯稠密向量检索（FAISS）        | 语义理解强的查询 |
| **BM25**   | 纯稀疏关键词检索               | 精确术语匹配     |
| **Hybrid** | BM25 + 向量线性加权融合        | 兼顾语义和关键词 |
| **RRF**    | Reciprocal Rank Fusion（推荐） | 整体最优召回     |
| **MMR**    | Maximal Marginal Relevance     | 去重多样化结果   |

**配置参数**：

```python
@dataclass
class RetrievalConfig:
    strategy: str = "rrf"           # 检索策略
    topK: int = 6                   # 返回文档块数
    scoreThreshold: float = 0.0     # 最低相关度过滤
    vectorWeight: float = 0.6       # Hybrid 向量权重
    bm25Weight: float = 0.4         # Hybrid BM25 权重
    rerank: bool = False            # 是否二次排序
    rerankTopN: int = 3             # 重排后保留数量
```

**轻量重排**：

- 基于 Token 重叠的本地计算
- 计算查询与文档片段的共享 Token 比例
- 分析核心名词、动词在片段中的频率和分布
- 优点：延迟极小、可解释性强、资源消耗低

### 4.7 语音交互

#### 功能说明

系统集成语音识别能力，支持用户通过语音输入问题，拓展交互方式。

#### 技术实现

**文件位置**：`RagBackend/multimodal/whisper_asr.py`

**技术方案**：

- 基于 OpenAI Whisper 模型进行语音识别
- 支持模型尺寸选择：`base` / `small` / `medium` / `large`
- 环境变量配置：`WHISPER_MODEL=base`

**工作流程**：

1. 用户录制或上传音频文件
2. 后端调用 Whisper 模型进行语音转文字
3. 识别结果作为用户问题输入 RAG 问答流程
4. 返回文本回答（可扩展为语音合成回复）

### 4.8 联网搜索

#### 功能说明

Agent 任务模式下，当本地知识库无法满足查询需求时，系统自动触发联网搜索获取最新信息。

#### 技术实现

**文件位置**：`RagBackend/agent_tools/web_search_tool.py`

**技术方案**：

- 基于 DuckDuckGo API 实现网络搜索
- 无需 API Key，免费使用
- 返回结构化搜索结果（标题、摘要、链接）

**集成方式**：

- 封装为 LangChain Tool：`web_search`
- Agent 自主决策何时调用（Prompt 规则约束）
- 搜索结果作为 Observation 进入 ReAct 循环

### 4.9 文档创作

#### 功能说明

系统内置多模式智能文档创作引擎，覆盖报告、摘要、大纲、博客、论文等典型写作场景。

#### 技术实现

**文件位置**：`RagBackend/creation/doc_creation.py`

**创作模式**：

| 模式     | 说明                             |
| -------- | -------------------------------- |
| 报告生成 | 基于知识库内容自动生成结构化报告 |
| 摘要提取 | 对长文档进行智能摘要             |
| 大纲生成 | 根据主题生成文章大纲             |
| 博客写作 | 生成适合发布的博客文章           |
| 论文辅助 | 学术论文的文献综述、方法论等     |

**技术特点**：

- 基于 RAG 检索的上下文增强生成
- 支持模板化输出格式
- 可指定写作风格、字数、语言等参数

### 4.10 RAG 评测

#### 功能说明

系统提供内置评测面板，支持对检索质量和生成质量进行量化评估。

#### 技术实现

**文件位置**：`RagBackend/evaluation/eval_panel.py`、`RagBackend/rag_enhancement/rag_evaluator.py`

**检索层评测指标**：

| 指标        | 说明                            |
| ----------- | ------------------------------- |
| Recall@K    | 前 K 个结果中召回相关文档的比例 |
| Precision@K | 前 K 个结果的精确率             |
| mAP         | 平均精度均值                    |
| NDCG@K      | 归一化折损累计增益              |

**生成层评测指标**：

| 指标              | 说明                     |
| ----------------- | ------------------------ |
| Faithfulness      | 答案对检索上下文的忠实度 |
| Answer Relevancy  | 答案与问题的相关性       |
| Context Precision | 上下文利用精确率         |

**测试方案**：

- 使用 RAGAs 自动化评测框架
- 支持自定义测试集导入（模拟「题库导入」功能）
- 生成雷达图对比不同策略/模型的表现

---

## 5. 扩展功能模块

### 5.1 个人主页与设置

- 用户个人资料展示与编辑
- 头像上传与管理
- 账户安全设置
- 偏好配置持久化

### 5.2 外观与主题

- 支持亮色/暗色主题切换
- 基于 TDesign 的设计令牌系统
- 自定义主题色配置

### 5.3 第三方账号绑定

- QQ 登录集成（OAuth2.0）
- 支持绑定/解绑第三方账号
- 文件位置：`RagBackend/RAGF_User_Management/QQ_Login.py`

### 5.4 历史记录

- 对话历史持久化存储
- 支持历史会话搜索与回溯
- 聊天记录导出功能
- 文件位置：`RagBackend/chat_units/chat_management/`

### 5.5 全局搜索

- 快捷键 `Ctrl+K` 唤起全局搜索
- 跨知识库内容检索
- 支持知识库、文档、笔记多维度搜索

### 5.6 置顶功能

- 知识库星标置顶
- 拖拽排序自定义顺序
- 个人/共享/广场三级可见性标签

### 5.7 全局交互动效

- 页面切换过渡动画
- 卡片悬浮效果
- 加载状态骨架屏
- 打字机效果（SSE 流式输出）

### 5.8 系统设置（Win11 风格）

- 仿 Windows 11 设置面板设计
- 分类清晰的设置项组织
- 实时预览配置效果

---

## 6. 集成与联动

### 6.1 Obsidian 笔记同步

**文件位置**：`RagBackend/integrations/obsidian_sync.py`

- 双向同步 Obsidian 笔记库
- 支持 Markdown 格式文档自动导入
- 配置位置：`RagBackend/metadata/obsidian_config.json`

### 6.2 飞书机器人

**文件位置**：`RagBackend/integrations/feishu_bot.py`

- 飞书自定义机器人集成
- 支持群聊中 @机器人进行知识库问答
- 环境变量配置：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_VERIFICATION_TOKEN`
  - `FEISHU_ENCRYPT_KEY`
  - `FEISHU_DEFAULT_KB_ID`

### 6.3 钉钉 / 企微 / Notion / GitHub

**文件位置**：`RagBackend/integrations/dingtalk_wecom.py`

- 钉钉/企业微信 Webhook 机器人集成
- Notion 页面导入（配置保存 + 测试接口）
- GitHub 仓库文档同步（配置保存 + 测试接口）

### 6.4 多数据源接入

**文件位置**：`RagBackend/data_sources/datasource_manager.py`

- 支持多种数据源类型：MySQL、PostgreSQL、MongoDB、OSS/S3/MinIO
- 统一数据源配置管理界面
- 数据源连接测试功能

---

## 7. 系统管理

### 7.1 开放 API

**文件位置**：`RagBackend/open_api/api_key_manager.py`

- API Key 生成与管理
- 请求频率限制
- 使用量统计与计费
- 文件位置：`RagBackend/billing/billing_manager.py`

### 7.2 审计日志

**文件位置**：`RagBackend/audit/audit_log.py`

- 全链路操作记录
- SQLite 存储审计数据
- 支持按用户、时间、操作类型筛选查询
- 请求链路追踪：每个请求生成唯一 `request_id`

### 7.3 增量向量化

**文件位置**：`RagBackend/document_processing/incremental_vectorizer.py`

**核心算法**：

1. 为每个文档计算 SHA-256 哈希值并存储
2. 重新上传时比对哈希值，未变化则跳过处理
3. 若变化，通过 `difflib` 进行文本差异比对
4. 仅对新增或修改的段落重新向量化
5. 更新开销从 O(n) 降低至接近 O(Δn)

### 7.4 RBAC 权限管理

**文件位置**：`RagBackend/knowledge/rbac_manager.py`

**权限层级**：

- **系统级**：管理员、普通用户角色
- **知识库级**：Owner、Editor、Viewer
- **文档级**：读、写、删除权限

### 7.5 OCR 文档解析

**文件位置**：`RagBackend/knowledge/ocr_parser.py`

**双引擎方案**：

| 引擎      | 优势               | 适用场景           |
| --------- | ------------------ | ------------------ |
| Tesseract | 英文识别、版面分析 | 英文文档、标准排版 |
| PaddleOCR | 中文识别、表格识别 | 中文文档、复杂版面 |

**融合策略**：

- 并行调用双引擎
- 行级对齐与置信度加权融合
- 常见 OCR 错误字符映射表轻量级纠错

### 7.6 系统监控

**文件位置**：`RagBackend/monitoring/metrics.py`

- Prometheus 中间件采集指标
- 接口响应延迟、QPS、错误率监控
- Grafana + ECharts 可视化展示
- 系统资源使用率监控（CPU、内存、磁盘）

---

## 8. 移动端 App

- 基于 Uni-app / Quasar 框架开发
- 支持 iOS 和 Android 双平台
- 核心功能与 Web 端保持一致
- 适配移动端触摸交互

---

## 9. 部署方案

### 9.1 Docker Compose 完整部署（推荐）

```yaml
# 服务组成：
# - redis: Redis 7 Alpine（消息队列）
# - mysql: MySQL 8.0（结构化数据）
# - ollama: Ollama 本地 LLM 服务
# - ollama-init: 模型预拉取初始化任务
# - backend: FastAPI 主服务（上传 + 问答）
# - worker: 文档处理 Worker（解析 + 向量化）
# - frontend: Vue3 + Nginx 前端
```

**资源限制**：

| 服务     | 内存限制 | CPU 限制 |
| -------- | -------- | -------- |
| backend  | 1500MB   | 1.0      |
| worker   | 2000MB   | 1.5      |
| mysql    | 512MB    | -        |
| ollama   | 2GB      | -        |
| frontend | 64MB     | -        |

### 9.2 桌面端打包（Windows / macOS / Linux）

#### Tauri 桌面端（轻量，推荐）

基于 Rust + WebView2，安装包仅 **3-5MB**（比 Electron 小 90%+）。

```bash
# 首次构建需安装 Rust（https://rustup.rs/）
cd RagFrontend
npm install
npm run tauri:build          # 构建 Windows 安装包
# 输出：src-tauri/target/release/bundle/nsis/*.exe
```

> **注意：** Tauri 打包仅封装前端，后端需独立运行（Docker 或 PyInstaller）。

#### PyInstaller 后端打包

将 FastAPI 后端打包为独立 `.exe`，无需 Python 环境。

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 打包（项目根目录执行）
pyinstaller rag_backend.spec
# 输出：dist/rag_backend.exe
```

详细打包文档：[docs/打包指南.md](./docs/打包指南.md)

### 9.3 开发环境部署

使用 `dev.ps1` 脚本快速启动：

- MySQL 和 Redis 通过 Docker 运行
- 前后端本地运行，支持热重载
- 前端端口：5173，后端端口：8000

### 9.4 生产环境优化

- 使用 `docker-compose.prod.yml` 覆盖生产配置
- Nginx 反向代理 + SSL 证书
- 数据库定期备份
- Worker 水平扩展

---

## 10. 目录结构

```
KnowledgeRAG-GZHU/
├── RagBackend/                          # 后端服务
│   ├── main.py                          # FastAPI 应用入口
│   ├── requirements.txt                 # Python 依赖
│   ├── Dockerfile                       # 后端镜像构建
│   ├── .env.example                     # 环境变量模板
│   │
│   ├── RAG_M/                           # RAG 核心模块
│   │   ├── src/
│   │   │   ├── rag/                     # RAG 流水线
│   │   │   │   ├── rag_pipeline.py      # RAG Pipeline v3
│   │   │   │   ├── native_rag.py        # 原生 RAG
│   │   │   │   └── hybrid_retriever.py  # 混合检索器
│   │   │   ├── agent/                   # Agent 智能体
│   │   │   │   └── react_agent.py       # ReAct Agent
│   │   │   ├── vectorstore/             # 向量存储
│   │   │   │   └── vector_store.py      # FAISS 封装
│   │   │   ├── ingestion/               # 文档摄入
│   │   │   │   ├── document_loader.py   # 文档加载器
│   │   │   │   └── google_drive.py      # Google Drive 集成
│   │   │   ├── models/                  # 模型配置
│   │   │   └── api/                     # API 路由
│   │   └── RAG_app.py                   # RAG 应用封装
│   │
│   ├── RAGF_User_Management/            # 用户管理
│   │   ├── LogonAndLogin.py             # 登录注册
│   │   ├── User_Management.py           # 用户管理
│   │   ├── QQ_Login.py                 # QQ 登录
│   │   ├── Reset_Password.py            # 密码重置
│   │   └── User_settings.py             # 用户设置
│   │
│   ├── knowledge_base/                   # 知识库管理
│   │   ├── knowledgeBASE4CURD.py        # 知识库 CRUD
│   │   └── knowledgebase_cover.py      # 知识库封面
│   │
│   ├── document_processing/              # 文档处理
│   │   ├── pipeline.py                 # 处理流水线
│   │   ├── retrieval_strategy.py       # 检索策略
│   │   ├── vectorize_task.py           # 向量化任务
│   │   ├── task_queue.py               # 任务队列
│   │   ├── incremental_vectorizer.py   # 增量向量化
│   │   ├── semantic_splitter.py         # 语义分块
│   │   ├── doc_upload.py               # 文档上传
│   │   ├── doc_list.py                 # 文档列表
│   │   └── doc_manage.py               # 文档管理
│   │
│   ├── chat_units/                      # 聊天管理
│   │   └── chat_management/
│   │       ├── chat_main.py             # 聊天主逻辑
│   │       ├── chat_send.py            # 消息发送
│   │       ├── chat_history_attacher.py # 历史记录
│   │       └── chat_download.py        # 记录下载
│   │
│   ├── multi_model/                     # 多模型适配
│   │   ├── model_router.py             # 模型路由
│   │   └── extended_model_router.py    # 扩展路由
│   │
│   ├── agent_tools/                     # Agent 工具
│   │   ├── web_search_tool.py          # 联网搜索
│   │   └── enterprise_tools.py         # 企业工具
│   │
│   ├── integrations/                    # 第三方集成
│   │   ├── feishu_bot.py               # 飞书机器人
│   │   ├── obsidian_sync.py            # Obsidian 同步
│   │   └── dingtalk_wecom.py           # 钉钉/企微
│   │
│   ├── knowledge/                       # 知识管理
│   │   ├── rbac_manager.py             # RBAC 权限
│   │   ├── ocr_parser.py              # OCR 解析
│   │   ├── doc_version_manager.py      # 文档版本
│   │   └── doc_tag_manager.py          # 文档标签
│   │
│   ├── rag_enhancement/                 # RAG 增强
│   │   ├── reranker.py                 # 重排序
│   │   ├── conversation_memory.py       # 对话记忆
│   │   └── rag_evaluator.py            # RAG 评测
│   │
│   ├── evaluation/                      # 评测面板
│   │   └── eval_panel.py               # 评测接口
│   │
│   ├── creation/                        # 文档创作
│   │   └── doc_creation.py             # 创作引擎
│   │
│   ├── audit/                           # 审计日志
│   │   └── audit_log.py                # 日志管理
│   │
│   ├── monitoring/                      # 系统监控
│   │   └── metrics.py                  # 指标采集
│   │
│   ├── open_api/                        # 开放 API
│   │   └── api_key_manager.py          # API Key 管理
│   │
│   ├── data_sources/                   # 数据源管理
│   │   └── datasource_manager.py       # 数据源管理器
│   │
│   ├── multimodal/                      # 多模态
│   │   └── whisper_asr.py              # 语音识别
│   │
│   ├── search/                          # 全文搜索
│   │   └── fulltext_search.py          # 全文检索
│   │
│   ├── billing/                        # 计费系统
│   │   └── billing_manager.py          # 计费管理
│   │
│   ├── enterprise/                      # 企业功能
│   │   ├── compliance_manager.py      # 合规管理
│   │   └── kb_backup.py               # 知识库备份
│   │
│   ├── knowledge_graph/                 # 知识图谱
│   │   ├── generate_kg.py             # 图谱生成
│   │   └── testGPH.py                # 图谱测试
│   │
│   ├── models/                         # 数据模型
│   │   ├── model_config.py            # 模型配置
│   │   └── kb_schema.py              # 知识库 Schema
│   │
│   ├── config/                         # 配置文件
│   │   └── settings.py                 # 全局设置
│   │
│   └── tests/                          # 单元测试
│
├── RagFrontend/                         # 前端应用
│   ├── package.json                     # 前端依赖
│   ├── vite.config.ts                   # Vite 配置
│   ├── tailwind.config.js               # Tailwind 配置
│   ├── Dockerfile                       # 前端镜像
│   ├── nginx.conf                       # Nginx 配置
│   │
│   ├── src-tauri/                      # Tauri 桌面端打包配置
│   │   ├── tauri.conf.json             # 窗口 / 打包目标 / 图标配置
│   │   ├── Cargo.toml                  # Rust 依赖
│   │   ├── src/lib.rs                 # Rust 主进程入口
│   │   ├── capabilities/               # 前端权限配置
│   │   └── icons/                     # 应用图标
│   │
│   ├── src/
│   │   ├── main.ts                    # 应用入口
│   │   ├── App.vue                    # 根组件
│   │   ├── router/                    # 路由配置
│   │   ├── stores/                    # Pinia 状态管理
│   │   ├── components/                 # 公共组件
│   │   ├── views/                    # 页面视图
│   │   ├── api/                      # API 接口封装
│   │   ├── utils/                    # 工具函数
│   │   └── styles/                   # 全局样式
│   │
│   └── public/                        # 公共资源
│
├── docker-compose.yml                   # Docker 编排
├── docker-compose.lite.yml             # 轻量 Docker 编排
├── rag_backend.spec                    # PyInstaller 后端打包配置
├── dev.ps1                             # 一键开发启动脚本
├── docs/
│   └── 打包指南.md                    # 桌面端打包完整指南
│
└── README.md                           # 项目说明
```

---

## 11. 环境变量说明

### 11.1 核心配置

| 变量名            | 默认值              | 说明                                     |
| ----------------- | ------------------- | ---------------------------------------- |
| `ENV_MODE`        | `development`       | 运行环境：development/testing/production |
| `KB_STORAGE_PATH` | `./local-KLB-files` | 知识库文件存储路径                       |
| `MAX_FILE_SIZE`   | `52428800`          | 最大上传文件大小（50MB）                 |
| `CHUNK_SIZE`      | `102400`            | 文件分块大小（100KB）                    |

### 11.2 数据库配置

| 变量名        | 默认值               | 说明           |
| ------------- | -------------------- | -------------- |
| `DB_HOST`     | `127.0.0.1`          | MySQL 主机地址 |
| `DB_PORT`     | `3307`               | MySQL 端口     |
| `DB_USER`     | `root`               | 数据库用户名   |
| `DB_PASSWORD` | `your_password_here` | 数据库密码     |
| `DB_NAME`     | `rag_user_db`        | 数据库名称     |
| `DB_CHARSET`  | `utf8mb4`            | 字符集         |

### 11.3 JWT 认证

| 变量名                 | 默认值            | 说明                             |
| ---------------------- | ----------------- | -------------------------------- |
| `JWT_SECRET`           | `your-secret-key` | JWT 签名密钥（生产环境必须修改） |
| `JWT_EXPIRATION_HOURS` | `24`              | Token 有效期（小时）             |

### 11.4 Ollama / 模型配置

| 变量名            | 默认值                   | 说明            |
| ----------------- | ------------------------ | --------------- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `OLLAMA_TIMEOUT`  | `300`                    | 请求超时（秒）  |
| `MODEL`           | `qwen2:0.5b`             | 默认使用模型    |

### 11.5 向量 / 嵌入配置

| 变量名                | 默认值                                   | 说明     |
| --------------------- | ---------------------------------------- | -------- |
| `EMBEDDING_MODEL`     | `sentence-transformers/all-MiniLM-L6-v2` | 嵌入模型 |
| `EMBEDDING_DIMENSION` | `384`                                    | 向量维度 |

### 11.6 Redis 配置

| 变量名          | 默认值                     | 说明           |
| --------------- | -------------------------- | -------------- |
| `REDIS_URL`     | `redis://localhost:6379/0` | Redis 连接 URL |
| `REDIS_ENABLED` | `false`                    | 是否启用 Redis |

### 11.7 知识库默认参数

| 变量名                            | 默认值 | 说明           |
| --------------------------------- | ------ | -------------- |
| `KB_DEFAULT_CHUNK_SIZE`           | `1000` | 默认分块大小   |
| `KB_DEFAULT_CHUNK_OVERLAP`        | `200`  | 默认块重叠大小 |
| `KB_DEFAULT_SIMILARITY_THRESHOLD` | `0.7`  | 默认相似度阈值 |

### 11.8 CORS 配置

| 变量名         | 默认值                      | 说明           |
| -------------- | --------------------------- | -------------- |
| `CORS_ORIGINS` | `http://localhost:5173,...` | 允许的跨域来源 |

### 11.9 云端模型 API（可选）

| 变量名               | 说明                |
| -------------------- | ------------------- |
| `OPENAI_API_KEY`     | OpenAI API 密钥     |
| `OPENAI_BASE_URL`    | OpenAI 代理地址     |
| `DEEPSEEK_API_KEY`   | DeepSeek API 密钥   |
| `HUNYUAN_SECRET_ID`  | 腾讯混元 Secret ID  |
| `HUNYUAN_SECRET_KEY` | 腾讯混元 Secret Key |
| `DASHSCOPE_API_KEY`  | 阿里 DashScope 密钥 |
| `XFYUN_APP_ID`       | 讯飞 APP ID         |
| `XFYUN_API_KEY`      | 讯飞 API Key        |
| `XFYUN_API_SECRET`   | 讯飞 API Secret     |

### 11.10 飞书集成（可选）

| 变量名                      | 说明          |
| --------------------------- | ------------- |
| `FEISHU_APP_ID`             | 飞书应用 ID   |
| `FEISHU_APP_SECRET`         | 飞书应用密钥  |
| `FEISHU_VERIFICATION_TOKEN` | 验证 Token    |
| `FEISHU_ENCRYPT_KEY`        | 加密密钥      |
| `FEISHU_DEFAULT_KB_ID`      | 默认知识库 ID |

### 11.11 QQ 登录（可选）

| 变量名            | 默认值                                  | 说明        |
| ----------------- | --------------------------------------- | ----------- |
| `QQ_APP_ID`       | -                                       | QQ 应用 ID  |
| `QQ_APP_KEY`      | -                                       | QQ 应用密钥 |
| `QQ_REDIRECT_URI` | `http://localhost:8000/api/qq/callback` | 回调地址    |
| `FRONTEND_URL`    | `http://localhost:5173`                 | 前端地址    |

### 11.12 邮件服务（可选）

| 变量名      | 默认值         | 说明        |
| ----------- | -------------- | ----------- |
| `SMTP_HOST` | `smtp.163.com` | SMTP 服务器 |
| `SMTP_PORT` | `465`          | SMTP 端口   |
| `SMTP_USER` | -              | 邮箱账号    |
| `SMTP_PASS` | -              | 邮箱密码    |

---

## 附录：测试体系

项目包含完整的单元测试覆盖：

| 测试文件                     | 测试内容         |
| ---------------------------- | ---------------- |
| `test_auth_routes.py`        | 认证路由测试     |
| `test_rag_app_routes.py`     | RAG API 测试     |
| `test_rag_vectorstore.py`    | 向量存储测试     |
| `test_rag_vectorization.py`  | 向量化流程测试   |
| `test_retrieval_strategy.py` | 检索策略测试     |
| `test_react_agent.py`        | Agent 功能测试   |
| `test_reranker.py`           | 重排序测试       |
| `test_kb_crud.py`            | 知识库 CRUD 测试 |
| `test_model_router.py`       | 模型路由测试     |
| `test_audit_log_routes.py`   | 审计日志路由测试 |

---

## 许可证

本项目为学术研究及竞赛作品，遵循开源精神。

---

> **项目地址**：https://github.com/March030303/KnowledgeRAG-GZHU
> **开发团队**：广州大学计算机学院
> **竞赛**：2025年（第18届）中国大学生计算机设计大赛 — 人工智能实践赛
