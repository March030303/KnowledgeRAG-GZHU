#!/usr/bin/env python3
"""
Open PPT in PowerPoint for manual editing with iSlide
"""

import os
import sys
import subprocess

# Path to the PPT file
pptx_path = r"D:\KnowledgeRAG-GZHU-Backup\slides\ASF-RAG-Complete.pptx"

# Path to PowerPoint
powerpoint_path = r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"

if not os.path.exists(pptx_path):
    print(f"[ERROR] PPT file not found: {pptx_path}")
    sys.exit(1)

if not os.path.exists(powerpoint_path):
    print(f"[ERROR] PowerPoint not found: {powerpoint_path}")
    # Try to find PowerPoint
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\POWERPNT.EXE")
        powerpoint_path, _ = winreg.QueryValueEx(key, None)
        print(f"[INFO] Found PowerPoint via registry: {powerpoint_path}")
    except:
        print("[ERROR] Could not find PowerPoint installation")
        sys.exit(1)

print("=" * 60)
print("Opening PowerPoint with ASF-RAG Presentation")
print("=" * 60)
print(f"File: {pptx_path}")
print(f"PowerPoint: {powerpoint_path}")
print()
print("You can now:")
print("  1. Apply iSlide designs manually")
print("  2. Edit content as needed")
print("  3. Save when done")
print()

# Open PowerPoint with the file
try:
    subprocess.Popen([powerpoint_path, pptx_path], shell=True)
    print("[SUCCESS] PowerPoint launched!")
except Exception as e:
    print(f"[ERROR] Failed to open: {e}")
    # Fallback: use os.startfile
    try:
        os.startfile(pptx_path)
        print("[SUCCESS] Opened via os.startfile")
    except Exception as e2:
        print(f"[ERROR] Fallback also failed: {e2}")
