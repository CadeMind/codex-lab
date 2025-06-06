"""Generate simple docs for Python files using AST and optional LLM."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Iterable, List, Tuple


def llm_generate_doc(code: str) -> str:
    """Return generated documentation for *code* via LLM stub."""
    # Placeholder for integration with real LLM service.
    first_line = code.strip().splitlines()[0] if code else ""
    return f"Auto-generated doc for: {first_line}"


def find_py_files(root: Path) -> List[Path]:
    """Return a list of Python files under *root* recursively."""
    return [p for p in root.rglob("*.py")]


def get_signature(func: ast.FunctionDef | ast.AsyncFunctionDef) -> Tuple[str, str]:
    """Return (args, return_annotation) for *func*."""
    args = []
    for a in func.args.posonlyargs:
        args.append(a.arg)
    if func.args.posonlyargs:
        args.append("/")
    for a in func.args.args:
        args.append(a.arg)
    if func.args.vararg:
        args.append("*" + func.args.vararg.arg)
    elif func.args.kwonlyargs:
        args.append("*")
    for a in func.args.kwonlyargs:
        args.append(a.arg)
    if func.args.kwarg:
        args.append("**" + func.args.kwarg.arg)
    args_str = ", ".join(args)
    ret = ast.unparse(func.returns) if func.returns else ""
    return args_str, ret


def parse_file(path: Path) -> List[Tuple[str, str]]:
    """Return list of documentation strings for elements in *path*.

    Files that fail to parse are skipped gracefully.
    """
    try:
        src = path.read_text(encoding="utf-8")
    except OSError:
        return []

    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        # Skip files with syntax errors
        return []
    docs: List[Tuple[str, str]] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            if not doc:
                doc = llm_generate_doc(ast.get_source_segment(src, node) or node.name)
            docs.append((f"class {node.name}", doc))
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fdoc = ast.get_docstring(child)
                    if not fdoc:
                        fdoc = llm_generate_doc(ast.get_source_segment(src, child) or child.name)
                    args, ret = get_signature(child)
                    header = f"def {child.name}({args})"
                    if ret:
                        header += f" -> {ret}"
                    docs.append((header, fdoc))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if not doc:
                doc = llm_generate_doc(ast.get_source_segment(src, node) or node.name)
            args, ret = get_signature(node)
            header = f"def {node.name}({args})"
            if ret:
                header += f" -> {ret}"
            docs.append((header, doc))
    return docs


def format_markdown(file_path: Path, items: List[Tuple[str, str]]) -> str:
    """Return Markdown documentation for *file_path*."""
    lines = [f"# {file_path.name}", ""]
    for header, doc in items:
        lines.append(f"## {header}")
        lines.append("")
        lines.append(doc)
        lines.append("")
    return "\n".join(lines)


def format_pyi(items: List[Tuple[str, str]]) -> str:
    """Return .pyi stub text for *items*."""
    lines = []
    for header, doc in items:
        if header.startswith("class "):
            lines.append(f"{header}:")
            lines.append(f"    \"\"\"{doc}\"\"\"")
            lines.append("    ...")
        else:
            lines.append(f"{header}:")
            lines.append(f"    \"\"\"{doc}\"\"\"")
            lines.append("    ...")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate simple docs via AST")
    parser.add_argument("--path", default=".", help="Directory to scan")
    parser.add_argument("--output", default="./docs/", help="Output directory")
    parser.add_argument(
        "--format", choices=["markdown", "pyi"], default="markdown", help="Output format"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.path).resolve()
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    for py_file in find_py_files(root):
        rel = py_file.relative_to(root)
        docs = parse_file(py_file)
        if args.format == "markdown":
            text = format_markdown(py_file, docs)
            dest = out_dir / rel.with_suffix(".md")
        else:
            text = format_pyi(docs)
            dest = out_dir / rel.with_suffix(".pyi")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        print(f"Wrote {dest}")


if __name__ == "__main__":
    main()
