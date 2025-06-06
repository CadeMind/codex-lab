import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import requests



def run_project_map(mode: str, root: Path, output: Path) -> None:
    """Execute project_map.py with *mode* and write to *output*."""
    cmd = [
        sys.executable,
        str(Path(__file__).with_name("project_map.py")),
        "--mode",
        mode,
        "--path",
        str(root),
        "--output",
        str(output),
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def update_readme(root: Path, report_dir: Path, stats: dict) -> None:
    """Insert a summary section into README.md."""
    readme_path = root / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
    else:
        content = f"# {root.name}\n"

    summary_lines = [
        "## Codex Report",
        "",
        f"- files scanned: {stats.get('files', 0)}",
        f"- total lines: {stats.get('total_lines', 0)}",
        f"- import statements: {stats.get('imports', 0)}",
        f"- from-imports: {stats.get('from_imports', 0)}",
        "",
        f"[Project documentation]({report_dir/'project_structure.md'})",
        f"![Import graph]({report_dir/'import_tree.png'})",
        "",
    ]
    summary = "\n".join(summary_lines)

    marker = "## Codex Report"
    if marker in content:
        pre = content.split(marker)[0].rstrip()
        content = pre + "\n\n" + summary
    else:
        content = content.rstrip() + "\n\n" + summary

    readme_path.write_text(content, encoding="utf-8")
    print("README.md updated")


def prepare_pages(root: Path, report_dir: Path) -> None:
    """Copy report to ./public for GitHub Pages."""
    public = root / "public"
    if public.exists():
        shutil.rmtree(public)
    shutil.copytree(report_dir, public)
    print(f"Copied report to {public}")


def generate_badges(root: Path, stats: dict) -> None:
    badges_dir = root / "badges"
    badges_dir.mkdir(parents=True, exist_ok=True)
    line_badge = f"https://img.shields.io/badge/lines-{stats.get('total_lines', 0)}-blue.svg"
    imports_total = stats.get("imports", 0) + stats.get("from_imports", 0)
    imports_badge = (
        f"https://img.shields.io/badge/imports-{imports_total}-blue.svg"
    )
    for url, name in (
        (line_badge, "lines.svg"),
        (imports_badge, "imports.svg"),
    ):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            (badges_dir / name).write_bytes(resp.content)
            print(f"Badge saved: {name}")
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to fetch badge {url}: {exc}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run project map tasks for CI")
    parser.add_argument("--path", default=".", help="Project directory")
    parser.add_argument("--update-readme", action="store_true", help="Update README.md")
    parser.add_argument("--gh-pages", action="store_true", help="Prepare GitHub Pages artifact")
    parser.add_argument("--badge", action="store_true", help="Generate SVG badges")
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.path).resolve()
    report_dir = root / "codex_report"
    report_dir.mkdir(parents=True, exist_ok=True)

    doc_file = report_dir / "project_structure.md"
    graph_file = report_dir / "import_tree.png"
    stats_file = report_dir / "stats.json"

    run_project_map("doc", root, doc_file)
    run_project_map("graph", root, graph_file)
    run_project_map("stats", root, stats_file)

    if stats_file.exists():
        stats = json.loads(stats_file.read_text(encoding="utf-8"))
    else:
        stats = {}

    if args.update_readme:
        update_readme(root, report_dir.relative_to(root), stats)

    if args.gh_pages:
        prepare_pages(root, report_dir)

    if args.badge:
        generate_badges(root, stats)


if __name__ == "__main__":
    main()
