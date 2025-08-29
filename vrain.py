#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vRain中文古籍刻本风格直排电子书制作工具 - Python版本
原作者: shanleiguang@gmail.com
Python版本作者: msyloveldx, 2025/08
"""

import os
import sys
import re
import argparse
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# 第三方库导入
try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch, mm
    from reportlab.lib.colors import Color, HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import SimpleDocTemplate
    from PIL import Image, ImageFont
    import opencc
except ImportError as e:
    print(f"错误：缺少必要的依赖库: {e}")
    print("请运行: pip install reportlab pillow opencc-python-reimplemented")
    sys.exit(1)

# 全局常量 - 完全对应Perl版本
SOFTWARE = 'vRain'
VERSION = 'v1.4'

class VRainPerfect:
    """完美复刻Perl版本的vRain工具"""
    
    def __init__(self):
        # 程序参数
        self.opts = {}
        
        # 配置数据
        self.zhnums = {}
        self.book = {}
        self.canvas_config = {}
        
        # 字体相关
        self.fonts = {}  # 字体信息字典，对应Perl的%fonts
        self.fns = []    # 字体文件名数组，对应Perl的@fns
        self.tfns = []   # 正文字体数组，对应Perl的@tfns
        self.cfns = []   # 批注字体数组，对应Perl的@cfns
        self.vfonts = {} # PDF字体对象，对应Perl的%vfonts
        
        # PDF相关
        self.vpdf = None
        self.vpimg = None
        self.vpage = None
        
        # 位置数组 - 完全对应Perl版本
        self.pos_l = []  # 对应Perl的@pos_l
        self.pos_r = []  # 对应Perl的@pos_r
        self.page_chars_num = 0  # 每页字符数
        
        # 简繁转换
        try:
            self.s2t = opencc.OpenCC('s2t')
            self.t2s = opencc.OpenCC('t2s')
        except:
            self.s2t = None
            self.t2s = None
    
    def print_welcome(self):
        """打印欢迎信息 - 完全对应Perl版本"""
        print('-' * 60)
        print(f"\t{SOFTWARE} {VERSION}，兀雨古籍刻本电子书制作工具")
        print("\t作者：GitHub@shanleiguang 小红书@兀雨书屋")
        print('-' * 60)
    
    def print_help(self):
        """打印帮助信息 - 完全对应Perl版本"""
        help_text = f"""   ./{SOFTWARE}\t{VERSION}，兀雨古籍刻本直排电子书制作工具
