import json
import os
import collections

for label, path in [
    ('frontend', r'C:\Users\ASUS\WorkBuddy\20260324003945\KnowledgeRAG-GZHU\RagFrontend\eslint-after-fix2.json'),
    ('mobile',   r'C:\Users\ASUS\WorkBuddy\20260324003945\KnowledgeRAG-GZHU\RagMobile\eslint-after-fix.json'),
]:
    data = json.load(open(path, encoding='utf-8'))
    errors = 0
    warnings = 0
    rule_counter = collections.Counter()
    for f in data:
        for m in f['messages']:
            sev = m.get('severity', 1)
            rule = m.get('ruleId') or '(parse-error)'
            if sev == 2:
                errors += 1
            else:
                warnings += 1
            rule_counter[rule] += 1
    print(f'=== {label}: {errors} errors, {warnings} warnings ===')
    for rule, cnt in rule_counter.most_common(15):
        sev_sym = 'E' if any(
            m.get('severity') == 2 and (m.get('ruleId') or '') == rule
            for f in data for m in f['messages']
        ) else 'W'
        print(f'  {sev_sym} {cnt:4d}  {rule}')
    print()
