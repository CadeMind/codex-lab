# Codex-Lab

Codex-Lab is a sandbox collection of command line utilities for exploring Python projects. These tools build import graphs, generate documentation and gather basic code statistics. Each script exposes a `main()` entry point so they can be used directly or through the unified `project_map.py` dispatcher.

## Installation

Install the required packages into a virtual environment:

```bash
pip install -r requirements.txt
```

## Import Graph

Create a dependency graph for the project:

```bash
python import_graph.py --output graph.png --html import_graph.html
```

This generates a PNG file and an interactive HTML page rendered with **pyvis**.

## Project Structure Doc

Generate a Markdown overview of all imports:

```bash
python project_doc_gen.py --output project_structure.md
```

## Code Statistics

Collect statistics about the Python files:

```bash
python code_stats.py --path . --output stats.json
```

## HTML Reporter

Combine statistics with an optional import graph into a single HTML report:

```bash
python html_reporter.py --path . --output report.html
```

## README Generator

Automatically build a README based on modules and statistics:

```bash
python readme_gen.py --path . --output README.md
```

## TODO Scanner

Find `TODO`/`FIXME` comments in the project:

```bash
python todo_scanner.py --path . --output todos.md
```

## AI Documentation

Generate simple documentation or `.pyi` stubs using AST parsing:

```bash
python ai_docgen.py --path . --output docs --format markdown
```

## Unified CLI

Most utilities can be invoked via `project_map.py` using the `--mode` option:

```bash
python project_map.py --mode doc   --path . --output project_structure.md
python project_map.py --mode graph --path . --output graph.png
python project_map.py --mode stats --path . --output stats.json
```

## CI Runner

`ci_runner.py` runs the above tasks and can update the README, prepare a `public/` directory for GitHub Pages and generate badges:

```bash
python ci_runner.py --update-readme --gh-pages --badge
```

## Contribution Guidelines

For details on adding new modules and integrating them with `project_map.py` see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the terms of the MIT License. See [LICENSE](LICENSE) for details.
