#!/usr/bin/env python3
"""
人物出场顺序及时间线验证脚本
Verify character appearances and timeline consistency across all chapters
"""

import re
import os
from datetime import datetime
from collections import defaultdict
import json

# 主要人物列表
MAIN_CHARACTERS = {
    '林深': {'first_expected': 1, 'role': '男主角'},
    '苏晚': {'first_expected': 4, 'role': '女主角'},  # 第4章标题即为"调查员苏晚"
    '林雨': {'first_expected': 1, 'role': '妹妹'},
    '赵医生': {'first_expected': 1, 'role': '复杂角色'},
    '赵启明': {'first_expected': None, 'role': '赵医生的真名'},
    '陈煜': {'first_expected': 1, 'role': '主要反派'},
    '李明': {'first_expected': 31, 'role': '反派,永生会创始人'},  # 第31章"永生会现身"
    '周明': {'first_expected': 51, 'role': '终极BOSS'},  # 第51章"父亲的秘密"
    '韩世杰': {'first_expected': None, 'role': '警局长'},
    '韩江': {'first_expected': 5, 'role': '地下医生'},  # 第5章出现
    '沈微': {'first_expected': 8, 'role': '神秘女子'},  # 第8章出现
    '宋文博': {'first_expected': None, 'role': '记忆技术天才'},
}

# 时间线格式
TIMELINE_PATTERN = r'\*\*时间\*\*[：:]\s*(\d+月\d+日|12月\d+日)[（(](.+?)[）)]?\s*(\d+:\d+)?'

def extract_chapter_number(filename):
    """从文件名提取章节号"""
    match = re.search(r'chapter_(\d+)\.md', filename)
    if match:
        return int(match.group(1))
    return None

def extract_time_markers(content):
    """提取章节中的时间标记"""
    times = []
    for match in re.finditer(TIMELINE_PATTERN, content):
        date_str = match.group(1)
        weekday = match.group(2) if match.group(2) else ''
        time_str = match.group(3) if match.group(3) else ''
        times.append({
            'date': date_str,
            'weekday': weekday,
            'time': time_str,
            'full_text': match.group(0)
        })
    return times

def find_character_mentions(content, character_name):
    """查找人物在文本中的提及次数和位置"""
    mentions = []
    # 查找人物名字（完整匹配）
    for match in re.finditer(re.escape(character_name), content):
        context_start = max(0, match.start() - 50)
        context_end = min(len(content), match.end() + 50)
        context = content[context_start:context_end]
        mentions.append({
            'position': match.start(),
            'context': context.strip()
        })
    return mentions

