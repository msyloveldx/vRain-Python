#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vRain中文古籍刻本风格直排电子书制作工具 - GUI版本
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

# 导入原有的vrain.py中的类
from vrain import VRainPDFGenerator, FontChecker, ChineseConverter

# 全局变量
SOFTWARE = 'vRain'
VERSION = 'v1.4-GUI'

class VRainGUI:
    """vRain GUI主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{SOFTWARE} {VERSION} - 古籍刻本电子书制作工具")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap("cover.png")
        except:
            pass
        
        # 创建消息队列用于线程间通信
        self.message_queue = queue.Queue()
        
        # 初始化变量
        self.text_file_var = tk.StringVar()
        self.book_cfg_var = tk.StringVar()
        self.cover_file_var = tk.StringVar()
        self.from_page_var = tk.IntVar(value=1)
        self.to_page_var = tk.IntVar()
        self.test_pages_var = tk.IntVar()
        self.compress_var = tk.BooleanVar(value=False)
        self.verbose_var = tk.BooleanVar(value=True)
        
        # 创建界面
        self.create_widgets()
        
        # 启动消息处理
        self.process_messages()
    
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
        
        # 文件选择区域
        self.create_file_selection_frame(main_frame)
        
        # 参数配置区域
        self.create_parameter_frame(main_frame)
        
        # 选项区域
        self.create_options_frame(main_frame)
        
        # 控制按钮区域
        self.create_control_frame(main_frame)
        
        # 配置管理区域
        self.create_config_frame(main_frame)
        
        # 日志输出区域
        self.create_log_frame(main_frame)
        
        # 状态栏
        self.create_status_bar(main_frame)
    
    def create_config_frame(self, parent):
        """创建配置管理区域"""
        # 配置框架
        config_frame = ttk.LabelFrame(parent, text="配置管理", padding="10")
        config_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 配置按钮
        ttk.Button(config_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(config_frame, text="加载配置", command=self.load_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(config_frame, text="重置配置", command=self.reset_config).pack(side=tk.LEFT)
    
    def create_file_selection_frame(self, parent):
        """创建文件选择区域"""
        # 文件选择框架
        file_frame = ttk.LabelFrame(parent, text="文件选择", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # 文本文件选择
        ttk.Label(file_frame, text="文本文件:").grid(row=0, column=0, sticky=tk.W, pady=2)
        text_entry = ttk.Entry(file_frame, textvariable=self.text_file_var, width=50)
        text_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="浏览", command=self.browse_text_file).grid(row=0, column=2, pady=2)
        
        # 书籍配置文件选择
        ttk.Label(file_frame, text="书籍配置:").grid(row=1, column=0, sticky=tk.W, pady=2)
        book_entry = ttk.Entry(file_frame, textvariable=self.book_cfg_var, width=50)
        book_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="浏览", command=self.browse_book_cfg).grid(row=1, column=2, pady=2)
        
        # 封面文件选择（可选）
        ttk.Label(file_frame, text="封面文件:").grid(row=2, column=0, sticky=tk.W, pady=2)
        cover_entry = ttk.Entry(file_frame, textvariable=self.cover_file_var, width=50)
        cover_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="浏览", command=self.browse_cover_file).grid(row=2, column=2, pady=2)
        ttk.Label(file_frame, text="(可选，留空将创建简易封面)").grid(row=2, column=3, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 快速选择按钮
        quick_frame = ttk.Frame(file_frame)
        quick_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        ttk.Button(quick_frame, text="史记示例", command=self.load_shiji_example).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(quick_frame, text="神武天帝示例", command=self.load_shenwu_example).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(quick_frame, text="庄子示例", command=self.load_zhuangzi_example).pack(side=tk.LEFT)
    
    def create_parameter_frame(self, parent):
        """创建参数配置区域"""
        # 参数框架
        param_frame = ttk.LabelFrame(parent, text="页面参数", padding="10")
        param_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        param_frame.columnconfigure(1, weight=1)
        
        # 起始页
        ttk.Label(param_frame, text="起始页:").grid(row=0, column=0, sticky=tk.W, pady=2)
        from_spinbox = ttk.Spinbox(param_frame, from_=1, to=9999, textvariable=self.from_page_var, width=10)
        from_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 结束页
        ttk.Label(param_frame, text="结束页:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        to_spinbox = ttk.Spinbox(param_frame, from_=0, to=9999, textvariable=self.to_page_var, width=10)
        to_spinbox.grid(row=0, column=3, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Label(param_frame, text="(0表示输出全部)").grid(row=0, column=4, sticky=tk.W, padx=(5, 0), pady=2)
        
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
        control_frame.grid(row=5, column=0, columnspan=3, pady=(0, 10))
        
        # 按钮
        self.generate_btn = ttk.Button(control_frame, text="生成PDF", command=self.generate_pdf)
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="打开结果目录", command=self.open_results_dir).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="帮助", command=self.show_help).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT)
    
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
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(log_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E))
    
    def browse_text_file(self):
        """浏览文本文件"""
        filename = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.text_file_var.set(filename)
    
    def browse_book_cfg(self):
        """浏览书籍配置文件"""
        filename = filedialog.askopenfilename(
            title="选择书籍配置文件",
            filetypes=[("配置文件", "*.cfg"), ("所有文件", "*.*")]
        )
        if filename:
            self.book_cfg_var.set(filename)
    
    def browse_cover_file(self):
        """浏览封面文件"""
        filename = filedialog.askopenfilename(
            title="选择封面文件",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png"), ("所有文件", "*.*")]
        )
        if filename:
            self.cover_file_var.set(filename)
    
    def load_shiji_example(self):
        """加载史记示例"""
        self.text_file_var.set("books/01/text/000.txt")
        self.book_cfg_var.set("books/01/book.cfg")
        self.cover_file_var.set("books/01/cover.jpg")
        self.log_message("已加载史记示例配置")
    
    def load_shenwu_example(self):
        """加载神武天帝示例"""
        self.text_file_var.set("books/04/text/神武天帝.txt")
        self.book_cfg_var.set("books/04/book.cfg")
        self.cover_file_var.set("books/04/cover.jpg")
        self.log_message("已加载神武天帝示例配置")
    
    def load_zhuangzi_example(self):
        """加载庄子示例"""
        self.text_file_var.set("books/03/text/01.txt")
        self.book_cfg_var.set("books/03/book.cfg")
        self.cover_file_var.set("books/03/cover.jpg")
        self.log_message("已加载庄子示例配置")
    
    def validate_inputs(self):
        """验证输入参数"""
        if not self.text_file_var.get():
            messagebox.showerror("错误", "请选择文本文件")
            return False
        
        if not self.book_cfg_var.get():
            messagebox.showerror("错误", "请选择书籍配置文件")
            return False
        
        # 检查文件是否存在
        text_file = Path(self.text_file_var.get())
        book_cfg = Path(self.book_cfg_var.get())
        
        if not text_file.exists():
            messagebox.showerror("错误", f"文本文件不存在: {text_file}")
            return False
        
        if not book_cfg.exists():
            messagebox.showerror("错误", f"书籍配置文件不存在: {book_cfg}")
            return False
        
        # 封面文件是可选的，如果提供了就检查是否存在
        if self.cover_file_var.get():
            cover_file = Path(self.cover_file_var.get())
            if not cover_file.exists():
                messagebox.showerror("错误", f"封面文件不存在: {cover_file}")
                return False
        
        return True
    
    def generate_pdf(self):
        """生成PDF文件"""
        if not self.validate_inputs():
            return
        
        # 禁用生成按钮
        self.generate_btn.config(state='disabled')
        self.status_var.set("正在生成PDF...")
        self.progress_var.set(0)
        
        # 在新线程中运行PDF生成
        thread = threading.Thread(target=self._generate_pdf_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_pdf_thread(self):
        """PDF生成线程"""
        try:
            # 准备参数
            text_file = Path(self.text_file_var.get())
            book_cfg_path = Path(self.book_cfg_var.get())
            
            # 处理封面文件（可选）
            cover_path = None
            if self.cover_file_var.get():
                cover_path = Path(self.cover_file_var.get())
                if not cover_path.exists():
                    self.log_message("警告：封面文件不存在，将创建简易封面")
                    cover_path = None
            
            from_page = self.from_page_var.get()
            to_page = self.to_page_var.get() if self.to_page_var.get() > 0 else None
            test_pages = self.test_pages_var.get() if self.test_pages_var.get() > 0 else None
            compress = self.compress_var.get()
            verbose = self.verbose_var.get()
            
            # 创建生成器
            generator = VRainPDFGenerator(
                text_file=text_file,
                book_cfg_path=book_cfg_path,
                cover_path=cover_path,
                from_page=from_page,
                to_page=to_page,
                test_pages=test_pages,
                compress=compress,
                verbose=verbose,
                progress_callback=self.update_progress,
                log_callback=self.log_message
            )
            
            # 生成PDF
            generator.generate_pdf(text_file)
            
            # 完成
            self.message_queue.put(("complete", "PDF生成完成！"))
            
        except Exception as e:
            self.message_queue.put(("error", f"生成PDF时出错: {str(e)}"))
    

    
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, progress: float):
        """更新进度条"""
        self.progress_var.set(progress)
        self.root.update_idletasks()
    
    def save_config(self):
        """保存配置到文件"""
        import json
        
        config = {
            'text_file': self.text_file_var.get(),
            'book_cfg': self.book_cfg_var.get(),
            'cover_file': self.cover_file_var.get(),
            'from_page': self.from_page_var.get(),
            'to_page': self.to_page_var.get(),
            'test_pages': self.test_pages_var.get(),
            'compress': self.compress_var.get(),
            'verbose': self.verbose_var.get()
        }
        
        filename = filedialog.asksaveasfilename(
            title="保存配置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                self.log_message(f"配置已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def load_config(self):
        """从文件加载配置"""
        import json
        
        filename = filedialog.askopenfilename(
            title="加载配置",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.text_file_var.set(config.get('text_file', ''))
                self.book_cfg_var.set(config.get('book_cfg', ''))
                self.cover_file_var.set(config.get('cover_file', ''))
                self.from_page_var.set(config.get('from_page', 1))
                self.to_page_var.set(config.get('to_page', 0))
                self.test_pages_var.set(config.get('test_pages', 0))
                self.compress_var.set(config.get('compress', False))
                self.verbose_var.set(config.get('verbose', True))
                
                self.log_message(f"配置已从 {filename} 加载")
            except Exception as e:
                messagebox.showerror("错误", f"加载配置失败: {e}")
    
    def reset_config(self):
        """重置配置为默认值"""
        if messagebox.askyesno("确认", "确定要重置所有配置吗？"):
            self.text_file_var.set("")
            self.book_cfg_var.set("")
            self.cover_file_var.set("")
            self.from_page_var.set(1)
            self.to_page_var.set(0)
            self.test_pages_var.set(0)
            self.compress_var.set(False)
            self.verbose_var.set(True)
            self.log_message("配置已重置为默认值")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = f"""
