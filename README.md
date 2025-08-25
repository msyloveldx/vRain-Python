# vRain Python版本使用指南

## 项目简介

vRain是一款中文古籍刻本风格直排电子书制作工具的Python版本。本版本完整转换了原Perl版本的功能，提供了更好的跨平台兼容性和更简单的安装部署方式。

## 主要特性

- 🔄 **完整功能移植**: 保持了Perl原版的所有核心功能
- 🐍 **Python实现**: 使用现代Python技术栈重新开发
- 📱 **跨平台支持**: 支持Windows、macOS、Linux
- 📦 **简化部署**: 通过pip即可安装所有依赖
- 🎨 **古籍风格**: 完美复刻古籍刻本的视觉效果

## 系统要求

- Python 3.8 或更高版本
- 操作系统: Windows 10+、macOS 10.14+、Ubuntu 18.04+ 或其他Linux发行版

## 安装步骤

### 1. 克隆项目
```bash
git clone https://github.com/shanleiguang/vRain.git
cd vRain
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

### 主程序 - 生成古籍电子书

```bash
# 基本用法
python vrain.py -b 书籍ID -f 起始文本序号 -t 结束文本序号

# 示例：生成史记卷1-3
python vrain.py -b 01 -f 1 -t 3

# 测试模式（仅生成前5页）
python vrain.py -b 01 -f 1 -t 1 -z 5

# 生成并压缩PDF
python vrain.py -b 01 -f 1 -t 3 -c

# 显示详细信息
python vrain.py -b 01 -f 1 -t 3 -v
```

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
├── vrain.py                 # 主程序
├── requirements.txt         # Python依赖
├── README.md               # 项目说明
├── PYTHON_README.md        # Python版本说明
├── books/                  # 书籍目录
│   ├── 01/                # 书籍01
│   │   ├── book.cfg       # 书籍配置
│   │   ├── text/          # 文本文件
│   │   ├── indentxt.py    # 缩进处理脚本
│   │   └── addyins.py     # 印章添加脚本
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
└── pdf/                   # 输出PDF目录
```

## 配置文件说明

### 书籍配置文件 (book.cfg)

主要配置项：
- `title`: 书籍标题
- `author`: 作者
- `canvas_id`: 背景图ID
- `font1-5`: 字体文件名
- `row_num`: 每列字数
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

### 与Perl版本的兼容性
- 配置文件格式完全兼容
- 输出PDF效果一致
- 支持所有原有功能

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
**项目地址**: https://github.com/shanleiguang/vRain
