 codex-lab
StartSandBox

## Import Graph

Run `import_graph.py` to build a dependency graph for the project.

```bash
python import_graph.py --output graph.png --html import_graph.html
```

This command creates a PNG image and an interactive HTML file named
`import_graph.html` with the graph rendered using **pyvis**.

## Project Structure Doc

Run `project_doc_gen.py` to generate a Markdown file summarizing imports.

```bash
python project_doc_gen.py --output project_structure.md
```

## Contribution Guidelines

For detailed instructions on adding new CLI modules and integrating them with `project_map.py`, see [CONTRIBUTING.md](CONTRIBUTING.md).
