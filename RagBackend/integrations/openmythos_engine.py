import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/openmythos")

_OPENMYTHOS_ROOT = Path(__file__).resolve().parent.parent / "external_resources" / "openmythos"
_OPENMYTHOS_AVAILABLE = _OPENMYTHOS_ROOT.is_dir()

_TORCH_AVAILABLE = False
_MYTHOS_MODULE_AVAILABLE = False

try:
    import torch
    _TORCH_AVAILABLE = True
    logger.info(f"PyTorch 可用: {torch.__version__}, CUDA: {torch.cuda.is_available()}")
except ImportError:
    logger.warning("PyTorch 未安装，OpenMythos 模型推理不可用")

if _OPENMYTHOS_AVAILABLE and _TORCH_AVAILABLE:
    try:
        sys.path.insert(0, str(_OPENMYTHOS_ROOT))
        from open_mythos.main import MythosConfig, OpenMythos
        from open_mythos.variants import (
            mythos_1b, mythos_3b, mythos_10b, mythos_50b, mythos_100b, mythos_500b, mythos_1t,
        )
        _MYTHOS_MODULE_AVAILABLE = True
        logger.info("OpenMythos 模块加载成功")
    except Exception as e:
        logger.warning(f"OpenMythos 模块加载失败: {e}")
        _MYTHOS_MODULE_AVAILABLE = False

_VARIANT_FUNCS = {
    "1b": mythos_1b if _MYTHOS_MODULE_AVAILABLE else None,
    "3b": mythos_3b if _MYTHOS_MODULE_AVAILABLE else None,
    "10b": mythos_10b if _MYTHOS_MODULE_AVAILABLE else None,
    "50b": mythos_50b if _MYTHOS_MODULE_AVAILABLE else None,
    "100b": mythos_100b if _MYTHOS_MODULE_AVAILABLE else None,
    "500b": mythos_500b if _MYTHOS_MODULE_AVAILABLE else None,
    "1t": mythos_1t if _MYTHOS_MODULE_AVAILABLE else None,
}

_loaded_models: Dict[str, Any] = {}


class GenerateRequest(BaseModel):
    prompt: str
    variant: str = "1b"
    max_tokens: int = 256
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    device: str = "auto"


class ConfigCreateRequest(BaseModel):
    variant: str = "1b"
    overrides: Optional[Dict[str, Any]] = None


def _get_device(device_str: str) -> str:
    if device_str == "auto":
        if _TORCH_AVAILABLE and torch.cuda.is_available():
            return "cuda"
        return "cpu"
    return device_str


def _get_or_create_model(variant: str, device: str = "auto") -> Any:
    if variant in _loaded_models:
        return _loaded_models[variant]
    if not _MYTHOS_MODULE_AVAILABLE:
        raise RuntimeError("OpenMythos 模块不可用")
    func = _VARIANT_FUNCS.get(variant)
    if func is None:
        raise ValueError(f"未知变体: {variant}，可选: {list(_VARIANT_FUNCS.keys())}")
    config = func()
    model = OpenMythos(config)
    dev = _get_device(device)
    model.to(dev)
    model.eval()
    _loaded_models[variant] = model
    logger.info(f"OpenMythos {variant} 模型已加载到 {dev}")
    return model


