"""Unified CLI interface for project utilities."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Iterable


def call_module(module_name: str, args: list[str]) -> None:
    """Import *module_name* safely and execute its ``main`` function with *args*."""
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        if module_name == "import_graph_builder" and (
            getattr(exc, "name", "") == "graphviz" or "graphviz" in str(exc)
        ):
            print(
                "Error: 'graphviz' package is required for graph mode.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"Error importing {module_name}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not hasattr(module, "main"):
        print(f"Module {module_name} has no main()", file=sys.stderr)
        sys.exit(1)

    module.main(args)


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Project helper CLI")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["doc", "graph", "stats"],
        help="Operation mode",
    )
    parser.add_argument("--path", default=".", help="Project directory")
    parser.add_argument("--output", help="Optional output file")
    parsed = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(parsed.path).resolve()

    if parsed.mode == "doc":
        args = [str(root)]
        if parsed.output:
            args += ["--output", parsed.output]
        call_module("project_doc_gen", args)
    elif parsed.mode == "graph":
        args = [str(root)]
        if parsed.output:
            args += ["--output", parsed.output]
        call_module("import_graph_builder", args)
    else:  # stats
        args = ["--path", str(root)]
        if parsed.output:
            args += ["--output", parsed.output]
        call_module("code_stats", args)


if __name__ == "__main__":
    main()