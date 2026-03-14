# PDF 转 Markdown 工具

两个版本的 PDF 转 Markdown 转换器：

## 1. 基础版 (pdf_to_md.py)

简单轻量，仅提取文本内容。

### 安装依赖

```bash
pip install PyMuPDF
```

### 使用方法

```bash
# 基本用法（输出到同名 .md 文件）
python pdf_to_md.py input.pdf

# 指定输出文件
python pdf_to_md.py input.pdf -o output.md

# 仅输出到控制台
python pdf_to_md.py input.pdf --stdout
```

---

## 2. 增强版 (pdf_to_md_advanced.py)

支持图片提取、表格提取和更好的格式保留。

### 安装依赖

```bash
pip install PyMuPDF
```

### 使用方法

```bash
# 基本用法
python pdf_to_md_advanced.py input.pdf

# 提取图片和表格
python pdf_to_md_advanced.py input.pdf --images --tables

# 将图片嵌入为 base64（单文件方案）
python pdf_to_md_advanced.py input.pdf --images --base64

# 指定输出文件
python pdf_to_md_advanced.py input.pdf -o output.md --images --tables

# 仅输出到控制台
python pdf_to_md_advanced.py input.pdf --stdout
```

### 功能特点

| 功能 | 基础版 | 增强版 |
|------|--------|--------|
| 文本提取 | ✅ | ✅ |
| 标题检测 | ✅ | ✅（更智能）|
| 图片提取 | ❌ | ✅ |
| 表格提取 | ❌ | ✅ |
| 列表识别 | ❌ | ✅ |
| Base64 图片嵌入 | ❌ | ✅ |

---

## 使用示例

### Python 代码调用

```python
from pdf_to_md import pdf_to_markdown

# 基础版
markdown = pdf_to_markdown("document.pdf", "output.md")
```

```python
from pdf_to_md_advanced import pdf_to_markdown_advanced

# 增强版
markdown = pdf_to_markdown_advanced(
    "document.pdf",
    "output.md",
    extract_images_flag=True,
    extract_tables_flag=True
)
```

---

## 注意事项

1. **表格提取**：简单表格可以正常提取，复杂表格可能需要额外处理
2. **图片提取**：提取的图片会保存在 `PDF文件名_images` 目录下
3. **格式保留**：转换后的 Markdown 可能需要手动微调
4. **扫描版 PDF**：如果是图片扫描的 PDF，需要先进行 OCR 处理

## 推荐的 OCR 工具（针对扫描版 PDF）

如果需要处理扫描版 PDF，可以结合 OCR 工具：

```bash
# 使用 pdf2image + pytesseract
pip install pdf2image pytesseract
```
