from __future__ import annotations

from pathlib import Path
from graphviz import Digraph

from import_map import build_import_tree, find_py_files


def main() -> None:
    """Generate and save a dependency graph of imports."""
    root = Path('.').resolve()
    py_files = find_py_files(root)
    tree = build_import_tree(py_files, root)

    dot = Digraph('import_graph', format='png')

    # Add nodes for each python file and its imports
    for file_path, imports in tree.items():
        dot.node(file_path, label=file_path)
        for module in imports:
            dot.node(module, label=module)
            dot.edge(file_path, module)

    dot.render('import_graph', cleanup=True)


if __name__ == '__main__':
    main()
