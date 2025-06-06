"""Utilities for building a map of imports used in Python files."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path
import argparse
from typing import Dict, Iterable, List, Mapping


def find_py_files(root: Path) -> List[Path]:
    """Return a list of Python files under *root* recursively."""
    return [p for p in root.rglob("*.py")]


def parse_imports(file_path: Path) -> Dict[str, List[str | None]]:
    """Parse *file_path* and return a mapping of modules to imported names."""
    imports: Dict[str, List[str | None]] = defaultdict(list)
    with file_path.open("r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.name].append(None)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports[module].append(alias.name)
    return imports


def build_import_tree(
    py_files: Iterable[Path], root: Path
) -> Dict[str, Dict[str, List[str | None]]]:
    """Build a mapping of relative file paths to their imports."""
    tree: Dict[str, Dict[str, List[str | None]]] = {}
    for path in py_files:
        relative = str(path.relative_to(root))
        tree[relative] = parse_imports(path)
    return tree


def format_markdown(tree: Mapping[str, Mapping[str, List[str | None]]]) -> str:
    """Return a Markdown representation of the *tree* of imports."""
    if not tree:
        return "No Python files found."
    lines: List[str] = []
    for file_path in sorted(tree):
        lines.append(f"- **{file_path}**")
        imports = tree[file_path]
        if not imports:
            lines.append("  - (no imports)")
            continue
        for module, names in sorted(imports.items()):
            if module and any(names):
                lines.append(f"  - `{module}`:")
            elif module:
                lines.append(f"  - `import {module}`")
                continue
            else:
                module = ""
            for name in names:
                if name:
                    lines.append(f"    - {name}")
                else:
                    lines.append(f"  - `import {module}`")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> None:
    """Entry point for command line execution."""
    parser = argparse.ArgumentParser(description="Build a Markdown map of imports")
    parser.add_argument("path", nargs="?", default=".", help="Root directory to scan")
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.path).resolve()
    py_files = find_py_files(root)
    tree = build_import_tree(py_files, root)
    md_graph = format_markdown(tree)
    print(md_graph)


if __name__ == "__main__":
    main()
