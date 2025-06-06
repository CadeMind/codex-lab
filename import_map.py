"""Utilities for building a map of imports used in Python files."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path
import argparse
from typing import DefaultDict, Dict, Iterable, List, Mapping


def find_py_files(root: Path) -> List[Path]:
    """Return a list of Python files under *root* recursively."""
    return [p for p in root.rglob("*.py")]


def parse_imports(file_path: Path) -> Dict[str, List[str | None]]:
    """Parse *file_path* and return a mapping of modules to imported names.

    ``None`` entries represent ``import <module>`` statements, while strings
    contain imported names and optional aliases.
    """
    imports: DefaultDict[str, List[str | None]] = defaultdict(list)

    # 🔧 Устойчивое чтение файла с fallback:
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = file_path.read_text(encoding="latin-1")

    tree = ast.parse(content, filename=str(file_path))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    imports[alias.name].append(f"as {alias.asname}")
                else:
                    imports[alias.name].append(None)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            for alias in node.names:
                name = alias.name
                if alias.asname:
                    name += f" as {alias.asname}"
                imports[module].append(name)

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
            import_items = [n for n in names if n is None or str(n).startswith("as ")]
            from_items = [n for n in names if n not in import_items]

            for item in import_items:
                if item is None:
                    lines.append(f"  - `import {module}`")
                else:
                    alias = str(item)[3:]
                    lines.append(f"  - `import {module} as {alias}`")

            if from_items:
                lines.append(f"  - `{module}`:")
                for name in from_items:
                    lines.append(f"    - {name}")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> None:
    """Entry point for command line execution."""
    parser = argparse.ArgumentParser(
        description="Build a Markdown map of imports"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root directory to scan",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.path).resolve()
    py_files = find_py_files(root)
    tree = build_import_tree(py_files, root)
    md_graph = format_markdown(tree)
    print(md_graph)


if __name__ == "__main__":
    main()
