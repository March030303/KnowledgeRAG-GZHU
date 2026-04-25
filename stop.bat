@echo off
chcp 65001 >nul 2>&1
echo 正在停止 KnowledgeRAG...
docker compose -f docker-compose.offline.yml down
echo.
echo ✅ 服务已停止！
pause
