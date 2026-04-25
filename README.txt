=====================================
  KnowledgeRAG v2.0 - Docker 离线版
  智能知识库系统
=====================================

【快速开始（3步）】

第1步：确保已安装 Docker Desktop
       下载地址: https://www.docker.com/products/docker-desktop/

第2步：双击运行 install.bat
       等待镜像导入完成（约3-5分钟）

第3步：打开浏览器访问
       前端界面: http://localhost:8089
       后端文档: http://localhost:8000/docs


【常用命令】

启动服务:   双击 start.bat
停止服务:   双击 stop.bat
查看日志:   docker compose -f docker-compose.offline.yml logs -f
重启服务:   docker compose -f docker-compose.offline.yml restart


【系统要求】

操作系统: Windows 10/11 (64-bit)
内存:     4 GB 以上
磁盘空间: 5 GB 以上（镜像约3.5GB + 数据）
网络:     首次对话需要联网调用 LLM API
           知识库管理功能完全离线可用


【文件说明】

knowledge-rag-v2.tar        离线Docker镜像包（核心文件，勿删）
docker-compose.offline.yml  服务编排配置
install.bat                 安装脚本（首次使用）
start.bat                   启动脚本
stop.bat                    停止脚本
.env                        配置文件（安装后自动生成）


【关于 API Key】

系统已预埋 DeepSeek API Key，开箱即用。
如需更换，编辑 .env 文件中的 DEEPSEEK_API_KEY 字段。

支持的 LLM 提供商：
  - DeepSeek (默认, 性价比最高)
  - 阿里云百炼 (修改 LLM_PROVIDER=dashscope)
  - OpenAI (修改 LLM_PROVIDER=openai)


【数据存储】

所有数据存储在 Docker Volume 中：
  - ragf_data:  应用数据、SQLite 数据库
  - ragf_kb:    知识库文件

备份命令:
  docker run --volumes-from ragf-backend-v2 -v $(pwd)/backup:/backup alpine tar cvf /backup/rag-data-backup.tar /app/data /app/local-KLB-files


【故障排除】

问题: 端口被占用
解决: 修改 docker-compose.offline.yml 中的端口映射 (如 8000->8001)

问题: 容器无法启动
解决: docker compose -f docker-compose.offline.yml logs 查看详细错误

问题: 需要重装
解决: 
  1. stop.bat 停止服务
  2. docker rmi knowledgerag-gzhu-backend knowledgerag-gzhu-frontend
  3. 重新运行 install.bat


【版本信息】

版本: v2.0.0
构建时间: 2025-04-25
包含组件: FastAPI后端 + Vue3前端 + Nginx + SQLite + LangChain

=====================================
  广州大学 KnowledgeRAG 团队
=====================================
