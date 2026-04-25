@echo off
chcp 65001 >nul 2>&1
echo 正在启动 KnowledgeRAG...
docker compose -f docker-compose.offline.yml up -d
echo.
echo ✅ 服务已启动！
echo   前端: http://localhost:8089
echo   后端: http://localhost:8000/docs
echo.
pause
