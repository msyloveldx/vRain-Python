#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字符替换工具
读取text_ba目录下的文件，根据replace.txt替换字符并覆盖写入text目录对应文件
Python版本 by msyloveldx, 2025/08
原作者: shanleiguang@gmail.com, 2025
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw

class CharacterReplacer:
    """字符替换工具类"""
    
    def __init__(self, book_id: str, from_file: int = 1, to_file: int = 1):
        self.book_id = book_id
        self.from_file = from_file
        self.to_file = to_file
        self.book_config = {}
        self.replacements = {}
        
        self._load_book_config()
        self._load_replacements()
    
    def _load_book_config(self):
        """加载书籍配置文件"""
        book_cfg_path = Path(f"books/{self.book_id}/book.cfg")
        if not book_cfg_path.exists():
            raise FileNotFoundError(f"错误：未找到books/{self.book_id}/book.cfg文件")
        
        print(f"读取书籍排版配置文件'books/{self.book_id}/book.cfg'...")
        
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
        print(f"\t每列字数：{self.book_config.get('row_num', '')}")
        print(f"\t是否无标点：{self.book_config.get('if_nocomma', '')}")
        print(f"\t标点归一化：{self.book_config.get('if_onlyperiod', '')}")
    
    def _load_replacements(self):
        """加载字符替换配置"""
        replace_path = Path("replace.txt")
        if not replace_path.exists():
            print("警告：未找到replace.txt文件，将不进行字符替换")
            return
        
        # 获取字体列表
        fonts = [
            self.book_config.get('font1', ''),
            self.book_config.get('font2', ''),
            self.book_config.get('font3', ''),
            self.book_config.get('font4', '')
        ]
        fonts = [f for f in fonts if f]  # 过滤空字体
        
        with open(replace_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('|')
                if len(parts) >= 4 and parts[3]:  # 确保有替换字符
                    original_char = parts[0]
                    replacement_char = parts[3]
                    
                    # 检查替换后字符的字体支持情况
                    replacement_font = self.get_font_for_char(replacement_char, fonts)
                    
                    # 只有当替换后字符被font1或font2支持时才进行替换
                    if replacement_font in fonts[:2]:  # font1和font2
                        self.replacements[original_char] = replacement_char
        
        print(f"加载了 {len(self.replacements)} 个字符替换规则")
    
    def check_font_support(self, font_path: str, char: str) -> bool:
        """检查字体是否支持某个字符"""
        try:
            font_full_path = Path(f"fonts/{font_path}")
            if not font_full_path.exists():
                return False
            
            font = ImageFont.truetype(str(font_full_path), 40)
            
            # 使用PIL检查字符是否被支持
            img = Image.new('RGB', (100, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                bbox = draw.textbbox((0, 0), char, font=font)
                return bbox[2] > bbox[0] and bbox[3] > bbox[1]
            except:
                return False
                
        except Exception as e:
            return False
    
    def get_font_for_char(self, char: str, font_list: list) -> str:
        """获取支持指定字符的字体"""
        for font_name in font_list:
            if font_name and self.check_font_support(font_name, char):
                return font_name
        return None
    
    def process_text_files(self):
        """处理文本文件"""
        text_ba_dir = Path("text_ba")
        text_dir = Path("text")
        
        if not text_ba_dir.exists():
            raise FileNotFoundError("错误：未找到text_ba目录")
        
        # 确保text目录存在
        text_dir.mkdir(exist_ok=True)
        
        # 处理所有txt文件
        txt_files = sorted([f for f in text_ba_dir.glob("*.txt")])
        
        for txt_file in txt_files:
            print(f"替换 'text_ba/{txt_file.name}' ...")
            
            # 读取原文件
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 应用字符替换
            for original_char, replacement_char in self.replacements.items():
                content = content.replace(original_char, replacement_char)
            
            # 写入到text目录
            output_file = text_dir / txt_file.name
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"处理完成，共处理了 {len(txt_files)} 个文件")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='字符替换工具')
    parser.add_argument('-b', '--book', required=True, help='书籍ID')
    parser.add_argument('-f', '--from', type=int, default=1, 
                       help='起始文件序号')
    parser.add_argument('-t', '--to', type=int, default=1, 
                       help='结束文件序号')
    
    args = parser.parse_args()
    
    try:
        replacer = CharacterReplacer(args.book, getattr(args, 'from'), args.to)
        replacer.process_text_files()
        
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