def analyze_chapter(chapter_file):
    """分析单个章节"""
    chapter_num = extract_chapter_number(chapter_file)
    if not chapter_num:
        return None
    
    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取章节标题
    title_match = re.search(r'^#\s*第\d+章[：:]\s*(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "未知标题"
    
    # 提取时间标记
    time_markers = extract_time_markers(content)
    
    # 检查人物出场
    character_appearances = {}
    for char_name in MAIN_CHARACTERS:
        mentions = find_character_mentions(content, char_name)
        if mentions:
            character_appearances[char_name] = len(mentions)
    
    return {
        'chapter_num': chapter_num,
        'title': title,
        'time_markers': time_markers,
        'characters': character_appearances,
        'file': chapter_file
    }

def verify_timeline_consistency(chapters_data):
    """验证时间线一致性"""
    issues = []
    
    # 按章节号排序
    sorted_chapters = sorted(chapters_data, key=lambda x: x['chapter_num'])
    
    prev_date = None
    prev_time = None
    
    for chapter in sorted_chapters:
        if not chapter['time_markers']:
            issues.append({
                'type': 'warning',
                'chapter': chapter['chapter_num'],
                'title': chapter['title'],
                'message': '本章没有明确的时间标记'
            })
            continue
        
        # 检查时间是否倒流
        for marker in chapter['time_markers']:
            date_str = marker['date']
            time_str = marker['time']
            
            # 简单的日期比较（基于12月）
            if date_str.startswith('12月'):
                day_match = re.search(r'12月(\d+)日', date_str)
                if day_match:
                    current_day = int(day_match.group(1))
                    
                    if prev_date:
                        prev_day = int(re.search(r'12月(\d+)日', prev_date).group(1))
                        if current_day < prev_day:
                            issues.append({
                                'type': 'error',
                                'chapter': chapter['chapter_num'],
                                'title': chapter['title'],
                                'message': f'时间倒流: 从{prev_date}到{date_str}'
                            })
            
            prev_date = date_str
            prev_time = time_str
    
    return issues

def verify_character_first_appearances(chapters_data):
    """验证人物首次出场是否符合预期"""
    issues = []
    
    # 收集每个人物的首次出场
    first_appearances = {}
    for chapter in sorted(chapters_data, key=lambda x: x['chapter_num']):
        for char_name in chapter['characters']:
            if char_name not in first_appearances:
                first_appearances[char_name] = chapter['chapter_num']
    
    # 检查是否符合预期
    for char_name, char_info in MAIN_CHARACTERS.items():
        expected_first = char_info.get('first_expected')
        actual_first = first_appearances.get(char_name)
        
        if expected_first is None:
            continue  # 跳过没有预期首次出场的人物
        
        if actual_first is None:
            issues.append({
                'type': 'warning',
                'character': char_name,
                'role': char_info['role'],
                'message': f'人物 {char_name} ({char_info["role"]}) 在所有章节中都未出现'
            })
        elif actual_first > expected_first:
            issues.append({
                'type': 'info',
                'character': char_name,
                'role': char_info['role'],
                'expected': expected_first,
                'actual': actual_first,
                'message': f'人物 {char_name} 预期第{expected_first}章出现，实际第{actual_first}章首次出现'
            })
        elif actual_first < expected_first:
            issues.append({
                'type': 'warning',
                'character': char_name,
                'role': char_info['role'],
                'expected': expected_first,
                'actual': actual_first,
                'message': f'人物 {char_name} 预期第{expected_first}章出现，但提前在第{actual_first}章出现'
            })
    
    return issues, first_appearances

def generate_character_appearance_matrix(chapters_data):
    """生成人物出场矩阵"""
    matrix = defaultdict(dict)
    
    for chapter in sorted(chapters_data, key=lambda x: x['chapter_num']):
        chapter_num = chapter['chapter_num']
        for char_name in MAIN_CHARACTERS:
            count = chapter['characters'].get(char_name, 0)
            matrix[char_name][chapter_num] = count
    
    return dict(matrix)

def print_report(chapters_data, timeline_issues, character_issues, first_appearances, appearance_matrix):
    """打印验证报告"""
    print("=" * 80)
    print("记忆当铺：人物出场顺序及时间线验证报告")
    print("=" * 80)
    print()
    
    print(f"总章节数: {len(chapters_data)}")
    print(f"分析的章节范围: 第{min(c['chapter_num'] for c in chapters_data)}章 - 第{max(c['chapter_num'] for c in chapters_data)}章")
    print()
    
    # 人物首次出场统计
    print("-" * 80)
    print("一、人物首次出场统计")
    print("-" * 80)
    for char_name in sorted(MAIN_CHARACTERS.keys()):
        first_ch = first_appearances.get(char_name, '未出现')
        expected = MAIN_CHARACTERS[char_name].get('first_expected', '无预期')
        role = MAIN_CHARACTERS[char_name]['role']
        status = "✓" if (first_ch == expected or expected == '无预期' or first_ch == '未出现') else "⚠"
        print(f"{status} {char_name:8} ({role:15}) - 首次出场: 第{first_ch}章 (预期: 第{expected}章)")
    print()
    
    # 时间线问题
    print("-" * 80)
    print("二、时间线一致性问题")
    print("-" * 80)
    if timeline_issues:
        for issue in timeline_issues:
            symbol = "❌" if issue['type'] == 'error' else "⚠️ "
            print(f"{symbol} 第{issue['chapter']}章 《{issue['title']}》")
            print(f"   {issue['message']}")
            print()
    else:
        print("✓ 未发现时间线一致性问题")
    print()
    
    # 人物出场问题
    print("-" * 80)
    print("三、人物出场顺序问题")
    print("-" * 80)
    if character_issues:
        for issue in character_issues:
            if issue['type'] == 'error':
                symbol = "❌"
            elif issue['type'] == 'warning':
                symbol = "⚠️ "
            else:
                symbol = "ℹ️ "
            print(f"{symbol} {issue['message']}")
    else:
        print("✓ 所有人物出场顺序符合预期")
    print()
    
    # 人物出场频率统计
    print("-" * 80)
    print("四、人物出场频率 (前10章)")
    print("-" * 80)
    print(f"{'章节':<8}", end='')
    for char in ['林深', '苏晚', '林雨', '赵医生', '陈煜']:
        print(f"{char:>6}", end='')
    print()
    print("-" * 80)
    
    for ch_num in range(1, min(11, max(c['chapter_num'] for c in chapters_data) + 1)):
        print(f"第{ch_num:2d}章  ", end='')
        for char in ['林深', '苏晚', '林雨', '赵医生', '陈煜']:
            count = appearance_matrix.get(char, {}).get(ch_num, 0)
            print(f"{count:6}", end='')
        print()
    print()
    
    # 总结
    print("-" * 80)
    print("五、验证总结")
    print("-" * 80)
    total_issues = len(timeline_issues) + len([i for i in character_issues if i['type'] in ['error', 'warning']])
    if total_issues == 0:
        print("✓ 所有章节的人物出场顺序和时间线都符合要求")
    else:
        errors = len([i for i in timeline_issues if i['type'] == 'error']) + \
                 len([i for i in character_issues if i['type'] == 'error'])
        warnings = len([i for i in timeline_issues if i['type'] == 'warning']) + \
                   len([i for i in character_issues if i['type'] == 'warning'])
        print(f"⚠ 发现 {total_issues} 个问题:")
        print(f"   - 错误: {errors}")
        print(f"   - 警告: {warnings}")
    print()
    print("=" * 80)

def main():
    """主函数"""
    # 查找所有章节文件
    chapters_dir = 'script/chapters'
    chapter_files = []
    
    for i in range(1, 91):  # 90章
        filename = f'chapter_{i:02d}.md'
        filepath = os.path.join(chapters_dir, filename)
        if os.path.exists(filepath):
            chapter_files.append(filepath)
    
    print(f"找到 {len(chapter_files)} 个章节文件")
    print("正在分析...")
    print()
    
    # 分析所有章节
    chapters_data = []
    for chapter_file in chapter_files:
        data = analyze_chapter(chapter_file)
        if data:
            chapters_data.append(data)
    
    # 验证时间线
    timeline_issues = verify_timeline_consistency(chapters_data)
    
    # 验证人物出场
    character_issues, first_appearances = verify_character_first_appearances(chapters_data)
    
    # 生成出场矩阵
    appearance_matrix = generate_character_appearance_matrix(chapters_data)
    
    # 打印报告
    print_report(chapters_data, timeline_issues, character_issues, first_appearances, appearance_matrix)
    
    # 保存详细报告到JSON
    report_data = {
        'summary': {
            'total_chapters': len(chapters_data),
            'total_issues': len(timeline_issues) + len(character_issues)
        },
        'first_appearances': first_appearances,
        'timeline_issues': timeline_issues,
        'character_issues': character_issues,
        'appearance_matrix': appearance_matrix
    }
    
    with open('verification_report.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print("详细报告已保存到 verification_report.json")

if __name__ == '__main__':
    main()
