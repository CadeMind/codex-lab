import argparse
import base64
from pathlib import Path
from typing import Iterable, Dict, List, Set

from code_stats import find_py_files, analyze_file
from import_map import parse_imports
from project_doc_gen import collect_local_modules, is_local, is_stdlib


CSS = """
body { font-family: Arial, sans-serif; padding: 20px; }
h1 { text-align: center; }
section { margin-bottom: 40px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 4px 8px; }
th { background-color: #f0f0f0; }
"""


def gather_statistics(root: Path) -> Dict[str, object]:
    py_files = find_py_files(root)
    if not py_files:
        return {}

    summary = {
        "files": len(py_files),
        "total_lines": 0,
        "blank_lines": 0,
        "comment_lines": 0,
        "defs": 0,
        "classes": 0,
        "imports": 0,
        "from_imports": 0,
    }
    file_stats: List[Dict[str, object]] = []

    for path in py_files:
        stats = analyze_file(path)
        summary["total_lines"] += stats["lines"]
        summary["blank_lines"] += stats["blank"]
        summary["comment_lines"] += stats["comments"]
        summary["defs"] += stats["defs"]
        summary["classes"] += stats["classes"]
        summary["imports"] += stats["imports"]
        summary["from_imports"] += stats["from_imports"]
        file_stats.append(
            {
                "file": str(path.relative_to(root)),
                "lines": stats["lines"],
                "functions": stats["defs"],
                "classes": stats["classes"],
            }
        )

    local_modules = collect_local_modules(py_files, root)
    modules: Dict[str, Set[str]] = {"stdlib": set(), "external": set(), "local": set()}
    for path in py_files:
        try:
            imports = parse_imports(path)
        except SyntaxError:
            continue
        for module in imports:
            if is_local(module, local_modules):
                modules["local"].add(module)
            elif is_stdlib(module):
                modules["stdlib"].add(module)
            else:
                modules["external"].add(module)

    summary["total_imports"] = (
        len(modules["stdlib"]) + len(modules["external"]) + len(modules["local"])
    )
    return {"summary": summary, "files": file_stats, "modules": modules}


def embed_image(path: Path) -> str | None:
    if not path.is_file():
        return None
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def build_html(data: Dict[str, object], img_src: str | None) -> str:
    summary = data["summary"]
    files = data["files"]
    modules = data["modules"]
    chart_data = [len(modules["stdlib"]), len(modules["external"]), len(modules["local"])]

    html = ["<!DOCTYPE html>", "<html lang='en'>", "<head>", "<meta charset='UTF-8'>",
            "<title>Project Report</title>", f"<style>{CSS}</style>",
            "<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>", "</head>", "<body>", "<h1>Project Report</h1>"]

    html.append("<section><h2>Overview</h2><table>")
    for key, label in (
        ("files", "Files"),
        ("total_lines", "Total lines"),
        ("imports", "Import statements"),
        ("from_imports", "From-imports"),
    ):
        html.append(f"<tr><th>{label}</th><td>{summary[key]}</td></tr>")
    html.append("</table></section>")

    if img_src:
        html.append("<section><h2>Import Graph</h2>")
        html.append(f"<img src='{img_src}' alt='Import graph' style='max-width:100%;'>")
        html.append("</section>")

    html.append("<section><h2>Files</h2><table><tr><th>File</th><th>Lines</th><th>Functions</th><th>Classes</th></tr>")
    for stat in files:
        html.append(
            f"<tr><td>{stat['file']}</td><td>{stat['lines']}</td>"
            f"<td>{stat['functions']}</td><td>{stat['classes']}</td></tr>"
        )
    html.append("</table></section>")

    html.append("<section><h2>Modules</h2>")
    for cat in ("stdlib", "external", "local"):
        html.append(f"<h3>{cat.title()}</h3><ul>")
        for mod in sorted(modules[cat]):
            html.append(f"<li>{mod}</li>")
        html.append("</ul>")
    html.append("</section>")

    html.append("<section><h2>Module Distribution</h2><canvas id='modulesChart'></canvas>")
    html.append("<script>\nconst ctx=document.getElementById('modulesChart').getContext('2d');\nnew Chart(ctx,{type:'pie',data:{labels:['stdlib','external','local'],datasets:[{data:[" + ",".join(map(str, chart_data)) + "],backgroundColor:['gray','green','blue']}]},options:{responsive:true}});\n</script>")
    html.append("</section>")

    html.append("</body></html>")
    return "\n".join(html)


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate HTML project report")
    parser.add_argument("--path", default=".", help="Project directory")
    parser.add_argument(
        "--output", default="report.html", help="Output HTML file"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.path).resolve()
    data = gather_statistics(root)
    if not data:
        print("No Python files found.")
        return
    img_src = embed_image(root / "import_tree.png")
    html = build_html(data, img_src)
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
