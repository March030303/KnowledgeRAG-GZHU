# ── 后端 Dockerfile（最轻量方案：python:3.11-slim）
# 目标镜像大小 < 600MB（不含 Ollama 模型权重，仅应用层）
#
# 使用分阶段构建：
#   Stage 1: builder — 安装依赖（带 build tools）
#   Stage 2: runtime — 只复制必要文件（无 build tools）

# ─────────────────── Stage 1: Builder ───────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# 使用阿里云 apt 镜像源（解决国内网络访问问题）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 安装编译依赖（构建阶段用完即丢弃）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 使用清华镜像加速 pip
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --upgrade pip

# 复制依赖文件并安装到 /install 目录（使用精简版，去除冲突包）
COPY requirements-docker.txt .
RUN pip install --no-cache-dir --prefix=/install \
    --prefer-binary \
    --requirement requirements-docker.txt


# ─────────────────── Stage 2: Runtime ───────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# 使用阿里云 apt 镜像源（解决国内网络访问问题）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 只安装运行时系统依赖（tesseract 用于 OCR，可选）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    # tesseract-ocr \   # 取消注释以启用 OCR（会增加 ~80MB）
    && rm -rf /var/lib/apt/lists/*

# 从 builder 阶段复制已安装的 Python 包
COPY --from=builder /install /usr/local

# 复制应用代码（排除开发文件）
COPY . .

# 创建必要目录
RUN mkdir -p local-KLB-files metadata user_avatars knowledge_base/uploaded_pics/covers

# 环境变量默认值（生产环境通过 docker-compose 或 -e 覆盖）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
