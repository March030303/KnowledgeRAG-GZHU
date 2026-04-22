#!/usr/bin/env python3
"""
COM PowerPoint Automation with iSlide Integration
Directly controls PowerPoint application via COM interface
"""

import os
import sys
import time
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ensure pywin32 is available
try:
    import win32com.client
    import win32api
    import win32con
except ImportError:
    print("[ERROR] pywin32 not installed. Run: pip install pywin32")
    sys.exit(1)


class PowerPointCOM:
    """PowerPoint COM自动化控制器"""
    
    def __init__(self, office_path: str = r"C:\Program Files\Microsoft Office\root\Office16"):
        self.office_path = office_path
        self.app = None
        self.presentation = None
        self.islide_available = False
        self.islide_commands = {}
        
    def start_powerpoint(self, visible: bool = True):
        """启动PowerPoint应用"""
        try:
            print("[COM] Starting PowerPoint...")
            self.app = win32com.client.Dispatch("PowerPoint.Application")
            try:
                self.app.Visible = visible
            except:
                pass  # Visible may not be settable in some contexts
            try:
                self.app.DisplayAlerts = False
            except:
                pass
            try:
                version = self.app.Version
                print(f"[COM] PowerPoint started (Version: {version})")
            except:
                print("[COM] PowerPoint started")
            return True
        except Exception as e:
            print(f"[COM] Failed to start PowerPoint: {e}")
            traceback.print_exc()
            return False
    
    def detect_islide(self) -> bool:
        """探测iSlide插件是否安装及其命令接口"""
        if not self.app:
            print("[COM] PowerPoint not started")
            return False
        
        try:
            print("[COM] Detecting iSlide plugin...")
            
            # Method 1: Check CommandBars for iSlide controls
            try:
                for i in range(1, self.app.CommandBars.Count + 1):
                    try:
                        bar = self.app.CommandBars(i)
                        bar_name = bar.Name
                        if "iSlide" in bar_name or "islide" in bar_name.lower():
                            print(f"  [iSlide] Found CommandBar: {bar_name}")
                            self.islide_available = True
                            
                            # Enumerate controls in this bar
                            for j in range(1, bar.Controls.Count + 1):
                                try:
                                    ctrl = bar.Controls(j)
                                    print(f"    Control: {ctrl.Caption} (ID: {ctrl.Id})")
                                    self.islide_commands[ctrl.Caption] = ctrl.Id
                                except:
                                    pass
                    except:
                        pass
            except Exception as e:
                print(f"  [iSlide] CommandBar scan error: {e}")
            
            # Method 2: Check COMAddIns
            try:
                for addin in self.app.COMAddIns:
                    try:
                        addin_name = addin.Description or addin.ProgId or "Unknown"
                        if "iSlide" in addin_name or "islide" in addin_name.lower():
                            print(f"  [iSlide] Found COMAddIn: {addin_name}")
                            print(f"    ProgId: {addin.ProgId}")
                            print(f"    Connected: {addin.Connect}")
                            self.islide_available = True
                    except:
                        pass
            except Exception as e:
                print(f"  [iSlide] COMAddIns scan error: {e}")
            
            # Method 3: Check Ribbon Tabs
            try:
                # Try to access ribbon XML
                if self.presentation:
                    ribbon_xml = self.presentation.RibbonXML
                    if "iSlide" in ribbon_xml:
                        print("  [iSlide] Found in Ribbon XML")
                        self.islide_available = True
            except:
                pass
            
            if self.islide_available:
                print("[COM] iSlide plugin detected!")
            else:
                print("[COM] iSlide plugin NOT detected")
                print("  Please ensure iSlide is installed in PowerPoint")
            
            return self.islide_available
            
        except Exception as e:
            print(f"[COM] iSlide detection error: {e}")
            traceback.print_exc()
            return False
    
    def create_blank_presentation(self):
        """创建空白演示文稿"""
        if not self.app:
            if not self.start_powerpoint():
                return False
        
        try:
            print("[COM] Creating blank presentation...")
            self.presentation = self.app.Presentations.Add()
            
            # Set 16:9 aspect ratio
            self.presentation.PageSetup.SlideWidth = 720  # 13.333 inches in points
            self.presentation.PageSetup.SlideHeight = 540  # 7.5 inches in points
            
            print("[COM] Blank presentation created")
            return True
        except Exception as e:
            print(f"[COM] Failed to create presentation: {e}")
            traceback.print_exc()
            return False
    
    def open_presentation(self, filepath: str):
        """打开现有PPT文件"""
        if not self.app:
            if not self.start_powerpoint():
                return False
        
        try:
            abs_path = os.path.abspath(filepath)
            print(f"[COM] Opening: {abs_path}")
            self.presentation = self.app.Presentations.Open(abs_path)
            print("[COM] Presentation opened")
            return True
        except Exception as e:
            print(f"[COM] Failed to open presentation: {e}")
            traceback.print_exc()
            return False
    
    def add_slide(self, layout_index: int = 12) -> Any:
        """添加幻灯片
        
        Args:
            layout_index: PowerPoint layout index (12 = blank)
        """
        if not self.presentation:
            print("[COM] No presentation open")
            return None
        
        try:
            slide = self.presentation.Slides.Add(
                self.presentation.Slides.Count + 1,
                layout_index
            )
            return slide
        except Exception as e:
            print(f"[COM] Failed to add slide: {e}")
            return None
    
    def set_slide_background(self, slide, color_rgb: tuple):
        """设置幻灯片背景色"""
        try:
            r, g, b = color_rgb
            # PowerPoint uses RGB in a specific format
            rgb_value = r + (g << 8) + (b << 16)
            
            slide.FollowMasterBackground = False
            background = slide.Background
            fill = background.Fill
            fill.Solid()
            fill.ForeColor.RGB = rgb_value
        except Exception as e:
            print(f"[COM] Background error: {e}")
    
    def add_textbox(self, slide, left: float, top: float, 
                   width: float, height: float,
                   text: str, font_size: int = 18,
                   bold: bool = False,
                   color_rgb: tuple = (255, 255, 255),
                   font_name: str = "Microsoft YaHei"):
        """添加文本框"""
        try:
            # Convert inches to points (1 inch = 72 points)
            left_pt = left * 72
            top_pt = top * 72
            width_pt = width * 72
            height_pt = height * 72
            
            shape = slide.Shapes.AddTextbox(
                1,  # msoTextOrientationHorizontal
                left_pt, top_pt, width_pt, height_pt
            )
            
            text_frame = shape.TextFrame
            text_frame.TextRange.Text = text
            text_frame.TextRange.Font.Size = font_size
            text_frame.TextRange.Font.Bold = bold
            text_frame.TextRange.Font.Name = font_name
            
            r, g, b = color_rgb
            text_frame.TextRange.Font.Color.RGB = r + (g << 8) + (b << 16)
            
            return shape
        except Exception as e:
            print(f"[COM] Textbox error: {e}")
            return None
    
    def add_shape(self, slide, shape_type: int,
                 left: float, top: float, 
                 width: float, height: float,
                 fill_rgb: tuple = (30, 30, 36),
                 line_rgb: Optional[tuple] = None):
        """添加形状"""
        try:
            left_pt = left * 72
            top_pt = top * 72
            width_pt = width * 72
            height_pt = height * 72
            
            shape = slide.Shapes.AddShape(
                shape_type,
                left_pt, top_pt, width_pt, height_pt
            )
            
            # Fill
            r, g, b = fill_rgb
            shape.Fill.Solid()
            shape.Fill.ForeColor.RGB = r + (g << 8) + (b << 16)
            
            # Line
            if line_rgb:
                r, g, b = line_rgb
                shape.Line.Visible = True
                shape.Line.ForeColor.RGB = r + (g << 8) + (b << 16)
                shape.Line.Weight = 1
            else:
                shape.Line.Visible = False
            
            return shape
        except Exception as e:
            print(f"[COM] Shape error: {e}")
            return None
    
    def try_islide_uniform(self):
        """尝试调用iSlide一键统一设计"""
        if not self.islide_available:
            print("[iSlide] Not available")
            return False
        
        try:
            print("[iSlide] Trying to apply uniform design...")
            
            # Try known iSlide command names
            commands = [
                "iSlideDesignUniform",
                "iSlide.Uniform",
                "iSlide_OneKey_Uniform",
                "iSlideDesign",
            ]
            
            for cmd in commands:
                try:
                    self.app.CommandBars.ExecuteMso(cmd)
                    print(f"  [iSlide] Success: {cmd}")
                    time.sleep(2)
                    return True
                except Exception as e:
                    print(f"  [iSlide] Failed: {cmd} - {e}")
            
            # Try by control ID
            for caption, ctrl_id in self.islide_commands.items():
                if "统一" in caption or "uniform" in caption.lower() or "设计" in caption:
                    try:
                        self.app.CommandBars.FindControl(ID=ctrl_id).Execute()
                        print(f"  [iSlide] Success via ID: {caption} ({ctrl_id})")
                        time.sleep(2)
                        return True
                    except:
                        pass
            
            print("[iSlide] Could not find uniform design command")
            return False
            
        except Exception as e:
            print(f"[iSlide] Uniform design error: {e}")
            return False
    
    def try_islide_icon(self):
        """尝试调用iSlide图标库"""
        if not self.islide_available:
            return False
        
        try:
            print("[iSlide] Trying to open icon library...")
            commands = [
                "iSlideIcon",
                "iSlide.Icon",
                "iSlide_Library_Icon",
            ]
            
            for cmd in commands:
                try:
                    self.app.CommandBars.ExecuteMso(cmd)
                    print(f"  [iSlide] Success: {cmd}")
                    return True
                except:
                    pass
            
            return False
        except Exception as e:
            print(f"[iSlide] Icon error: {e}")
            return False
    
    def apply_transitions(self, transition_type: int = 9):
        """应用幻灯片切换效果"""
        if not self.presentation:
            return
        
        try:
            print(f"[COM] Applying transitions (type: {transition_type})...")
            for slide in self.presentation.Slides:
                slide.SlideShowTransition.EntryEffect = transition_type
                slide.SlideShowTransition.Duration = 0.6
            print("[COM] Transitions applied")
        except Exception as e:
            print(f"[COM] Transition error: {e}")
    
    def save(self, filepath: str):
        """保存演示文稿"""
        if not self.presentation:
            return False
        
        try:
            abs_path = os.path.abspath(filepath)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            self.presentation.SaveAs(abs_path)
            print(f"[COM] Saved: {abs_path}")
            return True
        except Exception as e:
            print(f"[COM] Save error: {e}")
            traceback.print_exc()
            return False
    
    def close(self):
        """关闭演示文稿"""
        if self.presentation:
            try:
                self.presentation.Close()
                self.presentation = None
            except:
                pass
    
    def quit(self):
        """退出PowerPoint"""
        self.close()
        if self.app:
            try:
                self.app.Quit()
                self.app = None
                print("[COM] PowerPoint closed")
            except:
                pass
    
    def export_pdf(self, pdf_path: str):
        """导出为PDF"""
        if not self.presentation:
            return False
        
        try:
            abs_path = os.path.abspath(pdf_path)
            # 32 = ppSaveAsPDF
            self.presentation.SaveAs(abs_path, 32)
            print(f"[COM] PDF exported: {abs_path}")
            return True
        except Exception as e:
            print(f"[COM] PDF export error: {e}")
            return False


