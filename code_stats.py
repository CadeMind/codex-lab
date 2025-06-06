"""Collect statistics about Python code in a directory tree."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Iterable, Dict


IGNORE_DIRS = {"__pycache__", ".venv", "venv"}


def find_py_files(root: Path) -> list[Path]:
    """Return a list of Python files under *root* recursively."""
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def analyze_file(file_path: Path) -> Dict[str, int]:
    """Return statistics for a single Python file."""
    counts = {
        "lines": 0,
        "blank": 0,
        "comments": 0,
        "defs": 0,
        "classes": 0,
        "imports": 0,
        "from_imports": 0,
    }

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = file_path.read_text(encoding="latin-1")
    lines = content.splitlines()
    counts["lines"] = len(lines)
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            counts["blank"] += 1
        elif stripped.startswith("#"):
            counts["comments"] += 1
    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return counts

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            counts["defs"] += 1
        elif isinstance(node, ast.ClassDef):
            counts["classes"] += 1
        elif isinstance(node, ast.Import):
            counts["imports"] += 1
        elif isinstance(node, ast.ImportFrom):
            counts["from_imports"] += 1

    return counts


def main(argv: Iterable[str] | None = None) -> None:
    """Entry point for command line execution."""
    parser = argparse.ArgumentParser(description="Collect Python code statistics")
    parser.add_argument(
        "--path",
        default=".",
        help="Directory to scan",
    )
    parser.add_argument(
        "--output",
        help="Optional JSON file to write statistics",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.path).resolve()
    py_files = find_py_files(root)

    if not py_files:
        print("No Python files found.")
        return

    total_lines = total_blank = total_comments = 0
    total_defs = total_classes = total_imports = total_from = 0
    longest_file = ""
    longest_lines = 0

    for path in py_files:
        stats = analyze_file(path)
        total_lines += stats["lines"]
        total_blank += stats["blank"]
        total_comments += stats["comments"]
        total_defs += stats["defs"]
        total_classes += stats["classes"]
        total_imports += stats["imports"]
        total_from += stats["from_imports"]
        if stats["lines"] > longest_lines:
            longest_lines = stats["lines"]
            longest_file = str(path.relative_to(root))

    average_length = total_lines / len(py_files)

    report = {
        "files": len(py_files),
        "total_lines": total_lines,
        "blank_lines": total_blank,
        "comment_lines": total_comments,
        "defs": total_defs,
        "classes": total_classes,
        "imports": total_imports,
        "from_imports": total_from,
        "longest_file": {"path": longest_file, "lines": longest_lines},
        "average_length": average_length,
    }

    print("Python Code Statistics")
    print("----------------------")
    print(f"Files scanned: {report['files']}")
    print(f"Total lines: {report['total_lines']}")
    print(f"Blank lines: {report['blank_lines']}")
    print(f"Comment lines: {report['comment_lines']}")
    print(f"def statements: {report['defs']}")
    print(f"class definitions: {report['classes']}")
    print(f"import statements: {report['imports']}")
    print(f"from import statements: {report['from_imports']}")
    print(
        f"Longest file: {report['longest_file']['path']} "
        f"({report['longest_file']['lines']} lines)"
    )
    print(f"Average file length: {report['average_length']:.2f} lines")

    if args.output:
        output_path = Path(args.output)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
