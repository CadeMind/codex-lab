"""Generate an import dependency graph for Python projects."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set

from graphviz import Digraph


def find_py_files(root: Path) -> List[Path]:
    """Return all Python files under *root* recursively."""
    return [p for p in root.rglob("*.py")]


def parse_imports(file_path: Path) -> Set[str]:
    """Return a set of modules imported by *file_path*."""
    modules: Set[str] = set()
    with file_path.open("r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            modules.add(module)

    return modules


def build_import_tree(py_files: Iterable[Path], root: Path) -> Dict[str, Set[str]]:
    """Build a mapping of relative file paths to imported modules."""
    tree: Dict[str, Set[str]] = {}
    for path in py_files:
        relative = str(path.relative_to(root))
        tree[relative] = parse_imports(path)
    return tree


def module_name_from_path(path: Path) -> str:
    """Convert *path* to a dotted module name relative to project root."""
    parts = list(path.with_suffix("").parts)
    return ".".join(parts)


def collect_local_modules(py_files: Iterable[Path], root: Path) -> Set[str]:
    """Return a set of possible local module names for the project."""
    modules: Set[str] = set()
    for f in py_files:
        rel = f.relative_to(root)
        mod = module_name_from_path(rel)
        parts = mod.split(".")
        for i in range(1, len(parts) + 1):
            modules.add(".".join(parts[:i]))
        if rel.name == "__init__.py" and parts:
            modules.add(".".join(parts[:-1]))
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
    """Generate and save a dependency graph of imports."""
    parser = argparse.ArgumentParser(description="Build import graph")
    parser.add_argument(
        "--output",
        default="import_graph.png",
        help="Output PNG file",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(".").resolve()
    py_files = find_py_files(root)
    tree = build_import_tree(py_files, root)
    local_modules = collect_local_modules(py_files, root)

    dot = Digraph("import_graph", format="png")

    added_nodes: Set[str] = set()

    for file_path, imports in tree.items():
        if file_path not in added_nodes:
            dot.node(
                file_path,
                label=file_path,
                shape="box",
                style="filled",
                color="lightblue",
            )
            added_nodes.add(file_path)

        for module in sorted(imports):
            if module not in added_nodes:
                if is_local(module, local_modules):
                    color = "blue"
                elif is_stdlib(module):
                    color = "gray"
                else:
                    color = "green"
                dot.node(
                    module,
                    label=module,
                    shape="ellipse",
                    style="filled",
                    color=color,
                )
                added_nodes.add(module)

            dot.edge(file_path, module)

    output_file = Path(args.output)
    dot.render(
        output_file.stem,
        directory=str(output_file.parent) if output_file.parent != Path('') else None,
        cleanup=True,
    )


if __name__ == "__main__":
    main()
