# web-crawler-with-python

> A Python web crawler that fetches pages and extracts structured data from HTML.

![Python](https://img.shields.io/badge/python-3.12.9+-blue)
![uv](https://img.shields.io/badge/package%20manager-uv-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- Extract headings, first paragraphs, outgoing links, and image URLs from any HTML page
- Relative URLs resolved against a given base URL automatically
- Async-ready: ships with both `requests` (sync) and `aiohttp` (async) dependencies

## Requirements

- Python 3.12.9+
- [uv](https://github.com/astral-sh/uv)

## Setup

```bash
uv sync
```

## Usage

```python
from crawl import extract_page_data

page = extract_page_data(html_string, "https://example.com")
print(page["heading"])           # first h1/h2 text
print(page["first_paragraph"])   # first <p> text (prefers <main>)
print(page["outgoing_links"])    # list of resolved URLs
print(page["image_urls"])        # list of resolved image sources
```

## Development

| Command | Description |
|---|---|
| `uv run pytest tests/` | Run all tests |
| `uv run pytest --cov=. tests/` | Run tests with coverage |
| `uv run mypy .` | Type checking |
| `uv run pylint crawl.py` | Linting |
| `uv run bandit -r .` | Security scan |
| `uv run sphinx-build -b html docs docs/_build/html` | Build docs |
| `uv run sphinx-autobuild docs docs/_build/html` | Live-reload docs |
