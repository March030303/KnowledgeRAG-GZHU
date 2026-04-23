"""
obsidian_memory.py
Obsidian 无限记忆模块
- 实现 Obsidian 笔记的自动同步
- 将 Obsidian 笔记集成到 RAG 系统中
- 实现基于 Obsidian 笔记的上下文理解和自动调取
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from integrations.obsidian_sync import _load_config, _do_sync

logger = logging.getLogger(__name__)
router = APIRouter()

# - -
_MEMORY_CONFIG_PATH = Path(__file__).parent.parent / "metadata" / "obsidian_memory_config.json"
_MEMORY_STATE_PATH = Path(__file__).parent.parent / "metadata" / "obsidian_memory_state.json"


def _load_memory_config() -> dict:
    try:
        if _MEMORY_CONFIG_PATH.exists():
            return json.loads(_MEMORY_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_memory_config(config: dict):
    _MEMORY_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _MEMORY_CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_memory_state() -> dict:
    try:
        if _MEMORY_STATE_PATH.exists():
            return json.loads(_MEMORY_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_memory_state(state: dict):
    _MEMORY_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _MEMORY_STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# - Pydantic -


class ObsidianMemoryConfigRequest(BaseModel):
    auto_sync: bool = True
    sync_interval: int = 3600  # 自动同步间隔（秒）
    enable_memory: bool = True
    memory_weight: float = 0.7  # Obsidian 记忆在 RAG 中的权重
    max_retrieved_docs: int = 5  # 最多从 Obsidian 中检索的文档数


# - 自动同步任务 -


def _schedule_auto_sync():
    """调度自动同步任务"""
    import asyncio
    
    async def auto_sync_task():
        while True:
            try:
                config = _load_config().get("obsidian")
                memory_config = _load_memory_config()
                
                if config and memory_config.get("auto_sync", True):
                    sync_interval = memory_config.get("sync_interval", 3600)
                    
                    logger.info("[ObsidianMemory] 执行自动同步任务")
                    try:
                        vault_path = config["vault_path"]
                        kb_id = config.get("kb_id")
                        exclude_patterns = config.get("exclude_patterns", [])
                        _do_sync(vault_path, kb_id, exclude_patterns)
                        logger.info("[ObsidianMemory] 自动同步完成")
                    except Exception as e:
                        logger.error(f"[ObsidianMemory] 自动同步失败: {e}")
                
                # 等待下一次同步
                await asyncio.sleep(memory_config.get("sync_interval", 3600))
            except Exception as e:
                logger.error(f"[ObsidianMemory] 自动同步任务出错: {e}")
                await asyncio.sleep(3600)  # 出错后等待 1 小时再重试
    
    # 启动异步任务
    import threading
    def run_async_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(auto_sync_task())
    
    thread = threading.Thread(target=run_async_task, daemon=True)
    thread.start()


# 启动自动同步任务
_schedule_auto_sync()


# - API -


@router.post("/api/integrations/obsidian/memory/configure")
async def configure_obsidian_memory(req: ObsidianMemoryConfigRequest):
    """配置 Obsidian 无限记忆"""
    config = _load_memory_config()
    config.update({
        "auto_sync": req.auto_sync,
        "sync_interval": req.sync_interval,
        "enable_memory": req.enable_memory,
        "memory_weight": req.memory_weight,
        "max_retrieved_docs": req.max_retrieved_docs,
        "configured_at": time.time(),
    })
    _save_memory_config(config)
    
    return {
        "success": True,
        "config": config,
        "message": "Obsidian 无限记忆配置成功",
    }


@router.get("/api/integrations/obsidian/memory/status")
async def obsidian_memory_status():
    """获取 Obsidian 无限记忆状态"""
    config = _load_memory_config()
    state = _load_memory_state()
    
    return {
        "configured": bool(config),
        "auto_sync": config.get("auto_sync", True),
        "sync_interval": config.get("sync_interval", 3600),
        "enable_memory": config.get("enable_memory", True),
        "memory_weight": config.get("memory_weight", 0.7),
        "max_retrieved_docs": config.get("max_retrieved_docs", 5),
        "last_sync": state.get("last_sync"),
    }


@router.post("/api/integrations/obsidian/memory/sync")
async def sync_obsidian_memory():
    """手动触发 Obsidian 记忆同步"""
    config = _load_config().get("obsidian")
    if not config:
        raise HTTPException(
            status_code=400,
            detail="尚未配置 Obsidian Vault，请先调用 /api/integrations/obsidian/configure",
        )
    
    try:
        vault_path = config["vault_path"]
        kb_id = config.get("kb_id")
        exclude_patterns = config.get("exclude_patterns", [])
        
        stats = _do_sync(vault_path, kb_id, exclude_patterns)
        
        # 更新记忆状态
        state = _load_memory_state()
        state["last_sync"] = time.time()
        _save_memory_state(state)
        
        return JSONResponse({"success": True, "stats": stats})
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[ObsidianMemory] 同步失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")
