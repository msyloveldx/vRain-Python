# vRain Python版本使用指南
![cover.png](cover.png)
## 项目简介

vRain是一款中文古籍刻本风格直排电子书制作工具的Python版本。本版本完整转换了原Perl版本的功能，提供了更好的跨平台兼容性和更简单的安装部署方式。

## 主要特性

- 🔄 **完整功能移植**: 保持了Perl原版的所有核心功能
- 🐍 **Python实现**: 使用现代Python技术栈重新开发
- 📱 **跨平台支持**: 支持Windows、macOS、Linux
- 📦 **简化部署**: 通过pip即可安装所有依赖
- 🎨 **古籍风格**: 完美复刻古籍刻本的视觉效果
- 📖 **章节模式**: 支持小说章节排版，章节标题在第一列，内容从第二列开始
- 🔄 **双模式支持**: 章节模式和连续模式，适应不同类型的文本排版需求

## 系统要求

- Python 3.8 或更高版本
- 操作系统: Windows 10+、macOS 10.14+、Ubuntu 18.04+ 或其他Linux发行版

## 安装步骤

### 1. 克隆项目
```bash
git clone https://github.com/msyloveldx/vRain-Python.git
cd vRain-Python
```

### 2. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 3. 安装可选依赖（PDF压缩功能）