vRain GUI {VERSION} 使用帮助

基本使用：
1. 选择文本文件和配置文件（必需）
2. 选择封面文件（可选，留空将创建简易封面）
3. 设置页面参数（可选）
4. 选择需要的选项
5. 点击"生成PDF"按钮

快速开始：
- 点击"史记示例"等按钮快速加载示例配置
- 使用"保存配置"和"加载配置"保存常用设置

文件要求：
- 文本文件：UTF-8编码的.txt文件（必需）
- 配置文件：.cfg格式的书籍配置（必需）
- 封面文件：.jpg或.png格式的图片（可选）

注意事项：
- 确保所有文件路径正确
- 检查fonts目录中的字体文件
- 建议勾选"压缩PDF"选项
- 封面文件可选，程序会自动创建简易封面

更多信息请参考 README_GUI.md 文件
        """
        messagebox.showinfo("帮助", help_text)
    
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
            messagebox.showinfo("提示", "结果目录不存在")
    
    def process_messages(self):
        """处理消息队列"""
        try:
            while True:
                msg_type, message = self.message_queue.get_nowait()
                
                if msg_type == "complete":
                    self.log_message(f"✓ {message}")
                    self.status_var.set("完成")
                    self.progress_var.set(100)
                    self.generate_btn.config(state='normal')
                    messagebox.showinfo("完成", message)
                    
                elif msg_type == "error":
                    self.log_message(f"✗ {message}")
                    self.status_var.set("错误")
                    self.generate_btn.config(state='normal')
                    messagebox.showerror("错误", message)
                    
                elif msg_type == "progress":
                    self.progress_var.set(message)
                    
                elif msg_type == "log":
                    self.log_message(message)
                    
        except queue.Empty:
            pass
        
        # 继续处理消息
        self.root.after(100, self.process_messages)

def main():
    """主函数"""
    root = tk.Tk()
    app = VRainGUI(root)
    
    # 设置窗口图标
    try:
        root.iconbitmap("cover.png")
    except:
        pass
    
    # 启动GUI
    root.mainloop()

if __name__ == '__main__':
    main()
    