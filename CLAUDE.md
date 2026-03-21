# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in development mode
pip install -e .

# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=jcatch
```

## Architecture

JCatch uses a **strategy pattern** with dependency injection for the scraper layer. The key insight is that `MediaProcessor` doesn't know *how* to fetch metadata—it only knows *that* it can ask a scraper for it.

### Data Flow

```
Video Path
    ↓
[BaseScraper.parse_number] → Movie Number (e.g., "FSDSS-549")
    ↓
[BaseScraper.fetch_metadata] → MovieMetadata (Pydantic model)
    ↓
[MediaProcessor.process]
    ├─→ Copy video to output/{number}/
    ├─→ Download images (poster, thumb, fanart, extrafanart/)
    └─→ Generate {number}.nfo (XML)
```

### Layer Responsibilities

| Layer | File | Purpose |
|-------|------|---------|
| Core | `core/models.py` | `MovieMetadata` - single source of truth for all data |
| Core | `core/processor.py` | Orchestrates workflow, delegates to scraper |
| Core | `core/nfo.py` | XML generation from `MovieMetadata` |
| Scrapers | `scrapers/base.py` | `BaseScraper` abstract interface |
| Scrapers | `scrapers/*.py` | Concrete implementations (implement `BaseScraper`) |
| Utils | `utils/file.py` | `extract_number_from_path()` - common number extraction logic |
| Utils | `utils/download.py` | `download_image()` - generic HTTP download |

### Extensibility

To add a new data source, implement `BaseScraper`:

```python
from jcatch.scrapers.base import BaseScraper
from jcatch.core.models import MovieMetadata

class MyScraper(BaseScraper):
    def parse_number(self, filepath: str) -> str:
        # Extract number from filepath
        ...

    def fetch_metadata(self, number: str) -> MovieMetadata:
        # Fetch and return MovieMetadata with all fields
        ...

    def download_image(self, url: str, save_path: str) -> None:
        # Download image to save_path
        ...
```

Then configure in `main.py`'s `get_scraper()` function.

### Key Design Decisions

1. **Scraper injection**: `MediaProcessor.__init__` takes a `BaseScraper`, allowing runtime selection of data source.

2. **Unified data model**: All scrapers must return `MovieMetadata`. The NFO generator only reads from this model, not the scraper directly.

3. **Filename conventions**: Output files use `{number}-*.jpg` format (e.g., `FSDSS-549-poster.jpg`). The NFO generator uses these same filenames in its XML output.

4. **NFO structure**: Always generates exactly 2 `<tag>` and 2 `<genre>` elements (even if empty) to match reference format.

5. **Number extraction defaults to uppercase**: Patterns like `[A-Z]+-\d+` are expected. Implement custom `parse_number` if your files use different naming.
