import json
import logging
import os
import platform
import subprocess
import shutil
import base64
import io
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/manop")

_MANOP_ROOT = Path(__file__).resolve().parent.parent / "external_resources" / "mano-p"
_MANOP_AVAILABLE = _MANOP_ROOT.is_dir()

_TASKS_DIR = Path(__file__).resolve().parent.parent / "manop_tasks"
_TASKS_DIR.mkdir(parents=True, exist_ok=True)

_SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "manop_screenshots"
_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

_is_macos = platform.system() == "Darwin"
_has_apple_silicon = False
if _is_macos:
    try:
        _cpu_info = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=5)
        _has_apple_silicon = "Apple" in _cpu_info.stdout
    except Exception:
        pass


class CUAAction(BaseModel):
    action_type: str
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[List[int]] = None
    key_combination: Optional[str] = None
    scroll_direction: Optional[str] = None
    scroll_amount: Optional[int] = None
    wait_seconds: Optional[float] = None
    description: Optional[str] = None


class CUATask(BaseModel):
    name: str
    description: str
    steps: List[CUAAction]
    auto_verify: bool = False
    max_retries: int = 3


class ScreenshotRequest(BaseModel):
    region: Optional[List[int]] = None


class ExecuteTaskRequest(BaseModel):
    task_name: str
    dry_run: bool = True


def _take_screenshot(region: Optional[List[int]] = None) -> Optional[bytes]:
    try:
        if platform.system() == "Darwin":
            cmd = ["screencapture", "-x", "-t", "png"]
            if region and len(region) == 4:
                cmd.extend(["-R", f"{region[0]},{region[1]},{region[2]},{region[3]}"])
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0:
                return result.stdout
        elif platform.system() == "Windows":
            try:
                from PIL import ImageGrab
                if region:
                    img = ImageGrab.grab(bbox=tuple(region))
                else:
                    img = ImageGrab.grab()
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return buf.getvalue()
            except ImportError:
                pass
        elif platform.system() == "Linux":
            result = subprocess.run(["scrot", "-"], capture_output=True, timeout=10)
            if result.returncode == 0:
                return result.stdout
    except Exception as e:
        logger.error(f"截图失败: {e}")
    return None


