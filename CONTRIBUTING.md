# Codex-Lab Module Guidelines

The following rules standardize how analytic and generative modules are added to the project. All contributions **must** adhere to these requirements.

## 1. Standalone CLI Modules

Each new script (e.g. `html_reporter.py`, `readme_gen.py`, `ci_runner.py`, `todo_scanner.py`, `ai_docgen.py`) must be implemented as an independent CLI component with a mandatory entry point:

```python
def main(argv: list[str]) -> None:
    ...
```

The function handles argument parsing and performs the module's main work without returning a value.

## 2. Unified Invocation through `project_map.py`

All modules are executed via `project_map.py` using the `--mode` flag. The following modes are reserved:

- `--mode html`
- `--mode readme`
- `--mode ci`
- `--mode todo`
- `--mode ai-doc`

## 3. Centralized Routing

`project_map.py` must route to modules using `call_module("module_name", args)` and print a clear error when a module is unavailable.

## 4. Module Requirements

New modules **must**:

- Accept `--path` and `--output` arguments where relevant.
- Run without any interactive UI dependencies.
- Avoid side effects unless explicitly requested (e.g. only push to GitHub when `--gh-pages` is provided).

## 5. Plugin Architecture (Optional)

As a stricter alternative to `--mode`, a plugin system can be implemented in `codex_core.py`. Modules register with:

```python
@codex_plugin("name")
```

The project CLI then discovers and executes plugins dynamically.

Any contribution that deviates from these rules must be discussed and justified in advance.
