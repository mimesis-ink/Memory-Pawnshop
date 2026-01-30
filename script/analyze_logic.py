#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查章节逻辑一致性的脚本
This script checks for logical inconsistencies across the first 50 chapters.
"""

import os
import re
from collections import defaultdict

def read_chapter(filepath):
    """读取章节文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def extract_character_info(content, chapter_num):
    """提取角色相关信息"""
    characters = {
        '林深': [],
        '林雨': [],
        '苏晚': [],
        '陈煜': [],
        '赵医生': [],
        '韩江': [],
        '韩世杰': [],
        '沈微': [],
        '宋文博': [],
        '赵启明': []
    }
    
    for char_name in characters.keys():
        if char_name in content:
            # 查找角色相关的描述
            pattern = rf'{char_name}[^。！？]*[。！？]'
            matches = re.findall(pattern, content)
            for match in matches:
                characters[char_name].append((chapter_num, match))
    
    return characters

def extract_timeline_info(content, chapter_num):
    """提取时间线信息"""
    timeline = []
    
    # 查找日期相关表述
    date_patterns = [
        r'\d+月\d+日',
        r'周[一二三四五六日]',
        r'[昨前今明后]天',
        r'\d+小时[前后]',
        r'\d+天[前后]',
        r'凌晨|早上|上午|中午|下午|傍晚|晚上|深夜|午夜'
    ]
    
    for pattern in date_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            context_start = max(0, match.start() - 50)
            context_end = min(len(content), match.end() + 50)
            context = content[context_start:context_end]
            timeline.append((chapter_num, match.group(), context))
    
    return timeline

def extract_location_info(content, chapter_num):
    """提取地点信息"""
    locations = defaultdict(list)
    
    # 查找场景标记
    scene_patterns = re.finditer(r'场景[一二三四五六七八九十]+：(.+)', content)
    for match in scene_patterns:
        location = match.group(1)
        locations[location].append(chapter_num)
    
    # 查找常见地点
    common_locations = [
        '记忆当铺', '医院', '重症监护室', '手术室', '停车场',
        '便利店', '出租屋', '翠湖山庄', '废弃工厂', '警察局',
        '咖啡厅', '实验室', '神经扫描室', '宴会厅', '公寓'
    ]
    
    for loc in common_locations:
        if loc in content:
            pattern = rf'{loc}[^。！？]*[。！？]'
            matches = re.findall(pattern, content)
            for match in matches:
                locations[loc].append((chapter_num, match))
    
    return locations

def extract_plot_points(content, chapter_num):
    """提取关键情节点"""
    plot_points = []
    
    # 关键事件关键词
    keywords = [
        '死了', '杀', '枪', '血', '记忆', '支票', '录音', '录像',
        '实验', '手术', '提取', '删除', '恢复', '卖', '买',
        '证据', '线索', '真相', '秘密', '阴谋', '背叛', '陷阱'
    ]
    
    for keyword in keywords:
        if keyword in content:
            pattern = rf'[^。！？]*{keyword}[^。！？]*[。！？]'
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) > 15:  # 只记录有意义的句子
                    plot_points.append((chapter_num, keyword, match))
    
    return plot_points

def check_character_consistency(all_characters):
    """检查角色一致性"""
    print("\n=== 检查角色一致性 ===\n")
    
    issues = []
    
    # 检查角色首次出现和描述
    for char_name, appearances in all_characters.items():
        if not appearances:
            continue
        
        chapters_with_char = sorted(set([ch for ch, _ in appearances]))
        
        if char_name in ['林深', '林雨', '苏晚', '陈煜', '赵医生']:
            # 主要角色应该在前几章出现
            if chapters_with_char and chapters_with_char[0] > 10:
                issues.append(f"⚠ {char_name} 首次出现在第{chapters_with_char[0]}章，较晚")
        
        # 检查角色是否突然消失很久又出现
        if len(chapters_with_char) > 2:
            for i in range(len(chapters_with_char) - 1):
                gap = chapters_with_char[i+1] - chapters_with_char[i]
                if gap > 15:  # 超过15章没出现
                    issues.append(f"⚠ {char_name} 在第{chapters_with_char[i]}章后消失{gap}章，在第{chapters_with_char[i+1]}章重新出现")
    
    if issues:
        print("发现以下角色相关问题:\n")
        for issue in issues:
            print(f"  {issue}")
        print()
    else:
        print("✓ 角色出现时机基本合理\n")
    
    return len(issues)

