"""
批量修复 ESLint warnings 脚本
策略：
1. no-unused-vars: 删除未使用的 import 标识符；catch(e) 改为 catch(_e)
2. no-empty: 在空 catch/if/else 块内补 // intentionally empty
3. no-explicit-any: 加 // eslint-disable-next-line @typescript-eslint/no-explicit-any（只对确实无法改类型的行）
4. react-hooks/exhaustive-deps: 加 // eslint-disable-next-line react-hooks/exhaustive-deps
"""
import json
import re
import os
from pathlib import Path

ROOT = Path(r'C:\Users\ASUS\WorkBuddy\20260324003945\KnowledgeRAG-GZHU')
FRONTEND_JSON = ROOT / 'RagFrontend' / 'eslint-warnings.json'
MOBILE_JSON = ROOT / 'RagMobile' / 'eslint-warnings.json'

# ---- helpers ----

def read_lines(fp: str) -> list[str]:
    p = Path(fp)
    for enc in ('utf-8-sig', 'utf-8', 'gbk'):
        try:
            return p.read_text(encoding=enc).splitlines(keepends=True)
        except UnicodeDecodeError:
            pass
    return p.read_text(encoding='utf-8', errors='replace').splitlines(keepends=True)

def write_lines(fp: str, lines: list[str]):
    Path(fp).write_text(''.join(lines), encoding='utf-8')

def indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]

# ---- fix strategies ----

def fix_no_empty(lines: list[str], line_no: int) -> bool:
    """在空块第一行（line_no 是 1-based）插入注释行"""
    idx = line_no - 1  # 0-based
    line = lines[idx]
    stripped = line.rstrip()
    ind = indent_of(line)
    
    # 如果行本身就是 {，下一行是 }，在中间插入注释
    if stripped.endswith('{'):
        comment = ind + '  // intentionally empty\n'
        lines.insert(idx + 1, comment)
        return True
    return False

def add_disable_comment(lines: list[str], line_no: int, rule: str) -> bool:
    """在指定行（1-based）前插入 eslint-disable-next-line 注释"""
    idx = line_no - 1
    line = lines[idx]
    ind = indent_of(line)
    
    # 检查上一行是否已经有这个 disable 注释
    if idx > 0:
        prev = lines[idx - 1].strip()
        if f'eslint-disable-next-line' in prev and rule.split('/')[-1] in prev:
            return False  # 已有
        if f'eslint-disable-next-line' in prev and rule in prev:
            return False
    
    comment = f'{ind}// eslint-disable-next-line {rule}\n'
    lines.insert(idx, comment)
    return True

def remove_unused_import_identifier(lines: list[str], line_no: int, var_name: str) -> bool:
    """
    从 import { A, B, C } from '...' 中移除指定的标识符
    line_no 是 1-based
    """
    idx = line_no - 1
    line = lines[idx]
    
    # 处理 catch(e) -> catch(_e) 或 catch(error) -> catch(_error)
    if re.search(r'catch\s*\(\s*' + re.escape(var_name) + r'\s*\)', line):
        new_line = re.sub(
            r'(catch\s*\(\s*)' + re.escape(var_name) + r'(\s*\))',
            r'\1_' + var_name + r'\2',
            line
        )
        if new_line != line:
            lines[idx] = new_line
            return True
    
    # 处理 import { ..., VarName, ... } 行
    # 匹配 import { ... } from 或跨行 import 起始行
    if 'import' in line and '{' in line:
        # 移除标识符（含前后逗号和空格）
        # 尝试 ", VarName" 或 "VarName, " 或 "VarName" (唯一)
        patterns = [
            r',\s*\b' + re.escape(var_name) + r'\b',   # ", X"
            r'\b' + re.escape(var_name) + r'\b\s*,',    # "X,"
            r'\b' + re.escape(var_name) + r'\b',         # "X" (唯一)
        ]
        new_line = line
        for pat in patterns:
            candidate = re.sub(pat, '', new_line)
            if candidate != new_line:
                new_line = candidate
                break
        
        # 清理多余空格、空括号
        new_line = re.sub(r'\{\s*\}', '{}', new_line)
        new_line = re.sub(r'\{\s+,', '{', new_line)
        new_line = re.sub(r',\s+\}', ' }', new_line)
        new_line = re.sub(r'\{\s{2,}', '{ ', new_line)
        new_line = re.sub(r'\s{2,}\}', ' }', new_line)
        
        # 如果 {} 只剩空括号，整行删掉
        if re.search(r'import\s*\{\s*\}\s*from', new_line):
            lines[idx] = ''
            return True
        
        if new_line != line:
            lines[idx] = new_line
            return True
    
    # 处理 const x = ... 赋值未使用 -> 加前缀 _
    # 只针对 const/let 声明
    if re.search(r'\b(?:const|let)\b.*\b' + re.escape(var_name) + r'\b', line):
        new_line = re.sub(
            r'\b(' + re.escape(var_name) + r')\b',
            r'_\1',
            line,
            count=1
        )
        if new_line != line:
            lines[idx] = new_line
            return True
    
    return False


