#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vRain中文古籍刻本风格直排电子书制作工具
Python版本 by msyloveldx, 2025/08
原作者: shanleiguang

这是一个专门用于生成古籍刻本风格直排电子书的工具。
主要功能包括：
- 支持古籍风格的PDF生成
- 章节模式和连续模式两种排版方式
- 字体混合排版和智能字符转换
- 批注处理和特殊标点符号处理
"""

import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union

# 第三方库导入
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.colors import Color, black, white, red, blue
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image, ImageFont, ImageDraw
import opencc

# 应用常量
SOFTWARE = 'vRain'
VERSION = 'v1.4.1'
DEFAULT_ENCODING = 'utf-8'

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FontChecker:
    """
    字体检查工具类
    
    提供字体支持检查功能，并使用缓存提高性能。
    """
    
    def __init__(self):
        self._font_cache: Dict[Tuple[str, str], bool] = {}
        self._font_objects: Dict[str, ImageFont.FreeTypeFont] = {}
    
    def _get_font_object(self, font_path: str) -> Optional[ImageFont.FreeTypeFont]:
        """获取字体对象，使用缓存优化性能"""
        if font_path not in self._font_objects:
            try:
                self._font_objects[font_path] = ImageFont.truetype(font_path, 40)
            except Exception as e:
                logger.warning(f"无法加载字体 {font_path}: {e}")
                return None
        
        return self._font_objects[font_path]
    
    def check_font_support(self, font_path: str, char: str) -> bool:
        """
        检查字体是否支持某个字符
        
        Args:
            font_path: 字体文件路径
            char: 要检查的字符
            
        Returns:
            bool: 是否支持该字符
        """
        # 特殊字符处理：空格总是被支持的
        if char in [' ', '\t', '\n', '\r']:
            return True
        
        # 检查缓存
        cache_key = (font_path, char)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        # 检查字体支持
        try:
            font = self._get_font_object(font_path)
            if font is None:
                self._font_cache[cache_key] = False
                return False
            
            # 使用PIL检查字符是否被支持
            bbox = font.getbbox(char)
            is_supported = bbox[2] > bbox[0] and bbox[3] > bbox[1]
            
            # 缓存结果
            self._font_cache[cache_key] = is_supported
            return is_supported
            
        except Exception as e:
            logger.debug(f"字体支持检查失败 {font_path} - {char}: {e}")
            self._font_cache[cache_key] = False
            return False
    
    def clear_cache(self):
        """清空缓存"""
        self._font_cache.clear()
        self._font_objects.clear()

class ChineseConverter:
    """
    中文简繁转换工具
    
    提供简体中文和繁体中文之间的转换功能。
    """
    
    def __init__(self):
        try:
            self.s2t = opencc.OpenCC('s2t')  # 简转繁
            self.t2s = opencc.OpenCC('t2s')  # 繁转简
            self._available = True
        except Exception as e:
            logger.warning(f"简繁转换初始化失败: {e}")
            self._available = False
    
    def simp_to_trad(self, text: str) -> str:
        """
        简体转繁体
        
        Args:
            text: 简体中文文本
            
        Returns:
            str: 繁体中文文本
        """
        if not self._available:
            return text
            
        try:
            return self.s2t.convert(text)
        except Exception as e:
            logger.debug(f"简转繁失败: {e}")
            return text
    
    def trad_to_simp(self, text: str) -> str:
        """
        繁体转简体
        
        Args:
            text: 繁体中文文本
            
        Returns:
            str: 简体中文文本
        """
        if not self._available:
            return text
            
        try:
            return self.t2s.convert(text)
        except Exception as e:
            logger.debug(f"繁转简失败: {e}")
            return text
    
    @property
    def available(self) -> bool:
        """返回转换器是否可用"""
        return self._available

class VRainPDFGenerator:
    """
    vRain PDF生成器主类
    
    负责生成古籍风格的直排PDF电子书。
    支持章节模式和连续模式两种排版方式。
    """
    
    def __init__(self, 
                 text_file: Union[str, Path], 
                 book_cfg_path: Union[str, Path], 
                 cover_path: Optional[Union[str, Path]] = None,
                 from_page: int = 1, 
                 to_page: Optional[int] = None,
                 test_pages: Optional[int] = None, 
                 compress: bool = False, 
                 verbose: bool = False, 
                 progress_callback=None, 
                 log_callback=None):
        """
        初始化PDF生成器
        
        Args:
            text_file: 文本文件路径
            book_cfg_path: 书籍配置文件路径
            cover_path: 封面图片路径
            from_page: 起始页数
            to_page: 结束页数
            test_pages: 测试模式页数
            compress: 是否压缩PDF
            verbose: 是否输出详细信息
            progress_callback: 进度回调函数
            log_callback: 日志回调函数
        """
        # 路径参数转换
        self.text_file = Path(text_file)
        self.book_cfg_path = Path(book_cfg_path)
        self.cover_path = Path(cover_path) if cover_path else None
        
        # 参数验证
        if not self.text_file.exists():
            raise FileNotFoundError(f"错误: 未发现该书籍文本{self.text_file}！")
        if not self.book_cfg_path.exists():
            raise FileNotFoundError(f"错误：未发现该书籍排版配置文件{self.book_cfg_path}！")
        
        # 页面参数验证
        self.from_page = max(1, from_page)
        self.to_page = to_page
        if self.to_page is not None and self.to_page < self.from_page:
            raise ValueError(f"错误：结束页{self.to_page}不能小于起始页{self.from_page}")
        
        self.test_pages = test_pages
        if self.test_pages is not None and self.test_pages <= 0:
            raise ValueError(f"错误：测试页数{self.test_pages}必须大于0")
        
        # 其他参数
        self.compress = compress
        self.verbose = verbose
        
        # 回调函数
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        
        # 配置数据初始化
        self.book_config: Dict[str, Any] = {}
        self.canvas_config: Dict[str, Any] = {}
        self.zh_numbers: Dict[int, str] = {}
        
        # 字体管理初始化
        self.fonts: Dict[str, Dict[str, Any]] = {}
        self.font_paths: List[str] = []
        self.text_fonts: List[str] = []
        self.comment_fonts: List[str] = []
        
        # PDF相关属性初始化
        self.page_chars_num = 0
        self.positions_left: List[Tuple[float, float]] = []
        self.positions_right: List[Tuple[float, float]] = []
        
        # 工具类实例
        self.font_checker = FontChecker()
        self.converter = ChineseConverter()
        
        # 初始化配置和计算
        try:
            self._load_configurations()
            self._setup_fonts()
            self._calculate_positions()
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    def _log_info(self, message: str):
        """
        输出信息日志
        
        Args:
            message: 日志信息
        """
        if self.log_callback:
            self.log_callback(message)
        elif self.verbose:
            logger.info(message)
        # 当verbose=False且没有log_callback时，不输出任何信息
    
    def _log_debug(self, message: str):
        """
        输出调试日志
        
        Args:
            message: 调试信息
        """
        if self.verbose:
            if self.log_callback:
                self.log_callback(f"DEBUG: {message}")
            else:
                logger.debug(message)
    
    def _log_warning(self, message: str):
        """
        输出警告日志
        
        Args:
            message: 警告信息
        """
        if self.log_callback:
            self.log_callback(f"WARNING: {message}")
        else:
            logger.warning(message)
    
    def _log_error(self, message: str):
        """
        输出错误日志
        
        Args:
            message: 错误信息
        """
        if self.log_callback:
            self.log_callback(f"ERROR: {message}")
        else:
            logger.error(message)


    def _load_configurations(self):
        """
        加载配置文件
        
        加载书籍配置和背景图配置，以及中文数字映射。
        """
        # 加载中文数字映射
        zh_num_path = Path("db/num2zh_jid.txt")
        if zh_num_path.exists():
            self._log_debug(f"加载中文数字映射: {zh_num_path}")
            try:
                with open(zh_num_path, 'r', encoding=DEFAULT_ENCODING) as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if '|' in line:
                            try:
                                num, zh = line.split('|', 1)
                                self.zh_numbers[int(num)] = zh
                            except ValueError as e:
                                self._log_warning(f"中文数字映射文件第{line_num}行格式错误: {line}")
            except Exception as e:
                self._log_warning(f"加载中文数字映射失败: {e}")
        else:
            self._log_warning(f"未找到中文数字映射文件: {zh_num_path}")

        # 加载书籍配置
        self._log_debug(f"加载书籍配置: {self.book_cfg_path}")
        self._load_config_file(self.book_cfg_path, self.book_config)
        
        # 输出书籍信息
        self._log_info(f"\t标题：{self.book_config.get('title', '')}")
        self._log_info(f"\t作者：{self.book_config.get('author', '')}")
        self._log_info(f"\t背景：{self.book_config.get('canvas_id', '')}")
        self._log_info(f"\t每列字数：{self.book_config.get('row_num', '')}")
        self._log_info(f"\t是否无标点：{self.book_config.get('if_nocomma', '')}")
        self._log_info(f"\t标点归一化：{self.book_config.get('if_onlyperiod', '')}")

        # 加载背景图配置
        canvas_id = self.book_config.get('canvas_id')
        if not canvas_id:
            raise ValueError("错误：未定义背景图ID 'canvas_id'！")

        canvas_cfg_path = Path(f"canvas/{canvas_id}.cfg")
        canvas_jpg_path = Path(f"canvas/{canvas_id}.jpg")

        if not canvas_cfg_path.exists():
            raise FileNotFoundError(f"错误：未发现背景图cfg配置文件: {canvas_cfg_path}")
        if not canvas_jpg_path.exists():
            raise FileNotFoundError(f"错误：未发现背景图jpg图片文件: {canvas_jpg_path}")

        self._log_debug(f"加载背景图配置: {canvas_cfg_path}")
        self._load_config_file(canvas_cfg_path, self.canvas_config)
        self._log_info(f"\t尺寸：{self.canvas_config.get('canvas_width', '')} x {self.canvas_config.get('canvas_height', '')}")
        self._log_info(f"\t列数：{self.canvas_config.get('leaf_col', '')}")
    
    def _load_config_file(self, file_path: Path, config_dict: Dict[str, Any]):
        """
        加载配置文件到字典
        
        Args:
            file_path: 配置文件路径
            config_dict: 存储配置的字典
        """
        try:
            with open(file_path, 'r', encoding=DEFAULT_ENCODING) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释行
                    if not line or line.startswith('#'):
                        continue
                    
                    # 处理行内注释
                    if '#' in line and '=#' not in line:
                        line = line.split('#')[0].strip()
                    
                    if '=' not in line:
                        self._log_warning(f"配置文件{file_path}第{line_num}行格式错误：{line}")
                        continue
                    
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 类型转换
                        if value.isdigit():
                            config_dict[key] = int(value)
                        elif value.replace('.', '').replace('-', '').isdigit():
                            config_dict[key] = float(value)
                        elif value.lower() in ['true', 'false']:
                            config_dict[key] = value.lower() == 'true'
                        else:
                            config_dict[key] = value
                        
                        self._log_debug(f"加载配置: {key} = {config_dict[key]}")
                        
                    except ValueError as e:
                        self._log_warning(f"配置文件{file_path}第{line_num}行解析失败: {line} - {e}")
                        
        except Exception as e:
            self._log_error(f"加载配置文件{file_path}失败: {e}")
            raise
    
    def _setup_fonts(self):
        """
        设置字体
        
        加载配置中指定的字体文件，并注册到reportlab。
        """
        font_names = ['font1', 'font2', 'font3', 'font4', 'font5']
        loaded_fonts = []
        
        for font_name in font_names:
            font_file = self.book_config.get(font_name)
            if not font_file:
                self._log_debug(f"跳过未配置的字体: {font_name}")
                continue
                
            font_path = Path(f"fonts/{font_file}")
            if not font_path.exists():
                self._log_warning(f"未发现字体'{font_path}'，跳过该字体")
                continue
            
            # 注册字体到reportlab
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                
                # 存储字体信息
                self.fonts[font_name] = {
                    'path': str(font_path),
                    'text_size': self.book_config.get(f'text_{font_name}_size', 42),
                    'comment_size': self.book_config.get(f'comment_{font_name}_size', 30),
                    'rotate': self.book_config.get(f'{font_name}_rotate', 0)
                }
                
                self.font_paths.append(str(font_path))
                loaded_fonts.append(font_name)
                self._log_info(f"成功加载字体：{font_file}")
                
            except Exception as e:
                self._log_warning(f"字体 {font_file} 注册失败: {e}")
                self._log_info("  提示：reportlab不支持PostScript轮廓的OTF字体，请使用TTF格式字体")
        
        if not loaded_fonts:
            self._log_warning("没有成功加载任何字体，尝试加载默认字体")
            self._load_default_fonts()
        
        # 设置字体数组
        self._setup_font_arrays(loaded_fonts)
    
    def _load_default_fonts(self):
        """加载默认字体"""
        default_fonts = ['HanaMinA.ttf', 'HanaMinB.ttf', 'NotoSerifCJK-Regular.ttc']
        
        for i, default_font in enumerate(default_fonts):
            font_path = Path(f"fonts/{default_font}")
            if font_path.exists():
                try:
                    font_name = f'default_font_{i+1}'
                    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                    
                    self.fonts[font_name] = {
                        'path': str(font_path),
                        'text_size': 42,
                        'comment_size': 30,
                        'rotate': 0
                    }
                    
                    self.font_paths.append(str(font_path))
                    self._log_info(f"加载默认字体：{default_font}")
                    return  # 成功加载一个就足够
                    
                except Exception as e:
                    self._log_debug(f"加载默认字体{default_font}失败: {e}")
        
        raise RuntimeError("错误：没有可用的字体文件！请检查fonts目录")
    
    def _setup_font_arrays(self, available_fonts: List[str]):
        """
        设置字体数组
        
        Args:
            available_fonts: 可用的字体名称列表
        """
        text_fonts_array = str(self.book_config.get('text_fonts_array', '123'))
        comment_fonts_array = str(self.book_config.get('comment_fonts_array', '23'))
        
        # 设置正文字体数组
        for char in text_fonts_array:
            try:
                idx = int(char) - 1
                if 0 <= idx < len(available_fonts):
                    self.text_fonts.append(available_fonts[idx])
            except (ValueError, IndexError) as e:
                self._log_warning(f"正文字体数组配置错误: {char} - {e}")
        
        # 设置批注字体数组
        for char in comment_fonts_array:
            try:
                idx = int(char) - 1
                if 0 <= idx < len(available_fonts):
                    self.comment_fonts.append(available_fonts[idx])
            except (ValueError, IndexError) as e:
                self._log_warning(f"批注字体数组配置错误: {char} - {e}")
        
        # 确保至少有一个字体
        if not self.text_fonts and available_fonts:
            self.text_fonts.append(available_fonts[0])
            self._log_info(f"使用默认正文字体: {available_fonts[0]}")
            
        if not self.comment_fonts and available_fonts:
            self.comment_fonts.append(available_fonts[0])
            self._log_info(f"使用默认批注字体: {available_fonts[0]}")
        
        self._log_info(f"正文字体数组: {self.text_fonts}")
        self._log_info(f"批注字体数组: {self.comment_fonts}")
    
    def _calculate_positions(self):
        """
        计算文字位置
        
        根据背景图配置和书籍配置计算每个字符的精确位置。
        """
        try:
            # 获取配置参数
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
            
            # 验证参数合理性
            if col_num <= 0 or row_num <= 0:
                raise ValueError(f"列数({col_num})和行数({row_num})必须大于0")
            
            if canvas_width <= margins_left + margins_right + lc_width:
                raise ValueError(f"画布宽度({canvas_width})太小，无法容纳所有边距")
            
            if canvas_height <= margins_top + margins_bottom:
                raise ValueError(f"画布高度({canvas_height})太小，无法容纳所有边距")
            
            self._log_debug(f"计算位置: 画布{canvas_width}x{canvas_height}, 列数{col_num}, 行数{row_num}")
            
            # 计算列宽、行高
            effective_width = canvas_width - margins_left - margins_right - lc_width
            effective_height = canvas_height - margins_top - margins_bottom
            
            cw = effective_width / col_num  # 列宽
            rh = effective_height / row_num  # 行高
            
            self._log_debug(f"列宽: {cw:.2f}, 行高: {rh:.2f}")
            
            # 生成文字坐标（优化版本）
            self.positions_left = []
            self.positions_right = []
            
            position_index = 0
            for i in range(1, col_num + 1):
                # 计算X坐标
                if i <= col_num / 2:
                    pos_x = canvas_width - margins_right - cw * i
                else:
                    pos_x = canvas_width - margins_right - cw * i - lc_width
                
                for j in range(1, row_num + 1):
                    # 计算Y坐标
                    pos_y = canvas_height - margins_top - rh * j + row_delta_y
                    
                    # 存储位置
                    self.positions_left.append((pos_x, pos_y))
                    self.positions_right.append((pos_x + cw/2, pos_y))
                    position_index += 1
            
            total_positions = len(self.positions_left)
            self.page_chars_num = total_positions
            
            self._log_info(f"位置计算完成: 共{total_positions}个位置")
            
        except Exception as e:
            self._log_error(f"位置计算失败: {e}")
            raise
    
    def get_font_for_char(self, char: str, font_list: List[str]) -> Optional[str]:
        """
        获取支持指定字符的字体
        
        Args:
            char: 要检查的字符
            font_list: 候选字体列表
            
        Returns:
            Optional[str]: 支持该字符的字体名，如果没有则返回None
        """
        # 特殊字符处理：空格直接返回第一个字体
        if char in [' ', '\t', '\n', '\r']:
            return font_list[0] if font_list else None
        
        # 逐个检查字体支持
        for font_name in font_list:
            if font_name in self.fonts:
                font_path = self.fonts[font_name]['path']
                if self.font_checker.check_font_support(font_path, char):
                    return font_name
        
        # 如果没有找到支持的字体，返回第一个字体作为退路
        if font_list:
            self._log_debug(f"字符 '{char}' 在所有字体中都不受支持，使用默认字体")
            return font_list[0]
        
        return None
    
    def try_char_conversion(self, char: str) -> Tuple[str, Optional[str]]:
        """
        尝试字符转换以改善字体支持
        
        Args:
            char: 原始字符
            
        Returns:
            Tuple[str, Optional[str]]: (转换后的字符, 支持该字符的字体)
        """
        # 检查是否启用简繁转换
        if not self.book_config.get('try_st', 0) or not self.converter.available:
            return char, None
        
        # 获取主要字体
        main_font = self.text_fonts[0] if self.text_fonts else None
        if not main_font:
            return char, None
        
        # 尝试简繁转换
        char_s2t = self.converter.simp_to_trad(char)
        char_t2s = self.converter.trad_to_simp(char)
        
        # 检查简转繁的结果
        if char_s2t != char:
            font_s2t = self.get_font_for_char(char_s2t, self.text_fonts)
            if font_s2t == main_font:
                self._log_debug(f"字符转换: '{char}' -> '{char_s2t}' (简转繁)")
                return char_s2t, font_s2t
        
        # 检查繁转简的结果
        if char_t2s != char:
            font_t2s = self.get_font_for_char(char_t2s, self.text_fonts)
            if font_t2s == main_font:
                self._log_debug(f"字符转换: '{char}' -> '{char_t2s}' (繁转简)")
                return char_t2s, font_t2s
        
        return char, None
    
    def load_texts(self, text_file: Path) -> str:
        """
        加载文本文件
        
        Args:
            text_file: 文本文件路径
            
        Returns:
            str: 处理后的文本内容
        """
        if not text_file.exists():
            raise FileNotFoundError(f"文本文件不存在: {text_file}")
        
        self._log_info(f"读取文件: {text_file.name}")
        
        try:
            # 读取文件内容
            with open(text_file, 'r', encoding=DEFAULT_ENCODING) as f:
                raw_content = f.read()
            
            self._log_debug(f"文件 {text_file.name} 原始内容长度: {len(raw_content)}")
            
            processed_content = ""
            line_count = 0
            
            # 逐行处理
            for line in raw_content.split('\n'):
                line_count += 1
                
                if line.strip():  # 非空行
                    try:
                        # 标点符号处理
                        processed_line = self._process_punctuation(line.strip())
                        
                        # 处理特殊字符
                        processed_line = processed_line.replace('@', ' ')  # @代表空格
                        
                        processed_content += processed_line
                        
                    except Exception as e:
                        self._log_warning(f"处理第{line_count}行时出错: {e}")
                        # 继续处理下一行
                        continue
                else:
                    # 保留换行符作为分隔
                    processed_content += '\n'
            
            self._log_info(f"文件 {text_file.name} 处理后内容长度: {len(processed_content)}")
            self._log_debug(f"处理了 {line_count} 行文本")
            
            return processed_content
            
        except UnicodeDecodeError as e:
            self._log_error(f"文件编码错误: {e}")
            self._log_info("尝试使用其他编码格式读取...")
            
            # 尝试其他编码
            for encoding in ['gbk', 'gb2312', 'utf-16']:
                try:
                    with open(text_file, 'r', encoding=encoding) as f:
                        raw_content = f.read()
                    self._log_info(f"使用 {encoding} 编码成功读取文件")
                    
                    # 重新处理内容
                    processed_content = ""
                    line_count = 0
                    
                    for line in raw_content.split('\n'):
                        line_count += 1
                        
                        if line.strip():  # 非空行
                            try:
                                processed_line = self._process_punctuation(line.strip())
                                processed_line = processed_line.replace('@', ' ')
                                processed_content += processed_line
                                
                            except Exception as e:
                                self._log_warning(f"处理第{line_count}行时出错: {e}")
                                continue
                        else:
                            processed_content += '\n'
                    
                    return processed_content
                    
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"无法使用任何支持的编码读取文件: {text_file}")
                
        except Exception as e:
            self._log_error(f"加载文本文件失败: {e}")
            raise

    def _process_punctuation(self, text: str) -> str:
        """
        处理标点符号
        
        Args:
            text: 原始文本
            
        Returns:
            str: 处理后的文本
        """
        if not text:
            return text
        
        original_text = text
        
        try:
            # 标点符号替换
            exp_replace_comma = self.book_config.get('exp_replace_comma', '')
            if exp_replace_comma:
                replacements = exp_replace_comma.split('|')
                for replacement in replacements:
                    if len(replacement) >= 2:
                        old_char, new_char = replacement[0], replacement[1]
                        text = text.replace(old_char, new_char)
                        if old_char in original_text:
                            self._log_debug(f"标点替换: '{old_char}' -> '{new_char}'")
            
            # 数字替换
            exp_replace_number = self.book_config.get('exp_replace_number', '')
            if exp_replace_number:
                replacements = exp_replace_number.split('|')
                for replacement in replacements:
                    if len(replacement) >= 2:
                        old_char, new_char = replacement[0], replacement[1]
                        text = text.replace(old_char, new_char)
                        if old_char in original_text:
                            self._log_debug(f"数字替换: '{old_char}' -> '{new_char}'")
            
            # 标点符号删除
            exp_delete_comma = self.book_config.get('exp_delete_comma', '')
            if exp_delete_comma:
                chars_to_delete = exp_delete_comma.split('|')
                for char in chars_to_delete:
                    if char and char in text:
                        text = text.replace(char, '')
                        self._log_debug(f"删除标点: '{char}'")
            
            # 无标点模式
            if self.book_config.get('if_nocomma') == 1:
                exp_nocomma = self.book_config.get('exp_nocomma', '')
                if exp_nocomma:
                    chars_to_remove = exp_nocomma.split('|')
                    for char in chars_to_remove:
                        if char and char in text:
                            text = text.replace(char, '')
                            self._log_debug(f"无标点模式删除: '{char}'")
            
            # 标点符号归一化
            if self.book_config.get('if_onlyperiod') == 1:
                exp_onlyperiod = self.book_config.get('exp_onlyperiod', '')
                if exp_onlyperiod:
                    chars_to_replace = exp_onlyperiod.split('|')
                    for char in chars_to_replace:
                        if char and char in text:
                            text = text.replace(char, '。')
                            self._log_debug(f"标点归一化: '{char}' -> '。'")
                
                # 去除重复句号
                while '。。' in text:
                    text = text.replace('。。', '。')
                
                # 去除行首句号
                text = text.lstrip('。')
            
            return text
            
        except Exception as e:
            self._log_warning(f"标点符号处理失败: {e}")
            return original_text
    
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
        self._log_info(f"创建新PDF页[{page_num}]...")
        
        # 添加背景图
        if background_path.exists():
            c.drawImage(str(background_path), 0, 0, canvas_width, canvas_height)
        else:
            self._log_warning(f"警告：背景图 {background_path} 不存在")
        
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
            self._log_warning(f"警告：无法找到字符 '{char}' 的合适字体")
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
            self._log_warning(f"警告：无法绘制字符 '{char}': {e}")
    
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
                    self._log_warning(f"警告：无法绘制章节标题字符 '{char}': {e}")
        
        return chars_drawn
    
    def print_welcome(self):
        """打印欢迎信息"""
        welcome_msg = f"""
{'-' * 60}
\t{SOFTWARE} {VERSION}，兀雨古籍刻本电子书制作工具
\t作者：GitHub@shanleiguang 小红书@兀雨书屋
\tPython版本转换：msyloveldx
{'-' * 60}"""
        self._log_info(welcome_msg)
    
    def generate_pdf(self, text_file):
        """生成PDF文件"""
        self.print_welcome()
        
        if self.test_pages:
            self._log_info(f"注意：-z 测试模式，仅输出{self.test_pages}页用于调试排版参数！")
        
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
        
        self._log_info(f"生成PDF文件'results/{pdf_filename}.pdf'...完成！")
        
        # 压缩处理
        if self.compress:
            self._compress_pdf(pdf_path)
        else:
            self._log_info("建议：使用'-c'参数对PDF文件进行压缩！")
    

    def _add_cover(self, c, canvas_width: float, canvas_height: float):
        """添加封面"""
        if self.cover_path and self.cover_path.exists():
            self._log_info(f"发现封面图片{self.cover_path}")
            c.drawImage(str(self.cover_path), 0, 0, canvas_width, canvas_height)
        else:
            if self.cover_path:
                self._log_info(f"未发现封面图片{self.cover_path}，创建简易封面...")
            else:
                self._log_info("未提供封面图片，创建简易封面...")
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
            self._log_warning("警告：文本内容为空")
            return
        
        # 检查是否启用章节模式
        enable_chapter_mode = self.book_config.get('enable_chapter_mode', 0)
        self._log_info(f"章节模式: {'启用' if enable_chapter_mode else '禁用'}")
        
        if enable_chapter_mode:
            self._process_with_chapters(c, text_content, canvas_width, canvas_height, background_path)
        else:
            self._process_without_chapters(c, text_content, canvas_width, canvas_height, background_path)
    
    def _process_with_chapters(self, c, text_content: str, canvas_width: float, canvas_height: float, background_path: Path):
        """章节模式处理文本"""
        self._log_info(f"处理文本，总字符数: {len(text_content)}")
        
        # 解析章节
        chapters = self._parse_chapters(text_content)
        self._log_info(f"检测到 {len(chapters)} 个章节")
        
        page_num = 0
        total_processed_chars = 0
        page_char_count = 0  # 初始化变量
        
        for chapter_index, (chapter_title, chapter_content) in enumerate(chapters):
            if self.test_pages and page_num >= self.test_pages:
                break
            
            self._log_info(f"处理章节: {chapter_title}")
            
            # 开始新页面（每章一页）
            current_page = self.from_page + page_num
            self._start_new_page(c, current_page, canvas_width, canvas_height, background_path)
            
            # 在第一列绘制章节标题
            chapter_chars_used = self._draw_chapter_title(c, chapter_title, canvas_width, canvas_height)
            
            # 计算内容开始位置（跳过第一列）
            row_num = int(self.book_config.get('row_num', 30))
            content_start_pos = row_num  # 从第二列开始
            page_char_count = content_start_pos
            
            self._log_debug(f"章节内容长度: {len(chapter_content)}, 内容开始位置: {content_start_pos}, 页面总字符数: {self.page_chars_num}")
            
            # 处理章节内容
            chars = list(chapter_content)
            char_index = 0
            
            while char_index < len(chars):
                # 检查是否需要换页
                if page_char_count >= self.page_chars_num:
                    self._log_debug(f"换页：当前字符位置 {page_char_count} >= 页面字符数 {self.page_chars_num}")
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
                    self._log_debug(f"绘制字符 '{char}' 在位置 {page_char_count}")
                    self._draw_char_at_position(c, char, page_char_count)
                    page_char_count += 1
                    total_processed_chars += 1
                else:
                    self._log_warning(f"字符位置 {page_char_count} 超出范围 {len(self.positions_left)}")
            
            # 章节结束，准备下一页
            if chapter_index < len(chapters) - 1:  # 不是最后一章
                c.showPage()
                page_num += 1
        
        # 不需要为最后一页单独调用showPage()，因为：
        # 1. 如果页面没有内容，不应该创建空白页
        # 2. 如果页面有内容，但是PDF生成器会在save()时自动处理最后一页
        # 3. 满页的情况已经在换页逻辑中处理了
        
        actual_pages = page_num + 1
        self._log_info(f"生成完成，共 {actual_pages} 页，处理了 {total_processed_chars} 个字符")
    
    def _process_without_chapters(self, c, text_content: str, canvas_width: float, canvas_height: float, background_path: Path):
        """非章节模式处理文本（原逻辑）"""
        # 将文本转换为字符列表
        chars = list(text_content)
        total_chars = len(chars)
        self._log_info(f"处理文本，总字符数: {total_chars}")
        
        # 计算需要跳过的字符数（如果指定了起始页）
        chars_to_skip = 0
        if self.from_page > 1:
            chars_to_skip = (self.from_page - 1) * self.page_chars_num
            self._log_info(f"从第 {self.from_page} 页开始，跳过前 {chars_to_skip} 个字符")
        
        # 计算最大输出字符数（如果指定了结束页）
        max_chars_to_process = None
        if self.to_page is not None and self.to_page >= self.from_page:
            page_count = self.to_page - self.from_page + 1
            max_chars_to_process = page_count * self.page_chars_num
            self._log_info(f"输出 {self.from_page} 到 {self.to_page} 页，共 {page_count} 页，最多处理 {max_chars_to_process} 个字符")
        else:
            self._log_info(f"从第 {self.from_page} 页开始，输出全部剩余内容")
        
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
        
        self._log_debug(f"跳过了 {processed_chars} 个有效字符，从字符索引 {char_index} 开始处理")
        
        # 重置计数器，开始实际页面生成
        processed_chars = 0
        page_char_count = 0
        page_num = 0
        
        # 开始第一页
        self._start_new_page(c, self.from_page, canvas_width, canvas_height, background_path)
        
        while char_index < total_chars:
            # 检查测试页数限制
            if self.test_pages and page_num >= self.test_pages:
                break
            
            # 检查是否达到指定的最大字符数
            if max_chars_to_process is not None and processed_chars >= max_chars_to_process:
                self._log_info(f"已达到指定页数范围，停止处理")
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
        
        # 不需要为最后一页单独调用showPage()，因为：
        # 1. 如果页面没有内容，不应该创建空白页
        # 2. 如果页面有内容，但是PDF生成器会在save()时自动处理最后一页
        # 3. 满页的情况已经在换页逻辑中处理了
        # if page_char_count > 0:
        #     c.showPage()
        
        actual_pages = page_num + 1
        actual_page_range = f"{self.from_page} 到 {self.from_page + page_num}"
        self._log_info(f"生成完成，共 {actual_pages} 页（第 {actual_page_range} 页）")
    
    def _parse_chapters(self, text_content: str) -> List[Tuple[str, str]]:
        """解析章节
        返回: [(章节标题, 章节内容), ...]
        """
        import re
        
        chapters = []
        
        # 查找所有章节标题
        chapter_pattern = r'第(\d+)章\s+([^\n\r]+)'
        matches = list(re.finditer(chapter_pattern, text_content))
        
        self._log_debug(f"章节解析：找到 {len(matches)} 个章节")
        
        if not matches:
            # 如果没有找到章节，将整个文本作为一个章节
            self._log_debug("未找到章节，将整个文本作为一个章节")
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
            self._log_debug(f"章节 {i+1}: '{chapter_title}', 内容长度: {len(chapter_content)}")
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
            self._log_info(f"压缩PDF文件'{output_path}'...完成！")
            
        except subprocess.CalledProcessError:
            self._log_warning("PDF压缩失败，请检查是否安装了Ghostscript")
        except FileNotFoundError:
            self._log_warning("未找到Ghostscript，无法压缩PDF")

def create_custom_generator(text_file_path: str, book_config_path: str, 
                          cover_path: Optional[str] = None, from_page: int = 1, 
                          to_page: Optional[int] = None, test_pages: Optional[int] = None, 
                          compress: bool = False, verbose: bool = False):
    """
    创建自定义配置的PDF生成器
    
    Args:
        text_file_path: 文本文件路径
        book_config_path: 书籍配置文件路径
        cover_path: 封面图片路径
        from_page: 起始页数
        to_page: 结束页数
        test_pages: 测试模式页数
        compress: 是否压缩PDF
        verbose: 是否详细输出
        
    Returns:
        VRainPDFGenerator: 配置好的PDF生成器
    """
    text_file = Path(text_file_path)
    book_cfg_path = Path(book_config_path)
    cover_file = Path(cover_path) if cover_path and Path(cover_path).exists() else None
    
    return VRainPDFGenerator(
        text_file=text_file,
        book_cfg_path=book_cfg_path,
        cover_path=cover_file,
        from_page=from_page,
        to_page=to_page,
        test_pages=test_pages,
        compress=compress,
        verbose=verbose
    )

def main():
    """
    主函数
    
    直接运行示例，不使用命令行参数。
    """
    try:        
        # 处理神武天帝小说（章节模式）
        text_file = Path('books/04/text/神武天帝.txt')
        book_cfg_path = Path('books/04/book.cfg')
        cover_path = Path('books/04/cover.jpg') if Path('books/04/cover.jpg').exists() else None
        
        # 初始化生成器
        generator = VRainPDFGenerator(
            text_file=text_file,
            book_cfg_path=book_cfg_path,
            cover_path=cover_path,
            from_page=1,
            # test_pages=3,  # 测试模式，只生成3页
            verbose=True
        )
        
        # 生成PDF
        generator.generate_pdf(text_file)
        
        # 在verbose=False时不输出任务完成信息
        # logger.info("任务完成！")
        
    except KeyboardInterrupt:
        print("用户取消了操作")
        sys.exit(130)
        
    except FileNotFoundError as e:
        print(f"错误：{e}")
        print("请检查books目录下是否存在所需的文件")
        sys.exit(1)
        
    except ValueError as e:
        print(f"错误：{e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"发生意外错误: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    # 直接运行主函数，不使用命令行参数
    main()
    
    # 如果需要自定义配置，可以使用以下方式：
    # 
    # 示例1：处理神武天帝小说（章节模式）
    # generator = create_custom_generator(
    #     text_file_path='books/04/text/神武天帝.txt',
    #     book_config_path='books/04/book.cfg',
    #     cover_path='books/04/cover.jpg',
    #     test_pages=5,  # 测试模式，只生成5页
    #     verbose=True
    # )
    # generator.generate_pdf(generator.text_file)
    #
    # 示例2：生成指定页数范围的PDF
    # generator = create_custom_generator(
    #     text_file_path='books/01/text/000.txt',
    #     book_config_path='books/01/book.cfg',
    #     from_page=5,
    #     to_page=10,
    #     compress=True,  # 生成后压缩PDF
    #     verbose=True
    # )
    # generator.generate_pdf(generator.text_file)


