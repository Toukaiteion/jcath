# JCatch

JAV video metadata fetcher and organizer.

## Features

- Extract movie numbers from video file paths
- Fetch metadata from configurable scrapers
- Download cover images and screenshots
- Generate NFO XML files for media center compatibility
- Extensible scraper architecture - easy to add new data sources

## Installation

### 使用虚拟环境（推荐）

```bash
# 1. 创建虚拟环境
python3 -m venv venv

# 2. 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 3. 安装依赖（开发模式）
pip install -e .
```

激活虚拟环境后，所有后续命令都应在虚拟环境中执行。

### Development Mode

```bash
# 激活虚拟环境后
source venv/bin/activate

# 安装可编辑模式
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

### Linux / macOS

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 安装 PyInstaller
pip install pyinstaller

# 3. 打包
pyinstaller jcatch.spec

# 4. 运行可执行文件
./dist/jcatch
./dist/jcatch /path/to/video.mp4 -o output
```

### Windows

```powershell
# 1. 激活虚拟环境
venv\Scripts\activate

# 2. 安装 PyInstaller
pip install pyinstaller

# 3. 打包
pyinstaller jcatch.spec

# 4. 运行可执行文件
.\dist\jcatch.exe
.\dist\jcatch.exe C:\path\to\video.mp4 -o output
```

**打包配置说明：**

打包配置保存在 `jcatch.spec` 文件中，包含 Selenium 等依赖的隐藏导入设置。

> **注意**：首次运行打包后的可执行文件时，webdriver-manager 会自动下载 ChromeDriver 到用户目录。

## Usage

```bash
# 基本用法（headless 模式，默认）
jcatch /path/to/video.mp4 -o output

# 显示浏览器窗口（非 headless 模式）
jcatch /path/to/video.mp4 --no-headless
jcatch /path/to/video.mp4 -nh

# 仅获取元数据（不处理视频）
jcatch -k SSNI-443

# 压缩输出目录
jcatch -k SSNI-443 -z

# 清理模式：成功后删除源视频，失败时清理下载的文件
jcatch /path/to/video.mp4 --clean
jcatch /path/to/video.mp4 -c
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
