#!/usr/bin/env python3
"""
PPTWorkflow - Complete PPT production workflow orchestrator
Integrates PPTBuilder and ISlideEnhancer for end-to-end automation
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ppt_builder import PPTBuilder, CHAPTER_COLORS
from islide_enhancer import ISlideEnhancer


class PPTWorkflow:
    """PPT制作工作流编排器"""
    
    def __init__(self, output_dir: str = "./output"):
        """初始化工作流
        
        Args:
            output_dir: 输出文件目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.builder = PPTBuilder()
        self.enhancer = ISlideEnhancer()
        
        # Workflow configuration
        self.config = {
            "use_islide": False,  # Will be set based on availability
            "apply_transitions": True,
            "apply_animations": False,
            "export_pdf": True,
            "style": "cyberpunk",  # cyberpunk / business / academic / minimal
        }
    
    def parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """解析用户Prompt为结构化配置
        
        Args:
            prompt: 用户自然语言描述
            
        Returns:
            结构化配置字典
        """
        config = {
            "title": "",
            "subtitle": "",
            "description": "",
            "pages": 20,
            "style": "cyberpunk",
            "chapters": [],
            "content_source": None,
            "use_islide": False,
            "special_elements": [],
        }
        
        # Simple keyword extraction (in production, use LLM for parsing)
        prompt_lower = prompt.lower()
        
        # Extract title
        if "关于" in prompt:
            start = prompt.find("关于") + 2
            end = prompt.find("的", start)
            if end > start:
                config["title"] = prompt[start:end].strip()
        
        # Extract page count
        import re
        page_match = re.search(r'(\d+)\s*页', prompt)
        if page_match:
            config["pages"] = int(page_match.group(1))
        
        # Extract style
        style_keywords = {
            "深色": "cyberpunk",
            "科技": "cyberpunk",
            "赛博": "cyberpunk",
            "商务": "business",
            "简约": "minimal",
            "学术": "academic",
            "教育": "academic",
        }
        for keyword, style in style_keywords.items():
            if keyword in prompt:
                config["style"] = style
                break
        
        # Extract special elements
        if "代码" in prompt or "源码" in prompt:
            config["special_elements"].append("code")
        if "图表" in prompt or "数据" in prompt:
            config["special_elements"].append("chart")
        if "流程" in prompt:
            config["special_elements"].append("flowchart")
        
        # Check for iSlide
        if "islide" in prompt_lower or "美化" in prompt:
            config["use_islide"] = True
        
        # Default title if not extracted
        if not config["title"]:
            config["title"] = "演示文稿"
        
        config["subtitle"] = config["title"]
        config["description"] = f"基于{config['title']}的{config['style']}风格演示文稿"
        
        return config
    
    def generate_outline(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成PPT大纲
        
        Args:
            config: 结构化配置
            
        Returns:
            幻灯片配置列表
        """
        outline = []
        
        # Slide 1: Cover
        outline.append({
            "type": "cover",
            "title": config["title"],
            "subtitle": config["subtitle"],
            "description": config["description"],
        })
        
        # Slide 2: TOC
        chapters = config.get("chapters", [])
        if not chapters:
            # Auto-generate chapters based on topic
            chapters = self._auto_generate_chapters(config["title"])
        
        toc_items = []
        for i, chapter in enumerate(chapters, 1):
            toc_items.append((
                f"0{i}",
                chapter["title"],
                chapter["description"],
                CHAPTER_COLORS.get(i, CHAPTER_COLORS[1])
            ))
        
        outline.append({
            "type": "toc",
            "title": "目录",
            "items": toc_items,
        })
        
        # Chapter slides and content slides
        for i, chapter in enumerate(chapters, 1):
            accent = CHAPTER_COLORS.get(i, CHAPTER_COLORS[1])
            
            # Chapter transition slide
            outline.append({
                "type": "chapter",
                "number": f"0{i}",
                "title": chapter["title"],
                "subtitle": chapter["description"],
                "accent": accent,
            })
            
            # Content slides for this chapter
            for content_slide in chapter.get("slides", []):
                content_slide["accent"] = accent
                outline.append(content_slide)
        
        # Final slide
        outline.append({
            "type": "cover",
            "title": "谢谢观看",
            "subtitle": config["title"],
            "description": "感谢聆听",
        })
        
        return outline
    
    def _auto_generate_chapters(self, title: str) -> List[Dict[str, Any]]:
        """根据标题自动生成章节结构"""
        
        # Default structure for tech topics
        if any(kw in title for kw in ["技术", "系统", "平台", "框架", "RAG", "AI"]):
            return [
                {
                    "title": "项目综述",
                    "description": "背景、目标与整体架构",
                    "slides": [
                        {"type": "two_col", "title": "项目背景", "layout": "two_col",
                         "left": {"title": "问题背景", "items": ["行业痛点分析", "现有方案不足", "市场需求"]},
                         "right": {"title": "项目目标", "items": ["核心目标", "预期成果", "价值主张"]}},
                        {"type": "list", "title": "系统架构", "layout": "list",
                         "items": ["整体架构图", "技术选型", "模块划分"]},
                    ]
                },
                {
                    "title": "核心功能",
                    "description": "主要功能模块详解",
                    "slides": [
                        {"type": "grid", "title": "功能全景", "layout": "grid_4",
                         "items": [("功能1", "描述1", CHAPTER_COLORS[2]), ("功能2", "描述2", CHAPTER_COLORS[2]),
                                  ("功能3", "描述3", CHAPTER_COLORS[2]), ("功能4", "描述4", CHAPTER_COLORS[2])]},
                        {"type": "list", "title": "核心流程", "layout": "list",
                         "items": ["流程步骤1", "流程步骤2", "流程步骤3", "流程步骤4"]},
                    ]
                },
                {
                    "title": "技术实现",
                    "description": "关键技术点与实现细节",
                    "slides": [
                        {"type": "code", "title": "核心代码", "layout": "code",
                         "code": "# 示例代码\\nprint('Hello World')", "highlight": "关键实现"},
                        {"type": "two_col", "title": "技术对比", "layout": "two_col",
                         "left": {"title": "方案A", "items": ["优点1", "优点2", "缺点1"]},
                         "right": {"title": "方案B", "items": ["优点1", "优点2", "缺点1"]}},
                    ]
                },
                {
                    "title": "总结展望",
                    "description": "成果总结与未来规划",
                    "slides": [
                        {"type": "grid", "title": "核心成果", "layout": "grid_4",
                         "items": [("成果1", "描述", CHAPTER_COLORS[4]), ("成果2", "描述", CHAPTER_COLORS[4]),
                                  ("成果3", "描述", CHAPTER_COLORS[4]), ("成果4", "描述", CHAPTER_COLORS[4])]},
                        {"type": "two_col", "title": "未来规划", "layout": "two_col",
                         "left": {"title": "短期计划", "items": ["计划1", "计划2", "计划3"]},
                         "right": {"title": "长期愿景", "items": ["愿景1", "愿景2", "愿景3"]}},
                    ]
                },
            ]
        
        # Default generic structure
        return [
            {
                "title": "概述",
                "description": "背景与目标",
                "slides": [
                    {"type": "two_col", "title": "背景介绍", "layout": "two_col",
                     "left": {"title": "现状", "items": ["要点1", "要点2", "要点3"]},
                     "right": {"title": "挑战", "items": ["挑战1", "挑战2", "挑战3"]}},
                ]
            },
            {
                "title": "主体内容",
                "description": "核心内容展示",
                "slides": [
                    {"type": "list", "title": "主要内容", "layout": "list",
                     "items": ["内容1", "内容2", "内容3", "内容4", "内容5"]},
                ]
            },
            {
                "title": "总结",
                "description": "结论与展望",
                "slides": [
                    {"type": "grid", "title": "核心要点", "layout": "grid_4",
                     "items": [("要点1", "描述", CHAPTER_COLORS[3]), ("要点2", "描述", CHAPTER_COLORS[3]),
                              ("要点3", "描述", CHAPTER_COLORS[3]), ("要点4", "描述", CHAPTER_COLORS[3])]},
                ]
            },
        ]
    
    def build_ppt(self, outline: List[Dict[str, Any]], output_name: str = "output.pptx") -> str:
        """根据大纲构建PPT
        
        Args:
            outline: 幻灯片配置列表
            output_name: 输出文件名
            
        Returns:
            输出文件路径
        """
        builder = PPTBuilder()
        
        for slide_config in outline:
            slide_type = slide_config["type"]
            
            if slide_type == "cover":
                builder.add_cover(
                    title=slide_config["title"],
                    subtitle=slide_config.get("subtitle", ""),
                    description=slide_config.get("description", ""),
                    accent=slide_config.get("accent", CHAPTER_COLORS[1])
                )
            
            elif slide_type == "toc":
                builder.add_toc(
                    title=slide_config["title"],
                    items=slide_config["items"]
                )
            
            elif slide_type == "chapter":
                builder.add_chapter(
                    number=slide_config["number"],
                    title=slide_config["title"],
                    subtitle=slide_config.get("subtitle", ""),
                    accent=slide_config.get("accent", CHAPTER_COLORS[1])
                )
            
            elif slide_type == "two_col":
                builder.add_two_col(
                    title=slide_config["title"],
                    left_title=slide_config["left"]["title"],
                    left_items=slide_config["left"]["items"],
                    right_title=slide_config["right"]["title"],
                    right_items=slide_config["right"]["items"],
                    subtitle=slide_config.get("subtitle"),
                    left_accent=slide_config.get("left_accent", CHAPTER_COLORS[1]),
                    right_accent=slide_config.get("right_accent", CHAPTER_COLORS[2]),
                    quote=slide_config.get("quote")
                )
            
            elif slide_type == "list":
                builder.add_list(
                    title=slide_config["title"],
                    items=slide_config["items"],
                    subtitle=slide_config.get("subtitle"),
                    accent=slide_config.get("accent", CHAPTER_COLORS[1])
                )
            
            elif slide_type == "code":
                builder.add_code(
                    title=slide_config["title"],
                    code_text=slide_config["code"],
                    highlight=slide_config.get("highlight", ""),
                    subtitle=slide_config.get("subtitle"),
                    accent=slide_config.get("accent", CHAPTER_COLORS[1])
                )
            
            elif slide_type == "grid":
                builder.add_grid(
                    title=slide_config["title"],
                    items=slide_config["items"],
                    subtitle=slide_config.get("subtitle"),
                    cols=slide_config.get("cols", 4)
                )
            
            elif slide_type == "three_col":
                builder.add_three_col(
                    title=slide_config["title"],
                    cols=slide_config["cols"],
                    subtitle=slide_config.get("subtitle")
                )
            
            elif slide_type == "stats":
                builder.add_stats(
                    title=slide_config["title"],
                    left_data=slide_config.get("left"),
                    right_data=slide_config.get("right"),
                    stats=slide_config.get("stats"),
                    big_stat=slide_config.get("big_stat"),
                    subtitle=slide_config.get("subtitle")
                )
        
        output_path = os.path.join(self.output_dir, output_name)
        builder.save(output_path)
        return output_path
    
    def execute(self, prompt: str, output_name: str = "output.pptx") -> Dict[str, str]:
        """执行完整工作流
        
        Args:
            prompt: 用户Prompt
            output_name: 输出文件名
            
        Returns:
            包含输出路径和状态信息的字典
        """
        result = {
            "success": False,
            "pptx_path": "",
            "enhanced_path": "",
            "pdf_path": "",
            "message": "",
        }
        
        try:
            # Step 1: Parse prompt
            print("=" * 60)
            print("Step 1: Parsing prompt...")
            config = self.parse_prompt(prompt)
            print(f"  Title: {config['title']}")
            print(f"  Pages: {config['pages']}")
            print(f"  Style: {config['style']}")
            print(f"  Use iSlide: {config['use_islide']}")
            
            # Step 2: Generate outline
            print("\nStep 2: Generating outline...")
            outline = self.generate_outline(config)
            print(f"  Generated {len(outline)} slides")
            
            # Step 3: Build PPT
            print("\nStep 3: Building PPT...")
            pptx_path = self.build_ppt(outline, output_name)
            result["pptx_path"] = pptx_path
            print(f"  Saved: {pptx_path}")
            
            # Step 4: iSlide enhancement (if available and requested)
            if config["use_islide"]:
                print("\nStep 4: Applying iSlide enhancement...")
                if self.enhancer.check_availability():
                    enhanced_path = self.enhancer.enhance_presentation(
                        pptx_path,
                        apply_transitions=self.config["apply_transitions"],
                        apply_animations=self.config["apply_animations"],
                        export_pdf=self.config["export_pdf"],
                        output_folder=self.output_dir
                    )
                    result["enhanced_path"] = enhanced_path
                    
                    if self.config["export_pdf"]:
                        pdf_path = os.path.splitext(enhanced_path)[0] + ".pdf"
                        if os.path.exists(pdf_path):
                            result["pdf_path"] = pdf_path
                else:
                    print("  PowerPoint/iSlide not available, skipping enhancement")
                    result["message"] = "PPT generated successfully (iSlide enhancement skipped - PowerPoint not available)"
            else:
                result["message"] = "PPT generated successfully"
            
            result["success"] = True
            
        except Exception as e:
            result["message"] = f"Error: {str(e)}"
            print(f"\nError: {e}")
        
        return result


# ============================================================
# CLI Interface
# ============================================================

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PPT Workflow Automation")
    parser.add_argument("prompt", help="PPT description prompt")
    parser.add_argument("-o", "--output", default="output.pptx", help="Output filename")
    parser.add_argument("-d", "--output-dir", default="./output", help="Output directory")
    parser.add_argument("--islide", action="store_true", help="Enable iSlide enhancement")
    
    args = parser.parse_args()
    
    workflow = PPTWorkflow(output_dir=args.output_dir)
    
    if args.islide:
        args.prompt += " 使用iSlide美化"
    
    result = workflow.execute(args.prompt, args.output)
    
    print("\n" + "=" * 60)
    print("Result:")
    print(f"  Success: {result['success']}")
    print(f"  PPTX: {result['pptx_path']}")
    if result['enhanced_path']:
        print(f"  Enhanced: {result['enhanced_path']}")
    if result['pdf_path']:
        print(f"  PDF: {result['pdf_path']}")
    print(f"  Message: {result['message']}")


if __name__ == "__main__":
    main()
