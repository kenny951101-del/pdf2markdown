# PDF 转 Markdown 工具

支持单个文件和批量转换的 PDF 转 Markdown 工具。

## 安装依赖

```bash
pip install PyMuPDF
```

---

## 快速开始

### 基础版 (pdf_to_md.py)

简单轻量，适合纯文本转换。

```bash
# 单个文件
python pdf_to_md.py input.pdf

# 批量转换整个目录
python pdf_to_md.py /path/to/pdfs/ --batch

# 批量转换（递归子目录）
python pdf_to_md.py /path/to/pdfs/ --batch --recursive

# 批量转换（通配符）
python pdf_to_md.py "*.pdf" --batch

# 指定输出目录
python pdf_to_md.py input.pdf -o output/

# 4线程并行批量转换
python pdf_to_md.py /path/to/pdfs/ --batch -o output/ --workers 4
```

---

### 增强版 (pdf_to_md_advanced.py)

支持图片提取、表格提取和更好的格式保留。

```bash
# 单个文件
python pdf_to_md_advanced.py input.pdf

# 提取图片和表格
python pdf_to_md_advanced.py input.pdf --images --tables

# 批量转换并提取图片表格
python pdf_to_md_advanced.py /path/to/pdfs/ --batch --images --tables

# 递归批量转换
python pdf_to_md_advanced.py /path/to/pdfs/ --batch --recursive -o output/

# 多线程批量转换
python pdf_to_md_advanced.py /path/to/pdfs/ --batch --images --workers 4

# 图片嵌入为 base64（单文件方案）
python pdf_to_md_advanced.py input.pdf --images --base64
```

---

## 功能对比

| 功能 | 基础版 | 增强版 |
|------|--------|--------|
| 单个文件转换 | ✅ | ✅ |
| 批量转换 | ✅ | ✅ |
| 递归子目录 | ✅ | ✅ |
| 多线程并行 | ✅ | ✅ |
| 文本提取 | ✅ | ✅ |
| 标题检测 | ✅ | ✅（更智能）|
| 图片提取 | ❌ | ✅ |
| 表格提取 | ❌ | ✅ |
| 列表识别 | ❌ | ✅ |
| Base64 图片嵌入 | ❌ | ✅ |

---

## 命令行参数

### 通用参数（两个版本都支持）

| 参数 | 说明 |
|------|------|
| `input` | 输入路径（PDF文件、目录或通配符）|
| `-o, --output` | 输出文件或目录路径 |
| `--batch` | 启用批量模式 |
| `-r, --recursive` | 递归处理子目录 |
| `-w, --workers` | 并发线程数（默认: 1）|
| `-q, --quiet` | 静默模式，减少输出 |
| `--stdout` | 仅输出到控制台（单文件模式）|

### 增强版特有参数

| 参数 | 说明 |
|------|------|
| `--images` | 提取图片 |
| `--tables` | 提取表格 |
| `--base64` | 将图片嵌入为base64 |

---

## 使用示例

### 示例 1：批量转换整个文件夹

```bash
# 基础版
python pdf_to_md.py ~/Documents/PDFs/ --batch -o ~/Documents/Markdown/

# 增强版（带图片表格）
python pdf_to_md_advanced.py ~/Documents/PDFs/ --batch --images --tables -o ~/Documents/Markdown/
```

输出：
```
找到 5 个PDF文件
==================================================
  ✓ file1.pdf → file1.md
  ✓ file2.pdf → file2.md
  ✓ file3.pdf → file3.md
  ✓ file4.pdf → file4.md
  ✓ file5.pdf → file5.md

==================================================
转换完成!
  总计: 5 个文件
  成功: 5 个
  失败: 0 个
  耗时: 2.35 秒
```

### 示例 2：递归转换所有子目录

```bash
python pdf_to_md_advanced.py ~/Documents/ --batch --recursive -o ~/Output/
```

### 示例 3：通配符批量转换

```bash
# 转换当前目录所有PDF
python pdf_to_md.py "*.pdf" --batch

# 转换特定模式
python pdf_to_md_advanced.py "report_*.pdf" --batch --tables
```

### 示例 4：Python 代码调用

```python
from pdf_to_md import pdf_to_markdown, batch_convert

# 单个文件
markdown, success, error = pdf_to_markdown("document.pdf", "output.md")

# 批量转换
results = batch_convert(
    "/path/to/pdfs/",
    output_dir="/path/to/output/",
    recursive=True,
    workers=4
)
print(f"成功: {len(results['success'])}, 失败: {len(results['failed'])}")
```

```python
from pdf_to_md_advanced import pdf_to_markdown_advanced, batch_convert

# 单个文件（带图片表格）
markdown, success, error = pdf_to_markdown_advanced(
    "document.pdf",
    output_path="output.md",
    extract_images_flag=True,
    extract_tables_flag=True
)

# 批量转换（带图片表格）
results = batch_convert(
    "/path/to/pdfs/",
    output_dir="/path/to/output/",
    extract_images_flag=True,
    extract_tables_flag=True,
    workers=4
)
```

---

## 输出结构

### 单文件模式
```
input.pdf → input.md
input.pdf + --images → input.md + input_images/
```

### 批量模式
```
/pdfs/
  ├── a.pdf
  ├── b.pdf
  └── c.pdf

# 输出到 /output/：
/output/
  ├── a.md
  ├── a_images/      # 如果启用 --images
  ├── b.md
  ├── b_images/
  ├── c.md
  └── c_images/
```

---

## 注意事项

1. **表格提取**：简单表格可以正常提取，复杂表格可能需要额外处理
2. **图片提取**：提取的图片会保存在 `{pdf文件名}_images/` 目录下
3. **格式保留**：转换后的 Markdown 可能需要手动微调
4. **扫描版 PDF**：如果是图片扫描的 PDF，需要先进行 OCR 处理
5. **多线程**：IO密集型操作，多线程可加速；但线程数过多可能适得其反

## 推荐的 OCR 工具（针对扫描版 PDF）

```bash
pip install pdf2image pytesseract
```

---

## 许可证

MIT License