def create_ppt_with_com(output_path: str = r"D:\KnowledgeRAG-GZHU-Backup\slides\ASF-RAG-COM.pptx"):
    """使用COM自动化创建PPT"""
    
    ppt = PowerPointCOM()
    
    try:
        # Start PowerPoint
        if not ppt.start_powerpoint(visible=True):
            return False
        
        # Create blank presentation
        if not ppt.create_blank_presentation():
            return False
        
        # Detect iSlide
        ppt.detect_islide()
        
        # ============================================================
        # Slide 1: Cover
        # ============================================================
        print("\n[Build] Creating Slide 1: Cover")
        slide1 = ppt.add_slide()
        ppt.set_slide_background(slide1, (18, 18, 23))  # #121217
        
        ppt.add_textbox(slide1, 0, 2.5, 13.333, 1.5,
                       "ASF-RAG", 72, True, (168, 85, 247))
        ppt.add_textbox(slide1, 0, 4.2, 13.333, 0.8,
                       "智能知识管理平台", 32, False, (229, 231, 235))
        ppt.add_textbox(slide1, 0, 5.0, 13.333, 0.6,
                       "基于检索增强生成（RAG）的私有化知识中枢", 20, False, (156, 163, 175))
        
        # Neon line
        ppt.add_shape(slide1, 1, 5.5, 5.8, 2.333, 0.05,
                     fill_rgb=(168, 85, 247))
        
        # ============================================================
        # Slide 2: TOC
        # ============================================================
        print("[Build] Creating Slide 2: TOC")
        slide2 = ppt.add_slide()
        ppt.set_slide_background(slide2, (18, 18, 23))
        
        ppt.add_textbox(slide2, 0.5, 0.4, 12, 0.8,
                       "目录", 36, True, (255, 255, 255))
        
        toc_items = [
            ("01", "项目综述", "定位、架构与技术栈全景", (168, 85, 247)),
            ("02", "核心功能", "RAG引擎、知识库、Agent与检索", (52, 211, 153)),
            ("03", "工程实现", "源码解析、配置与部署方案", (251, 146, 60)),
            ("04", "测试验证", "检索质量与生成效果评估", (96, 165, 250)),
        ]
        
        for i, (num, title, desc, color) in enumerate(toc_items):
            row = i // 2
            col = i % 2
            x = 0.5 + col * 6.2
            y = 1.5 + row * 2.6
            
            ppt.add_shape(slide2, 5, x, y, 5.8, 2.2,
                         fill_rgb=(30, 30, 36), line_rgb=color)
            ppt.add_textbox(slide2, x + 0.2, y + 0.15, 1.5, 0.8,
                           num, 48, True, color)
            ppt.add_textbox(slide2, x + 0.2, y + 0.9, 5.4, 0.5,
                           title, 24, True, (255, 255, 255))
            ppt.add_textbox(slide2, x + 0.2, y + 1.4, 5.4, 0.5,
                           desc, 14, False, (156, 163, 175))
        
        # ============================================================
        # Slide 3: Chapter 1
        # ============================================================
        print("[Build] Creating Slide 3: Chapter 1")
        slide3 = ppt.add_slide()
        ppt.set_slide_background(slide3, (18, 18, 23))
        
        ppt.add_textbox(slide3, 0, 1.5, 13.333, 2.5,
                       "01", 180, True, (48, 48, 48))
        ppt.add_textbox(slide3, 0, 3.0, 13.333, 1.0,
                       "项目综述", 56, True, (255, 255, 255))
        ppt.add_shape(slide3, 1, 5.8, 4.0, 1.733, 0.05,
                     fill_rgb=(168, 85, 247))
        ppt.add_textbox(slide3, 0, 4.3, 13.333, 0.6,
                       "定位、架构与技术栈全景", 20, False, (156, 163, 175))
        
        # ============================================================
        # Slide 4: Content - Two Col
        # ============================================================
        print("[Build] Creating Slide 4: Content")
        slide4 = ppt.add_slide()
        ppt.set_slide_background(slide4, (18, 18, 23))
        
        ppt.add_textbox(slide4, 0.5, 0.3, 12, 0.7,
                       "项目定位", 32, True, (255, 255, 255))
        ppt.add_shape(slide4, 1, 0.5, 0.95, 2, 0.03,
                     fill_rgb=(168, 85, 247))
        
        # Left card
        ppt.add_shape(slide4, 5, 0.5, 1.5, 5.8, 4.5,
                     fill_rgb=(30, 30, 36), line_rgb=(168, 85, 247))
        ppt.add_textbox(slide4, 0.7, 1.65, 5.4, 0.5,
                       "核心定位", 20, True, (168, 85, 247))
        
        left_items = ["防幻觉问答系统", "私有化知识中枢", "个人与团队的可靠AI助手"]
        for i, item in enumerate(left_items):
            ppt.add_textbox(slide4, 0.7, 2.3 + i * 0.5, 5.4, 0.4,
                           f"▸  {item}", 14, False, (229, 231, 235))
        
        # Right card
        ppt.add_shape(slide4, 5, 6.8, 1.5, 5.8, 4.5,
                     fill_rgb=(30, 30, 36), line_rgb=(52, 211, 153))
        ppt.add_textbox(slide4, 7.0, 1.65, 5.4, 0.5,
                       "核心价值", 20, True, (52, 211, 153))
        
        right_items = ["每处信息可追溯原文出处", "深度理解用户私有文档", "多知识库联动检索"]
        for i, item in enumerate(right_items):
            ppt.add_textbox(slide4, 7.0, 2.3 + i * 0.5, 5.4, 0.4,
                           f"▸  {item}", 14, False, (229, 231, 235))
        
        # ============================================================
        # Try iSlide enhancement
        # ============================================================
        if ppt.islide_available:
            print("\n[iSlide] Applying enhancements...")
            ppt.try_islide_uniform()
        
        # Apply transitions
        ppt.apply_transitions(9)  # Fade
        
        # Save
        ppt.save(output_path)
        
        # Export PDF
        pdf_path = os.path.splitext(output_path)[0] + ".pdf"
        ppt.export_pdf(pdf_path)
        
        print(f"\n[SUCCESS] PPT created: {output_path}")
        print(f"[SUCCESS] PDF exported: {pdf_path}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        traceback.print_exc()
        return False
        
    finally:
        ppt.quit()


if __name__ == "__main__":
    print("=" * 60)
    print("PowerPoint COM Automation with iSlide")
    print("=" * 60)
    
    output = r"D:\KnowledgeRAG-GZHU-Backup\slides\ASF-RAG-COM.pptx"
    create_ppt_with_com(output)
