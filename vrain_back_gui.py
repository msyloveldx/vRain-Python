#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vRain中文古籍刻本风格直排电子书制作工具 - GUI版本（基于vrain_back.py）
Python版本 by msyloveldx, 2025/08
原作者: shanleiguang
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import queue

# 导入vrain_back.py中的类
from vrain_back import VRainPDFGenerator, FontChecker, ChineseConverter

# 全局变量
SOFTWARE = 'vRain'
VERSION = 'v1.4-GUI-Back'

class VRainBackGUI:
    """vRain Back GUI主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{SOFTWARE} {VERSION} - 古籍刻本电子书制作工具（书籍ID模式）")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap("cover.png")
        except:
            pass
        
        # 创建消息队列用于线程间通信
        self.message_queue = queue.Queue()
        
        # 初始化变量
        self.book_id_var = tk.StringVar()
        self.from_text_var = tk.IntVar(value=1)
        self.to_text_var = tk.IntVar(value=1)
        self.test_pages_var = tk.IntVar()
        self.compress_var = tk.BooleanVar(value=False)
        self.verbose_var = tk.BooleanVar(value=True)
        
        # 书籍列表
        self.books_list = []
        self.load_books_list()
        
        # 创建界面
        self.create_widgets()
        
        # 启动消息处理
        self.process_messages()
    
    def load_books_list(self):
        """加载books目录下的书籍列表"""
        books_dir = Path("books")
        if books_dir.exists():
            for book_dir in books_dir.iterdir():
                if book_dir.is_dir() and book_dir.name.isdigit():
                    self.books_list.append(book_dir.name)
        self.books_list.sort()
    
    def create_widgets(self):
        """创建GUI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text=f"{SOFTWARE} {VERSION}", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 书籍选择区域
        self.create_book_selection_frame(main_frame)
        
        # 参数配置区域
        self.create_parameter_frame(main_frame)
        
        # 选项区域
        self.create_options_frame(main_frame)
        
        # 控制按钮区域
        self.create_control_frame(main_frame)
        
        # 书籍信息区域
        self.create_book_info_frame(main_frame)
        
        # 日志输出区域
        self.create_log_frame(main_frame)
        
        # 状态栏
        self.create_status_bar(main_frame)
    
    def create_book_selection_frame(self, parent):
        """创建书籍选择区域"""
        # 书籍选择框架
        book_frame = ttk.LabelFrame(parent, text="书籍选择", padding="10")
        book_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        book_frame.columnconfigure(1, weight=1)
        
        # 书籍ID选择
        ttk.Label(book_frame, text="书籍ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # 创建下拉框
        self.book_combo = ttk.Combobox(book_frame, textvariable=self.book_id_var, 
                                      values=self.books_list, width=20, state="readonly")
        self.book_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 5), pady=2)
        self.book_combo.bind('<<ComboboxSelected>>', self.on_book_selected)
        
        # 刷新按钮
        ttk.Button(book_frame, text="刷新书籍列表", command=self.refresh_books_list).grid(row=0, column=2, pady=2)
        
        # 快速选择按钮
        quick_frame = ttk.Frame(book_frame)
        quick_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        ttk.Button(quick_frame, text="史记(01)", command=lambda: self.select_book("01")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(quick_frame, text="碧血剑(02)", command=lambda: self.select_book("02")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(quick_frame, text="庄子(03)", command=lambda: self.select_book("03")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(quick_frame, text="神武天帝(04)", command=lambda: self.select_book("04")).pack(side=tk.LEFT)
    
    def create_parameter_frame(self, parent):
        """创建参数配置区域"""
        # 参数框架
        param_frame = ttk.LabelFrame(parent, text="文本参数", padding="10")
        param_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        param_frame.columnconfigure(1, weight=1)
        
        # 起始文本
        ttk.Label(param_frame, text="起始文本:").grid(row=0, column=0, sticky=tk.W, pady=2)
        from_spinbox = ttk.Spinbox(param_frame, from_=1, to=999, textvariable=self.from_text_var, width=10)
        from_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 结束文本
        ttk.Label(param_frame, text="结束文本:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        to_spinbox = ttk.Spinbox(param_frame, from_=1, to=999, textvariable=self.to_text_var, width=10)
        to_spinbox.grid(row=0, column=3, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 测试页数
        ttk.Label(param_frame, text="测试页数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        test_spinbox = ttk.Spinbox(param_frame, from_=0, to=999, textvariable=self.test_pages_var, width=10)
        test_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Label(param_frame, text="(0表示正常模式)").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=2)
    
    def create_options_frame(self, parent):
        """创建选项区域"""
        # 选项框架
        options_frame = ttk.LabelFrame(parent, text="选项", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 复选框
        ttk.Checkbutton(options_frame, text="压缩PDF", variable=self.compress_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="详细输出", variable=self.verbose_var).pack(anchor=tk.W)
    
    def create_control_frame(self, parent):
        """创建控制按钮区域"""
        # 控制框架
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        # 按钮
        self.generate_btn = ttk.Button(control_frame, text="生成PDF", command=self.generate_pdf)
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="打开结果目录", command=self.open_results_dir).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="打开books目录", command=self.open_books_dir).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="帮助", command=self.show_help).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT)
    
    def create_book_info_frame(self, parent):
        """创建书籍信息显示区域"""
        # 书籍信息框架
        info_frame = ttk.LabelFrame(parent, text="书籍信息", padding="10")
        info_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        # 书籍信息标签
        self.book_title_label = ttk.Label(info_frame, text="标题: 未选择书籍")
        self.book_title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.book_author_label = ttk.Label(info_frame, text="作者: -")
        self.book_author_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.book_canvas_label = ttk.Label(info_frame, text="背景: -")
        self.book_canvas_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.book_text_count_label = ttk.Label(info_frame, text="文本文件数: -")
        self.book_text_count_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
    
    def create_log_frame(self, parent):
        """创建日志输出区域"""
        # 日志框架
        log_frame = ttk.LabelFrame(parent, text="处理日志", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(6, weight=1)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E))
    
    def on_book_selected(self, event=None):
        """书籍选择事件处理"""
        book_id = self.book_id_var.get()
        if book_id:
            self.load_book_info(book_id)
    
    def select_book(self, book_id):
        """选择指定书籍"""
        self.book_id_var.set(book_id)
        self.load_book_info(book_id)
    
    def load_book_info(self, book_id):
        """加载书籍信息"""
        book_dir = Path(f"books/{book_id}")
        book_cfg_path = book_dir / "book.cfg"
        
        if book_cfg_path.exists():
            try:
                # 读取配置文件
                config = {}
                with open(book_cfg_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
                
                # 更新显示
                title = config.get('title', '未知')
                author = config.get('author', '未知')
                canvas_id = config.get('canvas_id', '未知')
                
                self.book_title_label.config(text=f"标题: {title}")
                self.book_author_label.config(text=f"作者: {author}")
                self.book_canvas_label.config(text=f"背景: {canvas_id}")
                
                # 统计文本文件数量
                text_dir = book_dir / "text"
                if text_dir.exists():
                    txt_files = list(text_dir.glob("*.txt"))
                    self.book_text_count_label.config(text=f"文本文件数: {len(txt_files)}")
                else:
                    self.book_text_count_label.config(text="文本文件数: 0")
                
                self.log_message(f"已加载书籍信息: {title} - {author}")
                
            except Exception as e:
                self.log_message(f"加载书籍信息失败: {e}")
        else:
            self.book_title_label.config(text="标题: 配置文件不存在")
            self.book_author_label.config(text="作者: -")
            self.book_canvas_label.config(text="背景: -")
            self.book_text_count_label.config(text="文本文件数: -")
    
    def refresh_books_list(self):
        """刷新书籍列表"""
        self.books_list.clear()
        self.load_books_list()
        self.book_combo['values'] = self.books_list
        self.log_message(f"已刷新书籍列表，共找到 {len(self.books_list)} 本书籍")
    
    def generate_pdf(self):
        """生成PDF文件"""
        # 验证输入
        book_id = self.book_id_var.get()
        if not book_id:
            messagebox.showerror("错误", "请选择书籍ID")
            return
        
        from_text = self.from_text_var.get()
        to_text = self.to_text_var.get()
        
        if from_text > to_text:
            messagebox.showerror("错误", "起始文本不能大于结束文本")
            return
        
        # 禁用生成按钮
        self.generate_btn.config(state='disabled')
        self.status_var.set("正在生成PDF...")
        
        # 在新线程中生成PDF
        thread = threading.Thread(target=self._generate_pdf_thread, 
                                args=(book_id, from_text, to_text))
        thread.daemon = True
        thread.start()
    
    def _generate_pdf_thread(self, book_id, from_text, to_text):
        """在后台线程中生成PDF"""
        try:
            # 创建生成器
            generator = VRainPDFGenerator(
                book_id=book_id,
                from_text=from_text,
                to_text=to_text,
                test_pages=self.test_pages_var.get() if self.test_pages_var.get() > 0 else None,
                compress=self.compress_var.get(),
                verbose=self.verbose_var.get()
            )
            
            # 设置日志回调
            generator.log_callback = self.log_message
            
            # 生成PDF
            generator.generate_pdf()
            
            # 发送完成消息
            self.message_queue.put(("success", "PDF生成完成！"))
            
        except Exception as e:
            # 发送错误消息
            self.message_queue.put(("error", f"生成PDF时出错: {e}"))
    
    def log_message(self, message):
        """添加日志消息"""
        self.message_queue.put(("log", message))
    
    def process_messages(self):
        """处理消息队列"""
        try:
            while True:
                msg_type, message = self.message_queue.get_nowait()
                
                if msg_type == "log":
                    # 添加日志
                    self.log_text.insert(tk.END, message + "\n")
                    self.log_text.see(tk.END)
                elif msg_type == "success":
                    # 成功消息
                    self.log_text.insert(tk.END, f"✓ {message}\n")
                    self.log_text.see(tk.END)
                    self.status_var.set("PDF生成完成")
                    self.generate_btn.config(state='normal')
                    messagebox.showinfo("成功", message)
                elif msg_type == "error":
                    # 错误消息
                    self.log_text.insert(tk.END, f"✗ {message}\n")
                    self.log_text.see(tk.END)
                    self.status_var.set("生成失败")
                    self.generate_btn.config(state='normal')
                    messagebox.showerror("错误", message)
                    
        except queue.Empty:
            pass
        
        # 继续处理消息
        self.root.after(100, self.process_messages)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def open_results_dir(self):
        """打开结果目录"""
        results_dir = Path("results")
        if results_dir.exists():
            if sys.platform == "win32":
                os.startfile(str(results_dir))
            elif sys.platform == "darwin":
                os.system(f"open {results_dir}")
            else:
                os.system(f"xdg-open {results_dir}")
        else:
            messagebox.showinfo("信息", "results目录不存在")
    
    def open_books_dir(self):
        """打开books目录"""
        books_dir = Path("books")
        if books_dir.exists():
            if sys.platform == "win32":
                os.startfile(str(books_dir))
            elif sys.platform == "darwin":
                os.system(f"open {books_dir}")
            else:
                os.system(f"xdg-open {books_dir}")
        else:
            messagebox.showinfo("信息", "books目录不存在")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = f"""
{SOFTWARE} {VERSION} 使用说明

1. 书籍选择
   - 从下拉列表中选择书籍ID
   - 或点击快速选择按钮

2. 文本参数
   - 起始文本：从第几个文本文件开始
   - 结束文本：到第几个文本文件结束
   - 测试页数：测试模式，只生成指定页数

3. 选项
   - 压缩PDF：生成后自动压缩（需要Ghostscript）
   - 详细输出：显示详细处理信息

4. 操作
   - 生成PDF：开始生成PDF文件
   - 清空日志：清空日志显示
   - 打开目录：打开结果或books目录

注意事项：
- 确保books目录下有相应的书籍文件夹
- 文本文件应放在books/ID/text/目录下
- 配置文件为books/ID/book.cfg
        """
        messagebox.showinfo("帮助", help_text)

def main():
    """主函数"""
    root = tk.Tk()
    app = VRainBackGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
