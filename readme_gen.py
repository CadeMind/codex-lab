"""Generate README.md based on project code structure and statistics."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Iterable, List, Dict

from import_map import find_py_files, build_import_tree, format_markdown
from project_doc_gen import module_name
from code_stats import analyze_file


def gather_module_descriptions(py_files: Iterable[Path], root: Path) -> List[str]:
    """Return list of lines describing modules with their first docstring line."""
    lines: List[str] = []
    for path in py_files:
        mod = module_name(path, root)
        if not mod:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            doc = ast.get_docstring(tree)
            if doc:
                desc = doc.splitlines()[0]
            else:
                desc = "(no description)"
        except SyntaxError:
            desc = "(syntax error)"
        lines.append(f"- **{mod}** - {desc}")
    return lines


def gather_stats(py_files: Iterable[Path]) -> Dict[str, int]:
    """Aggregate statistics over *py_files* using analyze_file."""
    stats = {
        "files": 0,
        "lines": 0,
        "defs": 0,
        "classes": 0,
    }
    for path in py_files:
        file_stats = analyze_file(path)
        stats["files"] += 1
        stats["lines"] += file_stats["lines"]
        stats["defs"] += file_stats["defs"]
        stats["classes"] += file_stats["classes"]
    return stats


def build_description(root: Path) -> str:
    parts = []
    if (root / "main.py").exists():
        parts.append("contains a `main.py` entry point")
    if (root / "__init__.py").exists():
        parts.append("is a Python package")
    if (root / "setup.py").exists():
        parts.append("uses `setup.py` for installation")
    if not parts:
        return "Python project"
    return "This project " + ", ".join(parts) + "."


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate README.md")
    parser.add_argument("--path", default=".", help="Project directory")
    parser.add_argument(
        "--output", default="README.md", help="Output README file"
    )
    args = parser.parse_args(argv if argv is not None else None)

    root = Path(args.path).resolve()
    py_files = find_py_files(root)
    tree = build_import_tree(py_files, root)
    import_md = format_markdown(tree)
    modules_md = "\n".join(gather_module_descriptions(py_files, root))
    stats = gather_stats(py_files)

    description = build_description(root)
    project_name = root.name

    lines = [f"# {project_name}", "", description, ""]

    if modules_md:
        lines += ["## Modules", modules_md, ""]

    lines += ["## Architecture", import_md, ""]

    lines += [
        "## Code Statistics",
        f"- files: {stats['files']}",
        f"- total lines: {stats['lines']}",
        f"- functions: {stats['defs']}",
        f"- classes: {stats['classes']}",
        "",
    ]

    if (root / "main.py").exists():
        lines += ["## How to run", "```bash", "python main.py", "```", ""]

    Path(args.output).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
