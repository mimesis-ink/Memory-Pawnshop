#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查章节重复内容的脚本
This script checks for duplicate content across the first 50 chapters.
"""

import os
import re
from collections import defaultdict
from difflib import SequenceMatcher
import hashlib

# 配置常量
SIMILARITY_THRESHOLD = 0.85  # 相似度阈值
MIN_PARAGRAPH_LENGTH = 20    # 段落最小长度
MIN_SENTENCE_LENGTH = 10     # 句子最小长度

def read_chapter(filepath):
    """读取章节文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def extract_paragraphs(content):
    """提取段落（去除空行和标题）"""
    lines = content.split('\n')
    paragraphs = []
    current_para = []
    
    for line in lines:
        line = line.strip()
        # 跳过标题、分隔线和特殊标记
        if line.startswith('#') or line.startswith('**') or line == '---' or line.startswith('##'):
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
            continue
        
        if line:
            current_para.append(line)
        else:
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
    
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    return paragraphs

def extract_sentences(content):
    """提取句子"""
    # 按中文句号、问号、感叹号分句
    sentences = re.split('[。！？]', content)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]

def compute_hash(text):
    """计算文本的hash值"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def find_exact_duplicates(chapters_data):
    """查找完全重复的段落"""
    print("\n=== 查找完全重复的段落 ===\n")
    
    para_map = defaultdict(list)
    
    for chapter_num, paragraphs in chapters_data.items():
        for i, para in enumerate(paragraphs):
            if len(para) > MIN_PARAGRAPH_LENGTH:  # 只检查长度大于配置值的段落
                para_hash = compute_hash(para)
                para_map[para_hash].append((chapter_num, i, para))
    
    duplicates = {k: v for k, v in para_map.items() if len(v) > 1}
    
    if duplicates:
        print(f"发现 {len(duplicates)} 组完全重复的段落：\n")
        for i, (hash_val, occurrences) in enumerate(duplicates.items(), 1):
            print(f"重复组 {i}:")
            print(f"  出现次数: {len(occurrences)}")
            print(f"  内容: {occurrences[0][2][:100]}...")
            print(f"  位置:")
            for chapter_num, para_idx, _ in occurrences:
                print(f"    - 第{chapter_num}章 第{para_idx}段")
            print()
    else:
        print("✓ 未发现完全重复的段落\n")
    
    return len(duplicates)

def find_similar_paragraphs(chapters_data, threshold=0.8):
    """查找相似的段落（非完全重复但高度相似）"""
    print("\n=== 查找高度相似的段落 ===\n")
    
    all_paragraphs = []
    for chapter_num, paragraphs in chapters_data.items():
        for i, para in enumerate(paragraphs):
            if len(para) > 30:  # 只检查较长的段落
                all_paragraphs.append((chapter_num, i, para))
    
    similar_pairs = []
    
    # 比较所有段落对
    for i in range(len(all_paragraphs)):
        for j in range(i + 1, len(all_paragraphs)):
            ch1, idx1, para1 = all_paragraphs[i]
            ch2, idx2, para2 = all_paragraphs[j]
            
            # 跳过同一章节
            if ch1 == ch2:
                continue
            
            similarity = SequenceMatcher(None, para1, para2).ratio()
            if similarity >= threshold:
                similar_pairs.append((ch1, ch2, idx1, idx2, similarity, para1, para2))
    
    if similar_pairs:
        print(f"发现 {len(similar_pairs)} 对高度相似的段落（相似度 >= {threshold*100}%）：\n")
        for i, (ch1, ch2, idx1, idx2, sim, para1, para2) in enumerate(similar_pairs, 1):
            print(f"相似对 {i}:")
            print(f"  相似度: {sim*100:.1f}%")
            print(f"  第{ch1}章 第{idx1}段: {para1[:80]}...")
            print(f"  第{ch2}章 第{idx2}段: {para2[:80]}...")
            print()
    else:
        print(f"✓ 未发现相似度 >= {threshold*100}% 的段落\n")
    
    return len(similar_pairs)

def find_repeated_sentences(chapters_data):
    """查找重复的句子"""
    print("\n=== 查找重复出现的句子 ===\n")
    
    sentence_map = defaultdict(list)
    
    for chapter_num, paragraphs in chapters_data.items():
        content = ' '.join(paragraphs)
        sentences = extract_sentences(content)
        for sentence in sentences:
            if len(sentence) > MIN_SENTENCE_LENGTH:  # 只检查较长的句子
                sentence_map[sentence].append(chapter_num)
    
    repeated = {k: v for k, v in sentence_map.items() if len(set(v)) > 1}
    
    if repeated:
        print(f"发现 {len(repeated)} 个在多个章节重复出现的句子：\n")
        count = 0
        for sentence, chapters in sorted(repeated.items(), key=lambda x: len(x[1]), reverse=True):
            count += 1
            if count > 20:  # 只显示前20个
                print(f"... 还有 {len(repeated) - 20} 个重复句子未显示\n")
                break
            unique_chapters = sorted(set(chapters))
            print(f"句子: {sentence}")
            print(f"  出现在: 第{', '.join(map(str, unique_chapters))}章 (共{len(unique_chapters)}章)")
            print()
    else:
        print("✓ 未发现跨章节重复的句子\n")
    
    return len(repeated)

def check_chapter_titles(chapters_data, chapter_files):
    """检查章节标题是否重复"""
    print("\n=== 检查章节标题 ===\n")
    
    titles = {}
    for chapter_num in sorted(chapters_data.keys()):
        filepath = chapter_files[chapter_num]
        content = read_chapter(filepath)
        
        # 提取章节标题（第一个#标题）
        match = re.search(r'^# 第\d+章：(.+)$', content, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            if title in titles:
                print(f"⚠ 标题重复: 「{title}」")
                print(f"  第{titles[title]}章 和 第{chapter_num}章")
            else:
                titles[title] = chapter_num
    
    if len(titles) == len(chapters_data):
        print("✓ 所有章节标题唯一\n")
        return 0
    else:
        duplicate_count = len(chapters_data) - len(titles)
        print(f"\n发现 {duplicate_count} 个重复标题\n")
        return duplicate_count

def main():
    # 获取章节文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chapters_dir = os.path.join(script_dir, 'chapters')
    chapter_files = {}
    
    for i in range(1, 51):
        filepath = os.path.join(chapters_dir, f'chapter_{i:02d}.md')
        if os.path.exists(filepath):
            chapter_files[i] = filepath
    
    print(f"找到 {len(chapter_files)} 个章节文件\n")
    print("=" * 60)
    
    # 读取所有章节
    chapters_data = {}
    for chapter_num, filepath in chapter_files.items():
        content = read_chapter(filepath)
        paragraphs = extract_paragraphs(content)
        chapters_data[chapter_num] = paragraphs
    
    # 执行各项检查
    total_issues = 0
    
    total_issues += check_chapter_titles(chapters_data, chapter_files)
    total_issues += find_exact_duplicates(chapters_data)
    total_issues += find_similar_paragraphs(chapters_data, threshold=SIMILARITY_THRESHOLD)
    total_issues += find_repeated_sentences(chapters_data)
    
    # 生成总结
    print("\n" + "=" * 60)
    print("\n=== 检查总结 ===\n")
    if total_issues == 0:
        print("✓ 未发现明显的重复内容问题")
    else:
        print(f"⚠ 共发现 {total_issues} 处潜在的重复内容问题")
        print("\n建议:")
        print("  1. 检查上述重复内容是否为故意设计（如回忆/闪回场景）")
        print("  2. 如非故意，建议修改以避免重复")
        print("  3. 确保关键情节和对话的独特性")
    print()

if __name__ == '__main__':
    main()