def _execute_mouse_click(x: int, y: int, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
    try:
        if platform.system() == "Darwin":
            script = f'tell application "System Events" to click at {{{x}, {y}}}'
            subprocess.run(["osascript", "-e", script], timeout=5)
            return {"success": True, "action": "click", "x": x, "y": y}
        elif platform.system() == "Windows":
            try:
                import pyautogui
                pyautogui.click(x=x, y=y, clicks=clicks, button=button)
                return {"success": True, "action": "click", "x": x, "y": y}
            except ImportError:
                return {"success": False, "error": "pyautogui 未安装"}
        return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_key_input(text: str) -> Dict[str, Any]:
    try:
        if platform.system() == "Darwin":
            script = f'tell application "System Events" to keystroke "{text}"'
            subprocess.run(["osascript", "-e", script], timeout=5)
            return {"success": True, "action": "type", "text": text}
        elif platform.system() == "Windows":
            try:
                import pyautogui
                pyautogui.typewrite(text)
                return {"success": True, "action": "type", "text": text}
            except ImportError:
                return {"success": False, "error": "pyautogui 未安装"}
        return {"success": False, "error": f"不支持的平台: {platform.system()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_key_combo(key_combination: str) -> Dict[str, Any]:
    try:
        if platform.system() == "Darwin":
            keys = key_combination.split("+")
            key_str = " using {"
            modifiers = []
            main_key = None
            for k in keys:
                k = k.strip().lower()
                if k in ("cmd", "command"):
                    modifiers.append("command down")
                elif k == "ctrl":
                    modifiers.append("control down")
                elif k == "alt":
                    modifiers.append("option down")
                elif k == "shift":
                    modifiers.append("shift down")
                else:
                    main_key = k
            key_str += ", ".join(modifiers)
            key_str += "}"
            script = f'tell application "System Events" to keystroke "{main_key or ""}"{key_str}'
            subprocess.run(["osascript", "-e", script], timeout=5)
            return {"success": True, "action": "key_combo", "keys": key_combination}
        return {"success": False, "error": f"当前平台暂不支持快捷键操作"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_scroll(direction: str, amount: int = 3) -> Dict[str, Any]:
    try:
        if platform.system() == "Darwin":
            delta = -amount if direction == "up" else amount
            script = f'tell application "System Events" to scroll {delta}'
            subprocess.run(["osascript", "-e", script], timeout=5)
            return {"success": True, "action": "scroll", "direction": direction, "amount": amount}
        elif platform.system() == "Windows":
            try:
                import pyautogui
                delta = amount if direction == "up" else -amount
                pyautogui.scroll(delta)
                return {"success": True, "action": "scroll", "direction": direction, "amount": amount}
            except ImportError:
                return {"success": False, "error": "pyautogui 未安装"}
        return {"success": False, "error": f"不支持的平台"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _save_task(task: CUATask) -> Path:
    task_path = _TASKS_DIR / f"{task.name}.json"
    task_data = {
        "name": task.name,
        "description": task.description,
        "auto_verify": task.auto_verify,
        "max_retries": task.max_retries,
        "steps": [s.model_dump() for s in task.steps],
        "created_at": datetime.now().isoformat(),
    }
    task_path.write_text(json.dumps(task_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return task_path


def _load_task(name: str) -> Optional[Dict]:
    task_path = _TASKS_DIR / f"{name}.json"
    if not task_path.is_file():
        return None
    return json.loads(task_path.read_text(encoding="utf-8"))


def _list_tasks() -> List[Dict]:
    tasks = []
    for f in sorted(_TASKS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            tasks.append({
                "name": data.get("name", f.stem),
                "description": data.get("description", ""),
                "step_count": len(data.get("steps", [])),
                "created_at": data.get("created_at", ""),
            })
        except Exception:
            pass
    return tasks


# ==================== API Endpoints ====================

@router.get("/status", summary="获取Mano-P引擎状态")
async def manop_status():
    return {
        "manop_available": _MANOP_AVAILABLE,
        "manop_root": str(_MANOP_ROOT),
        "platform": platform.system(),
        "is_macos": _is_macos,
        "has_apple_silicon": _has_apple_silicon,
        "local_model_supported": _is_macos and _has_apple_silicon,
        "cua_skills_available": True,
        "saved_tasks_count": len(_list_tasks()),
        "capabilities": {
            "screenshot": True,
            "mouse_click": _is_macos or platform.system() == "Windows",
            "key_input": _is_macos or platform.system() == "Windows",
            "key_combo": _is_macos,
            "scroll": _is_macos or platform.system() == "Windows",
            "local_model_inference": _is_macos and _has_apple_silicon,
        },
    }


@router.get("/architecture", summary="获取Mano-P架构说明")
async def get_architecture():
    return {
        "name": "Mano-P 1.0",
        "full_name": "Mano-P: GUI-VLA Agent for Edge Devices",
        "description": "面向端侧设备的GUI感知智能体模型，支持复杂GUI自动化操作",
        "core_capabilities": [
            "复杂GUI自动化操作：自主完成包含数百个交互元素的复杂界面操作",
            "跨系统数据整合：无需API接口，通过纯视觉交互提取和整合多源数据",
            "长任务规划执行：支持数十步至上百步的企业级业务流程自动化",
            "智能报告生成：自动生成数据分析报告、工作总结等结构化文档",
        ],
        "technical_architecture": {
            "training_method": "Mano-Action 双向自增强学习 (SFT → 离线RL → 在线RL)",
            "inference_mechanism": "思考-行动-验证 循环推理",
            "optimization": "混合精度量化 + 视觉Token剪枝 + 边缘推理自适应",
            "deployment": "Mac mini (M4+32GB) / MacBook / 算力棒",
        },
        "benchmarks": {
            "OSWorld": "58.2% 成功率 (72B模型，所有专用GUI智能体模型第一)",
            "WebRetriever_Protocol_I": "41.7 NavEval分数",
            "inference_speed": "4B量化模型: 476 tokens/s预填充, 76 tokens/s解码 (M4 Pro)",
            "peak_memory": "4.3GB (4B量化模型)",
        },
        "three_phases": {
            "phase_1": "开源Mano-CUA技能 — Agent爱好者",
            "phase_2": "开源本地模型和SDK组件 — 高安全需求开发者",
            "phase_3": "开源训练方法、剪枝和量化技术 — 模型训练需求开发者",
        },
        "source": str(_MANOP_ROOT),
    }


@router.get("/skills", summary="获取Mano-P CUA技能列表")
async def list_skills():
    if not _MANOP_AVAILABLE:
        raise HTTPException(status_code=404, detail="Mano-P 资源未安装")
    return {
        "skills": [
            {
                "id": "screenshot_capture",
                "name": "屏幕截图",
                "description": "捕获当前屏幕或指定区域截图",
                "action_types": ["screenshot"],
            },
            {
                "id": "mouse_click",
                "name": "鼠标点击",
                "description": "在指定坐标位置执行鼠标点击",
                "action_types": ["click", "double_click", "right_click"],
            },
            {
                "id": "key_input",
                "name": "键盘输入",
                "description": "模拟键盘文字输入",
                "action_types": ["type"],
            },
            {
                "id": "key_combo",
                "name": "快捷键组合",
                "description": "执行键盘快捷键组合操作",
                "action_types": ["key_combo"],
            },
            {
                "id": "scroll",
                "name": "滚动操作",
                "description": "执行页面或区域滚动",
                "action_types": ["scroll_up", "scroll_down"],
            },
            {
                "id": "gui_automation",
                "name": "GUI自动化流程",
                "description": "组合多种操作完成复杂GUI自动化任务",
                "action_types": ["multi_step"],
            },
        ],
    }


@router.post("/screenshot", summary="捕获屏幕截图")
async def take_screenshot(req: ScreenshotRequest = None):
    img_data = _take_screenshot(req.region if req else None)
    if img_data is None:
        raise HTTPException(status_code=500, detail="截图失败，请检查平台支持")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = _SCREENSHOTS_DIR / filename
    filepath.write_bytes(img_data)
    b64 = base64.b64encode(img_data).decode("utf-8")
    return {
        "filename": filename,
        "size": len(img_data),
        "base64": b64,
        "region": req.region if req else None,
    }


@router.post("/action/click", summary="执行鼠标点击操作")
async def execute_click(x: int, y: int, button: str = "left", clicks: int = 1):
    result = _execute_mouse_click(x, y, button, clicks)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "点击操作失败"))
    return result


@router.post("/action/type", summary="执行键盘输入操作")
async def execute_type(text: str):
    result = _execute_key_input(text)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "输入操作失败"))
    return result


@router.post("/action/key-combo", summary="执行快捷键组合")
async def execute_key_combo(key_combination: str):
    result = _execute_key_combo(key_combination)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "快捷键操作失败"))
    return result


@router.post("/action/scroll", summary="执行滚动操作")
async def execute_scroll(direction: str = "down", amount: int = 3):
    result = _execute_scroll(direction, amount)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "滚动操作失败"))
    return result


