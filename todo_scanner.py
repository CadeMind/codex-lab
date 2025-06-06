#!/usr/bin/env python3
"""Scan project for TODO/FIXME/BUG/HACK comments."""

import argparse
import os
import re
import json
import tokenize
from collections import defaultdict


PATTERN = re.compile(r"\b(TODO|FIXME|BUG|HACK)\b", re.IGNORECASE)


def scan_file(path: str):
    """Return list of tasks found in file."""
    tasks = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.splitlines()
        with open(path, "r", encoding="utf-8") as f:
            tokens = tokenize.generate_tokens(f.readline)
            for toknum, tokval, start, _, _ in tokens:
                if toknum == tokenize.COMMENT:
                    match = PATTERN.search(tokval)
                    if match:
                        lineno = start[0]
                        before = lines[lineno - 2] if lineno - 2 >= 0 else ""
                        after = lines[lineno] if lineno < len(lines) else ""
                        tasks.append(
                            {
                                "line_number": lineno,
                                "keyword": match.group(1).upper(),
                                "line": lines[lineno - 1],
                                "before": before,
                                "after": after,
                            }
                        )
    except Exception:
        return tasks
    return tasks


def scan_dir(path: str):
    """Scan directory for .py files."""
    issues = defaultdict(list)
    for root, _, files in os.walk(path):
        for name in files:
            if name.endswith(".py"):
                file_path = os.path.join(root, name)
                tasks = scan_file(file_path)
                if tasks:
                    issues[file_path] = tasks
    return issues


def format_markdown(issues):
    lines = ["# Known Issues / Backlog", ""]
    for file in sorted(issues.keys()):
        lines.append(f"## {file}")
        for t in issues[file]:
            marker = "✅ [ ]" if t["keyword"] == "TODO" else "❌"
            lines.append(
                f"- {marker} {t['line'].strip()} (line {t['line_number']})"
            )
            context = "\n".join(
                filter(None, [t.get('before'), t['line'], t.get('after')])
            )
            lines.append("```")
            lines.append(context)
            lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Scan project for TODO comments.")
    parser.add_argument("--path", default=".", help="directory to scan")
    parser.add_argument(
        "--output",
        default="todos.md",
        help="output file path (use .json extension for JSON)",
    )
    args = parser.parse_args(argv if argv is not None else None)

    issues = scan_dir(args.path)

    if args.output.lower().endswith(".json"):
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(issues, f, indent=2, ensure_ascii=False)
    else:
        markdown = format_markdown(issues)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown)


if __name__ == "__main__":
    main()
