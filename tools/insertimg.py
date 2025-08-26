#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF插图工具 - 将图片插入到PDF文件的指定位置
Python版本 by msyloveldx, 2025/08
原作者: shanleiguang, 2024.1.5
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class PDFImageInserter:
    """PDF插图工具类"""
    
    def __init__(self, pdf_name: str):
        self.pdf_name = pdf_name
        self.book_config = {}
        self.canvas_config = {}
        self.images_config = []
        
        self._load_configurations()
    
    def _load_configurations(self):
        """加载配置文件"""
        # 加载书籍配置
        book_cfg_path = Path("book.cfg")
        if not book_cfg_path.exists():
            raise FileNotFoundError("错误：未找到book.cfg文件")
        
        self._load_config_file(book_cfg_path, self.book_config)
        
        canvas_id = self.book_config.get('canvas_id')
        if not canvas_id:
            raise ValueError("错误：book.cfg中未定义canvas_id")
        
        # 加载背景图配置
        canvas_cfg_path = Path(f"../../canvas/{canvas_id}.cfg")
        if not canvas_cfg_path.exists():
            raise FileNotFoundError(f"错误：未找到../../canvas/{canvas_id}.cfg文件")
        
        self._load_config_file(canvas_cfg_path, self.canvas_config)
        
        # 加载图片配置
        images_cfg_path = Path("images.cfg")
        if not images_cfg_path.exists():
            raise FileNotFoundError("错误：未找到images.cfg文件")
        
        self._load_images_config(images_cfg_path)
        
        print(f"背景尺寸: {self.canvas_config.get('canvas_width', '')} x {self.canvas_config.get('canvas_height', '')}")
    
    def _load_config_file(self, file_path: Path, config_dict: dict):
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
    
    def _load_images_config(self, file_path: Path):
        """加载图片配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('|')
                if len(parts) >= 4:
                    try:
                        pid = int(parts[0])
                        col_begin = int(parts[1])
                        col_end = int(parts[2])
                        img_id = parts[3]
                        
                        self.images_config.append((pid, col_begin, col_end, img_id))
                        print(f"图片配置: 页{pid}, 列{col_begin}-{col_end}, 图片{img_id}")
                        
                    except ValueError as e:
                        print(f"警告：无法解析图片配置行: {line} - {e}")
    
    def calculate_dimensions(self):
        """计算尺寸参数"""
        bg_width = int(self.canvas_config.get('canvas_width', 2480))
        bg_height = int(self.canvas_config.get('canvas_height', 1860))
        bg_top = int(self.canvas_config.get('margins_top', 200))
        bg_bottom = int(self.canvas_config.get('margins_bottom', 50))
        bg_left = int(self.canvas_config.get('margins_left', 50))
        bg_right = int(self.canvas_config.get('margins_right', 50))
        col_num = int(self.canvas_config.get('leaf_col', 24))
        lc_width = int(self.canvas_config.get('leaf_center_width', 120))
        row_num = int(self.book_config.get('row_num', 30))
        
        cw = (bg_width - bg_left - bg_right - lc_width) / col_num
        rh = (bg_height - bg_top - bg_bottom) / row_num
        
        return {
            'bg_width': bg_width,
            'bg_height': bg_height,
            'bg_top': bg_top,
            'bg_bottom': bg_bottom,
            'bg_left': bg_left,
            'bg_right': bg_right,
            'col_num': col_num,
            'lc_width': lc_width,
            'cw': cw,
            'rh': rh
        }
    
    def insert_image(self, pid: int, col_begin: int, col_end: int, img_id: str, 
                    c: canvas.Canvas, dims: dict):
        """在指定位置插入图片"""
        iw = (col_end - col_begin + 1) * dims['cw']
        ix = dims['bg_width'] - dims['bg_right'] - dims['cw'] * col_end
        
        if col_begin > dims['col_num'] / 2:
            ix -= dims['lc_width']
        
        iy = dims['bg_bottom']
        
        # 绘制白色背景
        c.setFillColor('white')
        c.setStrokeColor('white')
        c.rect(ix + 10, iy + 1, iw - 20, 
               dims['bg_height'] - dims['bg_top'] - dims['bg_bottom'] - 3, 
               fill=1, stroke=1)
        
        # 插入图片
        img_path = Path(f"images/{img_id}.jpg")
        if img_path.exists():
            c.drawImage(str(img_path), 
                       ix + 10, iy + 10, 
                       iw - 20, 
                       dims['bg_height'] - dims['bg_top'] - dims['bg_bottom'] - 20)
        else:
            print(f"警告：图片文件 {img_path} 不存在")
    
    def process_pdf(self):
        """处理PDF文件"""
        pdf_path = Path(f"{self.pdf_name}.pdf")
        if not pdf_path.exists():
            raise FileNotFoundError(f"错误：PDF文件 {pdf_path} 不存在")
        
        print(f"打开PDF文件 '{self.pdf_name}.pdf' ...")
        
        # 计算尺寸
        dims = self.calculate_dimensions()
        
        # 读取原PDF
        reader = PdfReader(str(pdf_path))
        writer = PdfWriter()
        
        # 处理每一页
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            
            # 检查是否需要在这一页插入图片
            page_images = [img for img in self.images_config if img[0] == page_num + 1]
            
            if page_images:
                # 创建临时画布来添加图片
                from io import BytesIO
                from reportlab.pdfgen import canvas as pdf_canvas
                
                packet = BytesIO()
                temp_canvas = pdf_canvas.Canvas(packet, 
                                              pagesize=(dims['bg_width'], dims['bg_height']))
                
                # 在临时画布上添加图片
                for pid, col_begin, col_end, img_id in page_images:
                    self.insert_image(pid, col_begin, col_end, img_id, temp_canvas, dims)
                
                temp_canvas.save()
                packet.seek(0)
                
                # 读取临时PDF并合并到原页面
                temp_pdf = PdfReader(packet)
                if temp_pdf.pages:
                    page.merge_page(temp_pdf.pages[0])
            
            writer.add_page(page)
        
        # 保存结果
        output_path = Path(f"{self.pdf_name}_image.pdf")
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"已保存到 {output_path}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PDF插图工具')
    parser.add_argument('-i', '--input', required=True, 
                       help='输入PDF文件名（不含扩展名）')
    
    args = parser.parse_args()
    
    try:
        inserter = PDFImageInserter(args.input)
        inserter.process_pdf()
        
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
