# KnowledgeRAG v2.0.2 补丁包

> 📅 发布日期：2026-04-25  
> 🎯 适用版本：KnowledgeRAG v2.0 / v2.0.1  
> ⚠️ 请确保已安装并运行过 v2.0 或 v2.0.1

---

## 🔧 本补丁修复的问题

### Bug 1：知识库获取失败（500 错误）

- **现象**：进入系统后知识库列表加载失败，后端报 500 内部错误
- **原因**：某个知识库的创建时间格式异常，导致排序函数崩溃
- **修复**：增加 try-except 容错保护，异常时降级为原始顺序

### Bug 2：「获取用户数据失败」红色报错弹窗

- **现象**：每次进入页面都弹出红色错误提示 "获取用户数据失败！"
- **原因**：单用户模式下没有有效 JWT，但系统仍调用需认证的用户接口
- **修复**：移除错误弹窗，静默使用默认用户数据

---

## 📦 使用方法

### 方法一：一键打补丁（推荐）

1. **解压本压缩包到任意目录**（如 `C:\patch-v2.0.2\`）
2. **双击 `apply-patch.bat`**
3. 脚本会自动：
   - 检测 KnowledgeRAG 安装位置
   - 备份将被替换的原始文件
   - 应用补丁文件
   - 提示是否重启服务

### 方法二：手动替换

将以下 3 个文件复制到你的 KnowledgeRAG 安装目录，**覆盖同名文件**：

| 补丁中的文件                                                     | 覆盖到                                                                    |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `patch\RagBackend\knowledge_base\knowledgeBASE4CURD.py`          | `<你的安装目录>\RagBackend\knowledge_base\knowledgeBASE4CURD.py`          |
| `patch\RagFrontend\src\store\modules\useDataUser.ts`             | `<你的安装目录>\RagFrontend\src\store\modules\useDataUser.ts`             |
| `patch\RagFrontend\src\components\user-primary\user-primary.vue` | `<你的安装目录>\RagFrontend\src\components\user-primary\user-primary.vue` |

替换完成后**重启前后端服务**即可。

---

## ✅ 验证修复

1. 打开浏览器访问 http://localhost:5173
2. 确认：
   - ❌ 不再出现「**获取用户数据失败**」的红色弹窗
   - ✅ 知识库列表正常显示，不再 500 报错

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
| 修改文件数       | 3 个（1 后端 Python + 2 前端 Vue/TS）   |
| 是否需要重新编译 | ❌ 不需要（Vite dev mode 直接读取源码） |
| 是否需要重启服务 | ✅ 是（后端修改了 Python 文件）         |
| 兼容性           | v2.0.x 全系列                           |

---

_KnowledgeRAG Team · 广州大学计算机学院_