@router.post("/action/wait", summary="等待指定时间")
async def execute_wait(seconds: float = 1.0):
    time.sleep(seconds)
    return {"success": True, "action": "wait", "seconds": seconds}


@router.post("/tasks/create", summary="创建CUA自动化任务")
async def create_task(task: CUATask):
    task_path = _save_task(task)
    return {
        "name": task.name,
        "step_count": len(task.steps),
        "saved_to": str(task_path),
        "message": f"任务 '{task.name}' 创建成功，共 {len(task.steps)} 个步骤",
    }


@router.get("/tasks", summary="获取已保存的任务列表")
async def list_tasks():
    tasks = _list_tasks()
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/tasks/{name}", summary="获取任务详情")
async def get_task(name: str):
    task = _load_task(name)
    if task is None:
        raise HTTPException(status_code=404, detail=f"任务 '{name}' 不存在")
    return task


@router.post("/tasks/{name}/execute", summary="执行CUA自动化任务")
async def execute_task(name: str, dry_run: bool = True):
    task = _load_task(name)
    if task is None:
        raise HTTPException(status_code=404, detail=f"任务 '{name}' 不存在")
    steps = task.get("steps", [])
    results = []
    for i, step in enumerate(steps):
        step_result = {
            "step": i + 1,
            "action": step.get("action_type", "unknown"),
            "dry_run": dry_run,
        }
        if dry_run:
            step_result["status"] = "simulated"
            step_result["detail"] = f"[模拟] 将执行: {step.get('action_type')}"
        else:
            action_type = step.get("action_type", "")
            if action_type == "click" and step.get("coordinates"):
                res = _execute_mouse_click(*step["coordinates"])
                step_result["status"] = "success" if res.get("success") else "failed"
                step_result["detail"] = res
            elif action_type == "type" and step.get("value"):
                res = _execute_key_input(step["value"])
                step_result["status"] = "success" if res.get("success") else "failed"
                step_result["detail"] = res
            elif action_type == "key_combo" and step.get("key_combination"):
                res = _execute_key_combo(step["key_combination"])
                step_result["status"] = "success" if res.get("success") else "failed"
                step_result["detail"] = res
            elif action_type in ("scroll_up", "scroll_down"):
                direction = "up" if "up" in action_type else "down"
                amount = step.get("scroll_amount", 3)
                res = _execute_scroll(direction, amount)
                step_result["status"] = "success" if res.get("success") else "failed"
                step_result["detail"] = res
            elif action_type == "wait":
                wait_secs = step.get("wait_seconds", 1.0)
                time.sleep(wait_secs)
                step_result["status"] = "success"
                step_result["detail"] = f"等待 {wait_secs}s"
            elif action_type == "screenshot":
                img_data = _take_screenshot()
                step_result["status"] = "success" if img_data else "failed"
                step_result["detail"] = f"截图: {len(img_data) if img_data else 0} bytes"
            else:
                step_result["status"] = "skipped"
                step_result["detail"] = f"不支持的操作类型: {action_type}"
            if step.get("wait_seconds"):
                time.sleep(step["wait_seconds"])
        results.append(step_result)
    return {
        "task_name": name,
        "total_steps": len(steps),
        "dry_run": dry_run,
        "results": results,
        "completed": all(r.get("status") in ("success", "simulated") for r in results),
    }


