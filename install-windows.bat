@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title KnowledgeRAG v2.0 — Windows 一键安装

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║   KnowledgeRAG v2.0 智能知识库系统 — Windows 安装程序     ║
echo ║   无需 Docker，无需复杂配置，一键启动                     ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: ── 获取脚本所在目录 ──
set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%RagBackend"
set "FRONTEND_DIR=%ROOT_DIR%RagFrontend"

:: ═══════════════════════════════════════════════════════════════
:: 第1步：检查 Python
:: ═══════════════════════════════════════════════════════════════
echo [1/6] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [!] 未检测到 Python！
    echo.
    echo   请先安装 Python 3.11 或更高版本：
    echo   下载地址：https://www.python.org/downloads/
    echo   安装时务必勾选 ★ "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=2 delims=. " %%v in ('python --version 2^>^&1') do set PY_MAJOR=%%v
for /f "tokens=3 delims=. " %%v in ('python --version 2^>^&1') do set PY_MINOR=%%v
echo   ✅ Python %PY_MAJOR%.%PY_MINOR% 已安装

if %PY_MAJOR% lss 3 (
    echo   [错误] Python 版本过低（需要 3.11+），当前 %PY_MAJOR%.%PY_MINOR%
    pause
    exit /b 1
)
if %PY_MAJOR% equ 3 if %PY_MINOR% lss 11 (
    echo   [错误] Python 版本过低（需要 3.11+），当前 %PY_MAJOR%.%PY_MINOR%
    pause
    exit /b 1
)
echo.

:: ═══════════════════════════════════════════════════════════════
:: 第2步：检查/启动 MySQL
:: ═══════════════════════════════════════════════════════════════
echo [2/6] 检查 MySQL...

:: 尝试常见路径查找 mysqld
set "MYSQLD_FOUND="
if exist "E:\PROGRAM\mysql-9.6.0-winx64\bin\mysqld.exe" (
    set "MYSQLD_PATH=E:\PROGRAM\mysql-9.6.0-winx64\bin\mysqld.exe"
    set "MYSQLD_FOUND=1"
)
if exist "C:\Program Files\MySQL\bin\mysqld.exe" (
    set "MYSQLD_PATH=C:\Program Files\MySQL\bin\mysqld.exe"
    set "MYSQLD_FOUND=1"
)

:: 检查端口是否在监听
netstat -an | findstr ":3306.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ MySQL 已运行 (端口 3306)
) else if defined MYSQLD_FOUND (
    echo   [*] 发现 MySQL，正在启动...
    start "" /b "%MYSQLD_PATH%" >nul 2>&1
    :: 等待最多15秒
    set "WAIT_COUNT=0"
:wait_mysql
    timeout /t 1 /nobreak >nul 2>&1
    set /a WAIT_COUNT+=1
    netstat -an | findstr ":3306.*LISTENING" >nul 2>&1
    if %errorlevel% equ 0 (
        echo   ✅ MySQL 启动成功 (端口 3306)
    ) else if !WAIT_COUNT! lss 15 (
        goto wait_mysql
    ) else (
        echo   [!] MySQL 启动超时，请手动启动后重试
    )
) else (
    echo   [!] 未检测到 MySQL！
    echo.
    echo   请选择以下方式之一安装：
    echo   方式A：下载 MySQL Installer https://dev.mysql.com/downloads/installer/
    echo   方式B：使用便携版 mysql-9.6 解压到 E:\PROGRAM\
    echo.
    echo   安装完成后重新运行此脚本。
    echo.
    pause
    exit /b 1
)
echo.

:: ═══════════════════════════════════════════════════════════════
:: 第3步：配置后端 .env
:: ═══════════════════════════════════════════════════════════════
echo [3/6] 初始化配置文件...

:: 后端 .env
if not exist "%BACKEND_DIR%\.env" (
    (
        echo # HuggingFace 离线模式
        HF_HUB_OFFLINE=1
        HF_HOME=C:/Users/%USERNAME%/.cache/hf
        TOKENIZERS_PARALLELISM=false
        echo.
        echo # 数据库（本地 MySQL 端口 3306）
        DB_HOST=127.0.0.1
        DB_PORT=3306
        DB_USER=root
        DB_PASSWORD=Www028820
        DB_NAME=rag_user_db
        DB_CHARSET=utf8mb4
        echo.
        echo # JWT 密钥
        JWT_SECRET=KnowledgeRAG_JWT_2026_secret
        echo.
        echo # 单用户模式
        SINGLE_USER_MODE=true
        echo.
        echo # Ollama 配置
        OLLAMA_BASE_URL=http://localhost:11434
        MODEL=qwen2:0.5b
    ) > "%BACKEND_DIR%\.env"
    echo   ✅ 后端 .env 已创建
) else (
    echo   ℹ️  后端 .env 已存在
)

