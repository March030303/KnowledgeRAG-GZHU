import json
import os

data = json.load(open(
    r'C:\Users\ASUS\WorkBuddy\20260324003945\KnowledgeRAG-GZHU\RagMobile\eslint-warnings.json',
    encoding='utf-8'
))

print('=== Mobile: no-unused-vars ===')
for f in data:
    fp = f['filePath']
    fname = os.path.basename(fp)
    for m in f['messages']:
        if m.get('ruleId') == '@typescript-eslint/no-unused-vars':
            print(f'  {fname}:{m["line"]}:{m["column"]} - {m["message"]}')

print()
print('=== Mobile: no-empty ===')
for f in data:
    fp = f['filePath']
    fname = os.path.basename(fp)
    for m in f['messages']:
        if m.get('ruleId') == 'no-empty':
            print(f'  {fname}:{m["line"]}:{m["column"]} - {m["message"]}')

print()
print('=== Mobile: react-hooks/exhaustive-deps ===')
for f in data:
    fp = f['filePath']
    fname = os.path.basename(fp)
    for m in f['messages']:
        if m.get('ruleId') == 'react-hooks/exhaustive-deps':
            print(f'  {fname}:{m["line"]}:{m["column"]} - {m["message"]}')

print()
print('=== Mobile: no-explicit-any ===')
for f in data:
    fp = f['filePath']
    fname = os.path.basename(fp)
    for m in f['messages']:
        if m.get('ruleId') == '@typescript-eslint/no-explicit-any':
            print(f'  {fname}:{m["line"]}:{m["column"]}')
