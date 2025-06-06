"""Generate a Markdown overview of project imports grouped by type."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Mapping, Set

from import_map import find_py_files, parse_imports

# We reuse helper logic from import_graph but reimplement minimal pieces to
# avoid depending on its incomplete functions.


def module_name(path: Path, root: Path) -> str:
    """Return dotted module name for *path* relative to *root*."""
    rel = path.relative_to(root)
    if rel.name == "__init__.py":
        parts = rel.parent.parts
    else:
        parts = rel.with_suffix("").parts
    return ".".join(parts)


def collect_local_modules(py_files: Iterable[Path], root: Path) -> Set[str]:
    """Return a set of dotted module names considered local to the project."""
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


def format_entry(module: str, names: List[str | None], indent: str = "") -> List[str]:
    """Return formatted lines for a single module entry."""
    lines: List[str] = []
    import_items = [n for n in names if n is None or str(n).startswith("as ")]
    from_items = [n for n in names if n not in import_items]

    for item in import_items:
        if item is None:
            lines.append(f"{indent}- `import {module}`")
        else:
            alias = str(item)[3:]
            lines.append(f"{indent}- `import {module} as {alias}`")

    if from_items:
        lines.append(f"{indent}- `{module}`:")
        for name in from_items:
            lines.append(f"{indent}  - {name}")
    return lines


def format_markdown(
    tree: Mapping[str, Mapping[str, List[str | None]]],
    local_modules: Set[str],
) -> tuple[str, Dict[str, int]]:
    """Return Markdown representation of the import tree and counts."""
    counts = {"stdlib": 0, "external": 0, "local": 0}
    total_imports = 0
    lines: List[str] = []

    for file_path in sorted(tree):
        lines.append(f"- **{file_path}**")
        imports = tree[file_path]
        if not imports:
            lines.append("  - (no imports)")
            continue

        groups: Dict[str, List[tuple[str, List[str | None]]]] = {
            "stdlib": [],
            "external": [],
            "local": [],
        }
        for module, names in sorted(imports.items()):
            if is_local(module, local_modules):
                group = "local"
            elif is_stdlib(module):
                group = "stdlib"
            else:
                group = "external"
            groups[group].append((module, names))
            counts[group] += 1
            total_imports += 1

        for group in ("stdlib", "external", "local"):
            entries = groups[group]
            if not entries:
                continue
            lines.append(f"  - **{group}**")
            for module, names in entries:
                lines.extend(format_entry(module, names, indent="    "))

    md = "\n".join(lines) if lines else "No Python files found."
    counts["total_imports"] = total_imports
    return md, counts


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate project structure")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root directory to scan",
    )
    parser.add_argument(
        "--output",
        default="project_structure.md",
        help="Output Markdown file",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.path).resolve()
    py_files = find_py_files(root)

    tree: Dict[str, Dict[str, List[str | None]]] = {}
    for path in py_files:
        try:
            imports = parse_imports(path)
        except SyntaxError:
            # Skip files that fail to parse
            continue
        tree[str(path.relative_to(root))] = imports
    local_modules = collect_local_modules(py_files, root)
    md, counts = format_markdown(tree, local_modules)

    output_path = Path(args.output)
    output_path.write_text(md, encoding="utf-8")

    print(f"Total files: {len(py_files)}")
    print(f"Total imports: {counts['total_imports']}")
    print(
        f"stdlib: {counts['stdlib']}, external: {counts['external']}, local: {counts['local']}"
    )


if __name__ == "__main__":
    main()