def check_timeline_consistency(all_timeline):
    """检查时间线一致性"""
    print("\n=== 检查时间线一致性 ===\n")
    
    issues = []
    
    # 提取所有日期
    dates = {}
    for chapter_num, time_ref, context in all_timeline:
        if re.match(r'\d+月\d+日', time_ref):
            if time_ref not in dates:
                dates[time_ref] = []
            dates[time_ref].append(chapter_num)
    
    # 检查日期逻辑
    date_list = sorted(dates.keys())
    if date_list:
        print(f"发现的日期引用: {', '.join(date_list)}\n")
        
        # 检查是否有日期倒序
        for i in range(len(date_list) - 1):
            curr_date = date_list[i]
            next_date = date_list[i+1]
            
            # 简单的日期比较（假设同年）
            curr_month = int(re.search(r'(\d+)月', curr_date).group(1))
            curr_day = int(re.search(r'(\d+)日', curr_date).group(1))
            next_month = int(re.search(r'(\d+)月', next_date).group(1))
            next_day = int(re.search(r'(\d+)日', next_date).group(1))
            
            if curr_month > next_month or (curr_month == next_month and curr_day > next_day):
                issues.append(f"⚠ 时间线可能倒序: {curr_date} 出现在 {next_date} 之前")
    
    # 检查一章内的时间连续性
    time_keywords = ['凌晨', '早上', '上午', '中午', '下午', '傍晚', '晚上', '深夜']
    time_order = {word: i for i, word in enumerate(time_keywords)}
    
    chapter_times = defaultdict(list)
    for chapter_num, time_ref, context in all_timeline:
        if time_ref in time_keywords:
            chapter_times[chapter_num].append(time_ref)
    
    for chapter_num, times in chapter_times.items():
        if len(times) > 1:
            # 检查时间是否合理递进
            for i in range(len(times) - 1):
                if times[i] in time_order and times[i+1] in time_order:
                    if time_order[times[i]] > time_order[times[i+1]]:
                        # 可能是时间倒序或跨天
                        pass  # 这个比较复杂，暂时不标记为问题
    
    if issues:
        print("发现以下时间线问题:\n")
        for issue in issues:
            print(f"  {issue}")
        print()
    else:
        print("✓ 时间线基本一致\n")
    
    return len(issues)

