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

# 2. 打包为单个可执行文件
pyinstaller --onefile --name jcatch jcatch/main.py

# 或者打包为目录（推荐，启动更快）
pyinstaller --onedir --name jcatch jcatch/main.py

# 3. 可执行文件位置
# 单文件模式: dist/jcatch
# 目录模式: dist/jcatch/jcatch
```

打包后可直接运行：
```bash
./dist/jcatch
./dist/jcatch -v /path/to/video.mp4 -o output
```

**打包参数说明：**

| 参数 | 说明 |
|------|------|
| `--onefile` | 打包为单个可执行文件（体积较大，启动较慢） |
| `--onedir` | 打包为目录（推荐，启动更快） |
| `--name jcatch` | 指定可执行文件名称 |

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
