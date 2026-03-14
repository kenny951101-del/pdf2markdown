#!/usr/bin/env python3
"""
PDF to Markdown Converter
将PDF文件转换为Markdown格式
"""

import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("错误: 请先安装 PyMuPDF: pip install PyMuPDF")
    sys.exit(1)


def pdf_to_markdown(pdf_path: str, output_path: str = None) -> str:
    """
    将PDF文件转换为Markdown格式

    Args:
        pdf_path: PDF文件路径
        output_path: 输出Markdown文件路径（可选）

    Returns:
        转换后的Markdown文本
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    # 打开PDF
    doc = fitz.open(pdf_path)
    md_content = []

    # 添加文档标题
    md_content.append(f"# {pdf_file.stem}\n")
    md_content.append(f"\n> 原文档: {pdf_file.name}\n")
    md_content.append(f"> 页数: {len(doc)} 页\n")
    md_content.append("---\n")

    # 遍历每一页
    for page_num in range(len(doc)):
        page = doc[page_num]

        # 添加分页标记（可选）
        md_content.append(f"\n## 第 {page_num + 1} 页\n")

        # 提取文本
        text = page.get_text()

        # 简单的文本清理和格式化
        lines = text.split('\n')
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue

            # 检测标题（简单启发式规则）
            if len(line) < 100 and line.isupper():
                formatted_lines.append(f"### {line}")
            elif len(line) < 50 and line.endswith(':'):
                formatted_lines.append(f"**{line}**")
            else:
                formatted_lines.append(line)

        # 合并段落
        paragraph = '\n'.join(formatted_lines)
        md_content.append(paragraph)
        md_content.append('\n')

    doc.close()

    # 合并所有内容
    markdown_text = '\n'.join(md_content)

    # 保存到文件
    if output_path:
        output_file = Path(output_path)
        output_file.write_text(markdown_text, encoding='utf-8')
        print(f"✓ Markdown已保存到: {output_file.absolute()}")

    return markdown_text


def main():
    parser = argparse.ArgumentParser(
        description='将PDF文件转换为Markdown格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python pdf_to_md.py input.pdf
  python pdf_to_md.py input.pdf -o output.md
  python pdf_to_md.py input.pdf --output output.md
        """
    )
    parser.add_argument('pdf', help='输入的PDF文件路径')
    parser.add_argument('-o', '--output', help='输出的Markdown文件路径（默认: 与PDF同名）')
    parser.add_argument('--stdout', action='store_true', help='仅输出到控制台，不保存文件')

    args = parser.parse_args()

    # 确定输出路径
    if args.stdout:
        output_path = None
    elif args.output:
        output_path = args.output
    else:
        output_path = str(Path(args.pdf).with_suffix('.md'))

    try:
        markdown = pdf_to_markdown(args.pdf, output_path)

        if args.stdout or not output_path:
            print(markdown)

    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"转换失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