#### Windows
1. 下载并安装 [Ghostscript](https://www.ghostscript.com/download/gsdnld.html)
2. 确保`gs`命令在系统PATH中

#### macOS
```bash
brew install ghostscript
```

#### Ubuntu/Debian
```bash
sudo apt-get install ghostscript
```

#### CentOS/RHEL
```bash
sudo yum install ghostscript
```

## 使用方法

### 主程序vrain.py - 生成古籍电子书

#### 基本用法
```bash
# 生成全部内容
python vrain.py

# 生成指定页数范围
python vrain.py -f 起始页 -t 结束页

# 从指定页开始生成全部内容
python vrain.py -f 起始页

# 测试模式（仅生成前5页）
python vrain.py -z 5

# 生成并压缩PDF
python vrain.py -c

# 显示详细信息
python vrain.py -v
```

#### 章节模式（小说排版）
vrain.py支持两种排版模式：

1. **章节模式**：适合小说等有明确章节结构的文本
   - 章节标题显示在第一列（红色，大字号）
   - 章节内容从第二列开始排版
   - 每章结束后自动换页开始新章节
   - 在`book.cfg`中设置`enable_chapter_mode=1`启用
   - ![小说模式.png](images/%E5%B0%8F%E8%AF%B4%E6%A8%A1%E5%BC%8F.png)

2. **连续模式**：适合古籍等传统文本的连续排版
   - 文本连续排版，无章节分隔
   - 在`book.cfg`中设置`enable_chapter_mode=0`或未设置
   - ![连续模式.png](images/%E8%BF%9E%E7%BB%AD%E6%A8%A1%E5%BC%8F.png)

#### 使用示例

**史记古籍（连续模式）**：
```python
text_file = Path('books/01/text/000.txt')
book_cfg_path = Path('books/01/book.cfg')  # enable_chapter_mode=0
generator = VRainPDFGenerator(text_file, book_cfg_path, cover_path)
```

**神武天帝小说（章节模式）**：
```python
text_file = Path('books/04/text/神武天帝.txt')
book_cfg_path = Path('books/04/book.cfg')  # enable_chapter_mode=1
generator = VRainPDFGenerator(text_file, book_cfg_path, cover_path)
```

#### 章节模式配置示例

**book.cfg（章节模式）**：
```ini
title=神武天帝
author=网络小说
canvas_id=01_Black
row_num=30
enable_chapter_mode=1  # 启用章节模式

# 字体配置
font1=XiaolaiMonoSC-Regular.ttf
font2=HanaMinA.ttf
font3=HanaMinB.ttf

# 章节标题样式
text_font1_size=42
text_font_color=#000000
```

**文本格式要求**：
- 章节标题格式：`第X章 章节名`
- 章节标题和内容之间可以有换行
- 支持多个章节连续排列

### 工具脚本

#### 1. 背景图生成
```bash
cd canvas
python canvas.py -c 01_Black
```

#### 2. 字体支持检查
```bash
cd books/01  # 进入书籍目录
python ../../tools/fontcheck.py -f 1 -t 1
```

#### 3. 字符替换
```bash
cd books/01  # 进入书籍目录
python ../../tools/chareplace.py -b 01 -f 1 -t 1
```

#### 4. PDF批量压缩
```bash
python tools/pdfcompress.py -d ./pdf
```

#### 5. PDF插图
```bash
cd books/01  # 进入书籍目录
python ../../tools/insertimg.py -i 《史记》文本1至3
```

#### 6. 文本缩进处理
```bash
cd books/01  # 进入书籍目录
python indentxt.py -f 1 -t 3
```

#### 7. 印章添加
```bash
cd books/01  # 进入书籍目录
python addyins.py
```

## 项目结构

```
vRain/
├── vrain.py                 # 主程序（支持章节模式）
├── vrain_back.py            # 原Perl版本模式
├── requirements.txt         # Python依赖
├── README.md               # 项目说明
├── books/                  # 书籍目录
│   ├── 01/                # 书籍01（史记-连续模式）
│   │   ├── book.cfg       # 书籍配置
│   │   ├── text/          # 文本文件
│   │   ├── indentxt.py    # 缩进处理脚本
│   │   └── addyins.py     # 印章添加脚本
│   ├── 04/                # 书籍04（神武天帝-章节模式）
│   │   ├── book.cfg       # 书籍配置（enable_chapter_mode=1）
│   │   └── text/          # 文本文件
│   └── ...
├── canvas/                 # 背景图
│   ├── canvas.py          # 背景图生成脚本
│   ├── *.cfg              # 背景图配置
│   └── *.jpg              # 背景图文件
├── tools/                  # 工具脚本
│   ├── pdfcompress.py     # PDF压缩
│   ├── insertimg.py       # 插图工具
│   ├── fontcheck.py       # 字体检查
│   └── chareplace.py      # 字符替换
├── fonts/                  # 字体文件
├── db/                    # 数据文件
└── results/               # 输出PDF目录
```

## 配置文件说明

### 书籍配置文件 (book.cfg)

主要配置项：
- `title`: 书籍标题
- `author`: 作者
- `canvas_id`: 背景图ID
- `font1-5`: 字体文件名
- `row_num`: 每列字数
- `enable_chapter_mode`: 章节模式开关（1=启用，0=禁用）
- 各种排版参数...

### 背景图配置文件 (canvas/*.cfg)

主要配置项：
- `canvas_width/height`: 画布尺寸
- `margins_*`: 页边距
- `leaf_col`: 列数
- 鱼尾、框线等装饰参数...

## 常见问题

### Q: 如何添加新的字体？
A: 将TTF字体文件放入`fonts/`目录，然后在`book.cfg`中配置`font1-5`参数。

### Q: 如何自定义背景图样式？
A: 复制现有的`.cfg`文件，修改参数后使用`canvas.py`生成新的背景图。

### Q: PDF压缩失败怎么办？
A: 确保已正确安装Ghostscript，并且`gs`命令在系统PATH中可用。

### Q: 字体显示异常怎么办？
A: 使用`fontcheck.py`检查字体支持情况，根据生成的`replace.tmp`文件编辑`replace.txt`进行字符替换。

### Q: 如何启用章节模式？
A: 在`book.cfg`中设置`enable_chapter_mode=1`，确保文本文件包含"第X章 标题"格式的章节标题。

### Q: 章节内容不显示怎么办？
A: 检查章节标题格式是否正确，确保文本文件编码为UTF-8，章节标题和内容之间没有特殊字符干扰。

## 性能优化建议

1. **大文件处理**: 对于超大文本，建议分批处理
2. **内存使用**: 处理大量图片时注意内存占用
3. **字体缓存**: 频繁使用的字体会自动缓存以提升性能

## 版本差异

### Python版本优势
- 更好的跨平台兼容性
- 简化的依赖管理
- 更现代的代码结构
- 更好的错误处理
- 新增章节模式支持
- 更灵活的页数控制

### 与Perl版本的兼容性
- 配置文件格式完全兼容
- 输出PDF效果一致
- 支持所有原有功能
- 新增章节处理功能

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 许可证

本项目继承原项目的许可证条款。

## 致谢

- 感谢原作者 [shanleiguang](https://github.com/shanleiguang) 的优秀工作
- 感谢所有为古籍数字化做出贡献的开发者和学者

---

**原作者**: GitHub@shanleiguang  
**Python版本转换作者**: GitHub@msyloveldx  
**项目地址**: https://github.com/msyloveldx/vRain-Python

## 更新日志

### v1.4.1 (2025-08-26)
- ✨ 新增章节模式支持
- 📖 支持小说章节排版（章节标题在第一列，内容从第二列开始）
- 🔄 新增双模式支持（章节模式和连续模式）
- 🎯 优化页数控制逻辑
- 🐛 修复文本加载和章节解析问题
