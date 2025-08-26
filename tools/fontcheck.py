#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体支持检查工具
检查text_ba目录下所选文本字符的主字体支持情况，把主字体不支持的字符及频次写入replace.tmp文件
Python版本 by msyloveldx, 2025/08
原作者: shanleiguang@gmail.com, 2025
"""

import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from PIL import Image, ImageFont, ImageDraw

class FontChecker:
    """字体检查工具类"""
    
    def __init__(self, from_file: int = 1, to_file: int = 1):
        self.from_file = from_file
        self.to_file = to_file
        self.book_config = {}
        self.unsupported_chars = defaultdict(lambda: {'font': '', 'count': 0})
        
        self._load_book_config()
    
    def _load_book_config(self):
        """加载书籍配置文件"""
        book_cfg_path = Path("book.cfg")
        if not book_cfg_path.exists():
            raise FileNotFoundError("错误：未找到book.cfg文件")
        
        print("读取 'book.cfg'...")
        
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
                    self.book_config[key] = value
        
        print(f"\t标题：{self.book_config.get('title', '')}")
        print(f"\t作者：{self.book_config.get('author', '')}")
        print(f"\t背景：{self.book_config.get('canvas_id', '')}")
        print(f"\t字体1：{self.book_config.get('font1', '')}")
        print(f"\t字体2：{self.book_config.get('font2', '')}")
        print(f"\t字体3：{self.book_config.get('font3', '')}")
        print(f"\t字体4：{self.book_config.get('font4', '')}")
    
    def check_font_support(self, font_path: str, char: str) -> bool:
        """检查字体是否支持某个字符"""
        try:
            font_full_path = Path(f"../../fonts/{font_path}")
            if not font_full_path.exists():
                return False
            
            font = ImageFont.truetype(str(font_full_path), 40)
            
            # 使用PIL检查字符是否被支持
            # 创建一个小图像来测试字符渲染
            img = Image.new('RGB', (100, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                bbox = draw.textbbox((0, 0), char, font=font)
                # 如果bbox有效且宽高都大于0，说明字符被支持
                return bbox[2] > bbox[0] and bbox[3] > bbox[1]
            except:
                return False
                
        except Exception as e:
            print(f"检查字体 {font_path} 对字符 '{char}' 的支持时出错: {e}")
            return False
    
    def get_font_for_char(self, char: str, font_list: list) -> str:
        """获取支持指定字符的字体"""
        for font_name in font_list:
            if font_name and self.check_font_support(font_name, char):
                return font_name
        return None
    
    def check_text_files(self):
        """检查文本文件中的字符"""
        text_ba_dir = Path("text_ba")
        if not text_ba_dir.exists():
            raise FileNotFoundError("错误：未找到text_ba目录")
        
        # 获取字体列表
        fonts = [
            self.book_config.get('font1', ''),
            self.book_config.get('font2', ''),
            self.book_config.get('font3', ''),
            self.book_config.get('font4', '')
        ]
        fonts = [f for f in fonts if f]  # 过滤空字体
        
        if not fonts:
            raise ValueError("错误：未配置任何字体")
        
        main_font = fonts[0]  # 主字体
        
        # 处理所有txt文件
        txt_files = sorted([f for f in text_ba_dir.glob("*.txt")])
        
        for txt_file in txt_files:
            print(f"检查 'text_ba/{txt_file.name}' ...")
            
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 移除分隔符
            content = content.replace('|', '')
            
            # 检查每个字符
            for char in content:
                if char not in self.unsupported_chars:
                    # 检查哪个字体支持这个字符
                    supporting_font = self.get_font_for_char(char, fonts)
                    
                    if supporting_font and supporting_font != main_font:
                        # 主字体不支持，但其他字体支持
                        self.unsupported_chars[char]['font'] = supporting_font
                        self.unsupported_chars[char]['count'] = 1
                    elif not supporting_font:
                        # 所有字体都不支持
                        self.unsupported_chars[char]['font'] = '无支持字体'
                        self.unsupported_chars[char]['count'] = 1
                else:
                    # 字符已存在，增加计数
                    self.unsupported_chars[char]['count'] += 1
    
    def save_results(self):
        """保存检查结果到replace.tmp文件"""
        output_path = Path("replace.tmp")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 按出现频次排序
            sorted_chars = sorted(self.unsupported_chars.items(), 
                                key=lambda x: x[1]['count'], reverse=True)
            
            for char, info in sorted_chars:
                f.write(f"{char}|{info['font']}|{info['count']}|\n")
        
        print(f"检查完成，结果已保存到 {output_path}")
        print(f"发现 {len(self.unsupported_chars)} 个主字体不支持的字符")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='字体支持检查工具')
    parser.add_argument('-f', '--from', type=int, default=1, 
                       help='起始文件序号')
    parser.add_argument('-t', '--to', type=int, default=1, 
                       help='结束文件序号')
    
    args = parser.parse_args()
    
    try:
        checker = FontChecker(getattr(args, 'from'), args.to)
        checker.check_text_files()
        checker.save_results()
        
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