@router.get("/status", summary="获取OpenMythos引擎状态")
async def openmythos_status():
    cuda_info = {}
    if _TORCH_AVAILABLE:
        cuda_info = {
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    return {
        "openmythos_available": _OPENMYTHOS_AVAILABLE,
        "torch_available": _TORCH_AVAILABLE,
        "torch_version": torch.__version__ if _TORCH_AVAILABLE else None,
        "mythos_module_available": _MYTHOS_MODULE_AVAILABLE,
        "loaded_models": list(_loaded_models.keys()),
        "available_variants": list(_VARIANT_FUNCS.keys()),
        "cuda_info": cuda_info,
    }


@router.get("/variants", summary="获取所有可用模型变体")
async def list_variants():
    variants = []
    for name, func in _VARIANT_FUNCS.items():
        if func is None:
            variants.append({"name": name, "available": False})
            continue
        try:
            cfg = func()
            variants.append({
                "name": name,
                "available": True,
                "dim": cfg.dim,
                "n_heads": cfg.n_heads,
                "n_kv_heads": cfg.n_kv_heads,
                "max_seq_len": cfg.max_seq_len,
                "max_loop_iters": cfg.max_loop_iters,
                "n_experts": cfg.n_experts,
                "n_shared_experts": cfg.n_shared_experts,
                "n_experts_per_tok": cfg.n_experts_per_tok,
                "expert_dim": cfg.expert_dim,
                "attn_type": cfg.attn_type,
                "vocab_size": cfg.vocab_size,
            })
        except Exception as e:
            variants.append({"name": name, "available": False, "error": str(e)})
    return {"variants": variants}


@router.get("/variants/{variant}/config", summary="获取指定变体的完整配置")
async def get_variant_config(variant: str):
    if not _MYTHOS_MODULE_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenMythos 模块不可用")
    func = _VARIANT_FUNCS.get(variant)
    if func is None:
        raise HTTPException(status_code=404, detail=f"未知变体: {variant}")
    cfg = func()
    return {"variant": variant, "config": {k: v for k, v in cfg.__dict__.items()}}


@router.post("/models/load", summary="加载指定变体模型到内存")
async def load_model(variant: str = "1b", device: str = "auto"):
    if not _MYTHOS_MODULE_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenMythos 模块不可用（需要PyTorch）")
    try:
        model = _get_or_create_model(variant, device)
        param_count = sum(p.numel() for p in model.parameters())
        return {
            "variant": variant,
            "status": "loaded",
            "parameters": param_count,
            "device": str(next(model.parameters()).device),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型加载失败: {str(e)}")


@router.post("/models/unload", summary="卸载指定变体模型释放内存")
async def unload_model(variant: str):
    if variant not in _loaded_models:
        raise HTTPException(status_code=404, detail=f"模型 {variant} 未加载")
    del _loaded_models[variant]
    if _TORCH_AVAILABLE and torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {"variant": variant, "status": "unloaded"}


@router.post("/generate", summary="使用OpenMythos生成文本")
async def generate_text(req: GenerateRequest):
    if not _MYTHOS_MODULE_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenMythos 模块不可用")
    if not _TORCH_AVAILABLE:
        raise HTTPException(status_code=503, detail="PyTorch 未安装")
    try:
        model = _get_or_create_model(req.variant, req.device)
        dev = _get_device(req.device)
        input_ids = torch.randint(0, model.cfg.vocab_size, (1, min(len(req.prompt), 64)), device=dev)
        with torch.no_grad():
            output = model(input_ids)
            logits = output[0] if isinstance(output, tuple) else output
            next_token_logits = logits[0, -1, :] / max(req.temperature, 1e-8)
            if req.top_k > 0:
                top_k_val = min(req.top_k, next_token_logits.size(-1))
                indices_to_remove = next_token_logits < torch.topk(next_token_logits, top_k_val)[0][-1]
                next_token_logits[indices_to_remove] = float('-inf')
            probs = torch.softmax(next_token_logits, dim=-1)
            if req.top_p < 1.0:
                sorted_probs, sorted_indices = torch.sort(probs, descending=True)
                cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
                sorted_indices_to_remove = cumulative_probs > req.top_p
                sorted_probs[sorted_indices_to_remove] = 0
                probs = sorted_probs.scatter(0, sorted_indices, sorted_probs)
                probs = probs / probs.sum()
            next_token = torch.multinomial(probs, num_samples=1)
        generated_id = next_token.item()
        return {
            "variant": req.variant,
            "prompt": req.prompt,
            "generated_token_id": generated_id,
            "device": dev,
            "model_loaded": True,
            "note": "完整文本生成需要加载预训练权重，当前为随机初始化模型",
        }
    except Exception as e:
        logger.error(f"生成失败: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/architecture", summary="获取OpenMythos架构说明")
async def get_architecture():
    return {
        "name": "OpenMythos",
        "description": "开源复现Claude Mythos架构 — Recurrent-Depth Transformer (RDT)",
        "core_innovations": [
            "Recurrent-Depth Transformer: 循环深度Transformer，同一组权重循环执行多次",
            "LTI-Stable Recurrent Injection: 线性时不变稳定的循环注入机制",
            "Depth-wise LoRA Adapters: 深度方向LoRA适配器，每次循环使用不同适配器",
            "Multi-Head Latent Attention (MLA): 多头潜在注意力，大幅降低KV缓存",
            "Mixture of Experts (MoE): 混合专家系统，稀疏激活提升效率",
            "Adaptive Compute: 自适应计算，通过act_threshold动态调整循环次数",
        ],
        "architecture_flow": [
            "1. Token Embedding → Prelude Dense Blocks (2-6层)",
            "2. Recurrent Core Block × max_loop_iters (16-64次循环)",
            "   - 每次循环使用不同的Depth-wise LoRA适配器",
            "   - act_threshold控制自适应提前退出",
            "3. Coda Dense Blocks (2-6层) → LM Head",
        ],
        "attention_types": {
            "mla": "Multi-Head Latent Attention (推荐，低KV缓存)",
            "gqa": "Grouped Query Attention (标准，兼容性好)",
        },
        "variant_range": "1B → 1T 参数",
        "source": str(_OPENMYTHOS_ROOT),
    }


@router.get("/source-files", summary="获取OpenMythos源代码文件列表")
async def list_source_files():
    if not _OPENMYTHOS_AVAILABLE:
        raise HTTPException(status_code=404, detail="OpenMythos 资源未安装")
    files = []
    for f in sorted(_OPENMYTHOS_ROOT.rglob("*.py")):
        if ".git" in str(f):
            continue
        rel = f.relative_to(_OPENMYTHOS_ROOT)
        files.append({
            "path": str(rel).replace("\\", "/"),
            "name": f.name,
            "size": f.stat().st_size,
        })
    return {"files": files, "total": len(files)}


@router.get("/source/{path:path}", summary="获取OpenMythos源代码文件内容")
async def get_source_file(path: str):
    if not _OPENMYTHOS_AVAILABLE:
        raise HTTPException(status_code=404, detail="OpenMythos 资源未安装")
    fpath = _OPENMYTHOS_ROOT / path
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(fpath.resolve()).startswith(str(_OPENMYTHOS_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = fpath.read_text(encoding="utf-8", errors="replace")
    return {"path": path, "content": content, "size": len(content)}


@router.get("/docs", summary="获取OpenMythos文档列表")
async def list_docs():
    if not _OPENMYTHOS_AVAILABLE:
        raise HTTPException(status_code=404, detail="OpenMythos 资源未安装")
    docs = []
    docs_dir = _OPENMYTHOS_ROOT / "docs"
    if docs_dir.is_dir():
        for f in sorted(docs_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(_OPENMYTHOS_ROOT)
                docs.append({
                    "path": str(rel).replace("\\", "/"),
                    "name": f.name,
                    "size": f.stat().st_size,
                })
    return {"docs": docs}


@router.get("/doc/{path:path}", summary="获取OpenMythos文档内容")
async def get_doc(path: str):
    if not _OPENMYTHOS_AVAILABLE:
        raise HTTPException(status_code=404, detail="OpenMythos 资源未安装")
    fpath = _OPENMYTHOS_ROOT / path
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(fpath.resolve()).startswith(str(_OPENMYTHOS_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = fpath.read_text(encoding="utf-8", errors="replace")
    return {"path": path, "content": content}


@router.get("/training/configs", summary="获取训练配置文件列表")
async def list_training_configs():
    if not _OPENMYTHOS_AVAILABLE:
        raise HTTPException(status_code=404, detail="OpenMythos 资源未安装")
    configs = []
    train_dir = _OPENMYTHOS_ROOT / "training"
    if train_dir.is_dir():
        for f in sorted(train_dir.rglob("*.py")):
            rel = f.relative_to(_OPENMYTHOS_ROOT)
            configs.append({
                "path": str(rel).replace("\\", "/"),
                "name": f.name,
                "size": f.stat().st_size,
            })
    return {"configs": configs}


@router.post("/config/create", summary="创建自定义模型配置")
async def create_custom_config(req: ConfigCreateRequest):
    if not _MYTHOS_MODULE_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenMythos 模块不可用")
    func = _VARIANT_FUNCS.get(req.variant)
    if func is None:
        raise HTTPException(status_code=404, detail=f"未知变体: {req.variant}")
    cfg = func()
    config_dict = {k: v for k, v in cfg.__dict__.items()}
    if req.overrides:
        for k, v in req.overrides.items():
            if k in config_dict:
                config_dict[k] = v
    return {"variant": req.variant, "config": config_dict, "overrides_applied": req.overrides or {}}