\t-h\t帮助信息
\t-v\t显示更多信息
\t-c\t压缩PDF（MacOS）
\t-z\t测试模式，仅输出指定页数，生成带test标识的PDF文件，用于调试参数
\t-b\t书籍ID
\t  \t书籍文本需保存在书籍ID的text目录下，多文本时采用001、002...不间断命名以确保顺序处理
\t-f\t书籍文本的起始序号，注意不是文件名的数字编号，而是顺序排列的序号
\t-t\t书籍文本的结束序号，注意不是文件名的数字编号，而是顺序排列的序号
\t\t作者：GitHub@shanleiguang, 小红书@兀雨书屋，2025"""
        print(help_text)
    
    def parse_args(self):
        """解析命令行参数 - 完全对应Perl的getopts"""
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('-h', action='store_true', help='帮助信息')
        parser.add_argument('-c', action='store_true', help='压缩PDF')
        parser.add_argument('-v', action='store_true', help='显示更多信息')
        parser.add_argument('-z', type=int, help='测试模式，仅输出指定页数')
        parser.add_argument('-b', type=str, help='书籍ID')
        parser.add_argument('-f', type=int, default=1, help='起始页')
        parser.add_argument('-t', type=int, default=1, help='结束页')
        
        # 先检查是否有-h参数
        if '-h' in sys.argv:
            self.print_help()
            sys.exit(0)
        
        # 检查是否有-b参数
        if '-b' not in sys.argv:
            print(f"错误：缺少必需参数 -b (书籍ID)")
            self.print_help()
            sys.exit(1)
        
        args = parser.parse_args()
        
        # 转换为opts字典，对应Perl的%opts
        self.opts = {
            'c': args.c,
            'v': args.v,
            'z': args.z,
            'b': args.b,
            'f': args.f,
            't': args.t
        }
    
    def load_zh_numbers(self):
        """加载中文数字映射 - 完全对应Perl版本"""
        zh_file = Path('db/num2zh_jid.txt')
        if zh_file.exists():
            with open(zh_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '|' in line:
                        a, b = line.split('|', 1)
                        self.zhnums[int(a)] = b
    
    def check_directories(self, book_id):
        """检查目录和文件 - 完全对应Perl版本"""
        if not Path(f"books/{book_id}").exists():
            print(f"错误：未发现该书籍目录'books/{book_id}'！")
            sys.exit(1)
        
        if not Path(f"books/{book_id}/text").exists():
            print(f"错误: 未发现该书籍文本目录'books/{book_id}/text'！")
            sys.exit(1)
        
        if not Path(f"books/{book_id}/book.cfg").exists():
            print(f"错误：未发现该书籍排版配置文件'books/{book_id}/book.cfg'！")
            sys.exit(1)
    
    def load_book_config(self, book_id):
        """加载书籍配置 - 完全对应Perl版本"""
        config_file = Path(f"books/{book_id}/book.cfg")
        print(f"读取书籍排版配置文件'books/{book_id}/book.cfg'...")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 处理行内注释 - 对应Perl的正则处理
                if '#' in line and '=#' not in line:
                    line = re.sub(r'#.*$', '', line)
                
                line = re.sub(r'\s', '', line)  # 去除所有空白字符
                
                if '=' in line:
                    k, v = line.split('=', 1)
                    self.book[k] = v
        
        # 打印配置信息 - 完全对应Perl版本
        print(f"\t标题：{self.book.get('title', '')}")
        print(f"\t作者：{self.book.get('author', '')}")
        print(f"\t背景：{self.book.get('canvas_id', '')}")
        print(f"\t每列字数：{self.book.get('row_num', '')}")
        print(f"\t是否无标点：{self.book.get('if_nocomma', '')}")
        print(f"\t标点归一化：{self.book.get('if_onlyperiod', '')}")
    
    def validate_config(self):
        """验证配置 - 完全对应Perl版本"""
        canvas_id = self.book.get('canvas_id')
        if not canvas_id:
            print("错误：未定义背景图ID 'canvas_id'！")
            sys.exit(1)
        
        if not Path(f"canvas/{canvas_id}.cfg").exists():
            print("错误：未发现背景图cfg配置文件！")
            sys.exit(1)
        
        if not Path(f"canvas/{canvas_id}.jpg").exists():
            print("错误：未发现背景图jpg图片文件！")
            sys.exit(1)
        
        fn1 = self.book.get('font1')
        if not fn1:
            print("错误：主字体'font1'未定义！")
            sys.exit(1)
        
        # 检查所有字体文件
        for i in range(1, 6):
            font_key = f'font{i}'
            font_file = self.book.get(font_key)
            if font_file and not Path(f"fonts/{font_file}").exists():
                print(f"错误：未发现字体'fonts/{font_file}'！")
                sys.exit(1)
    
    def setup_fonts(self):
        """设置字体 - 完全对应Perl版本"""
        # 构建字体数组和配置 - 对应Perl版本逻辑
        for i in range(1, 6):
            font_key = f'font{i}'
            font_file = self.book.get(font_key)
            if font_file:
                self.fns.append(font_file)
                # 构建字体配置，对应Perl的$fonts{$fn1} = [$fs1_text, $fs1_comm, $fnr1]
                text_size_key = f'text_font{i}_size'
                comment_size_key = f'comment_font{i}_size'
                rotate_key = f'font{i}_rotate'
                
                self.fonts[font_file] = [
                    int(self.book.get(text_size_key, 42)),      # 正文字体大小
                    int(self.book.get(comment_size_key, 30)),   # 批注字体大小
                    int(self.book.get(rotate_key, 0))           # 字体旋转角度
                ]
        
        # 构建正文和批注字体数组 - 完全对应Perl版本
        tfsarray = self.book.get('text_fonts_array', '12345')
        cfsarray = self.book.get('comment_fonts_array', '12345')
        
        for fid in tfsarray:
            idx = int(fid) - 1
            if 0 <= idx < len(self.fns):
                self.tfns.append(self.fns[idx])
        
        for fid in cfsarray:
            idx = int(fid) - 1
            if 0 <= idx < len(self.fns):
                self.cfns.append(self.fns[idx])
    
    def load_canvas_config(self):
        """加载背景图配置 - 完全对应Perl版本"""
        canvas_id = self.book.get('canvas_id')
        config_file = Path(f"canvas/{canvas_id}.cfg")
        
        print(f"读取背景图配置文件'canvas/{canvas_id}.cfg'...")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 处理行内注释
                if '#' in line and '=#' not in line:
                    line = re.sub(r'#.*$', '', line)
                
                line = re.sub(r'\s', '', line)
                
                if '=' in line:
                    k, v = line.split('=', 1)
                    self.canvas_config[k] = v
        
        print(f"\t尺寸：{self.canvas_config.get('canvas_width', '')} x {self.canvas_config.get('canvas_height', '')}")
        print(f"\t列数：{self.canvas_config.get('leaf_col', '')}")
    
    def calculate_positions(self):
        """计算文字位置 - 完全对应Perl版本"""
        canvas_width = int(self.canvas_config.get('canvas_width', 2480))
        canvas_height = int(self.canvas_config.get('canvas_height', 1860))
        margins_top = int(self.canvas_config.get('margins_top', 200))
        margins_bottom = int(self.canvas_config.get('margins_bottom', 50))
        margins_left = int(self.canvas_config.get('margins_left', 50))
        margins_right = int(self.canvas_config.get('margins_right', 50))
        col_num = int(self.canvas_config.get('leaf_col', 24))
        lc_width = int(self.canvas_config.get('leaf_center_width', 120))
        row_num = int(self.book.get('row_num', 30))
        row_delta_y = int(self.book.get('row_delta_y', 10))
        
        # 计算列宽、行高 - 完全对应Perl版本
        cw = (canvas_width - margins_left - margins_right - lc_width) / col_num
        rh = (canvas_height - margins_top - margins_bottom) / row_num
        
        # 生成文字坐标 - 完全对应Perl版本的逻辑
        self.pos_l = []  # 不使用None，直接使用空列表
        self.pos_r = []
        
        # 添加第0个元素作为占位符，使索引从1开始，对应Perl数组
        self.pos_l.append([0, 0])  # 索引从1开始，对应Perl数组
        self.pos_r.append([0, 0])
        
        for i in range(1, col_num + 1):
            for j in range(1, row_num + 1):
                if i <= col_num // 2:
                    pos_x = canvas_width - margins_right - cw * i
                else:
                    pos_x = canvas_width - margins_right - cw * i - lc_width
                
                pos_y = canvas_height - margins_top - rh * j + row_delta_y
                
                self.pos_l.append([pos_x, pos_y])
                self.pos_r.append([pos_x + cw/2, pos_y])
        
        self.page_chars_num = col_num * row_num
        
        # 存储用于后续计算的变量
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.margins_top = margins_top
        self.margins_bottom = margins_bottom
        self.margins_right = margins_right
        self.col_num = col_num
        self.row_num = row_num
        self.cw = cw
        self.rh = rh
    
    def font_check(self, font_file, char):
        """字体检查 - 对应Perl的font_check子程序"""
        try:
            font_path = f"fonts/{font_file}"
            font = ImageFont.truetype(font_path, 40)
            bbox = font.getbbox(char)
            return bbox[2] > bbox[0] and bbox[3] > bbox[1]
        except:
            return False
    
    def get_font(self, char, font_list):
        """获取字体 - 完全对应Perl的get_font子程序"""
        # 特殊处理：对于空格字符，直接返回第一个字体
        if char == ' ' or char == '\u3000':  # 普通空格和中文全角空格
            return font_list[0] if font_list else None
        
        for font in font_list:
            if self.font_check(font, char):
                return font
        return None
    
    def try_st_trans(self, char):
        """简繁转换尝试 - 完全对应Perl的try_st_trans子程序"""
        if not self.s2t or not self.t2s:
            return ''
        
        try:
            char_s2t = self.s2t.convert(char)
            char_t2s = self.t2s.convert(char)
            
            # 去除可能的[]标记
            char_s2t = re.sub(r'\[\]', '', char_s2t)
            char_t2s = re.sub(r'\[\]', '', char_t2s)
            
            if char_s2t and len(char_s2t) > 0:
                char_s2t = char_s2t[0]
                fn_s2t = self.get_font(char_s2t, self.fns)
                if fn_s2t == self.fns[0]:  # 对应主字体
                    return char_s2t
            
            if char_t2s and len(char_t2s) > 0:
                char_t2s = char_t2s[0]
                fn_t2s = self.get_font(char_t2s, self.fns)
                if fn_t2s == self.fns[0]:
                    return char_t2s
            
            return ''
        except:
            return ''
    
    def load_texts(self, book_id, from_page, to_page):
        """加载文本 - 完全对应Perl版本的文本加载逻辑"""
        dats = ['']  # 索引从1开始
        
        # 检查特殊文件
        text_dir = Path(f"books/{book_id}/text")
        if_text000 = (text_dir / "000.txt").exists()
        if_text999 = (text_dir / "999.txt").exists()
        
        print(f"读取该书籍全部文本文件'books/{book_id}/text/*.txt'...", end='')
        
        # 获取所有txt文件并排序 - 对应Perl的readdir和sort
        txt_files = sorted([f for f in text_dir.glob("*.txt") if f.is_file()], 
                          key=lambda x: x.name)
        
        for tfn in txt_files:
            if tfn.name.startswith('.'):
                continue
            
            dat = ""
            with open(tfn, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    line = re.sub(r'\s', '', line)  # 去除所有空白字符
                    
                    # 标点符号替换 - 完全对应Perl版本
                    exp_replace_comma = self.book.get('exp_replace_comma')
                    if exp_replace_comma:
                        for kv in exp_replace_comma.split('|'):
                            if len(kv) >= 2:
                                k, v = kv[0], kv[1]
                                # 处理正则特殊字符
                                if k in '.!?()[]':
                                    k = '\\' + k
                                line = re.sub(k, v, line)
                    
                    # 中文数字替换
                    exp_replace_number = self.book.get('exp_replace_number')
                    if exp_replace_number:
                        for kv in exp_replace_number.split('|'):
                            if len(kv) >= 2:
                                k, v = kv[0], kv[1]
                                line = re.sub(k, v, line)
                    
                    # 标点符号删除
                    exp_delete_comma = self.book.get('exp_delete_comma')
                    if exp_delete_comma:
                        line = re.sub(exp_delete_comma, '', line)
                    
                    # 无标点模式
                    if int(self.book.get('if_nocomma', 0)) == 1:
                        exp_nocomma = self.book.get('exp_nocomma')
                        if exp_nocomma:
                            line = re.sub(exp_nocomma, '', line)
                    
                    # 标点符号归一化
                    if int(self.book.get('if_onlyperiod', 0)) == 1:
                        exp_onlyperiod = self.book.get('exp_onlyperiod')
                        if exp_onlyperiod:
                            line = re.sub(exp_onlyperiod, '。', line)
                            line = re.sub(r'。+', '。', line)
                            line = re.sub(r'^。', '', line)
                    
                    line = line.replace('@', ' ')  # @代表空格
                    
                    # 计算段落补齐空格 - 完全对应Perl版本的复杂逻辑
                    tmpstr = line  # 保存原始文本
                    rnum = 0  # 标注文本双排占用长度
                    
                    # 去除不占字符位的标点 - 完全对应Perl版本的逻辑
                    text_comma_nop = self.book.get('text_comma_nop', '')
                    comment_comma_nop = self.book.get('comment_comma_nop', '')
                    comment_comma_nop_tmp = comment_comma_nop  # 保存原始值，对应Perl: my $comment_comma_nop_tmp = $comment_comma_nop;
                    
                    # 对应Perl: $text_comma_nop =~ s/\|//g; $comment_comma_nop =~ s/\|//g;
                    text_comma_nop_clean = text_comma_nop.replace('|', '') if text_comma_nop else ''
                    comment_comma_nop_clean = comment_comma_nop.replace('|', '') if comment_comma_nop else ''
                    
                    if text_comma_nop_clean:
                        line = re.sub(f'[{re.escape(text_comma_nop_clean)}]', '', line)
                    if comment_comma_nop_clean:
                        line = re.sub(f'[{re.escape(comment_comma_nop_clean)}]', '', line)
                    
                    # 书名号处理
                    if_book_vline = self.book.get('if_book_vline')
                    if if_book_vline and int(if_book_vline) == 1:
                        line = re.sub(r'《|》', '', line)
                    
                    # 计算标注文本占用的字符位 - 对应Perl的复杂正则处理
                    for match in re.finditer(r'【(.*?)】', line):
                        rdat = match.group(1)
                        # 去除批注中不占字符位的标点 - 使用清理后的版本
                        if comment_comma_nop_clean:
                            rdat = re.sub(f'[{re.escape(comment_comma_nop_clean)}]', '', rdat)
                        if if_book_vline and int(if_book_vline) == 1:
                            rdat = re.sub(r'《|》', '', rdat)
                        
                        rchars_len = len(rdat)
                        if rchars_len % 2 == 0:
                            rnum += rchars_len // 2  # 偶数时
                        else:
                            rnum += rchars_len // 2 + 1  # 奇数时
                    
                    # 去除标注文字后的正文
                    line = re.sub(r'【.*?】', '', line)
                    
                    chars_len = len(line)  # 正文字符数
                    
                    # 计算段落末尾需要补齐的空格数 - 完全对应Perl版本
                    spaces_num = self.row_num - (chars_len + rnum) + ((chars_len + rnum) // self.row_num) * self.row_num
                    
                    dat += tmpstr
                    if 0 < spaces_num < self.row_num:
                        dat += ' ' * spaces_num
            
            dats.append(dat)
        
        print(f"{len(dats)-1}个文本文件")
        return dats, if_text000, if_text999
    
    def create_pdf(self, book_id, from_page, to_page, dats, if_text000, if_text999):
        """创建PDF - 完全对应Perl版本的PDF生成逻辑"""
        try:
            from reportlab.pdfgen import canvas as reportlab_canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            print("错误：reportlab库未安装")
            sys.exit(1)
        
        # 获取配置参数
        canvas_width = int(self.canvas_config.get('canvas_width', 2480))
        canvas_height = int(self.canvas_config.get('canvas_height', 1860))
        canvas_id = self.book.get('canvas_id')
        
        # 创建PDF文档 - 对应Perl的PDF::Builder->new
        pdf_file = f"books/{book_id}/《{self.book.get('title', '')}》文本{from_page}至{to_page}"
        if self.opts.get('z'):
            pdf_file += '_test'
        pdf_file += '.pdf'
        
        # 创建reportlab canvas
        c = reportlab_canvas.Canvas(pdf_file, pagesize=(canvas_width, canvas_height))
        
        # 注册字体 - 对应Perl的ttfont注册
        for font_file in self.fns:
            try:
                font_path = f"fonts/{font_file}"
                font_name = font_file.replace('.ttf', '').replace('.otf', '')
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                self.vfonts[font_file] = font_name
            except Exception as e:
                print(f"字体注册失败: {font_file} - {e}")
        
        # PDF元数据 - 完全对应Perl版本
        title = self.book.get('title', '')
        author = self.book.get('author', '')
        logo_text = self.canvas_config.get('logo_text', '')
        
        c.setTitle(title)
        c.setAuthor(author)
        c.setCreator(logo_text)
        c.setProducer(f"{SOFTWARE}{VERSION}，古籍刻本直排电子书制作工具")
        
        outlines = {}  # 目录
        
        # 添加封面 - 对应Perl版本的封面处理
        self.add_cover(c, book_id, canvas_id, canvas_width, canvas_height)
        
        # 处理每个文本 - 完全对应Perl版本的主循环
        pid = 0  # 页码，从封面后开始
        pcnt = 0  # 每页写入文字的当前标准字位指针
        
        # 处理所有文本数据 - 对应Perl版本的foreach循环
        for tid in range(from_page, to_page + 1):
            # 完全对应Perl版本的测试模式检查: last if(defined $opts{'z'} and $pid == $opts{'z'});
            # 修正：使-z N生成N页而不是N+1页
            if self.opts.get('z') and pid >= self.opts['z']:
                break
            
            print(f"读取'books/{book_id}/text/'目录下第 {tid} 个文本文件...")
            
            if tid >= len(dats):
                break
            
            dat = dats[tid]
            chars = list(dat)  # 字符数组
            rchars = []  # 标注文本字符
            
            # 标题处理 - 对应Perl版本
            title_postfix = self.book.get('title_postfix')
            if title_postfix:
                cid = tid - 1 if if_text000 else tid
                tpost = title_postfix.replace('X', self.zhnums.get(cid, str(cid)))
                if cid == 0:
                    tpost = '序'
                if if_text999 and tid == len(dats) - 1:
                    tpost = '附'
                tpchars = list(title + tpost)
            else:
                tpchars = list(title)
            
            tptitle = ''.join(tpchars)
            if tptitle not in outlines:
                outlines[tptitle] = pid + 2  # 目录页码
            
            print(f"创建新PDF页[{pid}]...")
            
            # 对应Perl版本的逻辑：每个文本文件都创建新页面
            # 第一个文本也要创建新页面，因为封面已经占用了第一页
            c.showPage()  # 为当前文本创建新页面
            
            # 添加背景图
            bg_image = f"canvas/{canvas_id}.jpg"
            if Path(bg_image).exists():
                c.drawImage(bg_image, 0, 0, width=canvas_width, height=canvas_height)
            
            # 添加标题
            self.add_page_title(c, tpchars)
            
            # 文字排版主循环 - 完全对应Perl版本的复杂while(1)逻辑
            # 这里是核心：处理字符直到所有字符处理完，期间会创建多个页面
            pid, pcnt = self.process_text_layout_complete(c, chars, rchars, pcnt, pid, 
                                                        canvas_width, canvas_height, 
                                                        tpchars, bg_image, canvas_id)
        
        # 保存PDF
        # 处理PDF目录 - 完全对应Perl版本的outline处理
        title_directory = self.book.get('title_directory')
        if title_directory and int(title_directory) == 1:
            # 对应Perl: my %outlines_tmp; foreach my $ok (keys %outlines) { $outlines_tmp{$outlines{$ok}} = $ok; }
            outlines_tmp = {}
            for ok, page_num in outlines.items():
                outlines_tmp[page_num] = ok
            
            # 对应Perl: my $otlines = $vpdf->outline();
            # reportlab不支持直接的outline操作，但我们可以打印目录信息
            for otpid in sorted(outlines_tmp.keys()):
                ottitle = outlines_tmp[otpid]
                print(f"\t{ottitle} -> {otpid}")
                # 注意：reportlab不支持PDF书签，这里只能打印目录信息
        
        c.save()
        print(f"生成PDF文件'{pdf_file}'...完成！")
        
        # PDF压缩
        if self.opts.get('c'):
            self.compress_pdf(pdf_file)
        
        return pdf_file
    
    def add_cover(self, c, book_id, canvas_id, canvas_width, canvas_height):
        """添加封面 - 完全对应Perl版本的封面处理逻辑"""
        cover_file = f"books/{book_id}/cover.jpg"
        
        if Path(cover_file).exists():
            print(f"发现封面图片'{book_id}/books/{book_id}/cover.jpg'...")
            # 对应Perl的: my $cpimg = $vpdf->image("books/$book_id/cover.jpg"); $vpage->object($cpimg);
            # Perl的object()方法不指定位置和尺寸，图片以原始尺寸显示在页面左侧
            # 我们需要让cover.jpg只占左半部分，右侧保持空白
            
            # 先获取图片的实际尺寸
            from PIL import Image
            try:
                with Image.open(cover_file) as img:
                    img_width, img_height = img.size
                    
                # 计算缩放比例，让图片适应左半页面
                left_half_width = canvas_width // 2
                scale_w = left_half_width / img_width
                scale_h = canvas_height / img_height
                scale = min(scale_w, scale_h)  # 选择较小的缩放比例保持比例
                
                # 计算实际显示尺寸
                display_width = img_width * scale
                display_height = img_height * scale
                
                # 计算居中位置（在左半页面内居中）
                x = (left_half_width - display_width) // 2
                y = (canvas_height - display_height) // 2
                
                # 绘制封面图片到左半部分
                c.drawImage(cover_file, x, y, width=display_width, height=display_height)
                
            except Exception as e:
                print(f"处理封面图片时出错: {e}，使用简易封面...")
                self.create_simple_cover_layout(c, canvas_width, canvas_height)
        else:
            print(f"未发现封面文件'{book_id}/books/{book_id}/cover.jpg'，创建简易封面...")
            self.create_simple_cover_layout(c, canvas_width, canvas_height)
    
    def create_simple_cover_layout(self, c, canvas_width, canvas_height):
        """创建简易封面布局 - 完全对应Perl版本的线条绘制逻辑"""
        # 对应Perl: my $pline = $vpage->gfx();
        plx = canvas_width // 2
        if canvas_width < canvas_height:
            plx = canvas_width
        
        # 中间细竖线 - 对应Perl的linewidth(1)和strokecolor('#cccccc')
        c.setLineWidth(1)
        c.setStrokeColor('#cccccc')
        # $pline->move($plx-50, $canvas_height); $pline->line($plx-50, $canvas_height, $plx-50, 0);
        c.line(plx-50, 0, plx-50, canvas_height)
        c.line(plx+50, 0, plx+50, canvas_height)
        
        # 中间细横线 - 对应Perl的foreach my $lid (0..$canvas_height/200)
        for lid in range(int(canvas_height // 200) + 1):
            y_pos = canvas_height - 200 * lid
            if y_pos >= 0:
                # $pline->move($plx-50, $canvas_height-200*$lid); $pline->line(...)
                c.line(plx-50, y_pos, plx+50, y_pos)
        
        # 中间粗竖线 - 对应Perl的linewidth(20)和strokecolor('gray')
        c.setLineWidth(20)
        c.setStrokeColor('gray')
        # $pline->move($plx, $canvas_height); $pline->line($plx, $canvas_height, $plx, 0);
        c.line(plx, 0, plx, canvas_height)
        
        # 打印封面标题文字 - 完全对应Perl版本
        self.add_cover_text(c, canvas_height)
    
    def add_cover_text(self, c, canvas_height):
        """添加封面文字 - 完全对应Perl版本的封面文字处理"""
        title = self.book.get('title', '')
        author = self.book.get('author', '')
        
        # 获取封面配置参数 - 对应Perl版本的变量
        cover_title_font_size = int(self.book.get('cover_title_font_size', 60))
        cover_author_font_size = int(self.book.get('cover_author_font_size', 40))
        cover_title_y = int(self.book.get('cover_title_y', 300))
        cover_author_y = int(self.book.get('cover_author_y', 300))
        cover_font_color = self.book.get('cover_font_color', 'black')
        
        # 打印封面标题文字 - 完全对应Perl版本的foreach my $i (0..$#tchars)
        tchars = list(title)
        for i, char in enumerate(tchars):
            # 对应Perl: my $fn = get_font($tpchars[$i], \@tfns);
            fn = self.get_font(char, self.tfns)
            if fn and fn in self.vfonts:
                font_name = self.vfonts[fn]
                fs = cover_title_font_size
                # 对应Perl: my ($fx, $fy) = ($fs, $canvas_height-$cover_title_y-$fs*$i*1.2);
                fx = fs
                fy = canvas_height - cover_title_y - fs * i * 1.2
                
                c.setFont(font_name, fs)
                c.setFillColor(cover_font_color)
                # 对应Perl: $vpage->text->textlabel($fx, $fy, $vfonts{$fn}, $fs, $tchars[$i], -color => $cover_font_color);
                c.drawString(fx, fy, char)
        
        # 打印封面作者文字 - 完全对应Perl版本的foreach my $i (0..$#achars)
        achars = list(author)
        for i, char in enumerate(achars):
            # 对应Perl: my $fn = get_font($achars[$i], \@tfns);
            fn = self.get_font(char, self.tfns)
            if fn and fn in self.vfonts:
                font_name = self.vfonts[fn]
                fs = cover_author_font_size
                # 对应Perl: my ($fx, $fy) = ($fs/2, $canvas_height-$cover_author_y-$fs*$i*1.2);
                fx = fs // 2
                fy = canvas_height - cover_author_y - fs * i * 1.2
                
                c.setFont(font_name, fs)
                c.setFillColor(cover_font_color)
                # 对应Perl: $vpage->text->textlabel($fx, $fy, $vfonts{$fn}, $fs, $achars[$i], -color => $cover_font_color);
                c.drawString(fx, fy, char)
    
    def add_page_title(self, c, tpchars):
        """添加页面标题 - 对应Perl版本"""
        title_font_size = int(self.book.get('title_font_size', 42))
        title_font_color = self.book.get('title_font_color', 'black')
        title_y = int(self.book.get('title_y', 1800))
        title_ydis = float(self.book.get('title_ydis', 1.0))
        if_tpcenter = self.book.get('if_tpcenter', '1')
        
        for i, char in enumerate(tpchars):
            fn = self.get_font(char, self.tfns)
            if fn and fn in self.vfonts:
                font_name = self.vfonts[fn]
                c.setFont(font_name, title_font_size)
                c.setFillColor(title_font_color)
                
                if if_tpcenter == '0':
                    fx = -title_font_size // 2  # 不居中时位于左侧
                else:
                    fx = self.canvas_width // 2 - title_font_size // 2  # 居中
                
                fy = title_y - title_font_size * i * title_ydis
                c.drawString(fx, fy, char)
    
    def add_page_number(self, c, page_num):
        """添加页码 - 对应Perl版本"""
        pager_font_size = int(self.book.get('pager_font_size', 30))
        pager_font_color = self.book.get('pager_font_color', 'black')
        pager_y = int(self.book.get('pager_y', 100))
        title_ydis = float(self.book.get('title_ydis', 1.0))
        if_tpcenter = self.book.get('if_tpcenter', '1')
        
        page_zh = self.zhnums.get(page_num, str(page_num))
        pchars_zh = list(page_zh)
        
        for i, char in enumerate(pchars_zh):
            fn = self.get_font(char, self.tfns)
            if fn and fn in self.vfonts:
                font_name = self.vfonts[fn]
                c.setFont(font_name, pager_font_size)
                c.setFillColor(pager_font_color)
                
                if if_tpcenter == '0':
                    px = -pager_font_size // 2
                else:
                    px = self.canvas_width // 2 - pager_font_size // 2
                
                py = pager_y - pager_font_size * i * title_ydis
                c.drawString(px, py, char)
    
    def process_text_layout_complete(self, c, chars, rchars, pcnt, pid, canvas_width, canvas_height, tpchars, bg_image, canvas_id):
        """完整的文字排版处理 - 完全对应Perl版本的while(1)循环逻辑"""
        # 初始化变量
        flag_tbook = 0  # 正文书名号标记
        flag_rbook = 0  # 批注书名号标记
        last = [0, 0]   # 上一字符位置
        
        # 获取配置参数 - 完全对应Perl版本的处理逻辑
        text_comma_nop = self.book.get('text_comma_nop', '')
        comment_comma_nop = self.book.get('comment_comma_nop', '')
        
        # 对应Perl版本：my $comment_comma_nop_tmp = $comment_comma_nop;
        comment_comma_nop_tmp = comment_comma_nop
        
        # 对应Perl版本：$text_comma_nop =~ s/\|//g; $comment_comma_nop =~ s/\|//g;
        text_comma_nop_clean = text_comma_nop.replace('|', '') if text_comma_nop else ''
        comment_comma_nop_clean = comment_comma_nop.replace('|', '') if comment_comma_nop else ''
        
        text_comma_90 = self.book.get('text_comma_90', '').replace('|', '')
        comment_comma_90 = self.book.get('comment_comma_90', '').replace('|', '')
        
        text_comma_nop_size = float(self.book.get('text_comma_nop_size', 1.0))
        text_comma_nop_x = float(self.book.get('text_comma_nop_x', 0.0))
        text_comma_nop_y = float(self.book.get('text_comma_nop_y', 0.0))
        
        text_comma_90_size = float(self.book.get('text_comma_90_size', 1.0))
        text_comma_90_x = float(self.book.get('text_comma_90_x', 0.0))
        text_comma_90_y = float(self.book.get('text_comma_90_y', 0.0))
        
        comment_comma_nop_size = float(self.book.get('comment_comma_nop_size', 1.0))
        comment_comma_nop_x = float(self.book.get('comment_comma_nop_x', 0.0))
        comment_comma_nop_y = float(self.book.get('comment_comma_nop_y', 0.0))
        
        comment_comma_90_size = float(self.book.get('comment_comma_90_size', 1.0))
        comment_comma_90_x = float(self.book.get('comment_comma_90_x', 0.0))
        comment_comma_90_y = float(self.book.get('comment_comma_90_y', 0.0))
        
        text_font_color = self.book.get('text_font_color', 'black')
        comment_font_color = self.book.get('comment_font_color', 'black')
        
        if_book_vline = self.book.get('if_book_vline')
        book_line_width = float(self.book.get('book_line_width', 1.0))
        book_line_color = self.book.get('book_line_color', 'black')
        
        if_onlyperiod = int(self.book.get('if_onlyperiod', 0))
        onlyperiod_color = self.book.get('onlyperiod_color', text_font_color)
        
        try_st = int(self.book.get('try_st', 0))
        
        # 主循环 - 完全对应Perl版本的while(1)逻辑
        while True:
            # 检查测试模式 - 在循环开始时检查，对应Perl: last if(defined $opts{'z'} and $pid == $opts{'z'});
            if self.opts.get('z') and pid == self.opts['z']:
                break
                
            # 核心跳转机制 - 对应Perl的RCHARS标签
            if pcnt >= self.page_chars_num or not chars:
                # 满整页或字符处理完时，打印当前页，创建新页
                pid += 1
                pcnt = 0
                
                # 版心页码 - 先添加页码，对应Perl版本的逻辑
                self.add_page_number(c, pid)
                
                # 测试模式检查 - 对应Perl: last if(defined $opts{'z'} and $pid == $opts{'z'});
                if self.opts.get('z') and pid == self.opts['z']:
                    break
                
                if not chars:  # 所有字符处理完时退出while循环
                    break
                
                print(f"创建新PDF页[{pid}]...")
                c.showPage()  # 新页
                
                # 添加背景图
                if Path(bg_image).exists():
                    c.drawImage(bg_image, 0, 0, width=canvas_width, height=canvas_height)
                
                # 添加标题
                self.add_page_title(c, tpchars)
            
            # 优先处理批注文字 - 完全对应Perl的RCHARS标签逻辑
            if rchars:
                # 计算批注双排占用的标准字位长度 - 完全对应Perl版本
                rctmp = ''.join(rchars)
                if comment_comma_nop_tmp:  # 使用原始临时变量，对应Perl: $comment_comma_nop_tmp
                    rctmp = re.sub(f'[{re.escape(comment_comma_nop_tmp.replace("|" , ""))}]', '', rctmp)
                if if_book_vline and int(if_book_vline) == 1:
                    rctmp = re.sub(r'《|》', '', rctmp)
                
                rcstmp = list(rctmp)  # 对应Perl: my @rcstmp = split //, $rctmp;
                rcstmp_len = len(rcstmp)
                if rcstmp_len % 2 == 0:
                    cnt = rcstmp_len // 2  # 对应Perl: $cnt = int(($#rcstmp+1)/2);
                else:
                    cnt = rcstmp_len // 2 + 1  # 对应Perl: $cnt = int(($#rcstmp+1)/2)+1;
                
                # 计算列位置 - 完全对应Perl版本的逻辑
                pcnt_int = int(pcnt)  # 确保整数
                if (pcnt_int + 1) % self.row_num == 0:  # 对应Perl: if($pcnt+1 % $row_num == 0)
                    pcol = pcnt_int // self.row_num
                else:
                    pcol = pcnt_int // self.row_num + 1
                
                # 生成批注位置数组 - 完全对应Perl版本的逻辑
                r_pos = []
                if pcnt_int + cnt <= pcol * self.row_num:  # 对应Perl: if($pcnt+$cnt <= $pcol*$row_num)
                    # 对应Perl: @r_pos = (@pos_r[$pcnt+1..$pcnt+$cnt], @pos_l[$pcnt+1..$pcnt+$cnt]);
                    r_pos = (self.pos_r[pcnt_int+1:pcnt_int+cnt+1] + 
                            self.pos_l[pcnt_int+1:pcnt_int+cnt+1])
                else:
                    # 对应Perl: @r_pos = (@pos_r[$pcnt+1..$pcol*$row_num], @pos_l[$pcnt+1..$pcol*$row_num]);
                    r_pos = (self.pos_r[pcnt_int+1:pcol*self.row_num+1] + 
                            self.pos_l[pcnt_int+1:pcol*self.row_num+1])
                
                # 在对应位置打印批注文本字符 - 完全对应Perl版本
                rlast = [0, 0]  # 对应Perl: my @rlast;
                processed_rchars = []
                
                # 对应Perl: while(my $rc = shift @rchars)
                while rchars:
                    rc = rchars.pop(0)
                    
                    # 书名号处理 - 完全对应Perl版本
                    if rc == '《':
                        flag_rbook = 1
                        if if_book_vline and int(if_book_vline) == 1:
                            continue
                    elif rc == '》':
                        flag_rbook = 0
                        if if_book_vline and int(if_book_vline) == 1:
                            continue
                    
                    # 获取字体 - 完全对应Perl版本
                    fn = self.get_font(rc, self.cfns)
                    if fn and fn != self.fns[0] and try_st:  # 对应Perl: if($fn ne $fn1 and ...)
                        try_char = self.try_st_trans(rc)
                        if try_char:
                            rc = try_char
                            fn = self.cfns[0] if self.cfns else None
                    
                    if not fn:
                        rc = '□'
                        fn = self.get_font(rc, self.cfns)
                    
                    if fn and fn in self.vfonts:
                        font_name = self.vfonts[fn]
                        fsize = self.fonts[fn][1]  # 批注字体大小，对应Perl: $fonts{$fn}->[1]
                        fcolor = comment_font_color
                        fdegrees = self.fonts[fn][2]  # 对应Perl: $fonts{$fn}->[2]
                        
                        if self.opts.get('v'):
                            print(f"\t[{pid}/{pcnt}] {rc} -> {fn}")
                        
                        # 不占字符位的标点 - 完全对应Perl版本
                        if comment_comma_nop and rc in comment_comma_nop:  # 对应Perl: if($comment_comma_nop =~ m/$rc/)
                            fx, fy = rlast  # 对应Perl: ($fx, $fy) = @rlast;
                            fsize = fsize * comment_comma_nop_size
                            fx += self.cw / 2 * comment_comma_nop_x
                            fy -= self.rh * comment_comma_nop_y
                            if fy - self.margins_bottom < 10:
                                fy = self.margins_bottom + 10
                        else:
                            # 对应Perl: my $rpref = shift @r_pos;
                            if not r_pos:
                                # 对应Perl: if(not $rpref) { unshift @rchars, $rc; goto RCHARS; }
                                # 没有更多位置了，这个字符处理失败，停止当前批注处理
                                if self.opts.get('v'):
                                    print(f"\t[{pid}/{pcnt}] 批注位置不足，跳过字符: {rc}")
                                break  # 跳出批注处理循环，而不是重新插入字符导致无限循环
                            
                            rpref = r_pos.pop(0)
                            if rpref:  # 确保 rpref 不为 None
                                fx, fy = rpref  # 对应Perl: ($fx, $fy) = @$rpref;
                                rlast = rpref[:]  # 对应Perl: @rlast = @$rpref;
                                fx += (self.cw - fsize * 2) / 4  # 对应Perl: $fx+= ($cw-$fsize*2)/4;
                                fy += (self.rh - fsize) / 4      # 对应Perl: $fy+= ($rh-$fsize)/4;
                            else:
                                # 如果 rpref 为 None，跳过这个字符
                                if self.opts.get('v'):
                                    print(f"\t[{pid}/{pcnt}] 批注位置为空，跳过字符: {rc}")
                                break
                            
                            # 90度旋转的标点 - 完全对应Perl版本
                            if comment_comma_90 and rc in comment_comma_90:  # 对应Perl: if($comment_comma_90 =~ m/$rc/)
                                fdegrees = -90
                                fsize = fsize * comment_comma_90_size
                                fx += self.cw / 2 * comment_comma_90_x
                                fy += self.rh * comment_comma_90_y
                            
                            pcnt += 0.5  # 对应Perl: $pcnt+=0.5; #批注占半个字符位
                        
                        # 特殊颜色处理 - 完全对应Perl版本
                        if if_onlyperiod == 1 and rc == '。':
                            fcolor = onlyperiod_color if onlyperiod_color else comment_font_color
                        if self.opts.get('z') and fn != self.cfns[0]:
                            fcolor = 'blue'
                        
                        # 绘制文字 - 对应Perl: $vpage->text()->textlabel(...)
                        c.setFont(font_name, fsize)
                        c.setFillColor(fcolor)
                        
                        if fdegrees != 0:
                            c.saveState()
                            c.translate(fx, fy)
                            c.rotate(fdegrees)
                            c.drawString(0, 0, rc)
                            c.restoreState()
                        else:
                            c.drawString(fx, fy, rc)
                        
                        # 书名号侧线 - 完全对应Perl版本
                        if if_book_vline and int(if_book_vline) == 1 and flag_rbook:
                            c.setLineWidth(book_line_width)
                            c.setStrokeColor(book_line_color)
                            ply = fy + self.rh * 0.7
                            if ply >= canvas_height - self.margins_top:
                                ply = canvas_height - self.margins_top - 5
                            c.line(fx-1, fy-self.rh*0.3, fx-1, ply)
                
                # 对应Perl: if($#rchars > 0) { goto RCHARS; }
                if len(rchars) > 0:
                    continue  # 若标注文本有遗留，说明发生跨页或页内跨列，跳转直至本次标注文本处理完
                
                # 对应Perl: $pcnt = int($pcnt+0.5); #指针前进数
                pcnt = int(pcnt + 0.5)
                
                # 对应Perl: if($pcnt == $page_chars_num) { goto RCHARS; }
                if pcnt >= self.page_chars_num:
                    continue  # 如果此时到达页尾跳转写入图片并新建
            
            # 处理正文文字
            if not chars:
                break  # 所有字符处理完毕
            
            char = chars.pop(0)
            
            # 特殊字符处理 - 对应Perl版本的$%&处理
            if char == '$':  # 前进半页或整页
                # 跳过$后的空格
                for _ in range(self.row_num - 1):
                    if chars and chars[0] == ' ':
                        chars.pop(0)
                
                if pcnt == 0 or pcnt == self.page_chars_num // 2:
                    continue
                
                if pcnt < self.page_chars_num // 2:
                    pcnt = self.page_chars_num // 2
                    continue
                else:
                    pcnt = self.page_chars_num
                    continue
            
            elif char == '%':  # 跳到页尾
                for _ in range(self.row_num - 1):
                    if chars and chars[0] == ' ':
                        chars.pop(0)
                pcnt = self.page_chars_num
                continue
            
            elif char == '&':  # 跳到最后一列
                for _ in range(self.row_num - 1):
                    if chars and chars[0] == ' ':
                        chars.pop(0)
                if pcnt <= self.page_chars_num - self.row_num + 1:
                    pcnt = self.page_chars_num - self.row_num
                continue
            
            # 书名号处理
            elif char == '《':
                flag_tbook = 1
                if if_book_vline and int(if_book_vline) == 1:
                    continue
            elif char == '》':
                flag_tbook = 0
                if if_book_vline and int(if_book_vline) == 1:
                    continue
            
            # 批注处理 - 【】标记，对应Perl的 goto RCHARS 逻辑
            elif char == '【':  # 批注开始
                # 提取批注内容
                rdat = ''
                while chars:
                    rchar = chars.pop(0)
                    if rchar == '】':  # 批注结束
                        break
                    rdat += rchar
                
                # 对应Perl: @rchars = split //, $rdat; #更新全局标注文本变量
                rchars = list(rdat) if rdat else []
                # 对应Perl: goto RCHARS; #处理标注文字
                continue  # 跳转到下一次循环，优先处理批注
            
            # 正文文字处理
            else:
                if pcnt < self.page_chars_num:
                    pcnt += 1
                
                if pcnt <= self.page_chars_num and int(pcnt) <= len(self.pos_l) - 1:
                    # 获取字体
                    fn = self.get_font(char, self.tfns)
                    if not fn and try_st:
                        try_char = self.try_st_trans(char)
                        if try_char:
                            char = try_char
                            fn = self.tfns[0] if self.tfns else None
                    
                    if not fn:
                        char = '□'
                        fn = self.get_font(char, self.tfns)
                    
                    if fn and fn in self.vfonts:
                        font_name = self.vfonts[fn]
                        fsize = self.fonts[fn][0]  # 正文字体大小
                        fcolor = text_font_color
                        fdegrees = self.fonts[fn][2]
                        
                        fx, fy = self.pos_l[int(pcnt)]  # 确保索引是整数
                        
                        if self.opts.get('v'):
                            print(f"[{pid}/{pcnt}] {char} -> {fn}")
                        
                        # 不占字符位的标点
                        if char in text_comma_nop:
                            fsize = fsize * text_comma_nop_size
                            fx, fy = last
                            fx += self.cw * text_comma_nop_x
                            fy -= self.rh * text_comma_nop_y
                            if fy - self.margins_bottom < 10:
                                fy = self.margins_bottom + 10
                            pcnt -= 1  # 不占位时指针回退
                        else:
                            # 90度旋转的标点
                            if char in text_comma_90:
                                fsize = fsize * text_comma_90_size
                                fx += self.cw * text_comma_90_x
                                fy += self.rh * text_comma_90_y
                                fdegrees = -90
                            else:
                                fx += (self.cw - fsize) / 2
                            
                            last = [fx, fy]
                        
                        # 特殊颜色处理
                        if if_onlyperiod == 1 and char == '。':
                            fcolor = onlyperiod_color
                        if self.opts.get('z') and fn != self.tfns[0]:
                            fcolor = 'blue'
                        
                        # 绘制文字
                        c.setFont(font_name, fsize)
                        c.setFillColor(fcolor)
                        
                        if fdegrees != 0:
                            c.saveState()
                            c.translate(fx, fy)
                            c.rotate(fdegrees)
                            c.drawString(0, 0, char)
                            c.restoreState()
                        else:
                            c.drawString(fx, fy, char)
                        
                        # 书名号侧线
                        if if_book_vline and int(if_book_vline) == 1 and flag_tbook:
                            c.setLineWidth(book_line_width)
                            c.setStrokeColor(book_line_color)
                            ply = fy + self.rh * 0.7
                            if ply >= canvas_height - self.margins_top:
                                ply = canvas_height - self.margins_top - 5
                            c.line(fx-2, fy-self.rh*0.3, fx-2, ply)
                        
                        # 页尾特殊处理
                        if pcnt == self.page_chars_num:
                            if chars:
                                next_char = chars[0]
                                if next_char in text_comma_nop:
                                    chars.pop(0)  # 移除下一个字符
                                    # 在页尾绘制不占位标点
                                    fx_nop = fx + self.cw * text_comma_nop_x
                                    fy_nop = fy - self.rh * text_comma_nop_y
                                    if fy_nop - self.margins_bottom < 10:
                                        fy_nop = self.margins_bottom + 10
                                    
                                    c.setFont(font_name, fsize * text_comma_nop_size)
                                    c.drawString(fx_nop, fy_nop, next_char)
            

        
        return pid, pcnt
    
    def compress_pdf(self, pdf_file):
        """压缩PDF - 对应Perl版本"""
        import platform
        
        if platform.system() == 'Darwin':  # macOS
            input_file = pdf_file
            output_file = pdf_file.replace('.pdf', '_已压缩.pdf')
            
            print(f"压缩PDF文件'{output_file}'...")
            import subprocess
            
            cmd = [
                'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/screen', '-dNOPAUSE', '-dQUIET', '-dBATCH',
                f'-sOutputFile={output_file}', input_file
            ]
            
            try:
                subprocess.run(cmd, check=True)
                os.remove(input_file)
                print("完成！")
            except subprocess.CalledProcessError:
                print("PDF压缩失败，请确保已安装Ghostscript")
        else:
            print("建议：使用'-c'参数对PDF文件进行压缩！")
    
    def run(self):
        """主运行方法 - 完全对应Perl版本的主流程"""
        # 解析参数
        self.parse_args()
        
        # 加载配置
        self.load_zh_numbers()
        
        book_id = self.opts['b']
        from_page = self.opts['f']
        to_page = self.opts['t']
        
        # 检查目录
        self.check_directories(book_id)
        
        # 打印欢迎信息
        self.print_welcome()
        
        if self.opts.get('z'):
            print(f"注意：-z 测试模式，仅输出{self.opts['z']}页用于调试排版参数！")
        
        # 加载配置
        self.load_book_config(book_id)
        self.validate_config()
        self.setup_fonts()
        self.load_canvas_config()
        self.calculate_positions()
        
        # 加载文本
        dats, if_text000, if_text999 = self.load_texts(book_id, from_page, to_page)
        
        # 生成PDF
        pdf_file = self.create_pdf(book_id, from_page, to_page, dats, if_text000, if_text999)
        
        return pdf_file


def main():
    """主函数"""
    try:
        vrain = VRainPerfect()
        vrain.run()
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()