:: 前端 .env
if not exist "%FRONTEND_DIR%\.env" (
    (
        echo VITE_APP_VERSION=dev
        echo VITE_API_BASE_URL=http://localhost:8000
        echo VITE_SINGLE_USER_MODE=true
    ) > "%FRONTEND_DIR%\.env"
    echo   ✅ 前端 .env 已创建
) else (
    echo   ℹ️  前端 .env 已存在
)
echo.

:: ═══════════════════════════════════════════════════════════════
:: 第4步：安装 Python 依赖
:: ═══════════════════════════════════════════════════════════════
echo [4/6] 安装 Python 依赖（首次约 5-10 分钟）...
echo   使用精简版依赖列表（避免"依赖树过深"问题）
echo.

:: 使用清华镜像加速
pip install -r "%BACKEND_DIR%\requirements-lite.txt" --prefer-binary -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=120
if %errorlevel% neq 0 (
    echo.
    echo   [警告] 部分依赖安装失败，重试中（使用宽松模式）...
    pip install -r "%BACKEND_DIR%\requirements-lite.txt" --prefer-binary -i https://pypi.tuna.tsinghua.edu.cn/simple --no-deps --default-timeout=120
    if %errorlevel% neq 0 (
        echo   [错误] 依赖安装失败！请检查网络或手动执行：
        echo   cd RagBackend ^&^& pip install -r requirements-lite.txt
        pause
        exit /b 1
    )
)
echo   ✅ Python 依赖安装完成
echo.

:: ═══════════════════════════════════════════════════════════════
:: 第5步：安装前端依赖 & 构建
:: ═══════════════════════════════════════════════════════════════
echo [5/6] 准备前端环境...
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo   安装前端依赖（首次约 2-5 分钟）...
    call npm config set registry https://registry.npmmirror.com
    call corepack pnpm install
    if %errorlevel% neq 0 (
        echo   pnpm 不可用，尝试 npm...
        call npm install
    )
) else (
    echo   ℹ️  前端依赖已存在，跳过安装
)
echo   ✅ 前端就绪
echo.

:: ═══════════════════════════════════════════════════════════════
:: 第6步：启动服务
:: ═══════════════════════════════════════════════════════════════
echo [6/6] 启动服务...
echo.

:: 启动后端
cd /d "%BACKEND_DIR%"
start "KnowledgeRAG-Backend" python main.py
echo   [*] 后端正在启动 (http://localhost:8000)...

:: 等待后端
set "BK_WAIT=0"
:wait_backend
timeout /t 2 /nobreak >nul 2>&1
set /a BK_WAIT+=1
curl -s http://localhost:8000/docs >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ 后端已就绪 http://localhost:8000/docs
) else if !BK_WAIT! lss 20 (
    goto wait_backend
) else (
    echo   [!] 后端启动较慢，继续启动前端...
)

:: 启动前端（新窗口）
cd /d "%FRONTEND_DIR%"
start "KnowledgeRAG-Frontend" cmd /k "corepack pnpm dev"
echo   [*] 前端正在启动 (http://localhost:5173)...

:: 等待前端
set "FE_WAIT=0"
:wait_frontend
timeout /t 2 /nobreak >nul 2>&1
set /a FE_WAIT+=1
curl -s http://localhost:5173 >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ 前端已就绪 http://localhost:5173
) else if !FE_WAIT! lss 25 (
    goto wait_frontend
) else (
    echo   [*] 前端可能还在编译中，稍等片刻即可访问
)

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                    🎉 安装完成！                        ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║                                                       ║
echo ║   前端界面：http://localhost:5173                       ║
echo ║   后端API： http://localhost:8000/docs                   ║
echo ║                                                       ║
echo ║   单用户模式已开启，可直接使用                           ║
echo ║                                                       ║
echo ║   停止服务：运行 stop-local.bat                         ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: 自动打开浏览器
timeout /t 3 /nobreak >nul 2>&1
start http://localhost:5173

pause
