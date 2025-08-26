#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vRain中文古籍刻本风格直排电子书制作工具
Python版本 by msyloveldx, 2025/08
原作者: shanleiguang@gmail.com
"""

import os
import sys
import argparse
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# 第三方库导入
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import Color, black, white, red, blue
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageFont, ImageDraw
import opencc

# 全局变量
SOFTWARE = 'vRain'
VERSION = 'v1.4'

class FontChecker:
    """字体检查工具类"""
    
    @staticmethod
    def check_font_support(font_path: str, char: str) -> bool:
        """检查字体是否支持某个字符"""
        try:
            font = ImageFont.truetype(font_path, 40)
            # 使用PIL检查字符是否被支持
            bbox = font.getbbox(char)
            return bbox[2] > bbox[0] and bbox[3] > bbox[1]
        except:
            return False

class ChineseConverter:
    """中文简繁转换工具"""
    
    def __init__(self):
        self.s2t = opencc.OpenCC('s2t')  # 简转繁
        self.t2s = opencc.OpenCC('t2s')  # 繁转简
    
    def simp_to_trad(self, text: str) -> str:
        """简体转繁体"""
        return self.s2t.convert(text)
    
    def trad_to_simp(self, text: str) -> str:
        """繁体转简体"""
        return self.t2s.convert(text)

class VRainPDFGenerator:
    """vRain PDF生成器主类"""
    
    def __init__(self, text_file, book_cfg_path, cover_path, from_page: int = 1, to_page: int = None,
                 test_pages: Optional[int] = None, compress: bool = False, 
                 verbose: bool = False):
        self.text_file = text_file
        self.book_cfg_path = book_cfg_path
        self.cover_path = cover_path
        self.from_page = from_page
        self.to_page = to_page
        self.test_pages = test_pages
        self.compress = compress
        self.verbose = verbose
        
        # 配置数据
        self.book_config = {}
        self.canvas_config = {}
        self.zh_numbers = {}
        self.fonts = {}
        self.font_paths = []
        self.text_fonts = []
        self.comment_fonts = []
        
        # PDF相关
        self.pdf_doc = None
        self.canvas = None
        self.page_chars_num = 0
        self.positions_left = []
        self.positions_right = []
        
        # 字体检查器和转换器
        self.font_checker = FontChecker()
        self.converter = ChineseConverter()
        
        self._load_configurations()
        self._setup_fonts()
        self._calculate_positions()
    
    # def _load_configurations(self):
    #     """加载配置文件"""
    #     # 检查必要的目录和文件
    #     book_dir = Path(f"books/{self.book_id}")
    #     if not book_dir.exists():
    #         raise FileNotFoundError(f"错误：未发现该书籍目录'books/{self.book_id}'！")
    #
    #     text_dir = book_dir / "text"
    #     if not text_dir.exists():
    #         raise FileNotFoundError(f"错误: 未发现该书籍文本目录'books/{self.book_id}/text'！")
    #
    #     book_cfg_path = book_dir / "book.cfg"
    #     if not book_cfg_path.exists():
    #         raise FileNotFoundError(f"错误：未发现该书籍排版配置文件'books/{self.book_id}/book.cfg'！")
    #
    #     # 加载中文数字映射
    #     zh_num_path = Path("db/num2zh_jid.txt")
    #     if zh_num_path.exists():
    #         with open(zh_num_path, 'r', encoding='utf-8') as f:
    #             for line in f:
    #                 line = line.strip()
    #                 if '|' in line:
    #                     num, zh = line.split('|', 1)
    #                     self.zh_numbers[int(num)] = zh
    #
    #     # 加载书籍配置
    #     self._load_config_file(book_cfg_path, self.book_config)
    #     print(f"\t标题：{self.book_config.get('title', '')}")
    #     print(f"\t作者：{self.book_config.get('author', '')}")
    #     print(f"\t背景：{self.book_config.get('canvas_id', '')}")
    #     print(f"\t每列字数：{self.book_config.get('row_num', '')}")
    #     print(f"\t是否无标点：{self.book_config.get('if_nocomma', '')}")
    #     print(f"\t标点归一化：{self.book_config.get('if_onlyperiod', '')}")
    #
    #     # 加载背景图配置
    #     canvas_id = self.book_config.get('canvas_id')
    #     if not canvas_id:
    #         raise ValueError("错误：未定义背景图ID 'canvas_id'！")
    #
    #     canvas_cfg_path = Path(f"canvas/{canvas_id}.cfg")
    #     canvas_jpg_path = Path(f"canvas/{canvas_id}.jpg")
    #
    #     if not canvas_cfg_path.exists():
    #         raise FileNotFoundError("错误：未发现背景图cfg配置文件！")
    #     if not canvas_jpg_path.exists():
    #         raise FileNotFoundError("错误：未发现背景图jpg图片文件！")
    #
    #     self._load_config_file(canvas_cfg_path, self.canvas_config)
    #     print(f"\t尺寸：{self.canvas_config.get('canvas_width', '')} x {self.canvas_config.get('canvas_height', '')}")
    #     print(f"\t列数：{self.canvas_config.get('leaf_col', '')}")

    def _load_configurations(self):
        """加载配置文件"""
        if not self.text_file.exists():
            raise FileNotFoundError(f"错误: 未发现该书籍文本{self.text_file}！")

        if not self.book_cfg_path.exists():
            raise FileNotFoundError(f"错误：未发现该书籍排版配置文件{self.book_cfg_path}！")

        # 加载中文数字映射
        zh_num_path = Path("db/num2zh_jid.txt")
        if zh_num_path.exists():
            with open(zh_num_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '|' in line:
                        num, zh = line.split('|', 1)
                        self.zh_numbers[int(num)] = zh

        # 加载书籍配置
        self._load_config_file(self.book_cfg_path, self.book_config)
        print(f"\t标题：{self.book_config.get('title', '')}")
        print(f"\t作者：{self.book_config.get('author', '')}")
        print(f"\t背景：{self.book_config.get('canvas_id', '')}")
        print(f"\t每列字数：{self.book_config.get('row_num', '')}")
        print(f"\t是否无标点：{self.book_config.get('if_nocomma', '')}")
        print(f"\t标点归一化：{self.book_config.get('if_onlyperiod', '')}")

        # 加载背景图配置
        canvas_id = self.book_config.get('canvas_id')
        if not canvas_id:
            raise ValueError("错误：未定义背景图ID 'canvas_id'！")

        canvas_cfg_path = Path(f"canvas/{canvas_id}.cfg")
        canvas_jpg_path = Path(f"canvas/{canvas_id}.jpg")

        if not canvas_cfg_path.exists():
            raise FileNotFoundError("错误：未发现背景图cfg配置文件！")
        if not canvas_jpg_path.exists():
            raise FileNotFoundError("错误：未发现背景图jpg图片文件！")

        self._load_config_file(canvas_cfg_path, self.canvas_config)
        print(f"\t尺寸：{self.canvas_config.get('canvas_width', '')} x {self.canvas_config.get('canvas_height', '')}")
        print(f"\t列数：{self.canvas_config.get('leaf_col', '')}")
    
    def _load_config_file(self, file_path: Path, config_dict: Dict):
        """加载配置文件到字典"""
        with open(file_path, 'r', encoding='utf-8') as f:
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
                        config_dict[key] = int(value)
                    elif value.replace('.', '').isdigit():
                        config_dict[key] = float(value)
                    else:
                        config_dict[key] = value
    
    def _setup_fonts(self):
        """设置字体"""
        font_names = ['font1', 'font2', 'font3', 'font4', 'font5']
        
        for font_name in font_names:
            font_file = self.book_config.get(font_name)
            if font_file:
                font_path = Path(f"fonts/{font_file}")
                if not font_path.exists():
                    print(f"警告：未发现字体'fonts/{font_file}'，跳过该字体")
                    continue
                
                self.font_paths.append(str(font_path))
                
                # 注册字体到reportlab
                try:
                    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                    self.fonts[font_name] = {
                        'path': str(font_path),
                        'text_size': self.book_config.get(f'text_{font_name}_size', 42),
                        'comment_size': self.book_config.get(f'comment_{font_name}_size', 30),
                        'rotate': self.book_config.get(f'{font_name}_rotate', 0)
                    }
                    print(f"成功加载字体：{font_file}")
                except Exception as e:
                    print(f"警告：字体 {font_file} 注册失败: {e}")
                    print("  提示：reportlab不支持PostScript轮廓的OTF字体，请使用TTF格式字体")
        
        # 设置字体数组
        text_fonts_array = str(self.book_config.get('text_fonts_array', '123'))
        comment_fonts_array = str(self.book_config.get('comment_fonts_array', '23'))
        
        available_fonts = list(self.fonts.keys())
        
        # 确保至少有一个可用字体
        if not available_fonts:
            print("警告：没有可用的字体！尝试使用默认字体")
            # 尝试加载默认字体
            default_fonts = ['HanaMinA.ttf', 'HanaMinB.ttf']
            for default_font in default_fonts:
                font_path = Path(f"fonts/{default_font}")
                if font_path.exists():
                    try:
                        pdfmetrics.registerFont(TTFont('default_font', str(font_path)))
                        self.fonts['default_font'] = {
                            'path': str(font_path),
                            'text_size': 42,
                            'comment_size': 30,
                            'rotate': 0
                        }
                        available_fonts.append('default_font')
                        break
                    except:
                        continue
        
        if not available_fonts:
            raise RuntimeError("错误：没有可用的字体文件！请检查fonts目录")
        
        for char in text_fonts_array:
            idx = int(char) - 1
            if 0 <= idx < len(available_fonts):
                self.text_fonts.append(available_fonts[idx])
        
        for char in comment_fonts_array:
            idx = int(char) - 1
            if 0 <= idx < len(available_fonts):
                self.comment_fonts.append(available_fonts[idx])
        
        # 确保至少有一个字体
        if not self.text_fonts and available_fonts:
            self.text_fonts.append(available_fonts[0])
        if not self.comment_fonts and available_fonts:
            self.comment_fonts.append(available_fonts[0])
    
    def _calculate_positions(self):
        """计算文字位置"""
        canvas_width = int(self.canvas_config.get('canvas_width', 2480))
        canvas_height = int(self.canvas_config.get('canvas_height', 1860))
        margins_top = int(self.canvas_config.get('margins_top', 200))
        margins_bottom = int(self.canvas_config.get('margins_bottom', 50))
        margins_left = int(self.canvas_config.get('margins_left', 50))
        margins_right = int(self.canvas_config.get('margins_right', 50))
        col_num = int(self.canvas_config.get('leaf_col', 24))
        lc_width = int(self.canvas_config.get('leaf_center_width', 120))
        row_num = int(self.book_config.get('row_num', 30))
        row_delta_y = int(self.book_config.get('row_delta_y', 10))
        
        # 计算列宽、行高
        cw = (canvas_width - margins_left - margins_right - lc_width) / col_num
        rh = (canvas_height - margins_top - margins_bottom) / row_num
        
        # 生成文字坐标
        self.positions_left = []
        self.positions_right = []
        
        for i in range(1, col_num + 1):
            for j in range(1, row_num + 1):
                if i <= col_num / 2:
                    pos_x = canvas_width - margins_right - cw * i
                else:
                    pos_x = canvas_width - margins_right - cw * i - lc_width
                
                pos_y = canvas_height - margins_top - rh * j + row_delta_y
                
                self.positions_left.append((pos_x, pos_y))
                self.positions_right.append((pos_x + cw/2, pos_y))
        
        self.page_chars_num = col_num * row_num
    
    def get_font_for_char(self, char: str, font_list: List[str]) -> Optional[str]:
        """获取支持指定字符的字体"""
        for font_name in font_list:
            if font_name in self.fonts:
                font_path = self.fonts[font_name]['path']
                if self.font_checker.check_font_support(font_path, char):
                    return font_name
        return None
    
    def try_char_conversion(self, char: str) -> Tuple[str, Optional[str]]:
        """尝试字符转换以改善字体支持"""
        if not self.book_config.get('try_st', 0):
            return char, None
        
        # 尝试简繁转换
        char_s2t = self.converter.simp_to_trad(char)
        char_t2s = self.converter.trad_to_simp(char)
        
        main_font = self.text_fonts[0] if self.text_fonts else None
        
        if char_s2t != char:
            font_s2t = self.get_font_for_char(char_s2t, self.text_fonts)
            if font_s2t == main_font:
                return char_s2t, font_s2t
        
        if char_t2s != char:
            font_t2s = self.get_font_for_char(char_t2s, self.text_fonts)
            if font_t2s == main_font:
                return char_t2s, font_t2s
        
        return char, None
    
    # def load_texts(self) -> List[str]:
    #     """加载文本文件"""
    #     texts = ['']  # 索引0为空，从1开始
    #     text_dir = Path(f"books/{self.book_id}/text")
    #
    #     # 检查是否存在特殊文件
    #     has_000 = (text_dir / "000.txt").exists()
    #     has_999 = (text_dir / "999.txt").exists()
    #
    #     print("读取该书籍全部文本文件'books/{}/text/*.txt'...".format(self.book_id), end='')
    #
    #     # 获取所有txt文件并排序
    #     txt_files = sorted([f for f in text_dir.glob("*.txt") if f.is_file()])
    #
    #     for txt_file in txt_files:
    #         print(f"读取文件: {txt_file.name}")
    #         content = ""
    #         with open(txt_file, 'r', encoding='utf-8') as f:
    #             for line in f:
    #                 line = line.strip()
    #                 if not line:
    #                     continue
    #
    #                 # 标点符号处理
    #                 line = self._process_punctuation(line)
    #
    #                 # 处理特殊字符
    #                 line = line.replace('@', ' ')  # @代表空格
    #
    #                 # 计算段落补齐空格
    #                 line = self._calculate_paragraph_spaces(line)
    #                 content += line
    #
    #         print(f"文件 {txt_file.name} 处理后内容长度: {len(content)}")
    #         texts.append(content)
    #
    #     print(f"{len(texts)-1}个文本文件")
    #     return texts

    def load_texts(self, text_file):
        """加载文本文件"""
        print(f"读取文件: {text_file.name}")
        content = ""
        
        # 直接读取整个文件，保持原始格式
        with open(text_file, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        print(f"文件 {text_file.name} 原始内容长度: {len(raw_content)}")
        
        # 简化处理：只做基本的标点符号处理
        for line in raw_content.split('\n'):
            if line.strip():  # 只有非空行才处理
                # 标点符号处理
                line = self._process_punctuation(line.strip())
                # 处理特殊字符
                line = line.replace('@', ' ')  # @代表空格
                content += line
            else:
                # 保留换行符作为分隔
                content += '\n'

        print(f"文件 {text_file.name} 处理后内容长度: {len(content)}")
        return content

    def _process_punctuation(self, text: str) -> str:
        """处理标点符号"""
        # 标点符号替换
        exp_replace_comma = self.book_config.get('exp_replace_comma', '')
        if exp_replace_comma:
            for replacement in exp_replace_comma.split('|'):
                if len(replacement) >= 2:
                    old_char, new_char = replacement[0], replacement[1]
                    text = text.replace(old_char, new_char)
        
        # 数字替换
        exp_replace_number = self.book_config.get('exp_replace_number', '')
        if exp_replace_number:
            for replacement in exp_replace_number.split('|'):
                if len(replacement) >= 2:
                    old_char, new_char = replacement[0], replacement[1]
                    text = text.replace(old_char, new_char)
        
        # 标点符号删除
        exp_delete_comma = self.book_config.get('exp_delete_comma', '')
        if exp_delete_comma:
            for char in exp_delete_comma.split('|'):
                text = text.replace(char, '')
        
        # 无标点模式
        if self.book_config.get('if_nocomma') == 1:
            exp_nocomma = self.book_config.get('exp_nocomma', '')
            if exp_nocomma:
                for char in exp_nocomma.split('|'):
                    text = text.replace(char, '')
        
        # 标点符号归一化
        if self.book_config.get('if_onlyperiod') == 1:
            exp_onlyperiod = self.book_config.get('exp_onlyperiod', '')
            if exp_onlyperiod:
                for char in exp_onlyperiod.split('|'):
                    text = text.replace(char, '。')
                # 去除重复句号
                while '。。' in text:
                    text = text.replace('。。', '。')
                text = text.lstrip('。')
        
        return text
    
    def _calculate_paragraph_spaces(self, text: str) -> str:
        """计算段落末尾需要补齐的空格数"""
        row_num = int(self.book_config.get('row_num', 30))
        
        # 保存原始文本
        original_text = text
        
        # 计算批注文本占用长度
        comment_length = 0
        import re
        comments = re.findall(r'【(.*?)】', text)
        for comment in comments:
            comment_chars = len(comment)
            if comment_chars % 2 == 0:
                comment_length += comment_chars // 2
            else:
                comment_length += comment_chars // 2 + 1
        
        # 去除批注文本后的正文
        text_without_comments = re.sub(r'【.*?】', '', text)
        
        # 去除不占字符位的标点符号
        text_comma_nop = self.book_config.get('text_comma_nop', '')
        comment_comma_nop = self.book_config.get('comment_comma_nop', '')
        
        if text_comma_nop:
            for char in text_comma_nop.split('|'):
                text_without_comments = text_without_comments.replace(char, '')
        
        # 处理书名号
        if self.book_config.get('if_book_vline') == 1:
            text_without_comments = text_without_comments.replace('《', '').replace('》', '')
        
        chars_count = len(text_without_comments) + comment_length
        
        # 计算需要补齐的空格数
        if chars_count > 0:
            spaces_needed = row_num - (chars_count % row_num)
            if 0 < spaces_needed < row_num:
                original_text += ' ' * spaces_needed
        
        return original_text
    
    def _should_skip_char(self, char: str, chars: List[str], char_index: int) -> bool:
        """判断是否应该跳过字符"""
        # 跳过空白字符
        if char in [' ', '\n', '\r', '\t']:
            return True
        
        # 跳过特殊控制字符
        if char in ['%', '$', '&']:
            return True
        
        # 处理书名号（如果配置为侧线）
        if char in ['《', '》'] and self.book_config.get('if_book_vline') == 1:
            return True
        
        # 处理@符号（空格）
        if char == '@':
            return True
        
        return False
    
    def _detect_chapter_title(self, text: str, start_index: int) -> Tuple[Optional[str], int]:
        """检测章节标题
        返回: (章节标题, 章节标题结束位置)
        """
        import re
        
        # 从当前位置开始查找章节标题
        remaining_text = text[start_index:]
        
        # 匹配章节标题模式：第X章 标题名
        chapter_pattern = r'^第(\d+)章\s+([^\n\r]+)'
        match = re.match(chapter_pattern, remaining_text)
        
        if match:
            chapter_title = match.group(0)  # 完整的章节标题
            end_pos = start_index + match.end()
            return chapter_title, end_pos
        
        return None, start_index
    
    def _find_chapter_end(self, text: str, start_index: int) -> int:
        """查找章节结束位置（下一章开始或文本结束）"""
        import re
        
        # 从章节内容开始位置查找下一章
        remaining_text = text[start_index:]
        next_chapter_pattern = r'第\d+章\s+'
        
        match = re.search(next_chapter_pattern, remaining_text)
        if match:
            return start_index + match.start()
        
        # 如果没有找到下一章，返回文本结束位置
        return len(text)
    
    def _find_comment_end(self, chars: List[str], start_index: int) -> int:
        """查找批注结束位置"""
        for i in range(start_index + 1, len(chars)):
            if chars[i] == '】':
                return i
        return -1
    
    def _start_new_page(self, c, page_num: int, canvas_width: float, canvas_height: float, background_path: Path):
        """开始新页面"""
        print(f"创建新PDF页[{page_num}]...")
        
        # 添加背景图
        if background_path.exists():
            c.drawImage(str(background_path), 0, 0, canvas_width, canvas_height)
        else:
            print(f"警告：背景图 {background_path} 不存在")
        
        # 添加页面标题
        self._add_page_title(c, 0, canvas_width, canvas_height)  # 使用固定标题
        
        # 添加页码
        self._add_page_number(c, page_num, canvas_width, canvas_height)
    
    def _draw_char_at_position(self, c, char: str, position_index: int, is_chapter_title: bool = False):
        """在指定位置绘制字符"""
        if position_index >= len(self.positions_left):
            return
        
        # 获取合适的字体
        font_name = self.get_font_for_char(char, self.text_fonts)
        if not font_name:
            font_name = self.text_fonts[0] if self.text_fonts else None
        
        if not font_name or font_name not in self.fonts:
            print(f"警告：无法找到字符 '{char}' 的合适字体")
            return
        
        # 尝试字符转换
        display_char, converted_font = self.try_char_conversion(char)
        if converted_font:
            font_name = converted_font
            char = display_char
        
        # 设置字体和大小
        if is_chapter_title:
            # 章节标题使用稍大的字体
            font_size = int(self.fonts[font_name]['text_size'] * 1.2)
        else:
            font_size = self.fonts[font_name]['text_size']
            
        c.setFont(font_name, font_size)
        c.setFillColor(black)
        
        # 获取位置
        x, y = self.positions_left[position_index]
        
        # 调整字符位置（居中）
        x += (self._get_column_width() - font_size) / 2
        
        try:
            c.drawString(x, y, char)
        except Exception as e:
            print(f"警告：无法绘制字符 '{char}': {e}")
    
    def _draw_chapter_title(self, c, chapter_title: str, canvas_width: float, canvas_height: float):
        """在第一列绘制章节标题"""
        if not chapter_title or not self.text_fonts:
            return 0
        
        font_name = self.text_fonts[0]
        font_size = int(self.fonts[font_name]['text_size'] * 1.2)  # 章节标题稍大
        c.setFont(font_name, font_size)
        c.setFillColor(red)  # 章节标题用红色
        
        # 获取第一列的位置信息
        row_num = int(self.book_config.get('row_num', 30))
        chars_drawn = 0
        
        # 在第一列绘制章节标题
        for i, char in enumerate(chapter_title):
            if i >= row_num:  # 如果章节标题超过一列长度，截断
                break
                
            if chars_drawn < len(self.positions_left):
                x, y = self.positions_left[chars_drawn]
                x += (self._get_column_width() - font_size) / 2
                
                try:
                    c.drawString(x, y, char)
                    chars_drawn += 1
                except Exception as e:
                    print(f"警告：无法绘制章节标题字符 '{char}': {e}")
        
        return chars_drawn
    
    def print_welcome(self):
        """打印欢迎信息"""
        print('-' * 60)
        print(f"\t{SOFTWARE} {VERSION}，兀雨古籍刻本电子书制作工具")
        print(f"\t作者：GitHub@shanleiguang 小红书@兀雨书屋")
        print(f"\tPython版本转换：msyloveldx")
        print('-' * 60)
    
    def generate_pdf(self, text_file):
        """生成PDF文件"""
        self.print_welcome()
        
        if self.test_pages:
            print(f"注意：-z 测试模式，仅输出{self.test_pages}页用于调试排版参数！")
        
        # 加载文本
        text_content = self.load_texts(text_file)
        
        # 创建PDF文件名
        title = self.book_config.get('title', '')
        if self.from_page == 1 and self.to_page is None:
            # 默认情况，输出全部内容
            pdf_filename = f"《{title}》文本"
        elif self.to_page is None:
            # 从指定页开始输出全部内容
            pdf_filename = f"《{title}》文本{self.from_page}至末"
        else:
            # 指定页数范围
            pdf_filename = f"《{title}》文本{self.from_page}至{self.to_page}"
        
        if self.test_pages:
            pdf_filename += '_test'
        
        pdf_path = Path(f"results/{pdf_filename}.pdf")
        
        # 确保results目录存在
        pdf_path.parent.mkdir(exist_ok=True)
        
        # 使用reportlab创建PDF
        canvas_width = float(self.canvas_config.get('canvas_width', 2480))
        canvas_height = float(self.canvas_config.get('canvas_height', 1860))
        
        from reportlab.pdfgen import canvas as pdf_canvas
        c = pdf_canvas.Canvas(str(pdf_path), pagesize=(canvas_width, canvas_height))
        
        # 设置PDF元数据
        c.setTitle(self.book_config.get('title', ''))
        c.setAuthor(self.book_config.get('author', ''))
        c.setCreator(f"{SOFTWARE} {VERSION}，古籍刻本直排电子书制作工具")
        
        # 添加封面
        self._add_cover(c, canvas_width, canvas_height)
        
        # 处理文本并生成页面
        self._process_texts_and_generate_pages(c, text_content, canvas_width, canvas_height)
        
        # 保存PDF
        c.save()
        
        print(f"生成PDF文件'results/{pdf_filename}.pdf'...完成！")
        
        # 压缩处理
        if self.compress:
            self._compress_pdf(pdf_path)
        else:
            print("建议：使用'-c'参数对PDF文件进行压缩！")
    
    # def _add_cover(self, c, canvas_width: float, canvas_height: float):
    #     """添加封面"""
    #     cover_path = Path(f"books/{self.book_id}/cover.jpg")
    #
    #     if cover_path.exists():
    #         print(f"发现封面图片'{self.book_id}/books/{self.book_id}/cover.jpg' ...")
    #         c.drawImage(str(cover_path), 0, 0, canvas_width, canvas_height)
    #     else:
    #         print(f"未发现封面文件'{self.book_id}/books/{self.book_id}/cover.jpg'，创建简易封面...")
    #         self._create_simple_cover(c, canvas_width, canvas_height)
    #
    #     c.showPage()  # 结束封面页

    def _add_cover(self, c, canvas_width: float, canvas_height: float):
        """添加封面"""
        if self.cover_path.exists():
            print(f"发现封面图片{self.cover_path}")
            c.drawImage(str(self.cover_path), 0, 0, canvas_width, canvas_height)
        else:
            print(f"未发现封面图片{self.cover_path}，创建简易封面...")
            self._create_simple_cover(c, canvas_width, canvas_height)

        c.showPage()  # 结束封面页
    
    def _create_simple_cover(self, c, canvas_width: float, canvas_height: float):
        """创建简易封面"""
        # 背景
        c.setFillColor(white)
        c.rect(0, 0, canvas_width, canvas_height, fill=1)
        
        # 中间竖线
        plx = canvas_width / 2
        if canvas_width < canvas_height:
            plx = canvas_width
        
        c.setStrokeColor(Color(0.8, 0.8, 0.8))  # 浅灰色
        c.setLineWidth(1)
        c.line(plx - 50, 0, plx - 50, canvas_height)
        c.line(plx + 50, 0, plx + 50, canvas_height)
        
        # 横线
        for i in range(int(canvas_height // 200) + 1):
            y = canvas_height - 200 * i
            if y >= 0:
                c.line(plx - 50, y, plx + 50, y)
        
        # 粗竖线
        c.setStrokeColor(Color(0.5, 0.5, 0.5))  # 灰色
        c.setLineWidth(20)
        c.line(plx, 0, plx, canvas_height)
        
        # 标题文字
        title = self.book_config.get('title', '')
        cover_title_font_size = int(self.book_config.get('cover_title_font_size', 120))
        cover_title_y = int(self.book_config.get('cover_title_y', 200))
        
        if self.text_fonts:
            c.setFont(self.text_fonts[0], cover_title_font_size)
            c.setFillColor(black)
            
            for i, char in enumerate(title):
                x = cover_title_font_size
                y = canvas_height - cover_title_y - cover_title_font_size * i * 1.2
                c.drawString(x, y, char)
        
        # 作者文字
        author = self.book_config.get('author', '')
        cover_author_font_size = int(self.book_config.get('cover_author_font_size', 60))
        cover_author_y = int(self.book_config.get('cover_author_y', 600))
        
        if self.text_fonts:
            c.setFont(self.text_fonts[0], cover_author_font_size)
            
            for i, char in enumerate(author):
                x = cover_author_font_size / 2
                y = canvas_height - cover_author_y - cover_author_font_size * i * 1.2
                c.drawString(x, y, char)
    
    def _process_texts_and_generate_pages(self, c, text_content: str, 
                                        canvas_width: float, canvas_height: float):
        """处理文本并生成页面（支持章节处理）"""
        canvas_id = self.book_config.get('canvas_id')
        background_path = Path(f"canvas/{canvas_id}.jpg")
        
        if not text_content or not text_content.strip():
            print("警告：文本内容为空")
            return
        
        # 检查是否启用章节模式
        enable_chapter_mode = self.book_config.get('enable_chapter_mode', 0)
        print(f"章节模式: {'启用' if enable_chapter_mode else '禁用'}")
        
        if enable_chapter_mode:
            self._process_with_chapters(c, text_content, canvas_width, canvas_height, background_path)
        else:
            self._process_without_chapters(c, text_content, canvas_width, canvas_height, background_path)
    
    def _process_with_chapters(self, c, text_content: str, canvas_width: float, canvas_height: float, background_path: Path):
        """章节模式处理文本"""
        print(f"处理文本，总字符数: {len(text_content)}")
        
        # 解析章节
        chapters = self._parse_chapters(text_content)
        print(f"检测到 {len(chapters)} 个章节")
        
        page_num = 0
        total_processed_chars = 0
        
        for chapter_index, (chapter_title, chapter_content) in enumerate(chapters):
            if self.test_pages and page_num >= self.test_pages:
                break
            
            print(f"处理章节: {chapter_title}")
            
            # 开始新页面（每章一页）
            current_page = self.from_page + page_num
            self._start_new_page(c, current_page, canvas_width, canvas_height, background_path)
            
            # 在第一列绘制章节标题
            chapter_chars_used = self._draw_chapter_title(c, chapter_title, canvas_width, canvas_height)
            
            # 计算内容开始位置（跳过第一列）
            row_num = int(self.book_config.get('row_num', 30))
            content_start_pos = row_num  # 从第二列开始
            page_char_count = content_start_pos
            
            print(f"章节内容长度: {len(chapter_content)}, 内容开始位置: {content_start_pos}, 页面总字符数: {self.page_chars_num}")
            
            # 处理章节内容
            chars = list(chapter_content)
            char_index = 0
            
            while char_index < len(chars):
                # 检查是否需要换页
                if page_char_count >= self.page_chars_num:
                    print(f"换页：当前字符位置 {page_char_count} >= 页面字符数 {self.page_chars_num}")
                    c.showPage()
                    page_num += 1
                    current_page = self.from_page + page_num
                    self._start_new_page(c, current_page, canvas_width, canvas_height, background_path)
                    page_char_count = 0  # 新页面从第一列开始
                
                char = chars[char_index]
                char_index += 1
                
                # 处理特殊字符和控制符
                if self._should_skip_char(char, chars, char_index - 1):
                    continue
                
                # 处理批注
                if char == '【':
                    comment_end = self._find_comment_end(chars, char_index - 1)
                    if comment_end != -1:
                        char_index = comment_end + 1
                        continue
                    else:
                        continue
                
                # 绘制字符
                if page_char_count < len(self.positions_left):
                    print(f"绘制字符 '{char}' 在位置 {page_char_count}")
                    self._draw_char_at_position(c, char, page_char_count)
                    page_char_count += 1
                    total_processed_chars += 1
                else:
                    print(f"警告：字符位置 {page_char_count} 超出范围 {len(self.positions_left)}")
            
            # 章节结束，准备下一页
            if chapter_index < len(chapters) - 1:  # 不是最后一章
                c.showPage()
                page_num += 1
        
        # 完成最后一页
        if page_char_count > 0:
            c.showPage()
        
        actual_pages = page_num + 1
        print(f"生成完成，共 {actual_pages} 页，处理了 {total_processed_chars} 个字符")
    
    def _process_without_chapters(self, c, text_content: str, canvas_width: float, canvas_height: float, background_path: Path):
        """非章节模式处理文本（原逻辑）"""
        # 将文本转换为字符列表
        chars = list(text_content)
        total_chars = len(chars)
        print(f"处理文本，总字符数: {total_chars}")
        
        # 计算需要跳过的字符数（如果指定了起始页）
        chars_to_skip = 0
        if self.from_page > 1:
            chars_to_skip = (self.from_page - 1) * self.page_chars_num
            print(f"从第 {self.from_page} 页开始，跳过前 {chars_to_skip} 个字符")
        
        # 计算最大输出字符数（如果指定了结束页）
        max_chars_to_process = None
        if self.to_page is not None and self.to_page >= self.from_page:
            page_count = self.to_page - self.from_page + 1
            max_chars_to_process = page_count * self.page_chars_num
            print(f"输出 {self.from_page} 到 {self.to_page} 页，共 {page_count} 页，最多处理 {max_chars_to_process} 个字符")
        else:
            print(f"从第 {self.from_page} 页开始，输出全部剩余内容")
        
        # 字符处理状态
        char_index = 0
        processed_chars = 0  # 已处理的有效字符数
        page_num = 0
        page_char_count = 0  # 当前页已放置的字符数
        
        # 跳过指定数量的有效字符
        while char_index < total_chars and processed_chars < chars_to_skip:
            char = chars[char_index]
            char_index += 1
            
            # 跳过特殊字符时不计入字符数
            if self._should_skip_char(char, chars, char_index - 1):
                continue
            
            # 处理批注
            if char == '【':
                comment_end = self._find_comment_end(chars, char_index - 1)
                if comment_end != -1:
                    char_index = comment_end + 1
                    continue
                else:
                    continue
            
            processed_chars += 1
        
        print(f"跳过了 {processed_chars} 个有效字符，从字符索引 {char_index} 开始处理")
        
        # 重置计数器，开始实际页面生成
        processed_chars = 0
        page_char_count = 0
        
        # 开始第一页
        self._start_new_page(c, self.from_page, canvas_width, canvas_height, background_path)
        
        while char_index < total_chars:
            # 检查测试页数限制
            if self.test_pages and page_num >= self.test_pages:
                break
            
            # 检查是否达到指定的最大字符数
            if max_chars_to_process is not None and processed_chars >= max_chars_to_process:
                print(f"已达到指定页数范围，停止处理")
                break
                
            # 检查是否需要换页
            if page_char_count >= self.page_chars_num:
                c.showPage()
                page_num += 1
                page_char_count = 0
                current_page = self.from_page + page_num
                self._start_new_page(c, current_page, canvas_width, canvas_height, background_path)
            
            char = chars[char_index]
            char_index += 1
            
            # 处理特殊字符和控制符
            if self._should_skip_char(char, chars, char_index - 1):
                continue
            
            # 处理批注
            if char == '【':
                comment_end = self._find_comment_end(chars, char_index - 1)
                if comment_end != -1:
                    comment_text = ''.join(chars[char_index:comment_end])
                    # 处理批注文本（简化处理，可以后续优化）
                    char_index = comment_end + 1
                    continue
                else:
                    continue
            
            # 绘制字符
            if page_char_count < len(self.positions_left):
                self._draw_char_at_position(c, char, page_char_count)
                page_char_count += 1
                processed_chars += 1
        
        # 完成最后一页
        if page_char_count > 0:
            c.showPage()
        
        actual_pages = page_num + 1
        actual_page_range = f"{self.from_page} 到 {self.from_page + page_num}"
        print(f"生成完成，共 {actual_pages} 页（第 {actual_page_range} 页）")
    
    def _parse_chapters(self, text_content: str) -> List[Tuple[str, str]]:
        """解析章节
        返回: [(章节标题, 章节内容), ...]
        """
        import re
        
        chapters = []
        
        # 查找所有章节标题
        chapter_pattern = r'第(\d+)章\s+([^\n\r]+)'
        matches = list(re.finditer(chapter_pattern, text_content))
        
        print(f"章节解析：找到 {len(matches)} 个章节")
        
        if not matches:
            # 如果没有找到章节，将整个文本作为一个章节
            print("未找到章节，将整个文本作为一个章节")
            return [("", text_content)]
        
        for i, match in enumerate(matches):
            chapter_title = match.group(0)  # 完整的章节标题
            content_start = match.end()
            
            # 查找章节内容结束位置
            if i + 1 < len(matches):
                content_end = matches[i + 1].start()
            else:
                content_end = len(text_content)
            
            chapter_content = text_content[content_start:content_end].strip()
            print(f"章节 {i+1}: '{chapter_title}', 内容长度: {len(chapter_content)}")
            chapters.append((chapter_title, chapter_content))
        
        return chapters
    
    def _add_page_title(self, c, text_id: int, canvas_width: float, canvas_height: float):
        """添加页面标题"""
        title = self.book_config.get('title', '')
        title_postfix = self.book_config.get('title_postfix', '')
        
        if title_postfix and text_id > 0:
            # 处理标题后缀
            zh_num = self.zh_numbers.get(text_id, str(text_id))
            title_postfix = title_postfix.replace('X', zh_num)
            if text_id == 0:
                title_postfix = '序'
            full_title = title + title_postfix
        else:
            full_title = '  ' + title
        
        title_font_size = int(self.book_config.get('title_font_size', 70))
        title_y = int(self.book_config.get('title_y', 1200))
        title_ydis = float(self.book_config.get('title_ydis', 1.2))
        
        if self.text_fonts:
            c.setFont(self.text_fonts[0], title_font_size)
            c.setFillColor(black)
            
            for i, char in enumerate(full_title):
                x = canvas_width / 2 - title_font_size / 2
                y = title_y - title_font_size * i * title_ydis
                c.drawString(x, y, char)
    

    
    def _get_column_width(self):
        """获取列宽"""
        canvas_width = int(self.canvas_config.get('canvas_width', 2480))
        margins_left = int(self.canvas_config.get('margins_left', 50))
        margins_right = int(self.canvas_config.get('margins_right', 50))
        col_num = int(self.canvas_config.get('leaf_col', 24))
        lc_width = int(self.canvas_config.get('leaf_center_width', 120))
        
        return (canvas_width - margins_left - margins_right - lc_width) / col_num
    
    def _add_page_number(self, c, page_num: int, canvas_width: float, canvas_height: float):
        """添加页码"""
        zh_page_num = self.zh_numbers.get(page_num, str(page_num))
        pager_font_size = int(self.book_config.get('pager_font_size', 30))
        pager_y = int(self.book_config.get('pager_y', 500))
        title_ydis = float(self.book_config.get('title_ydis', 1.2))
        
        if self.text_fonts:
            c.setFont(self.text_fonts[0], pager_font_size)
            c.setFillColor(black)
            
            for i, char in enumerate(zh_page_num):
                x = canvas_width / 2 - pager_font_size / 2
                y = pager_y - pager_font_size * i * title_ydis
                c.drawString(x, y, char)
    
    def _compress_pdf(self, pdf_path: Path):
        """压缩PDF文件"""
        import subprocess
        
        output_path = pdf_path.parent / f"{pdf_path.stem}_已压缩.pdf"
        
        try:
            # 使用Ghostscript压缩PDF
            cmd = [
                'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/screen', '-dNOPAUSE', '-dQUIET', '-dBATCH',
                f'-sOutputFile={output_path}', str(pdf_path)
            ]
            
            subprocess.run(cmd, check=True)
            pdf_path.unlink()  # 删除原文件
            print(f"压缩PDF文件'{output_path}'...完成！")
            
        except subprocess.CalledProcessError:
            print("警告：PDF压缩失败，请检查是否安装了Ghostscript")
        except FileNotFoundError:
            print("警告：未找到Ghostscript，无法压缩PDF")

def print_help():
    """打印帮助信息"""
    help_text = f"""
    ./{SOFTWARE}\t{VERSION}，兀雨古籍刻本直排电子书制作工具
    -h\t帮助信息
    -v\t显示更多信息
    -c\t压缩PDF
    -z\t测试模式，仅输出指定页数，生成带test标识的PDF文件，用于调试参数
    -b\t书籍ID
      \t书籍文本需保存在书籍ID的text目录下，多文本时采用001、002...不间断命名以确保顺序处理
    -f\t书籍文本的起始序号，注意不是文件名的数字编号，而是顺序排列的序号
    -t\t书籍文本的结束序号，注意不是文件名的数字编号，而是顺序排列的序号
        作者：GitHub@shanleiguang, 小红书@兀雨书屋，2025
        Python版本转换：GitHub@msyloveldx
    """
    print(help_text)

def main():
    """主函数"""
    # print_help()
    
    try:
        # 示例1：处理史记古籍（非章节模式）
        text_file = Path('books/01/text/000.txt')
        book_cfg_path = Path('books/01/book.cfg')
        cover_path = Path('books/01/cover.jpg')
        
        # 示例2：处理神武天帝小说（章节模式）
        # text_file = Path('books/04/text/神武天帝.txt')
        # book_cfg_path = Path('books/04/book.cfg')
        # cover_path = Path('books/04/cover.jpg')
        
        # 章节模式测试：只生成前3页
        # generator = VRainPDFGenerator(
        #     text_file = text_file,
        #     book_cfg_path = book_cfg_path,
        #     cover_path = cover_path,
        #     test_pages=3,  # 测试模式，只生成3页
        #     verbose=True
        # )
        
        # 示例3：输出指定页数范围
        # generator = VRainPDFGenerator(
        #     text_file = text_file,
        #     book_cfg_path = book_cfg_path,
        #     cover_path = cover_path,
        #     from_page=1,
        #     to_page=3,
        #     verbose=True
        # )
        
        # 示例4：从指定页开始输出全部内容
        generator = VRainPDFGenerator(
            text_file = text_file,
            book_cfg_path = book_cfg_path,
            cover_path = cover_path,
            from_page=1,
            verbose=True
        )
        
        generator.generate_pdf(text_file)
        
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
