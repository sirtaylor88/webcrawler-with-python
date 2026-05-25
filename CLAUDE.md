# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package Management

This project uses `uv`. Always use `uv` for installing dependencies and running commands.

```bash
uv sync           # install all dependencies including dev
uv run <command>  # run a command in the project virtualenv
```

## Common Commands

```bash
# Run all tests
uv run pytest tests/

# Run a single test
uv run pytest tests/test_crawl.py::test_normalize_url

# Run tests with coverage
uv run pytest --cov=. tests/

# Type checking
uv run mypy .

# Linting
uv run pylint crawl.py

# Security scan
uv run bandit -r .

# Build HTML docs (output: docs/_build/html)
uv run sphinx-build -b html docs docs/_build/html

# Live-reload docs server
uv run sphinx-autobuild docs docs/_build/html
```

## Architecture

The project is a web crawler built around HTML extraction utilities in `crawl.py`.

- **`crawl.py`** — core parsing module. Exposes `extract_page_data()` which returns a `PageData` TypedDict with: url, heading (first `h1`/`h2`), first paragraph (preferring content inside `<main>`), outgoing links, and image URLs. Relative URLs are resolved against `base_url` at extraction time.
- **`main.py`** — entry point stub (not yet wired to the crawler logic).
- **`tests/test_crawl.py`** — pytest tests for every function in `crawl.py`.
- **`docs/`** — Sphinx documentation. `conf.py` uses `autodoc` + `napoleon` (Google-style) + `viewcode`. `api.rst` documents `PageData` via `autoclass` (without `:members:`, so Napoleon renders the `Attributes:` section inline without duplicate index entries) and each function via `autofunction`.

The crawler uses `requests` for synchronous HTTP and `aiohttp` for async fetching (neither is wired up yet — only the HTML parsing layer exists).
