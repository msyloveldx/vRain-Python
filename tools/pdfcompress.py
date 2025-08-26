#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
压缩某一目录下的文件名不是以'_已压缩'结尾的PDF文件
Python版本 by msyloveldx, 2025/08
原作者: shanleiguang, 2025.4
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def compress_pdf(input_path: Path, output_path: Path) -> bool:
    """使用Ghostscript压缩PDF文件"""
    try:
        cmd = [
            'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
            '-dPDFSETTINGS=/screen', '-dNOPAUSE', '-dQUIET', '-dBATCH',
            f'-sOutputFile={output_path}', str(input_path)
        ]
        
        subprocess.run(cmd, check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"压缩失败: {e}")
        return False
    except FileNotFoundError:
        print("错误：未找到Ghostscript，请先安装Ghostscript")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量压缩PDF文件')
    parser.add_argument('-d', '--directory', required=True, 
                       help='目标目录路径')
    
    args = parser.parse_args()
    
    # 检查目录是否存在
    target_dir = Path(args.directory)
    if not target_dir.exists() or not target_dir.is_dir():
        print("错误：未定义'-d'目标目录或目标目录不存在！")
        sys.exit(1)
    
    # 查找所有需要压缩的PDF文件
    pdf_files = []
    for file_path in target_dir.glob("*.pdf"):
        if not file_path.name.endswith("_已压缩.pdf"):
            pdf_files.append(file_path)
    
    if not pdf_files:
        print("未找到需要压缩的PDF文件")
        return
    
    print(f"找到 {len(pdf_files)} 个PDF文件需要压缩")
    
    # 压缩每个PDF文件
    for pdf_file in pdf_files:
        stem = pdf_file.stem
        output_file = pdf_file.parent / f"{stem}_已压缩.pdf"
        
        print(f"压缩PDF文件'{output_file.name}'...", end='')
        
        if compress_pdf(pdf_file, output_file):
            # 删除原文件
            try:
                pdf_file.unlink()
                print("完成！")
            except Exception as e:
                print(f"警告：无法删除原文件 {pdf_file}: {e}")
        else:
            print("失败！")

if __name__ == '__main__':
    main()
