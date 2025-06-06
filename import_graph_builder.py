"""Build a Graphviz visualization of Python import relationships."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set

from graphviz import Digraph


IGNORE_DIRS = {"__pycache__", ".venv", "tests"}


def find_py_files(root: Path) -> List[Path]:
    """Return all Python files under *root* excluding ignored directories."""
    files: List[Path] = []
    for path in root.rglob("*.py"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def parse_imports(file_path: Path) -> Set[str]:
    """Return a set of module names imported by *file_path*."""
    modules: Set[str] = set()
    try:
        with file_path.open("r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except SyntaxError:
        return modules

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            modules.add(module)
    return modules


def build_import_tree(py_files: Iterable[Path], root: Path) -> Dict[str, Set[str]]:
    """Return mapping of relative file paths to imported modules."""
    tree: Dict[str, Set[str]] = {}
    for path in py_files:
        imports = parse_imports(path)
        tree[str(path.relative_to(root))] = imports
    return tree


def module_name(path: Path, root: Path) -> str:
    """Return dotted module name for *path* relative to *root*."""
    rel = path.relative_to(root)
    if rel.name == "__init__.py":
        parts = rel.parent.parts
    else:
        parts = rel.with_suffix("").parts
    return ".".join(parts)


def collect_local_modules(py_files: Iterable[Path], root: Path) -> Set[str]:
    """Return a set of dotted module names within the project."""
    modules = set()
    for p in py_files:
        mod = module_name(p, root)
        if mod:
            modules.add(mod)
    return modules


def is_local(module: str, local_modules: Set[str]) -> bool:
    """Return ``True`` if *module* belongs to the project."""
    if module.startswith("."):
        return True
    for local in local_modules:
        if module == local or module.startswith(local + "."):
            return True
    return False


def is_stdlib(module: str) -> bool:
    """Return ``True`` if *module* looks like a standard library module."""
    base = module.lstrip(".").split(".")[0]
    return base in sys.stdlib_module_names


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Visualize import graph")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory to scan",
    )
    parser.add_argument(
        "--output",
        default="import_tree.png",
        help="Output PNG file",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.path).resolve()
    py_files = find_py_files(root)
    tree = build_import_tree(py_files, root)
    local_modules = collect_local_modules(py_files, root)

    dot = Digraph("import_tree", format="png")

    root_node: str | None = None
    if (root / "main.py").exists():
        root_node = "main.py"
    elif (root / "__init__.py").exists():
        root_node = "__init__.py"

    added_nodes: Set[str] = set()

    for file_path, imports in tree.items():
        color = "red" if file_path == root_node else "lightblue"
        if file_path not in added_nodes:
            dot.node(file_path, label=file_path, shape="box", style="filled", color=color)
            added_nodes.add(file_path)

        for module in sorted(imports):
            if module not in added_nodes:
                if is_local(module, local_modules):
                    mcolor = "blue"
                elif is_stdlib(module):
                    mcolor = "gray"
                else:
                    mcolor = "green"
                dot.node(module, label=module, shape="ellipse", style="filled", color=mcolor)
                added_nodes.add(module)
            dot.edge(file_path, module)

    output_file = Path(args.output)
    dot.render(
        output_file.stem,
        directory=str(output_file.parent) if output_file.parent != Path("") else None,
        cleanup=True,
    )


if __name__ == "__main__":
    main()
