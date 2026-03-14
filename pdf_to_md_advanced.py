#!/usr/bin/env python3
"""
PDF to Markdown Converter (Advanced)
增强版：支持表格、图片提取和更好的格式保留
"""

import argparse
import base64
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("错误: 请先安装 PyMuPDF: pip install PyMuPDF")
    sys.exit(1)


def extract_images(page, page_num: int, output_dir: Path) -> list:
    """提取页面中的图片"""
    images_info = []
    image_list = page.get_images()

    for img_index, img in enumerate(image_list, start=1):
        xref = img[0]
        pix = fitz.Pixmap(page.parent, xref)

        # 跳过CMYK图片，转换为RGB
        if pix.n > 4:
            pix = fitz.Pixmap(fitz.csRGB, pix)

        # 保存图片
        img_filename = f"page_{page_num + 1}_img_{img_index}.png"
        img_path = output_dir / img_filename
        pix.save(str(img_path))
        pix = None

        images_info.append({
            'path': img_path,
            'filename': img_filename,
            'index': img_index
        })

    return images_info


def extract_tables(page) -> list:
    """
    尝试提取表格（简单实现）
    注意：复杂的表格可能需要更专业的库如 camelot-py
    """
    tables = []
    tabs = page.find_tables()

    if tabs.tables:
        for tab in tabs.tables:
            table_data = tab.extract()
            if table_data:
                tables.append(table_data)

    return tables


def table_to_markdown(table_data: list) -> str:
    """将表格数据转换为Markdown格式"""
    if not table_data or len(table_data) < 1:
        return ""

    md_lines = []

    # 表头
    headers = table_data[0]
    md_lines.append("| " + " | ".join(str(h) for h in headers) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    # 数据行
    for row in table_data[1:]:
        md_lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

    return "\n".join(md_lines)


def format_paragraph(text: str) -> str:
    """格式化段落，检测标题等结构"""
    lines = text.split('\n')
    result = []

    for line in lines:
        line = line.strip()
        if not line:
            result.append('')
            continue

        # 检测一级标题（短且全大写）
        if len(line) < 50 and line.isupper() and len(line) > 3:
            result.append(f"# {line}")
        # 检测二级标题
        elif len(line) < 80 and line.endswith(('：', ':')) and len(line) < 30:
            result.append(f"## {line}")
        # 检测列表项
        elif line.startswith(('•', '·', '-', '○', '●', '■', '□')):
            result.append(f"- {line[1:].strip()}")
        elif line[0:2] in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.']:
            result.append(line)
        else:
            result.append(line)

    return '\n'.join(result)


def pdf_to_markdown_advanced(
    pdf_path: str,
    output_path: str = None,
    extract_images_flag: bool = False,
    extract_tables_flag: bool = False,
    image_format: str = 'file'  # 'file' 或 'base64'
) -> str:
    """
    将PDF文件转换为Markdown格式（增强版）

    Args:
        pdf_path: PDF文件路径
        output_path: 输出Markdown文件路径
        extract_images_flag: 是否提取图片
        extract_tables_flag: 是否提取表格
        image_format: 图片格式，'file'保存为文件，'base64'嵌入为base64

    Returns:
        转换后的Markdown文本
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    # 创建输出目录（如果需要提取图片）
    if extract_images_flag and image_format == 'file':
        images_dir = pdf_file.parent / f"{pdf_file.stem}_images"
        images_dir.mkdir(exist_ok=True)
    else:
        images_dir = None

    # 打开PDF
    doc = fitz.open(pdf_path)
    md_content = []

    # 文档标题
    md_content.append(f"# {pdf_file.stem}\n")
    md_content.append(f"\n**原文档**: `{pdf_file.name}`  ")
    md_content.append(f"**页数**: {len(doc)} 页  ")
    md_content.append(f"**大小**: {pdf_file.stat().st_size / 1024:.1f} KB\n")
    md_content.append("---\n")

    # 遍历每一页
    for page_num in range(len(doc)):
        page = doc[page_num]

        md_content.append(f"\n## 第 {page_num + 1} 页\n")

        # 提取并处理文本
        text = page.get_text()
        if text.strip():
            formatted_text = format_paragraph(text)
            md_content.append(formatted_text)

        # 提取表格
        if extract_tables_flag:
            try:
                tables = extract_tables(page)
                if tables:
                    md_content.append("\n### 表格\n")
                    for i, table in enumerate(tables, 1):
                        md_content.append(f"\n**表格 {i}**\n")
                        md_content.append(table_to_markdown(table))
                        md_content.append("\n")
            except Exception as e:
                md_content.append(f"\n> ⚠️ 表格提取失败: {e}\n")

        # 提取图片
        if extract_images_flag:
            try:
                images = extract_images(page, page_num, images_dir)
                if images:
                    md_content.append("\n### 图片\n")
                    for img_info in images:
                        if image_format == 'file':
                            relative_path = f"{pdf_file.stem}_images/{img_info['filename']}"
                            md_content.append(f"\n![图片]({relative_path})\n")
                        else:
                            # base64嵌入
                            with open(img_info['path'], 'rb') as f:
                                img_data = base64.b64encode(f.read()).decode()
                            md_content.append(f"\n![图片](data:image/png;base64,{img_data})\n")
            except Exception as e:
                md_content.append(f"\n> ⚠️ 图片提取失败: {e}\n")

    doc.close()

    # 合并内容
    markdown_text = '\n'.join(md_content)

    # 保存文件
    if output_path:
        output_file = Path(output_path)
        output_file.write_text(markdown_text, encoding='utf-8')
        print(f"✓ Markdown已保存到: {output_file.absolute()}")
        if images_dir:
            print(f"✓ 图片已保存到: {images_dir.absolute()}")

    return markdown_text


def main():
    parser = argparse.ArgumentParser(
        description='将PDF文件转换为Markdown格式（增强版）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python pdf_to_md_advanced.py input.pdf
  python pdf_to_md_advanced.py input.pdf -o output.md --images --tables
  python pdf_to_md_advanced.py input.pdf --stdout
        """
    )
    parser.add_argument('pdf', help='输入的PDF文件路径')
    parser.add_argument('-o', '--output', help='输出的Markdown文件路径（默认: 与PDF同名）')
    parser.add_argument('--stdout', action='store_true', help='仅输出到控制台')
    parser.add_argument('--images', action='store_true', help='提取图片')
    parser.add_argument('--tables', action='store_true', help='提取表格')
    parser.add_argument('--base64', action='store_true', help='将图片嵌入为base64（与--images一起使用）')

    args = parser.parse_args()

    # 确定输出路径
    if args.stdout:
        output_path = None
    elif args.output:
        output_path = args.output
    else:
        output_path = str(Path(args.pdf).with_suffix('.md'))

    try:
        markdown = pdf_to_markdown_advanced(
            args.pdf,
            output_path,
            extract_images_flag=args.images,
            extract_tables_flag=args.tables,
            image_format='base64' if args.base64 else 'file'
        )

        if args.stdout or not output_path:
            print(markdown)

    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"转换失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
