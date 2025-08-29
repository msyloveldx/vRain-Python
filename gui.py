#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vRain中文古籍刻本风格直排电子书制作工具 - 现代化双模式GUI版本
支持两种工作模式：
1. 传统古籍模式（基于vrain.py）
2. 小说章节模式（基于vrainNovel.py）

现代化特性：
- 响应式布局设计
- 深色/浅色主题切换
- 现代化控件样式
- 优化的视觉层次
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import queue
import json

# 导入原有模块
try:
    from vrain import VRainPerfect
except ImportError:
    print("警告：无法导入vrain.py模块")
    VRainPerfect = None

try:
    from vrainNovel import VRainPDFGenerator
except ImportError:
    print("警告：无法导入vrainNovel.py模块")
    VRainPDFGenerator = None

# 全局变量
SOFTWARE = 'vRain'
VERSION = 'v1.4-ModernGUI'

# 现代化主题配置
class ModernTheme:
    """现代化主题配置类"""
    
    def __init__(self):
        self.current_theme = 'light'  # 默认浅色主题
        
        # 浅色主题
        self.light_theme = {
            'bg': '#f8f9fa',
            'fg': '#212529',
            'select_bg': '#007bff',
            'select_fg': '#ffffff',
            'entry_bg': '#ffffff',
            'entry_fg': '#495057',
            'button_bg': '#007bff',
            'button_fg': '#ffffff',
            'button_hover': '#0056b3',
            'frame_bg': '#ffffff',
            'accent': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'border': '#dee2e6',
            'success': '#28a745',
            'info': '#17a2b8'
        }
        
        # 深色主题
        self.dark_theme = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'select_bg': '#0d7377',
            'select_fg': '#ffffff',
            'entry_bg': '#3c3c3c',
            'entry_fg': '#ffffff',
            'button_bg': '#0d7377',
            'button_fg': '#ffffff',
            'button_hover': '#14a085',
            'frame_bg': '#3c3c3c',
            'accent': '#40e0d0',
            'warning': '#ffaa00',
            'error': '#ff6b6b',
            'border': '#555555',
            'success': '#4dd0e1',
            'info': '#81c784'
        }
    
    def get_theme(self):
        """获取当前主题"""
        return self.dark_theme if self.current_theme == 'dark' else self.light_theme
    
    def toggle_theme(self):
        """切换主题"""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        return self.get_theme()

