# JCatch

JAV video metadata fetcher and organizer.

## Features

- Extract movie numbers from video file paths
- Fetch metadata from configurable scrapers
- Download cover images and screenshots
- Generate NFO XML files for media center compatibility
- Extensible scraper architecture - easy to add new data sources

## Installation

### Development Mode

```bash
# Install in editable mode for development
pip install -e .
```

### From Built Package

```bash
# Build the package
pip install build
python -m build

# Install from built wheel
pip install dist/jcatch-0.1.0-py3-none-any.whl
```

### From PyPI (after publishing)

```bash
pip install jcatch
```

## Packaging & Publishing

To build and publish the package to PyPI:

```bash
# 1. Install build tools
pip install build twine

# 2. Build source and wheel distributions
python -m build

# 3. Upload to PyPI
twine upload dist/*
```

## PyInstaller 打包

打包为独立可执行文件（包含所有依赖）：

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 打包（使用配置文件 jcatch.spec）
pyinstaller jcatch.spec

# 3. 可执行文件位置
# dist/jcatch
```

打包后可直接运行：
```bash
./dist/jcatch
./dist/jcatch /path/to/video.mp4 -o output
```

**打包配置说明：**

打包配置保存在 `jcatch.spec` 文件中，包含 Selenium 等依赖的隐藏导入设置。

> **注意**：首次运行打包后的可执行文件时，webdriver-manager 会自动下载 ChromeDriver 到用户目录。

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