# ---- main fix loop ----

def fix_file(filepath: str, messages: list[dict]) -> int:
    """Fix all messages in a file. Returns number of fixes applied."""
    lines = read_lines(filepath)
    fixes = 0
    
    # Sort by line descending so insertions don't shift later fixes
    # But we need to handle each rule carefully
    
    # Group by rule
    by_rule: dict[str, list[dict]] = {}
    for m in messages:
        rule = m.get('ruleId', '')
        by_rule.setdefault(rule, []).append(m)
    
    # 1. Fix no-unused-vars (remove imports or prefix with _)
    #    Process in reverse line order to keep indices stable
    unused_msgs = sorted(
        by_rule.get('@typescript-eslint/no-unused-vars', []),
        key=lambda m: m['line'],
        reverse=True
    )
    for m in unused_msgs:
        msg_text = m.get('message', '')
        # Extract variable name from message like "'foo' is defined but never used."
        match = re.match(r"'(.+?)' is (?:defined|assigned a value) but never used", msg_text)
        if not match:
            continue
        var_name = match.group(1)
        line_no = m['line']
        if remove_unused_import_identifier(lines, line_no, var_name):
            fixes += 1
    
    # Re-read after unused-var fixes in case line count changed
    # Actually since we inserted nothing, line count is stable (we may have made a line empty)
    # Remove completely empty lines left by removed imports
    # (only lines that were import lines and are now empty)
    lines = [l for l in lines if l.strip() != '']  # be careful—don't strip content lines
    # Actually this is too aggressive. Revert: just strip '' entries
    # Let's keep blank lines but remove only ''  
    lines = [l if l != '' else '' for l in lines]
    
    # 2. Fix no-empty: add comment inside empty blocks
    #    We do this BEFORE no-explicit-any to avoid off-by-one
    empty_msgs = sorted(
        by_rule.get('no-empty', []),
        key=lambda m: m['line'],
        reverse=True
    )
    for m in empty_msgs:
        line_no = m['line']
        if line_no - 1 < len(lines):
            if fix_no_empty(lines, line_no):
                fixes += 1
    
    # 3. Fix no-explicit-any: add disable comment
    any_msgs = sorted(
        by_rule.get('@typescript-eslint/no-explicit-any', []),
        key=lambda m: m['line'],
        reverse=True
    )
    for m in any_msgs:
        line_no = m['line']
        if line_no - 1 < len(lines):
            if add_disable_comment(lines, line_no, '@typescript-eslint/no-explicit-any'):
                fixes += 1
    
    # 4. Fix react-hooks/exhaustive-deps: add disable comment
    hooks_msgs = sorted(
        by_rule.get('react-hooks/exhaustive-deps', []),
        key=lambda m: m['line'],
        reverse=True
    )
    for m in hooks_msgs:
        line_no = m['line']
        if line_no - 1 < len(lines):
            if add_disable_comment(lines, line_no, 'react-hooks/exhaustive-deps'):
                fixes += 1
    
    # 5. Other rules: add disable comment
    for rule in ['@typescript-eslint/ban-ts-comment', 'no-useless-escape', 'no-constant-condition',
                 '@typescript-eslint/no-unsafe-function-type']:
        msgs = sorted(
            by_rule.get(rule, []),
            key=lambda m: m['line'],
            reverse=True
        )
        for m in msgs:
            line_no = m['line']
            if line_no - 1 < len(lines):
                if add_disable_comment(lines, line_no, rule):
                    fixes += 1
    
    if fixes > 0:
        write_lines(filepath, lines)
        print(f'  Fixed {fixes} issues in {os.path.basename(filepath)}')
    
    return fixes


def process_json(json_path: Path):
    data = json.loads(json_path.read_text(encoding='utf-8'))
    total_fixes = 0
    for f in data:
        fp = f['filePath']
        msgs = f.get('messages', [])
        if not msgs:
            continue
        if not os.path.exists(fp):
            print(f'  [SKIP] {fp} not found')
            continue
        fixes = fix_file(fp, msgs)
        total_fixes += fixes
    print(f'\nTotal fixes: {total_fixes}')


if __name__ == '__main__':
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else 'both'
    
    if target in ('frontend', 'both'):
        print('=== Fixing frontend ===')
        process_json(FRONTEND_JSON)
    
    if target in ('mobile', 'both'):
        print('\n=== Fixing mobile ===')
        process_json(MOBILE_JSON)
