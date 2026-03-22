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
    ├─→ Generate {number}.nfo (XML)
    └─→ Validate output integrity before copy
```

### Layer Responsibilities

| Layer | File | Purpose |
|-------|------|---------|
| Core | `core/models.py` | `MovieMetadata` - single source of truth for all data |
| Core | `core/models.py` | `ImageUrl` - URL with download headers |
| Core | `core/processor.py` | Orchestrates workflow, delegates to scraper, validates output |
| Core | `core/nfo.py` | XML generation from `MovieMetadata` |
| Scrapers | `scrapers/base.py` | `BaseScraper` abstract interface |
| Scrapers | `scrapers/*.py` | Concrete implementations (implement `BaseScraper`) |
| Scrapers | `scrapers/decorators/*.py` | Decorator pattern for scraper composition |
| Utils | `utils/downloader.py` | `ImageDownloader` - generic HTTP download with headers |

### Decorator Pattern

Scrapers can be composed using decorators to mix-and-match data sources:

```python
from jcatch.scrapers import (
    JavBusScraper,
    MetadataDecorator,
    PosterDecorator,
    FanartDecorator,
)

# Chain: metadata from JavBus, fanart from DMM, poster from JavWine
base = JavBusScraper()
with_metadata = MetadataDecorator(base, MissAvWsScraper())
with_fanart = FanartDecorator(with_metadata, DMMScraper())
scraper = PosterDecorator(with_fanart, JavWineScraper())
```

- `MetadataDecorator`: Fills empty fields (title, studio, year, outline, genres, actors) from backup scraper
- `PosterDecorator`: Replaces poster URL from another scraper (with chain retry on empty)
- `FanartDecorator`: Replaces fanart/thumb URLs (logs empty, next decorator retries)

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
```

Then configure in `main.py`'s `get_scraper()` function.

### Key Design Decisions

1. **Scraper injection**: `MediaProcessor.__init__` takes a `BaseScraper`, allowing runtime selection of data source.

2. **Unified data model**: All scrapers must return `MovieMetadata`. The NFO generator only reads from this model, not the scraper directly.

3. **ImageUrl with headers**: Images are downloaded using `ImageUrl(url, headers)`, allowing per-source request customization (e.g., referer for JavBus).

4. **Filename conventions**: Output files use `{number}-*.jpg` format (e.g., `FSDSS-549-poster.jpg`). The NFO generator uses these same filenames in its XML output.

5. **NFO structure**: Always generates exactly 2 `<tag>` and 2 `<genre>` elements (even if empty) to match reference format.

6. **Number extraction defaults to uppercase**: Patterns like `[A-Z]+-\d+` are expected. Implement custom `parse_number` if your files use different naming.

7. **Chrome configuration**: Selenium-based scrapers (JavBus) read Chrome binary path from `.env` via `JCATCH_CHROME_PATH` or use platform defaults.

8. **Data validation**: `MediaProcessor._validate_output()` checks required files exist and NFO contains required tag values before copying video. On failure, cleans up the output directory.