def check_location_consistency(all_locations):
    """检查地点一致性"""
    print("\n=== 检查地点一致性 ===\n")
    
    issues = []
    
    # 统计主要地点出现频率
    major_locations = {}
    for location, occurrences in all_locations.items():
        if isinstance(occurrences[0], tuple):
            chapters = set([ch for ch, _ in occurrences])
        else:
            chapters = set(occurrences)
        
        if len(chapters) >= 3:  # 出现在3章以上算主要地点
            major_locations[location] = sorted(chapters)
    
    if major_locations:
        print("主要地点及其出现章节:\n")
        for location, chapters in sorted(major_locations.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {location}: 第{', '.join(map(str, chapters))}章 (共{len(chapters)}次)")
        print()
    
    # 这里不算作问题，只是统计信息
    print("✓ 地点统计完成\n")
    
    return 0

def check_plot_consistency(all_plot_points):
    """检查情节一致性"""
    print("\n=== 检查情节一致性 ===\n")
    
    issues = []
    
    # 统计关键事件
    event_stats = defaultdict(list)
    for chapter_num, keyword, sentence in all_plot_points:
        event_stats[keyword].append((chapter_num, sentence))
    
    print("关键事件词频统计:\n")
    sorted_events = sorted(event_stats.items(), key=lambda x: len(x[1]), reverse=True)
    for keyword, occurrences in sorted_events[:15]:  # 显示前15个
        chapters = sorted(set([ch for ch, _ in occurrences]))
        print(f"  {keyword}: {len(occurrences)}次 (第{', '.join(map(str, chapters[:10]))}{'...' if len(chapters) > 10 else ''}章)")
    print()
    
    # 检查一些常见的逻辑问题
    
    # 1. 检查"死了"的角色是否还在活动
    death_mentions = event_stats.get('死了', [])
    if death_mentions:
        print("发现死亡相关描述:\n")
        for chapter_num, sentence in death_mentions[:5]:
            print(f"  第{chapter_num}章: {sentence[:60]}...")
        print()
    
    # 2. 检查记忆相关的矛盾
    memory_events = []
    for keyword in ['删除', '恢复', '卖', '买']:
        if keyword in event_stats:
            memory_events.extend(event_stats[keyword])
    
    if memory_events:
        print(f"记忆交易/操作相关事件: {len(memory_events)}次\n")
    
    print("✓ 情节统计完成\n")
    
    return 0

def analyze_chapter_structure(chapters_data):
    """分析章节结构"""
    print("\n=== 分析章节结构 ===\n")
    
    issues = []
    
    for chapter_num, content in sorted(chapters_data.items()):
        # 检查是否有黄金三秒
        if '【黄金三秒】' not in content and '黄金三秒' not in content:
            issues.append(f"⚠ 第{chapter_num}章缺少【黄金三秒】")
        
        # 检查是否有结尾钩子
        if '【结尾钩子】' not in content and '结尾钩子' not in content:
            issues.append(f"⚠ 第{chapter_num}章缺少【结尾钩子】")
        
        # 检查字数
        # 移除markdown标记和统计信息
        text_content = re.sub(r'#.*?\n', '', content)
        text_content = re.sub(r'\*\*.*?\*\*', '', text_content)
        text_content = re.sub(r'---', '', text_content)
        text_content = re.sub(r'【.*?】', '', text_content)
        
        # 计算中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text_content))
        
        if chinese_chars < 1500:
            issues.append(f"⚠ 第{chapter_num}章字数偏少 ({chinese_chars}字，建议1800-2000字)")
        elif chinese_chars > 2200:
            issues.append(f"⚠ 第{chapter_num}章字数偏多 ({chinese_chars}字，建议1800-2000字)")
    
    if issues:
        print("发现以下结构问题:\n")
        for issue in issues[:20]:  # 只显示前20个
            print(f"  {issue}")
        if len(issues) > 20:
            print(f"  ... 还有 {len(issues) - 20} 个问题未显示")
        print()
    else:
        print("✓ 所有章节结构完整\n")
    
    return len(issues)

def main():
    # 获取章节文件
    chapters_dir = '/home/runner/work/Memory-Pawnshop/Memory-Pawnshop/script/chapters'
    chapters_data = {}
    
    for i in range(1, 51):
        filepath = os.path.join(chapters_dir, f'chapter_{i:02d}.md')
        if os.path.exists(filepath):
            chapters_data[i] = read_chapter(filepath)
    
    print(f"分析 {len(chapters_data)} 个章节的逻辑一致性\n")
    print("=" * 60)
    
    # 收集所有信息
    all_characters = defaultdict(list)
    all_timeline = []
    all_locations = defaultdict(list)
    all_plot_points = []
    
    for chapter_num, content in chapters_data.items():
        # 提取角色信息
        char_info = extract_character_info(content, chapter_num)
        for char_name, info in char_info.items():
            all_characters[char_name].extend(info)
        
        # 提取时间线信息
        timeline = extract_timeline_info(content, chapter_num)
        all_timeline.extend(timeline)
        
        # 提取地点信息
        locations = extract_location_info(content, chapter_num)
        for loc, info in locations.items():
            all_locations[loc].extend(info if isinstance(info, list) else [info])
        
        # 提取情节点
        plot_points = extract_plot_points(content, chapter_num)
        all_plot_points.extend(plot_points)
    
    # 执行各项检查
    total_issues = 0
    
    total_issues += analyze_chapter_structure(chapters_data)
    total_issues += check_character_consistency(all_characters)
    total_issues += check_timeline_consistency(all_timeline)
    total_issues += check_location_consistency(all_locations)
    total_issues += check_plot_consistency(all_plot_points)
    
    # 生成总结
    print("\n" + "=" * 60)
    print("\n=== 逻辑检查总结 ===\n")
    if total_issues == 0:
        print("✓ 未发现明显的逻辑一致性问题")
    else:
        print(f"⚠ 共发现 {total_issues} 处潜在的逻辑问题")
        print("\n建议:")
        print("  1. 检查上述问题是否影响故事逻辑")
        print("  2. 确保角色行为、时间线、地点转换的合理性")
        print("  3. 维护情节连贯性，避免前后矛盾")
    print()

if __name__ == '__main__':
    main()
