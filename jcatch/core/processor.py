"""Main media processor that orchestrates the workflow."""

from pathlib import Path
import os
import random
import shutil
import time
import zipfile

from xml.etree import ElementTree as ET
from PIL import Image

from jcatch.scrapers.base import BaseScraper
from jcatch.core.models import MovieMetadata, ProcessConfiguration
from jcatch.core.nfo import generate_nfo
from jcatch.utils.downloader import ImageDownloader
from jcatch.utils.file import extract_number_from_path


class MediaProcessor:
    """Process video files and generate complete media directory structure."""

    def __init__(self, scraper: BaseScraper):
        """Initialize processor with a scraper instance.

        Args:
            scraper: Scraper instance for fetching metadata and images
        """
        self.scraper = scraper

    def process(self, config: ProcessConfiguration) -> str:
        """Process a video file and generate complete directory structure.

        Args:
            config: Processing configuration object

        Returns:
            Path to the generated output directory (or zip file if zip_output=True)

        Raises:
            Exception: If processing fails
        """
        video_path = config.video_path
        output_dir = config.output_dir
        delete_source_file = config.delete_source
        metadata_only = config.metadata_only

        # 1. Extract movie number: key has highest priority
        jav_key = getattr(config, 'key', None)
        if jav_key:
            number = str(jav_key).upper()
        elif video_path:
            number = extract_number_from_path(str(video_path))
            if not number:
                raise ValueError(f"Could not extract movie number from: {video_path}")
        else:
            raise ValueError("Either key or video_path must be provided")

        print("1/5 识别到媒体号码: " + number)

        # 2. Fetch metadata from scraper
        print("2/5 开始搜刮媒体源数据")
        metadata = self.scraper.fetch_metadata(number)

        number = metadata.num
        output_path = output_dir / number
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # 3. Download and save images
            print("3/5 开始下载图片资源")
            self._download_images(metadata, output_path, number)

            # 4. Generate NFO file
            print("4/5 开始生成元数据文件.nfo")
            self._generate_nfo(metadata, output_path, number)

            # 5. Validate output integrity
            print("5/5 检查输出数据完整性")
            self._validate_output(output_path, number)

            # Skip video operations in metadata-only mode
            if not metadata_only:
                # Copy video file
                print(f"开始复制媒体文件，从 {video_path} 复制到 {output_path}")
                self._copy_video(video_path, output_path, number)

                # Delete source file if requested
                if delete_source_file and video_path.exists():
                    try:
                        print(f"正在删除源文件: {video_path}")
                        video_path.unlink()
                        print(f"✓ 已删除源文件: {video_path}")
                    except Exception as e:
                        print(f"⚠ 删除源文件失败: {e}")

            # Zip output if requested
            if config.zip_output:
                print("正在压缩输出目录...")
                zip_path = self._zip_output(output_path, number)
                shutil.rmtree(output_path, ignore_errors=True)
                return str(zip_path)

        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"正在删除输出目录: {output_path}")

            if output_path.exists():
                shutil.rmtree(output_path, ignore_errors=True)

            raise Exception(error_msg) from e

        return str(output_path)

    def process_from_params(self, video_path: str | Path, output_dir: str | Path = "output", delete_source: bool = False) -> str:
        """Process with individual parameters (backward compatibility).

        This method maintains backward compatibility with existing code.

        Args:
            video_path: Path to the input video file
            output_dir: Base directory for output (default: "output")
            delete_source: If True, delete the source file after successful processing (default: False)

        Returns:
            Path to the generated output directory
        """
        config = ProcessConfiguration(
            video_path=Path(video_path),
            output_dir=Path(output_dir),
            delete_source=delete_source
        )
        return self.process(config)

    def _copy_video(self, video_path: Path, output_dir: Path, number: str) -> None:
        """Copy video file to output directory.

        Args:
            video_path: Source video file path
            output_dir: Target directory
            number: Movie number for filename
        """
        suffix = video_path.suffix
        output_file = output_dir / f"{number}{suffix}"
        shutil.copy2(video_path, output_file)

    def _download_images(self, metadata: MovieMetadata, output_dir: Path, number: str) -> None:
        """Download all images and save to output directory.

        Args:
            metadata: Movie metadata containing image URLs
            output_dir: Target directory
            number: Movie number for filenames
        """
        # Main images
        if metadata.poster.url:
            ImageDownloader.download(metadata.poster, output_dir / f"{number}-poster.jpg")
            time.sleep(random.uniform(2, 8))

        if metadata.thumb.url:
            ImageDownloader.download(metadata.thumb, output_dir / f"{number}-thumb.jpg")
            time.sleep(random.uniform(2, 8))

        if metadata.fanart.url:
            ImageDownloader.download(metadata.fanart, output_dir / f"{number}-fanart.jpg")
            time.sleep(random.uniform(2, 8))

        # Extra fanart screenshots
        if metadata.extrafanart:
            extra_dir = output_dir / "extrafanart"
            extra_dir.mkdir(exist_ok=True)

            for i, image in enumerate(metadata.extrafanart, start=1):
                ImageDownloader.download(image, extra_dir / f"extrafanart-{i}.jpg")
                time.sleep(random.uniform(2, 8))

    def _generate_nfo(self, metadata: MovieMetadata, output_dir: Path, number: str) -> None:
        """Generate NFO file.

        Args:
            metadata: Movie metadata
            output_dir: Target directory
            number: Movie number for filename
        """
        nfo_content = generate_nfo(metadata)
        nfo_path = output_dir / f"{number}.nfo"
        nfo_path.write_text(nfo_content, encoding="utf-8")

    def _validate_output(self, output_dir: Path, number: str) -> None:
        """Validate output directory integrity before copying video.

        Checks:
        - extrafanart directory exists
        - poster, fanart, thumb image files exist
        - nfo file exists
        - nfo file contains required values (title, poster, thumb, fanart)

        Args:
            output_dir: Output directory to validate
            number: Movie number for filename

        Raises:
            Exception: If validation fails, after deleting the output directory
        """
        missing = []

        # 1. Check file system resources
        extrafanart_dir = output_dir / "extrafanart"
        if not extrafanart_dir.exists():
            missing.append("extrafanart目录")

        fanart_file = output_dir / f"{number}-fanart.jpg"
        if not fanart_file.exists():
            missing.append(f"{number}-fanart.jpg")

        thumb_file = output_dir / f"{number}-thumb.jpg"
        if not thumb_file.exists():
            missing.append(f"{number}-thumb.jpg")

        poster_file = output_dir / f"{number}-poster.jpg"
        if not poster_file.exists():
            # 检查fanart是否存在且宽度大于700px，如果满足则裁剪作为poster
            if fanart_file.exists():
                try:
                    with Image.open(fanart_file) as img:
                        width, height = img.size
                        if width > 700:
                            # 修改后的裁剪逻辑：限制宽度为最大379px
                            max_width = 379
                            crop_width = min(width // 2, max_width)
                            right_half = img.crop((width - crop_width, 0, width, height))
                            poster_path = output_dir / f"{number}-poster.jpg"
                            right_half.save(poster_path, quality=95)
                            print(f"✓ 使生成poster: {width}x{height} -> {crop_width}x{height}")
                        else:
                            missing.append(f"{number}-poster.jpg")
                except Exception as e:
                    missing.append(f"{number}-poster.jpg (裁剪失败: {e})")
            else:
                missing.append(f"{number}-poster.jpg")

        nfo_file = output_dir / f"{number}.nfo"
        if not nfo_file.exists():
            missing.append(f"{number}.nfo")

        # 2. Check NFO content if file exists
        if nfo_file.exists():
            try:
                tree = ET.parse(nfo_file)
                root = tree.getroot()

                required_tags = ["title", "poster", "thumb", "fanart"]
                for tag in required_tags:
                    elem = root.find(tag)
                    if elem is None or not elem.text or not elem.text.strip():
                        missing.append(f"NFO中{tag}标签为空")
            except ET.ParseError as e:
                missing.append(f"NFO文件解析失败: {e}")

        # 3. If any resources missing, clean up and raise error
        if missing:
            error_msg = "数据完整性检查失败，缺少资源: " + ", ".join(missing)
            print(f"❌ {error_msg}")
            print(f"正在删除输出目录: {output_dir}")
            shutil.rmtree(output_dir, ignore_errors=True)
            raise Exception(error_msg)

        print("✓ 数据完整性检查通过")

    def _zip_output(self, output_dir: Path, number: str) -> Path:
        """Zip the output directory.

        Args:
            output_dir: Directory to zip
            number: Movie number for zip filename

        Returns:
            Path to the created zip file
        """
        zip_path = output_dir.parent / f"{number}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(output_dir.parent)
                    zipf.write(file_path, arcname)

        print(f"✓ 已创建压缩包: {zip_path}")
        return zip_path
