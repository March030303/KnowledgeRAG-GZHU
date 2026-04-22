"""
URL 导入模块 - 从网页 URL 抓取内容并导入知识库

功能：
  - 从 URL 抓取网页正文（自动去噪，提取核心内容）
  - 支持批量 URL 导入
  - 自动保存为 Markdown 文件到知识库目录
  - 与增量向量化模块联动

API:
  POST /api/url-import/         -- 单个 URL 导入
  POST /api/url-import/batch    -- 批量 URL 导入
  GET  /api/url-import/status   -- 导入状态查询
"""

import logging
import os
import re
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import aiohttp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/url-import", tags=["URL导入"])

URL_IMPORT_DIR = os.getenv("URL_IMPORT_DIR", "url_imported")
os.makedirs(URL_IMPORT_DIR, exist_ok=True)


async def _fetch_url_content(url: str, timeout: int = 30) -> dict:
    """抓取 URL 内容，返回 {title, content, content_type}"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=400, detail=f"HTTP {resp.status}: 无法访问 {url}")
            content_type = resp.headers.get("Content-Type", "")
            raw = await resp.read()

    encoding = "utf-8"
    if "charset=" in content_type:
        encoding = content_type.split("charset=")[-1].split(";")[0].strip()
    try:
        text = raw.decode(encoding, errors="replace")
    except Exception:
        text = raw.decode("utf-8", errors="replace")

    if "text/html" in content_type:
        title, content = _extract_html(text)
    elif "application/pdf" in content_type:
        title = url.split("/")[-1] or "document.pdf"
        content = _extract_pdf(raw)
    elif "text/plain" in content_type or "text/markdown" in content_type:
        title = url.split("/")[-1] or "document"
        content = text
    else:
        title = url.split("/")[-1] or "document"
        content = text

    return {"title": title, "content": content, "content_type": content_type}


def _extract_html(html: str) -> tuple:
    """从 HTML 提取标题和正文"""
    title = ""
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()

    for tag in ["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]:
        html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", html, flags=re.IGNORECASE | re.DOTALL)

    article_match = re.search(r"<article[^>]*>(.*?)</article>", html, re.IGNORECASE | re.DOTALL)
    if article_match:
        body = article_match.group(1)
    else:
        body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.IGNORECASE | re.DOTALL)
        body = body_match.group(1) if body_match else html

    text = re.sub(r"<br\s*/?>", "\n", body, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</h[1-6]>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    if not title:
        title = "webpage"

    return title, text


def _extract_pdf(raw: bytes) -> str:
    """从 PDF 字节提取文本"""
    try:
        import fitz
        doc = fitz.open(stream=raw, filetype="pdf")
        texts = []
        for page in doc:
            t = page.get_text()
            if t.strip():
                texts.append(t)
        return "\n\n".join(texts)
    except Exception as e:
        return f"[PDF解析失败: {e}]"


def _save_to_kb(title: str, content: str, url: str, kb_id: str = "") -> str:
    """将内容保存为 Markdown 文件，返回文件路径"""
    safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)[:80]
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    filename = f"{safe_title}_{url_hash}.md"

    if kb_id:
        save_dir = os.path.join(URL_IMPORT_DIR, kb_id)
    else:
        save_dir = URL_IMPORT_DIR
    os.makedirs(save_dir, exist_ok=True)

    filepath = os.path.join(save_dir, filename)
    frontmatter = f"---\nsource_url: {url}\nimported_at: {datetime.now().isoformat()}\n---\n\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)

    return filepath


class UrlImportRequest(BaseModel):
    url: str
    kb_id: str = ""


class BatchUrlImportRequest(BaseModel):
    urls: List[str]
    kb_id: str = ""


@router.post("/")
async def import_url(req: UrlImportRequest):
    """从单个 URL 导入内容到知识库"""
    try:
        result = await _fetch_url_content(req.url)
        filepath = _save_to_kb(result["title"], result["content"], req.url, req.kb_id)
        return {
            "status": "ok",
            "message": f"已导入: {result['title']}",
            "url": req.url,
            "title": result["title"],
            "char_count": len(result["content"]),
            "filepath": filepath,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL导入失败: {req.url} - {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/batch")
async def import_urls_batch(req: BatchUrlImportRequest):
    """批量从 URL 导入内容"""
    results = []
    for url in req.urls:
        try:
            result = await _fetch_url_content(url)
            filepath = _save_to_kb(result["title"], result["content"], url, req.kb_id)
            results.append({
                "url": url,
                "status": "ok",
                "title": result["title"],
                "char_count": len(result["content"]),
                "filepath": filepath,
            })
        except Exception as e:
            results.append({"url": url, "status": "error", "message": str(e)})

    ok_count = sum(1 for r in results if r["status"] == "ok")
    return {
        "total": len(req.urls),
        "success": ok_count,
        "failed": len(req.urls) - ok_count,
        "results": results,
    }


@router.get("/status")
async def import_status():
    """返回 URL 导入模块状态"""
    return {
        "module": "url-import",
        "available": True,
        "import_dir": URL_IMPORT_DIR,
        "supported_content_types": ["text/html", "text/plain", "text/markdown", "application/pdf"],
    }
