#!/usr/bin/env python3
"""
PDF to Markdown Converter
将PDF文件转换为Markdown格式（支持批量转换）
"""

import argparse
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


def pdf_to_markdown(
    pdf_path: str,
    output_path: str = None,
    output_dir: str = None,
    quiet: bool = False
) -> Tuple[str, bool, str]:
    """
    将PDF文件转换为Markdown格式

    Args:
        pdf_path: PDF文件路径
        output_path: 输出Markdown文件路径
        output_dir: 输出目录
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

            # 添加分页标记
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
        final_output_path.write_text(markdown_text, encoding='utf-8')

        if not quiet:
            print(f"  ✓ {pdf_file.name} → {final_output_path.name}")

        return markdown_text, True, ""

    except Exception as e:
        error_msg = str(e)
        if not quiet:
            print(f"  ✗ {pdf_file.name} 失败: {error_msg}")
        return "", False, error_msg


def find_pdf_files(input_path: str, recursive: bool = False) -> List[Path]:
    """查找所有PDF文件"""
    path = Path(input_path)

    if path.is_file():
        if path.suffix.lower() == '.pdf':
            return [path]
        return []

    if path.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        return list(path.glob(pattern))

    if '*' in input_path or '?' in input_path:
        return list(Path('.').glob(input_path))

    return []


def batch_convert(
    input_path: str,
    output_dir: str = None,
    recursive: bool = False,
    workers: int = 1,
    quiet: bool = False
) -> dict:
    """批量转换PDF文件"""
    pdf_files = find_pdf_files(input_path, recursive)

    if not pdf_files:
        print(f"未找到PDF文件: {input_path}")
        return {'success': [], 'failed': [], 'total': 0}

    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    print("=" * 50)

    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = {'success': [], 'failed': [], 'total': len(pdf_files)}
    start_time = time.time()

    if workers == 1:
        for pdf_file in pdf_files:
            _, success, error = pdf_to_markdown(str(pdf_file), output_dir=output_dir, quiet=quiet)
            if success:
                results['success'].append(str(pdf_file))
            else:
                results['failed'].append((str(pdf_file), error))
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_pdf = {
                executor.submit(pdf_to_markdown, str(pdf_file), None, output_dir, True): pdf_file
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
        description='将PDF文件转换为Markdown格式（支持批量转换）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
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

  # 批量转换，4线程并行
  python pdf_to_md.py /path/to/pdfs/ --batch -o output/ --workers 4
        """
    )
    parser.add_argument('input', help='输入路径（PDF文件、目录或通配符模式）')
    parser.add_argument('-o', '--output', help='输出文件或目录路径')
    parser.add_argument('--stdout', action='store_true', help='仅输出到控制台（仅单文件模式）')
    parser.add_argument('--batch', action='store_true', help='批量模式')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('-w', '--workers', type=int, default=1, help='并发线程数（默认: 1）')
    parser.add_argument('-q', '--quiet', action='store_true', help='静默模式')

    args = parser.parse_args()

    input_path = Path(args.input)
    is_batch = args.batch or input_path.is_dir() or '*' in args.input

    if is_batch:
        batch_convert(
            args.input,
            output_dir=args.output,
            recursive=args.recursive,
            workers=args.workers,
            quiet=args.quiet
        )
    else:
        if args.stdout:
            output_path = None
        elif args.output:
            output_path = args.output
        else:
            output_path = str(input_path.with_suffix('.md'))

        try:
            markdown, success, error = pdf_to_markdown(args.input, output_path, quiet=args.quiet)

            if not success:
                print(f"错误: {error}")
                sys.exit(1)

            if args.stdout:
                print(markdown)

        except Exception as e:
            print(f"转换失败: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()
