#!/usr/bin/env python3
"""
PDF to Markdown Converter (Advanced)
增强版：支持批量转换、表格、图片提取和更好的格式保留
"""

import argparse
import base64
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple

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
    try:
        tabs = page.find_tables()
        if tabs.tables:
            for tab in tabs.tables:
                table_data = tab.extract()
                if table_data:
                    tables.append(table_data)
    except Exception:
        pass  # 某些PDF可能不支持表格提取
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
        elif len(line) > 2 and line[0:2] in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.']:
            result.append(line)
        else:
            result.append(line)

    return '\n'.join(result)


def pdf_to_markdown_advanced(
    pdf_path: str,
    output_path: str = None,
    output_dir: str = None,
    extract_images_flag: bool = False,
    extract_tables_flag: bool = False,
    image_format: str = 'file',
    quiet: bool = False
) -> Tuple[str, bool, str]:
    """
    将PDF文件转换为Markdown格式（增强版）

    Args:
        pdf_path: PDF文件路径
        output_path: 输出Markdown文件路径
        output_dir: 输出目录（优先级高于output_path的目录）
        extract_images_flag: 是否提取图片
        extract_tables_flag: 是否提取表格
        image_format: 图片格式，'file'保存为文件，'base64'嵌入为base64
        quiet: 是否静默输出

    Returns:
        (markdown文本, 是否成功, 错误信息)
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        return "", False, f"PDF文件不存在: {pdf_path}"

    try:
        # 确定输出路径
        if output_path:
            final_output_path = Path(output_path)
        elif output_dir:
            final_output_path = Path(output_dir) / f"{pdf_file.stem}.md"
        else:
            final_output_path = pdf_file.with_suffix('.md')

        # 创建输出目录（如果需要提取图片）
        if extract_images_flag and image_format == 'file':
            images_dir = final_output_path.parent / f"{pdf_file.stem}_images"
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
        final_output_path.write_text(markdown_text, encoding='utf-8')

        if not quiet:
            print(f"  ✓ {pdf_file.name} → {final_output_path.name}")
            if images_dir:
                print(f"    图片: {images_dir.absolute()}")

        return markdown_text, True, ""

    except Exception as e:
        error_msg = str(e)
        if not quiet:
            print(f"  ✗ {pdf_file.name} 失败: {error_msg}")
        return "", False, error_msg


def find_pdf_files(input_path: str, recursive: bool = False) -> List[Path]:
    """
    查找所有PDF文件

    Args:
        input_path: 输入路径（文件、目录或通配符模式）
        recursive: 是否递归搜索子目录

    Returns:
        PDF文件路径列表
    """
    path = Path(input_path)

    # 如果是文件
    if path.is_file():
        if path.suffix.lower() == '.pdf':
            return [path]
        else:
            return []

    # 如果是目录
    if path.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        return list(path.glob(pattern))

    # 如果是通配符模式
    if '*' in input_path or '?' in input_path:
        return list(Path('.').glob(input_path))

    return []


def batch_convert(
    input_path: str,
    output_dir: str = None,
    extract_images_flag: bool = False,
    extract_tables_flag: bool = False,
    image_format: str = 'file',
    recursive: bool = False,
    workers: int = 1,
    quiet: bool = False
) -> dict:
    """
    批量转换PDF文件

    Returns:
        包含成功/失败统计的字典
    """
    # 查找所有PDF文件
    pdf_files = find_pdf_files(input_path, recursive)

    if not pdf_files:
        print(f"未找到PDF文件: {input_path}")
        return {'success': [], 'failed': [], 'total': 0}

    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    print("=" * 50)

    # 创建输出目录
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = {'success': [], 'failed': [], 'total': len(pdf_files)}
    start_time = time.time()

    # 单线程处理
    if workers == 1:
        for pdf_file in pdf_files:
            _, success, error = pdf_to_markdown_advanced(
                str(pdf_file),
                output_dir=output_dir,
                extract_images_flag=extract_images_flag,
                extract_tables_flag=extract_tables_flag,
                image_format=image_format,
                quiet=quiet
            )
            if success:
                results['success'].append(str(pdf_file))
            else:
                results['failed'].append((str(pdf_file), error))
    else:
        # 多线程处理
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_pdf = {
                executor.submit(
                    pdf_to_markdown_advanced,
                    str(pdf_file),
                    None,
                    output_dir,
                    extract_images_flag,
                    extract_tables_flag,
                    image_format,
                    True  # quiet mode for threaded execution
                ): pdf_file
                for pdf_file in pdf_files
            }

            for future in as_completed(future_to_pdf):
                pdf_file = future_to_pdf[future]
                try:
                    _, success, error = future.result()
                    if success:
                        results['success'].append(str(pdf_file))
                        if not quiet:
                            print(f"  ✓ {pdf_file.name}")
                    else:
                        results['failed'].append((str(pdf_file), error))
                        if not quiet:
                            print(f"  ✗ {pdf_file.name}: {error}")
                except Exception as e:
                    results['failed'].append((str(pdf_file), str(e)))
                    if not quiet:
                        print(f"  ✗ {pdf_file.name}: {e}")

    elapsed_time = time.time() - start_time

    # 打印汇总
    print("\n" + "=" * 50)
    print("转换完成!")
    print(f"  总计: {results['total']} 个文件")
    print(f"  成功: {len(results['success'])} 个")
    print(f"  失败: {len(results['failed'])} 个")
    print(f"  耗时: {elapsed_time:.2f} 秒")

    if results['failed']:
        print("\n失败文件:")
        for pdf_path, error in results['failed']:
            print(f"  - {Path(pdf_path).name}: {error}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='将PDF文件转换为Markdown格式（增强版，支持批量转换）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单个文件转换
  python pdf_to_md_advanced.py input.pdf

  # 批量转换（整个目录）
  python pdf_to_md_advanced.py /path/to/pdfs/ --batch

  # 批量转换（递归子目录）
  python pdf_to_md_advanced.py /path/to/pdfs/ --batch --recursive

  # 批量转换（通配符）
  python pdf_to_md_advanced.py "*.pdf" --batch

  # 指定输出目录并提取图片表格
  python pdf_to_md_advanced.py input.pdf -o output/ --images --tables

  # 批量转换到指定目录，使用4线程
  python pdf_to_md_advanced.py /path/to/pdfs/ --batch -o output/ --workers 4
        """
    )
    parser.add_argument('input', help='输入路径（PDF文件、目录或通配符模式）')
    parser.add_argument('-o', '--output', help='输出文件或目录路径')
    parser.add_argument('--stdout', action='store_true', help='仅输出到控制台（仅单文件模式）')
    parser.add_argument('--images', action='store_true', help='提取图片')
    parser.add_argument('--tables', action='store_true', help='提取表格')
    parser.add_argument('--base64', action='store_true', help='将图片嵌入为base64（与--images一起使用）')
    parser.add_argument('--batch', action='store_true', help='批量模式（输入为目录时使用）')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('-w', '--workers', type=int, default=1, help='并发线程数（默认: 1）')
    parser.add_argument('-q', '--quiet', action='store_true', help='静默模式，减少输出')

    args = parser.parse_args()

    # 检查是否是批量模式
    input_path = Path(args.input)
    is_batch = args.batch or input_path.is_dir() or '*' in args.input

    if is_batch:
        # 批量模式
        batch_convert(
            args.input,
            output_dir=args.output,
            extract_images_flag=args.images,
            extract_tables_flag=args.tables,
            image_format='base64' if args.base64 else 'file',
            recursive=args.recursive,
            workers=args.workers,
            quiet=args.quiet
        )
    else:
        # 单文件模式
        if args.stdout:
            output_path = None
        elif args.output:
            output_path = args.output
        else:
            output_path = str(input_path.with_suffix('.md'))

        try:
            markdown, success, error = pdf_to_markdown_advanced(
                args.input,
                output_path,
                extract_images_flag=args.images,
                extract_tables_flag=args.tables,
                image_format='base64' if args.base64 else 'file',
                quiet=args.quiet
            )

            if not success:
                print(f"错误: {error}")
                sys.exit(1)

            if args.stdout:
                print(markdown)

        except Exception as e:
            print(f"转换失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()