class VRainDualGUI:
    """现代化vRain双模式GUI主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"古籍刻本电子书制作工具")
        self.root.geometry("1200x1200")
        self.root.minsize(1000, 700)
        self.root.resizable(True, True)
        
        # 初始化主题系统
        self.theme = ModernTheme()
        
        # 设置窗口图标
        try:
            self.root.iconbitmap("cover.png")
        except:
            pass
        
        # 配置现代化样式
        self.setup_modern_style()
        
        # 创建消息队列用于线程间通信
        self.message_queue = queue.Queue()
        
        # 初始化变量
        self.init_variables()
        
        # 创建工具提示系统
        self.setup_tooltips()
        
        # 创建界面
        self.create_widgets()
        
        # 启动消息处理
        self.process_messages()
        
        # 设置初始主题
        self.apply_theme()
    
    def setup_tooltips(self):
        """设置工具提示"""
        # 简单的工具提示系统
        self.tooltips = {}
    
    def setup_modern_style(self):
        """设置现代化样式"""
        style = ttk.Style()
        
        # 设置主题
        try:
            style.theme_use('clam')  # 使用现代化主题
        except:
            style.theme_use('default')
        
        # 自定义样式
        self.configure_custom_styles(style)
    
    def configure_custom_styles(self, style):
        """配置自定义样式"""
        theme_colors = self.theme.get_theme()
        
        # 配置标准按钮样式
        style.configure('TButton', 
                       font=('Segoe UI', 10),
                       padding=(12, 8))
        
        # 配置标签框样式
        style.configure('TLabelFrame', 
                       font=('Segoe UI', 10, 'bold'))
        
        style.configure('TLabelFrame.Label',
                       font=('Segoe UI', 10, 'bold'))
        
        # 配置笔记本样式
        style.configure('TNotebook.Tab', 
                       font=('Segoe UI', 11, 'bold'),
                       padding=(20, 10))
        
        # 配置复选框样式
        style.configure('TCheckbutton',
                       font=('Segoe UI', 10))
    
    def apply_theme(self):
        """应用主题颜色"""
        theme_colors = self.theme.get_theme()
        
        # 设置主窗口背景
        self.root.configure(bg=theme_colors['bg'])
        
        # 更新所有子控件的样式
        self.update_widget_colors(self.root, theme_colors)
    
    def update_widget_colors(self, widget, colors):
        """递归更新控件颜色"""
        try:
            widget_class = widget.winfo_class()
            
            if widget_class == 'Frame':
                widget.configure(bg=colors['frame_bg'])
            elif widget_class == 'Label':
                widget.configure(bg=colors['bg'], fg=colors['fg'])
            elif widget_class == 'Text':
                widget.configure(bg=colors['entry_bg'], fg=colors['entry_fg'],
                               insertbackground=colors['fg'],
                               selectbackground=colors['select_bg'],
                               selectforeground=colors['select_fg'])
            elif widget_class == 'Listbox':
                widget.configure(bg=colors['entry_bg'], fg=colors['entry_fg'],
                               selectbackground=colors['select_bg'],
                               selectforeground=colors['select_fg'])
            
            # 递归处理子控件
            for child in widget.winfo_children():
                self.update_widget_colors(child, colors)
                
        except tk.TclError:
            pass  # 忽略不支持的控件
    
    def toggle_theme(self):
        """切换主题"""
        old_theme = self.theme.current_theme
        self.theme.toggle_theme()
        self.apply_theme()
        self.configure_custom_styles(ttk.Style())
        
        # 更新主题按钮文字
        theme_icon = "🌓" if self.theme.current_theme == 'light' else "☀️"
        new_theme_name = "深色" if self.theme.current_theme == 'light' else "浅色"
        # 这里可以更新按钮文字，但需要对按钮的引用
        
        self.log_message(f"已切换到{self.theme.current_theme.upper()}主题")

    def init_variables(self):
        """初始化变量"""
        # 传统古籍模式变量
        self.perfect_book_id_var = tk.StringVar()
        self.perfect_from_page_var = tk.IntVar(value=1)
        self.perfect_to_page_var = tk.IntVar(value=1)
        self.perfect_test_pages_var = tk.IntVar()
        self.perfect_compress_var = tk.BooleanVar(value=False)
        self.perfect_verbose_var = tk.BooleanVar(value=True)
        
        # 小说章节模式变量
        self.novel_text_file_var = tk.StringVar()
        self.novel_book_cfg_var = tk.StringVar()
        self.novel_cover_file_var = tk.StringVar()
        self.novel_from_page_var = tk.IntVar(value=1)
        self.novel_to_page_var = tk.IntVar()
        self.novel_test_pages_var = tk.IntVar()
        self.novel_compress_var = tk.BooleanVar(value=False)
        self.novel_verbose_var = tk.BooleanVar(value=True)
    
    def create_widgets(self):
        """创建GUI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题和控制区域
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=tk.W+tk.E, pady=(0, 20))
        title_frame.columnconfigure(0, weight=1)
        
        # 标题
        title_label = ttk.Label(title_frame, text=f"🏛️ 古籍刻本电子书制作工具 {VERSION}", 
                               font=("Segoe UI", 16, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # 主题切换按钮
        theme_btn = ttk.Button(title_frame, text="🌓 切换主题", command=self.toggle_theme)
        theme_btn.grid(row=0, column=1, sticky=tk.E)
        
        # 创建标签页
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
        
        # 配置标签页样式
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[20, 10], font=('Segoe UI', 11, 'bold'))
        
        # 创建两个标签页
        self.create_perfect_tab()
        self.create_novel_tab()
        
        # 日志输出区域（共享）
        self.create_log_frame(main_frame)
        
        # 状态栏
        self.create_status_bar(main_frame)
    
    def create_perfect_tab(self):
        """创建传统古籍模式标签页"""
        # 创建标签页框架
        self.perfect_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.perfect_frame, text="📜 传统古籍模式")
        
        # 配置网格权重
        self.perfect_frame.columnconfigure(1, weight=1)
        
        # 说明文字
        desc_label = ttk.Label(self.perfect_frame, 
                              text="传统古籍原Perl版本功能，使用书籍ID模式，支持多文本文件处理",
                              font=("Arial", 10))
        desc_label.grid(row=0, column=0, columnspan=3, pady=(0, 15), sticky=tk.W)
        
        # 书籍ID选择
        self.create_perfect_book_selection(self.perfect_frame)
        
        # 参数配置
        self.create_perfect_parameters(self.perfect_frame)
        
        # 选项配置
        self.create_perfect_options(self.perfect_frame)
        
        # 控制按钮
        self.create_perfect_controls(self.perfect_frame)
        
        # 快速示例
        self.create_perfect_examples(self.perfect_frame)
    
    def create_novel_tab(self):
        """创建小说章节模式标签页"""
        # 创建标签页框架
        self.novel_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.novel_frame, text="📚 小说章节模式")
        
        # 配置网格权重
        self.novel_frame.columnconfigure(1, weight=1)
        
        # 说明文字
        desc_label = ttk.Label(self.novel_frame, 
                              text="📖 专为小说排版优化，支持章节自动识别和标题处理",
                              font=("Segoe UI", 10), foreground="#666666")
        desc_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky=tk.W)
        
        # 文件选择
        self.create_novel_file_selection(self.novel_frame)
        
        # 参数配置
        self.create_novel_parameters(self.novel_frame)
        
        # 选项配置
        self.create_novel_options(self.novel_frame)
        
        # 控制按钮
        self.create_novel_controls(self.novel_frame)
        
        # 快速示例
        self.create_novel_examples(self.novel_frame)
    
    def create_perfect_book_selection(self, parent):
        """创建传统古籍模式的书籍选择区域"""
        # 书籍选择框架
        book_frame = ttk.LabelFrame(parent, text="📚 书籍选择")
        book_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 15))
        book_frame.columnconfigure(1, weight=1)
        
        # 书籍ID输入
        ttk.Label(book_frame, text="书籍ID:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        book_id_entry = ttk.Entry(book_frame, textvariable=self.perfect_book_id_var, width=20, font=("Segoe UI", 10))
        book_id_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 10), pady=8)
        
        # 刷新按钮
        ttk.Button(book_frame, text="🔄 刷新书籍列表", command=self.refresh_book_list).grid(row=0, column=2, pady=8)
        
        # 书籍列表
        ttk.Label(book_frame, text="可用书籍:", font=("Segoe UI", 10)).grid(row=1, column=0, sticky=tk.W+tk.N, pady=(10, 8))
        
        # 创建书籍列表框架
        list_frame = ttk.Frame(book_frame)
        list_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, padx=(10, 0), pady=(10, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 书籍列表框
        self.book_listbox = tk.Listbox(list_frame, height=6, font=("Segoe UI", 9))
        self.book_listbox.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
        self.book_listbox.bind('<<ListboxSelect>>', self.on_book_select)
        
        # 滚动条
        book_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.book_listbox.yview)
        book_scrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)
        self.book_listbox.configure(yscrollcommand=book_scrollbar.set)
        
        # 初始化书籍列表
        self.refresh_book_list()
    
    def create_perfect_parameters(self, parent):
        """创建传统古籍模式的参数配置区域"""
        # 参数框架
        param_frame = ttk.LabelFrame(parent, text="⚙️ 页面参数")
        param_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 15))
        
        # 创建两列布局
        left_frame = ttk.Frame(param_frame)
        left_frame.grid(row=0, column=0, sticky=tk.W+tk.E, padx=(0, 20))
        
        right_frame = ttk.Frame(param_frame)
        right_frame.grid(row=0, column=1, sticky=tk.W+tk.E)
        
        # 左列：起始页
        ttk.Label(left_frame, text="起始文本序号:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        from_spinbox = ttk.Spinbox(left_frame, from_=1, to=999, textvariable=self.perfect_from_page_var, width=12, font=("Segoe UI", 10))
        from_spinbox.grid(row=1, column=0, sticky=tk.W, pady=(0, 8))
        
        # 右列：结束页
        ttk.Label(right_frame, text="结束文本序号:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        to_spinbox = ttk.Spinbox(right_frame, from_=1, to=999, textvariable=self.perfect_to_page_var, width=12, font=("Segoe UI", 10))
        to_spinbox.grid(row=1, column=0, sticky=tk.W, pady=(0, 8))
        
        # 测试页数（单独一行）
        test_frame = ttk.Frame(param_frame)
        test_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(10, 0))
        
        ttk.Label(test_frame, text="测试页数:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        test_spinbox = ttk.Spinbox(test_frame, from_=0, to=999, textvariable=self.perfect_test_pages_var, width=12, font=("Segoe UI", 10))
        test_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=8)
        ttk.Label(test_frame, text="(0表示正常模式)", font=("Segoe UI", 9), foreground="gray").grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=8)
    
    def create_perfect_options(self, parent):
        """创建传统古籍模式的选项区域"""
        # 选项框架
        options_frame = ttk.LabelFrame(parent, text="🔧 选项配置")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 15))
        
        # 使用水平布局
        option_container = ttk.Frame(options_frame)
        option_container.pack(fill='x', padx=10, pady=10)
        
        # 复选框
        compress_cb = ttk.Checkbutton(option_container, text="📋 压缩PDF", variable=self.perfect_compress_var)
        compress_cb.pack(side=tk.LEFT, padx=(0, 30))
        
        verbose_cb = ttk.Checkbutton(option_container, text="📝 详细输出", variable=self.perfect_verbose_var)
        verbose_cb.pack(side=tk.LEFT)
    
    def create_perfect_controls(self, parent):
        """创建传统古籍模式的控制按钮区域"""
        # 控制框架
        control_frame = ttk.LabelFrame(parent, text="🚀 操作控制")
        control_frame.grid(row=4, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 15))
        
        # 按钮容器
        button_container = ttk.Frame(control_frame)
        button_container.pack(fill='x', padx=10, pady=10)
        
        # 主要按钮
        self.perfect_generate_btn = ttk.Button(button_container, text="📝 生成PDF", command=self.generate_perfect_pdf)
        self.perfect_generate_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # 辅助按钮
        ttk.Button(button_container, text="📁 打开书籍目录", command=self.open_book_dir).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(button_container, text="🔍 检查字体", command=self.check_fonts).pack(side=tk.LEFT)
    
    def create_perfect_examples(self, parent):
        """创建传统古籍模式的快速示例区域"""
        # 示例框架
        example_frame = ttk.LabelFrame(parent, text="⚡ 快速示例")
        example_frame.grid(row=5, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 15))
        
        # 按钮容器
        example_container = ttk.Frame(example_frame)
        example_container.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(example_container, text="📜 史记示例", command=self.load_perfect_shiji).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(example_container, text="🌿 庄子示例", command=self.load_perfect_zhuangzi).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(example_container, text="❓ 帮助", command=self.show_perfect_help).pack(side=tk.LEFT)
    
    # 这里添加所有其他方法的占位符
    def create_novel_file_selection(self, parent):
        """创建小说章节模式的文件选择区域"""
        # 文件选择框架
        file_frame = ttk.LabelFrame(parent, text="📁 文件选择")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 15))
        file_frame.columnconfigure(1, weight=1)
        
        # 文本文件选择
        ttk.Label(file_frame, text="📝 文本文件:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        text_entry = ttk.Entry(file_frame, textvariable=self.novel_text_file_var, width=50, font=("Segoe UI", 9))
        text_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(10, 10), pady=8)
        ttk.Button(file_frame, text="🔍 浏览", command=self.browse_novel_text_file).grid(row=0, column=2, pady=8)
        
        # 书籍配置文件选择
        ttk.Label(file_frame, text="⚙️ 书籍配置:", font=("Segoe UI", 10)).grid(row=1, column=0, sticky=tk.W, pady=8)
        book_entry = ttk.Entry(file_frame, textvariable=self.novel_book_cfg_var, width=50, font=("Segoe UI", 9))
        book_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=(10, 10), pady=8)
        ttk.Button(file_frame, text="🔍 浏览", command=self.browse_novel_book_cfg).grid(row=1, column=2, pady=8)
        
        # 封面文件选择（可选）
        ttk.Label(file_frame, text="🎨 封面文件:", font=("Segoe UI", 10)).grid(row=2, column=0, sticky=tk.W, pady=8)
        cover_entry = ttk.Entry(file_frame, textvariable=self.novel_cover_file_var, width=50, font=("Segoe UI", 9))
        cover_entry.grid(row=2, column=1, sticky=tk.W+tk.E, padx=(10, 10), pady=8)
        ttk.Button(file_frame, text="🔍 浏览", command=self.browse_novel_cover_file).grid(row=2, column=2, pady=8)
        ttk.Label(file_frame, text="(可选，留空将创建简易封面)", font=("Segoe UI", 9), foreground="gray").grid(row=2, column=3, sticky=tk.W, padx=(10, 0), pady=8)
    def create_novel_parameters(self, parent):
        """创建小说章节模式的参数配置区域"""
        # 参数框架
        param_frame = ttk.LabelFrame(parent, text="⚙️ 页面参数")
        param_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 15))
        
        # 布局容器
        container = ttk.Frame(param_frame)
        container.pack(fill='x', padx=15, pady=15)
        
        # 第一行：起始页和结束页
        row1 = ttk.Frame(container)
        row1.pack(fill='x', pady=(0, 15))
        
        # 起始页
        start_frame = ttk.Frame(row1)
        start_frame.pack(side=tk.LEFT, padx=(0, 30))
        ttk.Label(start_frame, text="起始页:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        from_spinbox = ttk.Spinbox(start_frame, from_=1, to=9999, textvariable=self.novel_from_page_var, width=12, font=("Segoe UI", 10))
        from_spinbox.pack(pady=(5, 0))
        
        # 结束页
        end_frame = ttk.Frame(row1)
        end_frame.pack(side=tk.LEFT)
        ttk.Label(end_frame, text="结束页:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        end_container = ttk.Frame(end_frame)
        end_container.pack(fill='x', pady=(5, 0))
        to_spinbox = ttk.Spinbox(end_container, from_=0, to=9999, textvariable=self.novel_to_page_var, width=12, font=("Segoe UI", 10))
        to_spinbox.pack(side=tk.LEFT)
        ttk.Label(end_container, text="(0表示输出全部)", font=("Segoe UI", 9), foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
        
        # 第二行：测试页数
        row2 = ttk.Frame(container)
        row2.pack(fill='x')
        
        test_frame = ttk.Frame(row2)
        test_frame.pack(side=tk.LEFT)
        ttk.Label(test_frame, text="测试页数:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        test_container = ttk.Frame(test_frame)
        test_container.pack(fill='x', pady=(5, 0))
        test_spinbox = ttk.Spinbox(test_container, from_=0, to=999, textvariable=self.novel_test_pages_var, width=12, font=("Segoe UI", 10))
        test_spinbox.pack(side=tk.LEFT)
        ttk.Label(test_container, text="(0表示正常模式)", font=("Segoe UI", 9), foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
    
    def create_novel_options(self, parent):
        """创建小说章节模式的选项区域"""
        # 选项框架
        options_frame = ttk.LabelFrame(parent, text="🔧 选项配置")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 15))
        
        # 选项容器
        option_container = ttk.Frame(options_frame)
        option_container.pack(fill='x', padx=15, pady=15)
        
        # 复选框
        ttk.Checkbutton(option_container, text="📋 压缩PDF", variable=self.novel_compress_var).pack(side=tk.LEFT, padx=(0, 30))
        ttk.Checkbutton(option_container, text="📝 详细输出", variable=self.novel_verbose_var).pack(side=tk.LEFT)
    def create_novel_controls(self, parent):
        """创建小说章节模式的控制按钮区域"""
        # 控制框架
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        # 按钮
        self.novel_generate_btn = ttk.Button(control_frame, text="生成PDF", command=self.generate_novel_pdf)
        self.novel_generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="验证配置", command=self.validate_novel_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="预览章节", command=self.preview_chapters).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="配置管理", command=self.manage_novel_config).pack(side=tk.LEFT)
    def create_novel_examples(self, parent):
        """创建小说章节模式的快速示例区域"""
        # 示例框架
        example_frame = ttk.LabelFrame(parent, text="快速示例", padding="10")
        example_frame.grid(row=5, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 10))
        
        ttk.Button(example_frame, text="神武示例", command=self.load_novel_shenwu).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(example_frame, text="帮助", command=self.show_novel_help).pack(side=tk.LEFT)
    def create_log_frame(self, parent):
        """创建日志输出区域"""
        # 日志框架
        log_frame = ttk.LabelFrame(parent, text="日志输出", padding="10")
        log_frame.grid(row=2, column=0, sticky=tk.W+tk.E+tk.N+tk.S, pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 日志文本区域
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=12)
        self.log_text.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
        
        # 日志控制按钮
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.grid(row=1, column=0, sticky=tk.W+tk.E, pady=(5, 0))
        
        ttk.Button(log_control_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_control_frame, text="保存日志", command=self.save_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_control_frame, text="打开结果目录", command=self.open_results_dir).pack(side=tk.LEFT)
    def create_status_bar(self, parent):
        """创建状态栏"""
        # 状态栏框架
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, sticky=tk.W+tk.E, pady=(5, 0))
        status_frame.columnconfigure(0, weight=1)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(10, 0))
        status_frame.columnconfigure(1, weight=1)
    def refresh_book_list(self):
        """刷新书籍列表"""
        try:
            self.book_listbox.delete(0, tk.END)
            
            # 扫描书籍目录
            books_dir = Path('books')
            if books_dir.exists():
                for book_dir in books_dir.iterdir():
                    if book_dir.is_dir():
                        self.book_listbox.insert(tk.END, book_dir.name)
            
            self.log_message(f"🔄 已刷新书籍列表，找到 {self.book_listbox.size()} 本书籍", 'SUCCESS')
            
        except Exception as e:
            self.log_message(f"刷新书籍列表失败: {e}", 'ERROR')
    def on_book_select(self, event):
        """书籍选择事件处理"""
        try:
            selection = self.book_listbox.curselection()
            if selection:
                book_id = self.book_listbox.get(selection[0])
                self.perfect_book_id_var.set(book_id)
                self.log_message(f"📚 已选择书籍: {book_id}", 'INFO')
        except Exception as e:
            self.log_message(f"选择书籍失败: {e}", 'ERROR')
    def generate_perfect_pdf(self):
        """生成传统古籍模式PDF"""
        try:
            book_id = self.perfect_book_id_var.get().strip()
            if not book_id:
                messagebox.showerror("错误", "请选择或输入书籍ID")
                return
            
            if VRainPerfect is None:
                messagebox.showerror("错误", "无法加载 vrain.py 模块")
                return
            
            # 检查书籍目录是否存在
            book_path = Path('books') / book_id
            if not book_path.exists():
                messagebox.showerror("错误", f"书籍目录不存在: {book_path}")
                return
            
            # 禁用按钮
            self.perfect_generate_btn.configure(state='disabled')
            self.update_progress(0)
            self.status_var.set("正在生成PDF...")
            
            # 在新线程中生成PDF
            thread = threading.Thread(target=self._generate_perfect_pdf_thread, args=(book_id,), daemon=True)
            thread.start()
            
        except Exception as e:
            self.log_message(f"生成PDF失败: {e}")
            self.perfect_generate_btn.configure(state='normal')
            self.status_var.set("就绪")
    def _generate_perfect_pdf_thread(self, book_id):
        """在后台线程中生成完美复刿PDF"""
        try:
            # 检查 VRainPerfect 模块是否可用
            if VRainPerfect is None:
                self.message_queue.put(('log', "错误：无法加载 vrain.py 模块"))
                self.message_queue.put(('status', "模块加载失败"))
                return
            
            self.message_queue.put(('log', f"开始生成书籍: {book_id}"))
            self.message_queue.put(('progress', 10))
            
            # 创建 VRainPerfect 实例
            vrain = VRainPerfect()
            
            # 设置参数 - 模拟命令行参数
            vrain.opts = {
                'b': book_id,
                'f': self.perfect_from_page_var.get(),
                't': self.perfect_to_page_var.get(),
                'z': self.perfect_test_pages_var.get() if self.perfect_test_pages_var.get() > 0 else None,
                'c': self.perfect_compress_var.get(),
                'v': self.perfect_verbose_var.get()
            }
            
            self.message_queue.put(('progress', 30))
            
            # 加载配置
            vrain.load_zh_numbers()
            vrain.check_directories(book_id)
            vrain.load_book_config(book_id)
            vrain.validate_config()
            vrain.setup_fonts()
            vrain.load_canvas_config()
            vrain.calculate_positions()
            
            self.message_queue.put(('progress', 60))
            
            # 加载文本
            dats, if_text000, if_text999 = vrain.load_texts(book_id, vrain.opts['f'], vrain.opts['t'])
            
            self.message_queue.put(('progress', 80))
            
            # 生成PDF
            pdf_file = vrain.create_pdf(book_id, vrain.opts['f'], vrain.opts['t'], dats, if_text000, if_text999)
            
            self.message_queue.put(('progress', 100))
            self.message_queue.put(('log', f"PDF生成完成: {pdf_file}"))
            self.message_queue.put(('status', "生成完成"))
            
        except Exception as e:
            self.message_queue.put(('log', f"生成PDF错误: {e}"))
            self.message_queue.put(('status', "生成失败"))
        finally:
            self.message_queue.put(('enable_button', 'perfect'))
    def load_perfect_shiji(self):
        """加载史记示例"""
        self.perfect_book_id_var.set('01')
        self.perfect_from_page_var.set(1)
        self.perfect_to_page_var.set(3)
        self.perfect_test_pages_var.set(2)
        self.log_message("📜 已加载史记示例配置", 'SUCCESS')
    def load_perfect_zhuangzi(self):
        """加载庄子示例"""
        self.perfect_book_id_var.set('02')
        self.perfect_from_page_var.set(1)
        self.perfect_to_page_var.set(2)
        self.perfect_test_pages_var.set(1)
        self.log_message("🌿 已加载庄子示例配置", 'SUCCESS')
    def open_book_dir(self):
        """打开书籍目录"""
        try:
            books_dir = Path('books')
            if books_dir.exists():
                os.startfile(str(books_dir))
            else:
                messagebox.showwarning("警告", "books目录不存在")
        except Exception as e:
            self.log_message(f"打开目录失败: {e}", 'ERROR')
    def check_fonts(self):
        """检查字体"""
        try:
            # 检查字体文件是否存在
            font_files = ['fonts/FZShuSong-Z01S.ttf', 'fonts/FZKai-Z03S.ttf']
            missing_fonts = []
            
            for font_file in font_files:
                if not Path(font_file).exists():
                    missing_fonts.append(font_file)
            
            if missing_fonts:
                msg = f"缺少字体文件:\n" + "\n".join(missing_fonts)
                messagebox.showwarning("字体检查", msg)
            else:
                messagebox.showinfo("字体检查", "字体文件完整")
                
        except Exception as e:
            self.log_message(f"字体检查失败: {e}", 'ERROR')
    def show_perfect_help(self):
        """显示完美复刿模式帮助"""
        help_text = """完美复刿模式使用说明：

1. 选择或输入书籍ID（需要在books目录下存在对应文件夹）
2. 设置起始和结束文本序号
3. 设置测试页数（可选，0表示正常模式）
4. 选择是否压缩PDF和详细输出
5. 点击“生成PDF”开始生成

注意事项：
- 需要在books目录下放置书籍文件
- 需要在fonts目录下放置字体文件
- 生成的PDF会保存在对应的书籍目录中"""
        
        messagebox.showinfo("完美复刿模式帮助", help_text)
    def browse_novel_text_file(self):
        """浏览选择小说文本文件"""
        filename = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.novel_text_file_var.set(filename)
            self.log_message(f"已选择文本文件: {filename}")
    def browse_novel_book_cfg(self):
        """浏览选择书籍配置文件"""
        filename = filedialog.askopenfilename(
            title="选择书籍配置文件",
            filetypes=[("JSON files", "*.cfg"), ("All files", "*.*")]
        )
        if filename:
            self.novel_book_cfg_var.set(filename)
            self.log_message(f"已选择配置文件: {filename}")
    def browse_novel_cover_file(self):
        """浏览选择封面文件"""
        filename = filedialog.askopenfilename(
            title="选择封面文件",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        )
        if filename:
            self.novel_cover_file_var.set(filename)
            self.log_message(f"已选择封面文件: {filename}")
    def generate_novel_pdf(self):
        """生成小说章节模式PDF"""
        try:
            text_file = self.novel_text_file_var.get().strip()
            book_cfg = self.novel_book_cfg_var.get().strip()
            
            if not text_file:
                messagebox.showerror("错误", "请选择文本文件")
                return
                
            if not book_cfg:
                messagebox.showerror("错误", "请选择书籍配置文件")
                return
            
            if VRainPDFGenerator is None:
                messagebox.showerror("错误", "无法加载 vrainNovel.py 模块")
                return
            
            # 检查文件是否存在
            if not Path(text_file).exists():
                messagebox.showerror("错误", f"文本文件不存在: {text_file}")
                return
                
            if not Path(book_cfg).exists():
                messagebox.showerror("错误", f"配置文件不存在: {book_cfg}")
                return
            
            # 禁用按钮
            self.novel_generate_btn.configure(state='disabled')
            self.update_progress(0)
            self.status_var.set("正在生成PDF...")
            
            # 在新线程中生成PDF
            thread = threading.Thread(target=self._generate_novel_pdf_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            self.log_message(f"生成PDF失败: {e}")
            self.novel_generate_btn.configure(state='normal')
            self.status_var.set("就绪")
    def _generate_novel_pdf_thread(self):
        """在后台线程中生成小说PDF"""
        try:
            # 检查 VRainPDFGenerator 模块是否可用
            if VRainPDFGenerator is None:
                self.message_queue.put(('log', "错误：无法加载 vrainNovel.py 模块"))
                self.message_queue.put(('status', "模块加载失败"))
                return
            
            # 获取参数
            text_file = self.novel_text_file_var.get()
            book_cfg = self.novel_book_cfg_var.get()
            cover_file = self.novel_cover_file_var.get() if self.novel_cover_file_var.get() else None
            from_page = self.novel_from_page_var.get()
            to_page = self.novel_to_page_var.get() if self.novel_to_page_var.get() > 0 else None
            test_pages = self.novel_test_pages_var.get() if self.novel_test_pages_var.get() > 0 else None
            compress = self.novel_compress_var.get()
            verbose = self.novel_verbose_var.get()
            
            self.message_queue.put(('log', f"开始生成小说PDF: {Path(text_file).name}"))
            self.message_queue.put(('progress', 10))
            
            # 创建 VRainPDFGenerator 实例，使用正确的参数
            generator = VRainPDFGenerator(
                text_file=text_file,
                book_cfg_path=book_cfg,
                cover_path=cover_file,
                from_page=from_page,
                to_page=to_page,
                test_pages=test_pages,
                compress=compress,
                verbose=verbose
            )
            
            self.message_queue.put(('progress', 30))
            
            # 调用生成方法
            result = generator.generate_pdf(Path(text_file))
            
            self.message_queue.put(('progress', 100))
            self.message_queue.put(('log', f"小说PDF生成完成: {result}"))
            self.message_queue.put(('status', "生成完成"))
            
        except Exception as e:
            self.message_queue.put(('log', f"生成小说PDF错误: {e}"))
            self.message_queue.put(('status', "生成失败"))
        finally:
            self.message_queue.put(('enable_button', 'novel'))
    def validate_novel_config(self):
        """验证小说配置"""
        try:
            text_file = self.novel_text_file_var.get().strip()
            book_cfg = self.novel_book_cfg_var.get().strip()
            
            errors = []
            
            # 检查文本文件
            if not text_file:
                errors.append("未选择文本文件")
            elif not Path(text_file).exists():
                errors.append(f"文本文件不存在: {text_file}")
            
            # 检查配置文件
            if not book_cfg:
                errors.append("未选择书籍配置文件")
            elif not Path(book_cfg).exists():
                errors.append(f"配置文件不存在: {book_cfg}")
            else:
                # 验证JSON格式
                try:
                    with open(book_cfg, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    errors.append(f"配置文件JSON格式错误: {e}")
            
            # 检查封面文件（可选）
            cover_file = self.novel_cover_file_var.get().strip()
            if cover_file and not Path(cover_file).exists():
                errors.append(f"封面文件不存在: {cover_file}")
            
            if errors:
                messagebox.showerror("配置验证失败", "\n".join(errors))
            else:
                messagebox.showinfo("配置验证", "配置验证通过")
            
        except Exception as e:
            self.log_message(f"验证配置失败: {e}")
    def preview_chapters(self):
        """预览章节"""
        try:
            text_file = self.novel_text_file_var.get().strip()
            if not text_file or not Path(text_file).exists():
                messagebox.showerror("错误", "请选择有效的文本文件")
                return
            
            # 读取文本并检测章节
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的章节检测（可以根据实际需要修改）
            import re
            chapters = re.findall(r'第.*?章.*?\n', content)
            
            if chapters:
                preview_text = f"检测到 {len(chapters)} 个章节：\n\n"
                for i, chapter in enumerate(chapters[:10], 1):  # 只显示前10个
                    preview_text += f"{i}. {chapter.strip()}\n"
                
                if len(chapters) > 10:
                    preview_text += f"\n...还有 {len(chapters) - 10} 个章节"
            else:
                preview_text = "未检测到章节标题\n\n文本内容预览：\n" + content[:500] + "..."
            
            messagebox.showinfo("章节预览", preview_text)
            
        except Exception as e:
            self.log_message(f"预览章节失败: {e}")
    def load_novel_shenwu(self):
        """加载神武示例"""
        # 设置示例数据
        self.novel_text_file_var.set('examples/神武天帝.txt')
        self.novel_book_cfg_var.set('examples/books.cfg')
        self.novel_cover_file_var.set('')
        self.novel_from_page_var.set(1)
        self.novel_to_page_var.set(10)
        self.novel_test_pages_var.set(2)
        self.log_message("已加载神武示例配置")
    def manage_novel_config(self):
        """管理小说配置"""
        # 这里可以实现一个配置管理对话框
        messagebox.showinfo("配置管理", "配置管理功能暂未实现\n\n请手动编辑JSON配置文件")
    def show_novel_help(self):
        """显示小说章节模式帮助"""
        help_text = """小说章节模式使用说明：

1. 选择文本文件（.txt格式）
2. 选择书籍配置文件（.json格式）
3. 可选择封面文件（图片格式）
4. 设置页面范围和测试页数
5. 选择相关选项
6. 点击“生成PDF”开始生成

功能特点：
- 自动识别章节标题
- 支持自定义排版样式
- 支持封面自动生成
- 优化小说排版效果

注意事项：
- 文本文件应为UTF-8编码
- 配置文件应为有效的JSON格式
- 生成的PDF会保存在与文本文件相同的目录中"""
        
        messagebox.showinfo("小说章节模式帮助", help_text)
    def log_message(self, message, level='INFO'):
        """记录日志消息"""
        try:
            if hasattr(self, 'log_text'):
                import time
                timestamp = time.strftime('%H:%M:%S')
                
                # 根据日志级别添加图标
                level_icons = {
                    'INFO': '📝',
                    'SUCCESS': '✅',
                    'WARNING': '⚠️',
                    'ERROR': '❌',
                    'DEBUG': '🔍'
                }
                
                icon = level_icons.get(level, '📝')
                log_entry = f"[{timestamp}] {icon} {message}\n"
                
                self.log_text.insert(tk.END, log_entry)
                self.log_text.see(tk.END)
                print(f"LOG: {message}")  # 也输出到控制台
        except Exception as e:
            print(f"日志记录失败: {e}")
    def update_progress(self, progress):
        """更新进度条"""
        try:
            self.progress_var.set(progress)
            self.root.update_idletasks()
        except Exception as e:
            print(f"更新进度失败: {e}")
    def clear_log(self):
        """清空日志"""
        try:
            self.log_text.delete(1.0, tk.END)
            self.log_message("日志已清空")
        except Exception as e:
            print(f"清空日志失败: {e}")
    def save_log(self):
        """保存日志"""
        try:
            filename = filedialog.asksaveasfilename(
                title="保存日志",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                log_content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                self.log_message(f"日志已保存到: {filename}")
        except Exception as e:
            self.log_message(f"保存日志失败: {e}")
    def open_results_dir(self):
        """打开结果目录"""
        try:
            # 首先尝试打开当前工作目录
            current_dir = Path.cwd()
            os.startfile(str(current_dir))
            self.log_message(f"已打开结果目录: {current_dir}")
        except Exception as e:
            self.log_message(f"打开结果目录失败: {e}")
    def process_messages(self):
        """处理消息队列中的消息"""
        try:
            while True:
                try:
                    message_type, message_data = self.message_queue.get_nowait()
                    
                    if message_type == 'log':
                        self.log_message(message_data)
                    elif message_type == 'progress':
                        self.update_progress(message_data)
                    elif message_type == 'status':
                        self.status_var.set(message_data)
                    elif message_type == 'enable_button':
                        if message_data == 'perfect':
                            self.perfect_generate_btn.configure(state='normal')
                        elif message_data == 'novel':
                            self.novel_generate_btn.configure(state='normal')
                    
                except queue.Empty:
                    break
                    
        except Exception as e:
            print(f"处理消息失败: {e}")
        
        # 每100毫秒检查一次消息队列
        self.root.after(100, self.process_messages)


def main():
    """主函数"""
    root = tk.Tk()
    app = VRainDualGUI(root)
    
    # 欢迎信息
    app.log_message(f"🎆 欢迎使用古籍刻本电子书制作工具 {VERSION}", 'SUCCESS')
    app.log_message("请选择工作模式：")
    app.log_message("- 传统古籍模式：使用书籍ID，传统古籍原版功能")
    app.log_message("- 小说章节模式：直接选择文件，支持章节识别")
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("用户中断操作")
    except Exception as e:
        print(f"程序出错: {e}")


if __name__ == '__main__':
    main()