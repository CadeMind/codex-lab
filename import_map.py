import os
import ast
from collections import defaultdict


def find_py_files(root):
    py_files = []
    for current_root, _, files in os.walk(root):
        for name in files:
            if name.endswith('.py'):
                py_files.append(os.path.join(current_root, name))
    return py_files


def parse_imports(file_path):
    imports = defaultdict(list)
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=file_path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.name].append(None)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports[module].append(alias.name)
    return imports


def build_import_tree(py_files, root):
    tree = {}
    for path in py_files:
        relative = os.path.relpath(path, root)
        tree[relative] = parse_imports(path)
    return tree


def format_markdown(tree):
    if not tree:
        return "No Python files found."
    lines = []
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
                module = ''
            for name in names:
                if name:
                    lines.append(f"    - {name}")
                else:
                    lines.append(f"  - `import {module}`")
    return '\n'.join(lines)


if __name__ == '__main__':
    root = os.getcwd()
    py_files = find_py_files(root)
    tree = build_import_tree(py_files, root)
    md_graph = format_markdown(tree)
    print(md_graph)
