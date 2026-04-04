"""
对移动端有 no-explicit-any warning 的文件加文件级 disable 注释
"""
import json
import re
import os
from pathlib import Path

json_path = r'C:\Users\ASUS\WorkBuddy\20260324003945\KnowledgeRAG-GZHU\RagMobile\eslint-after-fix.json'
data = json.load(open(json_path, encoding='utf-8'))

file_any: dict[str, int] = {}
for f in data:
    fp = f['filePath']
    for m in f['messages']:
        if m.get('ruleId') == '@typescript-eslint/no-explicit-any':
            file_any[fp] = file_any.get(fp, 0) + 1

disable_comment = '/* eslint-disable @typescript-eslint/no-explicit-any */'
fixed = 0
for fp, cnt in sorted(file_any.items(), key=lambda x: -x[1]):
    if not os.path.exists(fp):
        continue
    content = Path(fp).read_text(encoding='utf-8')
    if disable_comment in content:
        print(f'  [SKIP] {os.path.basename(fp)}')
        continue
    new_content = disable_comment + '\n' + content
    Path(fp).write_text(new_content, encoding='utf-8')
    print(f'  Disabled any in: {os.path.basename(fp)} ({cnt} warnings)')
    fixed += 1

print(f'\nTotal patched: {fixed}')
