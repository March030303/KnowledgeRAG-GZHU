"""Auto-patch knowledgeBASE4CURD.py: wrap sort() in try-except.
Usage: python auto_patch_kb.py <path_to_knowledgeBASE4CURD.py>
"""
import sys
import re

filepath = sys.argv[1]
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already patched
if 'except (ValueError, KeyError) as e:' in content and '知识库排序失败' in content:
    print('Already patched')
    sys.exit(0)

# Pattern to match the old sort block (without try-except)
old_pattern = r'''    # 按 createdTime 降序排列
    knowledge_bases\.sort\(
        key=lambda x: datetime\.strftime\(x\["createdTime"\], "%Y-%m-%d %H:%M:%S"\),
        reverse=True,
    \)

    logger\.debug\(f"\[KB\] 加载知识库列表，共 \{len\(knowledge_bases\)\} 个"\)'''

new_block = '''    # 按 createdTime 降序排列（增加容错：跳过格式异常的条目）
    try:
        knowledge_bases.sort(
            key=lambda x: datetime.strptime(x["createdTime"], "%Y-%m-%d %H:%M:%S"),
            reverse=True,
        )
    except (ValueError, KeyError) as e:
        logger.warning(f"[KB] 知识库排序失败，使用原始顺序: {e}")

    logger.debug(f"[KB] 加载知识库列表，共 {len(knowledge_bases)} 个")'''

new_content = re.sub(old_pattern, new_block, content)

if new_content != content:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Patched successfully')
    sys.exit(0)
else:
    # Try a simpler pattern - just the sort line
    if '# 按 createdTime 降序排列' in content and 'try:' not in content[content.index('# 按 createdTime'):content.index('# 按 createdTime')+500]:
        lines = content.split('\n')
        result = []
        i = 0
        while i < len(lines):
            result.append(lines[i])
            if '# 按 createdTime 降序排列' in lines[i] and '容错' not in lines[i]:
                # Replace next block with try-except version
                # Skip the old un-wrapped sort + debug lines
                j = i + 1
                while j < len(lines) and ('knowledge_bases.sort' in lines[j] or 
                    'key=lambda' in lines[j] or 'datetime.strftime' in lines[j] or
                    'reverse=True' in lines[j] or lines[j].strip() == ')' or
                    ('logger.debug' in lines[j] and '[KB]' in lines[j])):
                    j += 1
                # Insert new wrapped version
                result.extend([
                    '    # 按 createdTime 降序排列（增加容错：跳过格式异常的条目）',
                    '    try:',
                    '        knowledge_bases.sort(',
                    "            key=lambda x: datetime.strptime(x['createdTime'], '%Y-%m-%d %H:%M:%S'),",
                    '            reverse=True,',
                    '        )',
                    '    except (ValueError, KeyError) as e:',
                    "        logger.warning(f'[KB] 知识库排序失败，使用原始顺序: {e}')",
                    '',
                    "    logger.debug(f'[KB] 加载知识库列表，共 {len(knowledge_bases)} 个')"
                ])
                i = j
                continue
            i += 1
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(result))
        print('Patched successfully (line-by-line)')
        sys.exit(0)
    
    print('WARNING: Could not find patch target, file may already be patched or has different format')
    sys.exit(1)
