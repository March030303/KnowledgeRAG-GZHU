"""
OCR 解析模块 - 支持扫描件/图片/音视频内容提取
依赖：magic-pdf(MinerU), paddleocr, pytesseract, pillow, moviepy, pydub, openai-whisper
"""

import base64
import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

router = APIRouter(prefix="/api/ocr")


def extract_text_with_mineru(file_bytes: bytes, filename: str) -> str:
    """使用 MinerU (magic-pdf) 进行深度学习版面分析和 OCR 提取"""
    try:
        from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
        from magic_pdf.data.dataset import PymuDocDataset

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, filename)
            with open(input_path, "wb") as f:
                f.write(file_bytes)

            reader = FileBasedDataReader("")
            pdf_bytes = reader.read(input_path)
            ds = PymuDocDataset(pdf_bytes)

            if ds.classify() == "ocr":
                ds.apply_ocr()
            else:
                ds.apply()

            content_list = ds.export_content_list()
            texts = []
            for item in content_list:
                if isinstance(item, dict) and item.get("type") == "text":
                    texts.append(item.get("text", ""))
                elif isinstance(item, str):
                    texts.append(item)

            return "\n".join(texts)
    except ImportError:
        return ""
    except Exception as e:
        return f"[MinerU解析失败: {e}]"


def extract_text_from_image(file_bytes: bytes, filename: str) -> str:
    """使用 MinerU（优先）→ PaddleOCR → pytesseract 三级降级提取图片文字"""
    mineru_result = extract_text_with_mineru(file_bytes, filename)
    if mineru_result and not mineru_result.startswith("[MinerU"):
        return mineru_result

    try:
        import io

        import numpy as np
        from paddleocr import PaddleOCR
        from PIL import Image

        ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        img = Image.open(io.BytesIO(file_bytes))
        img_array = np.array(img)
        result = ocr.ocr(img_array, cls=True)
        texts = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    texts.append(line[1][0])
        return "\n".join(texts)
    except ImportError:
        pass

    try:
        import io

        import pytesseract
        from PIL import Image

        img = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(img, lang="chi_sim+eng")
    except ImportError:
        pass

    return f"[OCR不可用] 文件 {filename} 需要安装 magic-pdf(MinerU), paddleocr 或 pytesseract"


def extract_text_from_pdf_scan(file_bytes: bytes, filename: str = "scan.pdf") -> str:
    """对扫描版PDF逐页OCR（优先使用MinerU）"""
    mineru_result = extract_text_with_mineru(file_bytes, filename)
    if mineru_result and not mineru_result.startswith("[MinerU"):
        return mineru_result

    try:
        import fitz

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        all_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                all_text.append(text)
            else:
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                ocr_text = extract_text_from_image(img_bytes, f"page_{page_num+1}.png")
                all_text.append(ocr_text)
        return "\n\n".join(all_text)
    except Exception as e:
        return f"[PDF OCR失败] {str(e)}"


# - Audio to textWhisper-
def extract_text_from_audio(file_bytes: bytes, filename: str) -> str:
    """使用 Whisper 将音频转文字"""
    try:
        import os
        import tempfile

        import whisper

        suffix = Path(filename).suffix or ".mp3"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        model_name = os.getenv("WHISPER_MODEL", "base")
        model = whisper.load_model(model_name)
        result = model.transcribe(tmp_path, language="zh")
        os.unlink(tmp_path)
        return result.get("text", "")
    except Exception as e:
        return f"[音频转写失败] {str(e)}"


# - -
def extract_text_from_video(file_bytes: bytes, filename: str) -> str:
    """提取视频音轨 → Whisper 转文字"""
    try:
        import os
        import tempfile
        from pathlib import Path

        suffix = Path(filename).suffix or ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            video_path = tmp.name
        audio_path = video_path + ".wav"
        # moviepy
        try:
            from moviepy.editor import VideoFileClip

            clip = VideoFileClip(video_path)
            clip.audio.write_audiofile(audio_path, logger=None)
            clip.close()
        except ImportError:
            # : ffmpeg
            os.system(
                f'ffmpeg -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 "{audio_path}" -y -loglevel quiet'
            )

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        text = extract_text_from_audio(audio_bytes, "audio.wav")
        os.unlink(video_path)
        if os.path.exists(audio_path):
            os.unlink(audio_path)
        return text
    except Exception as e:
        return f"[视频转写失败] {str(e)}"


# - -
def extract_content(file_bytes: bytes, filename: str, content_type: str = "") -> str:
    """根据文件类型自动选择解析策略"""
    ext = Path(filename).suffix.lower()
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}
    audio_exts = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma"}
    video_exts = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}

    if ext in image_exts or "image" in content_type:
        return extract_text_from_image(file_bytes, filename)
    elif ext in audio_exts or "audio" in content_type:
        return extract_text_from_audio(file_bytes, filename)
    elif ext in video_exts or "video" in content_type:
        return extract_text_from_video(file_bytes, filename)
    elif ext == ".pdf":
        return extract_text_from_pdf_scan(file_bytes)
    else:
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except:
            return "[无法提取内容]"


# - FastAPI -
@router.post("/extract")
async def ocr_extract(file: UploadFile = File(...)):
    """上传文件，返回提取的文本内容"""
    content = await file.read()
    text = extract_content(content, file.filename or "unknown", file.content_type or "")
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "char_count": len(text),
        "text": text,
    }


@router.post("/extract-base64")
async def ocr_extract_base64(data: dict):
    """Base64 编码文件内容解析"""
    b64 = data.get("content", "")
    filename = data.get("filename", "file.png")
    content_type = data.get("content_type", "")
    file_bytes = base64.b64decode(b64)
    text = extract_content(file_bytes, filename, content_type)
    return {"filename": filename, "text": text, "char_count": len(text)}
