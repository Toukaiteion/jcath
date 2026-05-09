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
from jcatch.scrapers import JavTrailersScraper
from jcatch.core.models import MovieMetadata, ProcessConfiguration
from jcatch.core.nfo import generate_nfo
from jcatch.utils.downloader import ImageDownloader
from jcatch.utils.file import extract_number_from_path
from jcatch.core.models import ImageUrl


class MediaProcessor:
    """Process video files and generate complete media directory structure."""

    # Extrafanart download validation thresholds
    MIN_EXTRA_FANART_COUNT = 6  # Minimum required images
    MIN_SUCCESS_RATE = 0.8     # Minimum success rate (75%)

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
        clean_mode = config.clean
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

                # Delete source file if clean mode
                if clean_mode and video_path.exists():
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
                return str(zip_path)

        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            print(f"❌ {error_msg}")

            # Only clean up output directory if clean mode is enabled
            if clean_mode:
                print(f"正在删除输出目录: {output_path}")
                if output_path.exists():
                    shutil.rmtree(output_path, ignore_errors=True)

            raise Exception(error_msg) from e

        return str(output_path)

    def process_from_params(self, video_path: str | Path, output_dir: str | Path = "output", clean: bool = False) -> str:
        """Process with individual parameters (backward compatibility).

        This method maintains backward compatibility with existing code.

        Args:
            video_path: Path to the input video file
            output_dir: Base directory for output (default: "output")
            clean: If True, clean mode (delete source on success, clean output on failure, default: False)

        Returns:
            Path to the generated output directory
        """
        config = ProcessConfiguration(
            video_path=Path(video_path),
            output_dir=Path(output_dir),
            clean=clean
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

            # Initial download attempt
            success_count, total_count = self._download_extrafanart_with_validation(
                metadata.extrafanart, extra_dir
            )

            # Check if validation passed
            if not self._validate_extrafanart_download(success_count, total_count):
                print("初次下载截图未达到要求，尝试备用源...")
                # Fallback to JavTrailers
                fallback_success_count = self._try_fallback_extrafanart(
                    metadata.num, extra_dir, start_index=total_count + 1
                )
                # If fallback also failed, raise exception
                if fallback_success_count == 0:
                    raise Exception(f"截图下载失败: 初次 {success_count}/{total_count}，备用源 0")

    def _download_extrafanart_with_validation(
        self,
        images: list[ImageUrl],
        output_dir: Path,
        start_index: int = 1
    ) -> tuple[int, int]:
        """Download extrafanart images and track success.

        Args:
            images: List of ImageUrl objects to download
            output_dir: Directory to save images
            start_index: Starting index for filename (default: 1)

        Returns:
            Tuple of (successful_count, total_count)
        """
        success_count = 0
        total_count = len(images)

        for i, image in enumerate(images, start=start_index):
            try:
                ImageDownloader.download(image, output_dir / f"extrafanart-{i}.jpg")
                success_count += 1
                time.sleep(random.uniform(2, 8))
            except Exception as e:
                print(f"截图下载失败 extrafanart-{i}: {e}")
                continue

        # Log success rate
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        print(f"截图下载完成: 成功 {success_count}/{total_count} ({success_rate:.1f}%)")

        return success_count, total_count

    def _validate_extrafanart_download(
        self,
        success_count: int,
        total_count: int
    ) -> bool:
        """Validate if extrafanart download meets requirements.

        Args:
            success_count: Number of successfully downloaded images
            total_count: Total number of images attempted

        Returns:
            True if validation passed, False otherwise
        """
        if total_count == 0:
            return False

        success_rate = success_count / total_count

        # Check both minimum count and success rate
        meets_count = success_count >= self.MIN_EXTRA_FANART_COUNT
        meets_rate = success_rate >= self.MIN_SUCCESS_RATE

        return meets_count and meets_rate

    def _try_fallback_extrafanart(
        self,
        number: str,
        output_dir: Path,
        start_index: int
    ) -> int:
        """Try to download extrafanart from fallback scraper.

        Args:
            number: Movie number
            output_dir: Directory to save images
            start_index: Starting index for filename

        Returns:
            Number of successfully downloaded images from fallback
        """
        try:
            # Initialize fallback scraper
            print(f"使用 JavTrailers 获取备用截图...")
            fallback_scraper = JavTrailersScraper(headless=True)
            fallback_metadata = fallback_scraper.fetch_metadata(number)

            if not fallback_metadata.extrafanart:
                print("备用源未找到截图")
                return 0

            # Download fallback images
            success_count, total_count = self._download_extrafanart_with_validation(
                fallback_metadata.extrafanart, output_dir, start_index
            )

            # Validate fallback download
            if self._validate_extrafanart_download(success_count, total_count):
                print(f"备用源截图下载成功: {success_count} 张")
                return success_count
            else:
                print(f"备用源截图下载未达到要求: {success_count}/{total_count}")
                return 0  # Return 0 to indicate failure

        except Exception as e:
            print(f"备用源下载失败: {e}")
            return 0

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
        """Zip the output directory (metadata only, excludes videos and large files).

        Args:
            output_dir: Directory to zip
            number: Movie number for zip filename

        Returns:
            Path to the created zip file
        """
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.webm'}
        large_file_threshold = 1 * 1024 * 1024 * 1024  # 1GB

        zip_path = output_dir.parent / f"{number}.zip"
        excluded_count = 0

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = Path(root) / file

                    # Skip video files
                    if file_path.suffix.lower() in video_extensions:
                        excluded_count += 1
                        continue

                    # Skip large files (>1GB)
                    if file_path.stat().st_size > large_file_threshold:
                        excluded_count += 1
                        print(f"  跳过大文件 (>1GB): {file.name}")
                        continue

                    arcname = file_path.relative_to(output_dir.parent)
                    zipf.write(file_path, arcname)

        if excluded_count > 0:
            print(f"  已跳过 {excluded_count} 个文件")

        print(f"✓ 已创建压缩包: {zip_path}")
        return zip_path