@router.delete("/tasks/{name}", summary="删除任务")
async def delete_task(name: str):
    task_path = _TASKS_DIR / f"{name}.json"
    if not task_path.is_file():
        raise HTTPException(status_code=404, detail=f"任务 '{name}' 不存在")
    task_path.unlink()
    return {"message": f"任务 '{name}' 已删除"}


@router.get("/screenshots", summary="获取截图列表")
async def list_screenshots():
    screenshots = []
    for f in sorted(_SCREENSHOTS_DIR.glob("*.png"), reverse=True):
        screenshots.append({
            "filename": f.name,
            "size": f.stat().st_size,
            "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
        })
    return {"screenshots": screenshots, "total": len(screenshots)}


@router.get("/screenshots/{filename}", summary="获取截图详情")
async def get_screenshot(filename: str):
    fpath = _SCREENSHOTS_DIR / filename
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="截图不存在")
    if not str(fpath.resolve()).startswith(str(_SCREENSHOTS_DIR.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    img_data = fpath.read_bytes()
    b64 = base64.b64encode(img_data).decode("utf-8")
    return {"filename": filename, "size": len(img_data), "base64": b64}


@router.get("/docs", summary="获取Mano-P文档列表")
async def list_docs():
    if not _MANOP_AVAILABLE:
        raise HTTPException(status_code=404, detail="Mano-P 资源未安装")
    docs = []
    for f in sorted(_MANOP_ROOT.rglob("*.md")):
        if ".git" in str(f):
            continue
        rel = f.relative_to(_MANOP_ROOT)
        docs.append({
            "path": str(rel).replace("\\", "/"),
            "name": f.name,
            "size": f.stat().st_size,
        })
    return {"docs": docs}


@router.get("/doc/{path:path}", summary="获取Mano-P文档内容")
async def get_doc(path: str):
    if not _MANOP_AVAILABLE:
        raise HTTPException(status_code=404, detail="Mano-P 资源未安装")
    fpath = _MANOP_ROOT / path
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(fpath.resolve()).startswith(str(_MANOP_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = fpath.read_text(encoding="utf-8", errors="replace")
    return {"path": path, "content": content}


@router.get("/resources", summary="获取Mano-P资源文件列表")
async def list_resources():
    if not _MANOP_AVAILABLE:
        raise HTTPException(status_code=404, detail="Mano-P 资源未安装")
    resources = []
    for f in sorted(_MANOP_ROOT.rglob("*")):
        if f.is_file() and ".git" not in str(f):
            rel = f.relative_to(_MANOP_ROOT)
            resources.append({
                "path": str(rel).replace("\\", "/"),
                "name": f.name,
                "size": f.stat().st_size,
                "suffix": f.suffix,
            })
    return {"resources": resources, "total": len(resources)}


@router.get("/resource/{path:path}", summary="获取Mano-P资源文件内容")
async def get_resource(path: str):
    if not _MANOP_AVAILABLE:
        raise HTTPException(status_code=404, detail="Mano-P 资源未安装")
    fpath = _MANOP_ROOT / path
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(fpath.resolve()).startswith(str(_MANOP_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    if fpath.suffix in (".png", ".jpg", ".jpeg", ".gif", ".ico"):
        img_data = fpath.read_bytes()
        b64 = base64.b64encode(img_data).decode("utf-8")
        return {"path": path, "type": "image", "base64": b64, "size": len(img_data)}
    content = fpath.read_text(encoding="utf-8", errors="replace")
    return {"path": path, "type": "text", "content": content, "size": len(content)}
