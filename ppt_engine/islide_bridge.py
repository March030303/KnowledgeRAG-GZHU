#!/usr/bin/env python3
"""
iSlide Bridge - Standalone script to apply iSlide enhancements to existing PPT
Run this on your local machine with PowerPoint and iSlide installed
"""

import os
import sys
import time
from pathlib import Path

def apply_islide_to_pptx(input_path: str, output_path: str = None):
    """
    Apply iSlide enhancements to an existing PPTX file
    
    This script must be run on a Windows machine with:
    - Microsoft PowerPoint installed
    - iSlide plugin installed
    
    Usage:
        python islide_bridge.py "input.pptx" ["output.pptx"]
    """
    
    try:
        import win32com.client
    except ImportError:
        print("[ERROR] pywin32 not installed. Run: pip install pywin32")
        return False
    
    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        print(f"[ERROR] File not found: {input_path}")
        return False
    
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_islide{ext}"
    output_path = os.path.abspath(output_path)
    
    print("=" * 60)
    print("iSlide Bridge - PPT Enhancement Tool")
    print("=" * 60)
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print()
    
    app = None
    presentation = None
    
    try:
        # Start PowerPoint
        print("[1/5] Starting PowerPoint...")
        app = win32com.client.Dispatch("PowerPoint.Application")
        try:
            app.Visible = True
        except:
            pass
        print("      PowerPoint started")
        
        # Open presentation
        print("[2/5] Opening presentation...")
        presentation = app.Presentations.Open(input_path)
        print(f"      Opened: {len(presentation.Slides)} slides")
        
        # Detect iSlide
        print("[3/5] Detecting iSlide plugin...")
        islide_found = False
        islide_commands = {}
        
        # Check COMAddIns
        try:
            for addin in app.COMAddIns:
                name = addin.Description or addin.ProgId or ""
                if "iSlide" in name or "islide" in name.lower():
                    print(f"      Found iSlide AddIn: {name}")
                    print(f"      ProgId: {addin.ProgId}")
                    print(f"      Connected: {addin.Connect}")
                    islide_found = True
        except Exception as e:
            print(f"      AddIn check error: {e}")
        
        # Check CommandBars
        try:
            for i in range(1, app.CommandBars.Count + 1):
                try:
                    bar = app.CommandBars(i)
                    if "iSlide" in bar.Name or "islide" in bar.Name.lower():
                        print(f"      Found CommandBar: {bar.Name}")
                        islide_found = True
                        for j in range(1, bar.Controls.Count + 1):
                            try:
                                ctrl = bar.Controls(j)
                                islide_commands[ctrl.Caption] = ctrl.Id
                                print(f"        - {ctrl.Caption} (ID: {ctrl.Id})")
                            except:
                                pass
                except:
                    pass
        except Exception as e:
            print(f"      CommandBar check error: {e}")
        
        if not islide_found:
            print("      [WARNING] iSlide not detected!")
            print("      Please ensure iSlide is installed in PowerPoint")
        else:
            print("      iSlide detected!")
        
        # Apply iSlide enhancements
        if islide_found:
            print("[4/5] Applying iSlide enhancements...")
            
            # Try to execute iSlide commands
            success_count = 0
            
            # Try known command names
            commands_to_try = [
                "iSlideDesignUniform",
                "iSlide.Uniform", 
                "iSlide_OneKey_Uniform",
                "iSlideDesign",
                "iSlide.OneKey.Uniform",
            ]
            
            for cmd in commands_to_try:
                try:
                    app.CommandBars.ExecuteMso(cmd)
                    print(f"      Success: {cmd}")
                    success_count += 1
                    time.sleep(3)  # Wait for iSlide to process
                    break
                except Exception as e:
                    print(f"      Failed: {cmd}")
            
            # Try by control ID
            if success_count == 0:
                for caption, ctrl_id in islide_commands.items():
                    if any(kw in caption for kw in ["统一", "Uniform", "设计", "Design"]):
                        try:
                            app.CommandBars.FindControl(ID=ctrl_id).Execute()
                            print(f"      Success via ID: {caption}")
                            success_count += 1
                            time.sleep(3)
                            break
                        except:
                            pass
            
            if success_count == 0:
                print("      [WARNING] Could not execute iSlide commands automatically")
                print("      Please apply iSlide enhancements manually in PowerPoint")
                print("      The PPT is now open - press Enter when done...")
                input()
        else:
            print("[4/5] Skipping iSlide enhancements (not available)")
        
        # Apply PowerPoint transitions
        print("[5/5] Applying transitions...")
        try:
            for slide in presentation.Slides:
                slide.SlideShowTransition.EntryEffect = 9  # Fade
                slide.SlideShowTransition.Duration = 0.6
            print("      Transitions applied")
        except Exception as e:
            print(f"      Transition error: {e}")
        
        # Save
        print("\nSaving...")
        presentation.SaveAs(output_path)
        print(f"Saved: {output_path}")
        
        # Export PDF
        pdf_path = os.path.splitext(output_path)[0] + ".pdf"
        try:
            presentation.SaveAs(pdf_path, 32)  # ppSaveAsPDF
            print(f"PDF: {pdf_path}")
        except Exception as e:
            print(f"PDF export error: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if presentation:
            try:
                presentation.Close()
            except:
                pass
        if app:
            try:
                app.Quit()
            except:
                pass
        print("\nPowerPoint closed")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python islide_bridge.py <input.pptx> [output.pptx]")
        print("Example: python islide_bridge.py ASF-RAG.pptx ASF-RAG-enhanced.pptx")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = apply_islide_to_pptx(input_file, output_file)
    sys.exit(0 if success else 1)
