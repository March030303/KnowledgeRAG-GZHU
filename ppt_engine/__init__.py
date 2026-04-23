"""
PPT Engine - AI-PowerPoint Integration Module

Provides automated PPT generation with cyberpunk styling and optional iSlide enhancement.

Usage:
    from ppt_engine import PPTWorkflow
    
    workflow = PPTWorkflow(output_dir="./output")
    result = workflow.execute("制作一份关于RAG技术的学术汇报PPT，深色科技风，20页")
    
    print(f"PPT saved: {result['pptx_path']}")
"""

from .ppt_builder import PPTBuilder
from .islide_enhancer import ISlideEnhancer
from .ppt_workflow import PPTWorkflow

__all__ = ["PPTBuilder", "ISlideEnhancer", "PPTWorkflow"]
__version__ = "1.0.0"
