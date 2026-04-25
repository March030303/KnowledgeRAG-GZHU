# KnowledgeRAG v2.0.3 补丁包（基于 v2.0.2）

> 📅 发布日期：2026-04-25
> 🎯 适用版本：KnowledgeRAG v2.0 / v2.0.1 / v2.0.2
> ⚠️ 请确保已安装并运行过上述任一版本

---

## 🔧 本补丁修复/新增的问题

### Bug 1：Mobile 端知识库功能完全不可用（致命）

- **现象**：Mobile 端（React Native）访问知识库时全部返回 **404**，无法获取列表、创建、删除知识库
- **原因**：后端只有老式风格路由（`/api/get-knowledge-item/`, `/api/create-knowledgebase/`），而 Mobile 端使用 RESTful 风格（`/api/knowledge-bases`），**路由完全不匹配**
- **修复**：新增 3 个 RESTful 兼容路由：
  - `GET /api/knowledge-bases` → 返回 `{ knowledge_bases: [...], total: N }`
  - `POST /api/knowledge-bases` → JSON body 创建知识库
  - `DELETE /api/knowledge-bases/{kb_id}` → 删除知识库

### Bug 2：Web 端删除知识库报"删除失败"无详情

- **现象**：点击删除后弹出笼统的 "删除失败"，无法判断具体原因
- **原因**：前端 catch 块吞掉了所有错误信息
- **修复**：增强错误处理，显示 HTTP 状态码 + 后端详细错误信息 + 控制台日志输出

### Bug 3：代码重复 & 缺少 updated_at 字段

- **现象**：创建知识库的数据字典在多处内联重复；缺少最后修改时间字段
- **修复**：提取 `_build_kb_data()` 统一构建函数；自动维护 `updated_at` 字段

### Bug 1+2 继承自 v2.0.2（已包含在本补丁中）

- ✅ 知识库排序容错保护（createdTime 格式异常不崩溃）
- ✅ 移除「获取用户数据失败」红色弹窗
- ✅ 路径遍历攻击防护（Pydantic 校验 + resolve 检测）
- ⬆️ 安全加固**全部保留并增强**

---

## 📦 使用方法

### 方法一：一键打补丁（推荐）

1. **解压本压缩包到任意目录**（如 `C:\patch-v2.0.3\`）
2. **双击 `apply-patch.bat`**
3. 脚本会自动：
   - 检测 KnowledgeRAG 安装位置
   - 备份将被替换的原始文件
   - 应用补丁文件（4 个）
   - 提示是否重启服务

### 方法二：手动替换

将以下 **4 个文件**复制到你的 KnowledgeRAG 安装目录，**覆盖同名文件**：

| 补丁中的文件                                                     | 覆盖到                                                                |
| ---------------------------------------------------------------- | --------------------------------------------------------------------- |
| `patch\RagBackend\knowledge_base\knowledgeBASE4CURD.py`          | `<安装目录>\RagBackend\knowledge_base\knowledgeBASE4CURD.py`          |
| `patch\RagFrontend\src\store\modules\useDataUser.ts`             | `<安装目录>\RagFrontend\src\store\modules\useDataUser.ts`             |
| `patch\RagFrontend\src\components\user-primary\user-primary.vue` | `<安装目录>\RagFrontend\src\components\user-primary\user-primary.vue` |
| `patch\RagFrontend\src\views\KnowledgePages\KnowledgeBase.vue`   | `<安装目录>\RagFrontend\src\views\KnowledgePages\KnowledgeBase.vue`   |

替换完成后**重启前后端服务**即可。

---

## ✅ 验证修复

1. 打开浏览器访问 http://127.0.0.1:5173
2. 确认：
   - ❌ 不再出现「**获取用户数据失败**」的红色弹窗
   - ✅ 知识库列表正常显示，不再 500 崩溃
3. 验证新路由（可选）：
   ```bash
   curl http://127.0.0.1:8000/api/knowledge-bases
   # 应返回 { "knowledge_bases": [...], "total": N }
   ```

---

## 📊 版本对比

| 功能                | v2.0 / v2.0.1 | v2.0.2  | v2.0.3 (本补丁)      |
| ------------------- | ------------- | ------- | -------------------- |
| 知识库排序容错      | ❌ 崩溃       | ✅      | ✅                   |
| 用户数据报错弹窗    | ❌ 弹窗       | ✅ 移除 | ✅                   |
| 路径遍历防护        | ❌ 无         | ✅      | ✅                   |
| Mobile端RESTful路由 | ❌ 404        | ❌ 404  | ✅ 新增              |
| 删除错误详情        | ❌ 笼统       | ❌ 笼统 | ✅ 显示详情          |
| 代码DRY             | ❌ 重复       | ❌ 重复 | ✅ \_build_kb_data() |
| updated_at字段      | ❌ 无         | ❌ 无   | ✅ 自动维护          |

---

## ⚙️ 回滚方式

如果需要回滚：

```batch
:: 备份文件在 patch-backup 目录下，按日期命名
xcopy /y /s "patch-backup\<日期时间>\*" "<你的KnowledgeRAG安装目录>\"
```

或直接重新从原版安装包解压覆盖即可。

---

## 📝 技术细节

| 项目             | 详情                                    |
| ---------------- | --------------------------------------- |
| 修改文件数       | 4 个（1 后端 Python + 3 前端 Vue/TS）   |
| 是否需要重新编译 | ❌ 不需要（Vite dev mode 直接读取源码） |
| 是否需要重启服务 | ✅ 是（后端修改了 Python 文件）         |
| 兼容性           | v2.0.x 全系列                           |
| 新增 API         | 3 个 RESTful 路由（完全向后兼容）       |

---

_KnowledgeRAG Team · 广州大学计算机学院_
