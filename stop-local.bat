@echo off
chcp 65001 >nul 2>&1
title KnowledgeRAG — 停止服务

echo 正在停止 KnowledgeRAG 本地服务...

:: 停止前端（Vite/Node）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173.*LISTENING" 2^>^&1') do (
    taskkill /PID %%a /F >nul 2>&1
    echo   已停止前端 (PID: %%a)
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5174.*LISTENING" 2^>^&1') do (
    taskkill /PID %%a /F >nul 2>&1
    echo   已停止前端 (PID: %%a)
)

:: 停止后端（Python uvicorn）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>^&1') do (
    taskkill /PID %%a /F >nul 2>&1
    echo   已停止后端 (PID: %%a)
)

echo.
echo ✅ 所有服务已停止！
echo.
pause
