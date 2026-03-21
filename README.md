# JCatch

JAV video metadata fetcher and organizer.

## Features

- Extract movie numbers from video file paths
- Fetch metadata from configurable scrapers
- Download cover images and screenshots
- Generate NFO XML files for media center compatibility
- Extensible scraper architecture - easy to add new data sources

## Installation

```bash
pip install -e .
```

Or using requirements:

```bash
pip install -r requirements.txt
```

## Usage

```bash
jcatch /path/to/video.mp4 -o output
```

## Project Structure

```
jcatch/
├── jcatch/
│   ├── core/           # Core business logic
│   ├── scrapers/       # Scraper implementations
│   ├── utils/          # Utility functions
│   └── main.py         # CLI entry point
└── tests/              # Unit tests
```

## Adding a New Scraper

To add support for a new data source, implement the `BaseScraper` interface:

```python
from jcatch.scrapers.base import BaseScraper
from jcatch.core.models import MovieMetadata

class MyScraper(BaseScraper):
    def parse_number(self, filepath: str) -> str:
        # Extract movie number from filepath
        ...

    def fetch_metadata(self, number: str) -> MovieMetadata:
        # Fetch and return metadata
        ...

    def download_image(self, url: str, save_path: str) -> None:
        # Download image
        ...
```

Then configure it in `main.py`.

## Development

Run tests:

```bash
pytest
```

## TODO

- Implement actual scraper logic
- Add error handling and retry mechanism
- Add logging
- Add more comprehensive tests
