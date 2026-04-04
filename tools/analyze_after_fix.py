import json
import os
import collections

data = json.load(open(
    r'C:\Users\ASUS\WorkBuddy\20260324003945\KnowledgeRAG-GZHU\RagFrontend\eslint-after-fix.json',
    encoding='utf-8'
))

errors = []
warnings = []
for f in data:
    fp = f['filePath']
    fname = fp.split('src\\')[-1] if 'src\\' in fp else os.path.basename(fp)
    for m in f['messages']:
        sev = m.get('severity', 1)
        rule = m.get('ruleId', '(parse-error)')
        line = m.get('line', 0)
        msg = m.get('message', '')
        entry = (fname, line, rule, msg)
        if sev == 2:
            errors.append(entry)
        else:
            warnings.append(entry)

print(f'Errors: {len(errors)}, Warnings: {len(warnings)}')
print()
if errors:
    print('=== ERRORS ===')
    for fname, line, rule, msg in errors:
        print(f'  [{rule}] {fname}:{line} - {msg[:80]}')
print()
print('=== Warning rules summary ===')
rc = collections.Counter(r for _,_,r,_ in warnings)
for rule, cnt in rc.most_common():
    print(f'  {cnt:4d}  {rule}')
