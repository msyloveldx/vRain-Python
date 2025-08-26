#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印章添加工具
读取yins.cfg配置文件，将印章图片插入到PDF文件相应页码的相应位置
Python版本 by msyloveldx, 2025/08
原作者: shanleiguang, 2025.7
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO

class YinInserter:
    """印章插入器"""
    
    def __init__(self):
        self.book_config = {}
        self.canvas_config = {}
        self.yins_config = {}
        
        self._load_configurations()
    
    def _load_configurations(self):
        """加载配置文件"""
        # 加载书籍配置
        book_cfg_path = Path("book.cfg")
        if not book_cfg_path.exists():
            raise FileNotFoundError("错误：未找到book.cfg文件")
        
        print("读取 'book.cfg'...")
        self._load_config_file(book_cfg_path, self.book_config)
        
        canvas_id = self.book_config.get('canvas_id')
        if not canvas_id:
            raise ValueError("错误：book.cfg中未定义canvas_id")
        
        # 加载背景图配置
        canvas_cfg_path = Path(f"../../canvas/{canvas_id}.cfg")
        if not canvas_cfg_path.exists():
            raise FileNotFoundError(f"错误：未找到../../canvas/{canvas_id}.cfg文件")
        
        print(f"读取 '../../canvas/{canvas_id}.cfg'...")
        self._load_config_file(canvas_cfg_path, self.canvas_config)
        
        # 加载印章配置
        yins_cfg_path = Path("yins.cfg")
        if not yins_cfg_path.exists():
            raise FileNotFoundError("错误：未找到yins.cfg文件")
        
        print("读取 'yins.cfg'...")
        self._load_yins_config(yins_cfg_path)
    
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
    
    def _load_yins_config(self, file_path: Path):
        """加载印章配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('|')
                if len(parts) >= 3:
                    pdf_name = parts[0]
                    position = parts[1]
                    yin_filename = parts[2]
                    
                    # 解析位置信息: pid,col_begin,row_begin,cols
                    pos_parts = position.split(',')
                    if len(pos_parts) >= 4:
                        try:
                            pid = int(pos_parts[0])
                            col_begin = int(pos_parts[1])
                            row_begin = int(pos_parts[2])
                            cols = int(pos_parts[3])
                            
                            if pdf_name not in self.yins_config:
                                self.yins_config[pdf_name] = []
                            
                            self.yins_config[pdf_name].append({
                                'pid': pid,
                                'col_begin': col_begin,
                                'row_begin': row_begin,
                                'cols': cols,
                                'filename': yin_filename
                            })
                            
                        except ValueError as e:
                            print(f"警告：无法解析印章配置行: {line} - {e}")
    
    def calculate_dimensions(self) -> Dict:
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
    
    def insert_yin(self, yin_info: Dict, c: canvas.Canvas, dims: Dict):
        """在指定位置插入印章"""
        pid = yin_info['pid']
        col_begin = yin_info['col_begin']
        row_begin = yin_info['row_begin']
        cols = yin_info['cols']
        yin_filename = yin_info['filename']
        
        # 计算印章位置和尺寸
        iw = cols * dims['cw']
        ix = dims['bg_width'] - dims['bg_right'] - dims['cw'] * col_begin
        iy = dims['bg_bottom'] + dims['rh'] * (row_begin - 1)
        
        if col_begin > dims['col_num'] / 2:
            ix -= dims['lc_width']
        
        # 插入印章图片
        yin_path = Path(f"yins/{yin_filename}")
        if yin_path.exists():
            c.drawImage(str(yin_path), ix, iy, width=iw, preserveAspectRatio=True)
            print(f"已插入印章 {yin_filename} 到页面 {pid}")
        else:
            print(f"警告：印章文件 {yin_path} 不存在")
    
    def process_pdfs(self):
        """处理所有PDF文件"""
        dims = self.calculate_dimensions()
        
        for pdf_name, yins_list in self.yins_config.items():
            pdf_path = Path(f"{pdf_name}.pdf")
            if not pdf_path.exists():
                print(f"警告：PDF文件 {pdf_path} 不存在，跳过处理")
                continue
            
            print(f"打开PDF文件 '{pdf_name}' ...")
            
            # 读取原PDF
            reader = PdfReader(str(pdf_path))
            writer = PdfWriter()
            
            # 处理每一页
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                
                # 检查是否需要在这一页插入印章
                page_yins = [yin for yin in yins_list if yin['pid'] == page_num + 1]
                
                if page_yins:
                    # 创建临时画布来添加印章
                    packet = BytesIO()
                    temp_canvas = canvas.Canvas(packet, 
                                              pagesize=(dims['bg_width'], dims['bg_height']))
                    
                    # 在临时画布上添加印章
                    for yin_info in page_yins:
                        self.insert_yin(yin_info, temp_canvas, dims)
                    
                    temp_canvas.save()
                    packet.seek(0)
                    
                    # 读取临时PDF并合并到原页面
                    temp_pdf = PdfReader(packet)
                    if temp_pdf.pages:
                        page.merge_page(temp_pdf.pages[0])
                
                writer.add_page(page)
            
            # 保存结果
            output_path = Path(f"{pdf_name}_印章.pdf")
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            print(f"已保存到 {output_path}")

def main():
    """主函数"""
    try:
        inserter = YinInserter()
        inserter.process_pdfs()
        
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
