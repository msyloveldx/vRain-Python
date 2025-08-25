#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
古籍刻本背景图生成工具
Python版本 by AI Assistant, 2025/01
原作者: shanleiguang, 2024.1.5
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

class CanvasGenerator:
    """背景图生成器"""
    
    def __init__(self, config_id: str):
        self.config_id = config_id
        self.config = {}
        
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        config_path = Path(f"{self.config_id}.cfg")
        if not config_path.exists():
            raise FileNotFoundError(f"错误: 未找到配置文件 {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
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
                        self.config[key] = int(value)
                    elif value.replace('.', '').isdigit():
                        self.config[key] = float(value)
                    else:
                        self.config[key] = value
    
    def create_canvas(self):
        """创建背景图"""
        # 获取配置参数
        cw = int(self.config.get('canvas_width', 2480))
        ch = int(self.config.get('canvas_height', 1860))
        cc = self.config.get('canvas_color', 'white')
        
        mt = int(self.config.get('margins_top', 200))
        mb = int(self.config.get('margins_bottom', 50))
        ml = int(self.config.get('margins_left', 50))
        mr = int(self.config.get('margins_right', 50))
        
        cln = int(self.config.get('leaf_col', 24))
        lcw = int(self.config.get('leaf_center_width', 120))
        
        # 鱼尾参数
        fty = int(self.config.get('fish_top_y', 500))
        ftc = self.config.get('fish_top_color', 'black')
        ftrh = int(self.config.get('fish_top_rectheight', 50))
        ftth = int(self.config.get('fish_top_triaheight', 30))
        ftlw = int(self.config.get('fish_top_linewidth', 15))
        
        fbd = int(self.config.get('fish_btm_direction', 1))
        fby = int(self.config.get('fish_btm_y', 1500))
        fbc = self.config.get('fish_btm_color', 'black')
        fbrh = int(self.config.get('fish_btm_rectheight', 50))
        fbth = int(self.config.get('fish_btm_triaheight', 30))
        fblw = int(self.config.get('fish_btm_linewidth', 15))
        
        flw = int(self.config.get('fish_line_width', 1))
        flm = int(self.config.get('fish_line_margin', 5))
        flc = self.config.get('fish_line_color', 'black')
        
        # 线条参数
        ilw = int(self.config.get('inline_width', 1))
        ilc = self.config.get('inline_color', 'black')
        olw = int(self.config.get('outline_width', 10))
        olc = self.config.get('outline_color', 'black')
        moh = int(self.config.get('outline_hmargin', 5))
        mov = int(self.config.get('outline_vmargin', 5))
        
        # 文字参数
        lgt = self.config.get('logo_text', '')
        lgy = int(self.config.get('logo_y', 1680))
        lgc = self.config.get('logo_color', 'white')
        lgf = self.config.get('logo_font', 'qiji-combo.ttf')
        lgs = int(self.config.get('logo_font_size', 40))
        
        clw = (cw - ml - mr - lcw) / cln
        
        print("创建背景图...")
        
        # 创建图像
        img = Image.new('RGB', (cw, ch), color=cc)
        draw = ImageDraw.Draw(img)
        
        # 绘制外框
        draw.rectangle([ml - olw//2 - moh, mt - olw//2 - mov, 
                       cw - mr + olw//2 + moh, ch - mb + olw//2 + mov],
                      outline=olc, width=olw)
        
        # 绘制内框
        draw.rectangle([ml, mt, cw - mr, ch - mb], 
                      outline=ilc, width=ilw)
        
        # 绘制列分割线
        for cid in range(1, cln + 1):
            wd = (lcw - clw) if cid > cln // 2 else 0
            x = ml + wd + clw * cid
            draw.line([x, mt, x, ch - mb], fill=ilc, width=ilw)
        
        # 绘制鱼尾
        self._draw_fish_top(draw, cw, fty, ftrh, ftth, flc, flw, ftc, lcw, flm)
        
        if fbd == 0:
            self._draw_fish_btm_down(draw, cw, fby, fbrh, fbth, flc, flw, fbc, lcw, flm)
        elif fbd == 1:
            self._draw_fish_btm_up(draw, cw, fby, fbrh, fbth, flc, flw, fbc, lcw, flm, mt, mb, mov)
        
        # 绘制鱼尾连接线
        if ftlw:
            draw.line([cw//2, mt - mov, cw//2, fty - flm], fill=flc, width=ftlw)
        if fblw:
            draw.line([cw//2, fby + flm, cw//2, ch - mb + mov], fill=flc, width=fblw)
        
        # 绘制文字
        if lgt:
            try:
                font_path = Path(lgf)
                if not font_path.exists():
                    # 尝试在当前目录查找字体文件
                    font_path = Path(f"./{lgf}")
                
                if font_path.exists():
                    font = ImageFont.truetype(str(font_path), lgs)
                else:
                    # 使用默认字体
                    font = ImageFont.load_default()
                    print(f"警告：未找到字体文件 {lgf}，使用默认字体")
                
                for i, char in enumerate(lgt):
                    print(f"\t{char} -> {lgf}")
                    x = cw//2 - lgs//2
                    y = lgy + lgs * i
                    draw.text((x, y), char, fill=lgc, font=font)
                    
            except Exception as e:
                print(f"绘制文字时出错: {e}")
        
        # 保存图像
        output_path = Path(f"{self.config_id}.jpg")
        print(f"保存 '{output_path}' ...", end=' ')
        img.save(output_path, 'JPEG', quality=95)
        print("完成")
    
    def _draw_fish_top(self, draw, cw, fy, dy1, dy2, flc, flw, ftc, lcw, flm):
        """绘制上鱼尾"""
        # 水平线
        draw.line([cw//2 - lcw//2, fy - flm, cw//2 + lcw//2, fy - flm], 
                 fill=flc, width=flw)
        
        # 鱼尾形状
        if dy1 > 0 or dy2 > 0:
            points = [
                (cw//2 - lcw//2, fy),
                (cw//2 + lcw//2, fy),
                (cw//2 + lcw//2, fy + dy1 + dy2),
                (cw//2, fy + dy1),
                (cw//2 - lcw//2, fy + dy1 + dy2)
            ]
            draw.polygon(points, fill=ftc, outline=flc, width=flw)
        
        # 下方连接线
        draw.line([cw//2 - lcw//2, fy + dy1 + dy2 + flm, cw//2, fy + dy1 + flm], 
                 fill=flc, width=1)
        draw.line([cw//2, fy + dy1 + flm, cw//2 + lcw//2, fy + dy1 + dy2 + flm], 
                 fill=flc, width=1)
    
    def _draw_fish_btm_down(self, draw, cw, fy, dy1, dy2, flc, flw, fbc, lcw, flm):
        """绘制下鱼尾（向下）"""
        # 水平线
        draw.line([cw//2 - lcw//2, fy - flm, cw//2 + lcw//2, fy - flm], 
                 fill=flc, width=flw)
        
        # 鱼尾形状
        if dy1 > 0 or dy2 > 0:
            points = [
                (cw//2 - lcw//2, fy),
                (cw//2 + lcw//2, fy),
                (cw//2 + lcw//2, fy + dy1 + dy2),
                (cw//2, fy + dy1),
                (cw//2 - lcw//2, fy + dy1 + dy2)
            ]
            draw.polygon(points, fill=fbc, outline=flc, width=flw)
        
        # 下方连接线
        draw.line([cw//2 - lcw//2, fy + dy1 + dy2 + flm, cw//2, fy + dy1 + flm], 
                 fill=flc, width=1)
        draw.line([cw//2, fy + dy1 + flm, cw//2 + lcw//2, fy + dy1 + dy2 + flm], 
                 fill=flc, width=1)
    
    def _draw_fish_btm_up(self, draw, cw, fy, dy1, dy2, flc, flw, fbc, lcw, flm, mt, mb, mov):
        """绘制下鱼尾（向上）"""
        # 水平线
        draw.line([cw//2 - lcw//2, fy + flm, cw//2 + lcw//2, fy + flm], 
                 fill=flc, width=flw)
        
        # 鱼尾形状
        if dy1 > 0 or dy2 > 0:
            points = [
                (cw//2 - lcw//2, fy),
                (cw//2 + lcw//2, fy),
                (cw//2 + lcw//2, fy - dy1 - dy2),
                (cw//2, fy - dy1),
                (cw//2 - lcw//2, fy - dy1 - dy2)
            ]
            draw.polygon(points, fill=fbc, outline=flc, width=flw)
        
        # 上方连接线
        draw.line([cw//2 - lcw//2, fy - dy1 - dy2 - flm, cw//2, fy - dy1 - flm], 
                 fill=flc, width=1)
        draw.line([cw//2, fy - dy1 - flm, cw//2 + lcw//2, fy - dy1 - dy2 - flm], 
                 fill=flc, width=1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='古籍刻本背景图生成工具')
    parser.add_argument('-c', '--config', required=True, 
                       help='配置文件ID（不含扩展名）')
    
    args = parser.parse_args()
    
    try:
        generator = CanvasGenerator(args.config)
        generator.create_canvas()
        
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
