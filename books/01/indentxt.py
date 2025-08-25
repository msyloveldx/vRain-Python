#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整段缩进文本格式化脚本
将本脚本放到书籍目录下，将原始文本保存在tmp目录下，需要整段缩进的段首添加S2标识（2代表缩进2个空格）
脚本格式化后的文本将存入text目录下，用于书籍制作
Python版本 by AI Assistant, 2025/01
原作者: shanleiguang, 2025.03
"""

import os
import sys
import argparse
from pathlib import Path
import re

class TextIndentProcessor:
    """文本缩进处理器"""
    
    def __init__(self, from_file: int, to_file: int):
        self.from_file = from_file
        self.to_file = to_file
        self.book_config = {}
        self.zh_numbers = {}
        
        self._load_configurations()
    
    def _load_configurations(self):
        """加载配置文件"""
        # 加载书籍配置
        book_cfg_path = Path("book.cfg")
        if not book_cfg_path.exists():
            raise FileNotFoundError("错误：未找到book.cfg文件")
        
        with open(book_cfg_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 处理行内注释
                if '#' in line and '=#' not in line:
                    line = line.split('#')[0].strip()
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 尝试转换数值
                    if value.isdigit():
                        self.book_config[key] = int(value)
                    elif value.replace('.', '').isdigit():
                        self.book_config[key] = float(value)
                    else:
                        self.book_config[key] = value
        
        # 加载中文数字映射
        zh_num_path = Path("../../db/num2zh_jid.txt")
        if zh_num_path.exists():
            with open(zh_num_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '|' in line:
                        num, zh = line.split('|', 1)
                        self.zh_numbers[int(num)] = zh
    
    def process_files(self):
        """处理文本文件"""
        tmp_dir = Path("tmp")
        text_dir = Path("text")
        
        if not tmp_dir.exists():
            raise FileNotFoundError("错误：未找到tmp目录")
        
        # 确保text目录存在
        text_dir.mkdir(exist_ok=True)
        
        row_num = self.book_config.get('row_num', 30)
        
        for pid in range(self.from_file, self.to_file + 1):
            tmp_file = tmp_dir / f"{pid}.txt"
            if not tmp_file.exists():
                print(f"警告：未找到文件 {tmp_file}")
                continue
            
            print(f"处理文件 '{tmp_file}'...")
            
            text_content = ""
            
            with open(tmp_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 去除空白字符
                    line = re.sub(r'\s', '', line)
                    
                    # 标点符号替换
                    if self.book_config.get('exp_replace_comma'):
                        for replacement in self.book_config['exp_replace_comma'].split('|'):
                            if len(replacement) >= 2:
                                old_char, new_char = replacement[0], replacement[1]
                                # 处理特殊字符的转义
                                if old_char in r'.\!?()[]/-':
                                    old_char = '\\' + old_char
                                line = re.sub(old_char, new_char, line)
                    
                    # 无标点模式
                    if self.book_config.get('if_nocomma') == 1:
                        exp_nocomma = self.book_config.get('exp_nocomma', '')
                        if exp_nocomma:
                            for char in exp_nocomma.split('|'):
                                line = line.replace(char, '')
                    
                    # 标点符号归一化
                    if self.book_config.get('if_onlyperiod') == 1:
                        exp_onlyperiod = self.book_config.get('exp_onlyperiod', '')
                        if exp_onlyperiod:
                            for char in exp_onlyperiod.split('|'):
                                line = line.replace(char, '。')
                            # 去除重复句号
                            while '。。' in line:
                                line = line.replace('。。', '。')
                            line = line.lstrip('。')
                            line = line.replace('】【', '')
                            line = line.replace('【。', '【')
                    
                    # 处理缩进段落
                    processed_line = self._process_indent_line(line, row_num)
                    text_content += processed_line + "\n"
            
            # 保存处理后的文件
            output_file = text_dir / f"{pid:03d}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            print(f"已保存到 {output_file}")
    
    def _process_indent_line(self, line: str, row_num: int) -> str:
        """处理缩进行"""
        # 检查是否是缩进段落
        indent_match = re.match(r'^S(\d)(.*?)$', line)
        if not indent_match:
            return line
        
        indent_num = int(indent_match.group(1))
        content = indent_match.group(2)
        
        text_comma_nop = self.book_config.get('text_comma_nop', '')
        comment_comma_nop = self.book_config.get('comment_comma_nop', '')
        if_book_vline = self.book_config.get('if_book_vline', 0)
        
        chars = list(content)
        new_chars = []
        
        rflag = 0  # 批注字符标识
        cnt = 0    # 列字数计数器
        
        i = 0
        while i < len(chars):
            char = chars[i]
            
            # 不占字符位的标点符号
            if (text_comma_nop and char in text_comma_nop.split('|')) or \
               (comment_comma_nop and char in comment_comma_nop.split('|')):
                new_chars.append(char)
                i += 1
                continue
            
            # 书名号处理
            if if_book_vline and char in ['《', '》']:
                new_chars.append(char)
                i += 1
                continue
            
            # 批注开始
            if char == '【':
                new_chars.append(char)
                rflag = 1
                cnt = int(cnt + 0.5)
                i += 1
                continue
            
            # 批注结束
            if char == '】':
                new_chars.append(char)
                rflag = 0
                i += 1
                continue
            
            # 正文字符
            if rflag == 0:
                cnt = int(cnt + 0.5) + 1
                if cnt == 1:  # 每列首字符前添加空格
                    new_chars.append('@' * indent_num + char)
                else:
                    if cnt <= row_num - indent_num:
                        new_chars.append(char)
                    else:
                        # 需要换列，重置计数器
                        cnt = 0
                        continue  # 不增加i，重新处理当前字符
            
            # 批注字符
            elif rflag == 1:
                cnt += 0.5
                if cnt == 0.5:  # 每列首字符前添加空格
                    new_chars.append('@@' * indent_num + '】【' + char)
                else:
                    if int(cnt + 0.5) <= row_num - indent_num:
                        new_chars.append(char)
                    else:
                        # 需要换列，重置计数器
                        cnt = 0
                        continue  # 不增加i，重新处理当前字符
            
            i += 1
        
        return ''.join(new_chars)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='整段缩进文本格式化脚本')
    parser.add_argument('-f', '--from', type=int, required=True, 
                       help='起始文件序号')
    parser.add_argument('-t', '--to', type=int, required=True, 
                       help='结束文件序号')
    
    args = parser.parse_args()
    
    try:
        processor = TextIndentProcessor(getattr(args, 'from'), args.to)
        processor.process_files()
        
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
