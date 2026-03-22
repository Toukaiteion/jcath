"""Main media processor that orchestrates the workflow."""

from pathlib import Path
import shutil

from xml.etree import ElementTree as ET

from jcatch.scrapers.base import BaseScraper
from jcatch.core.models import MovieMetadata
from jcatch.core.nfo import generate_nfo
from jcatch.utils.downloader import ImageDownloader


class MediaProcessor:
    """Process video files and generate complete media directory structure."""

    def __init__(self, scraper: BaseScraper):
        """Initialize processor with a scraper instance.

        Args:
            scraper: Scraper instance for fetching metadata and images
        """
        self.scraper = scraper

    def process(self, video_path: str, output_dir: str = "output") -> str:
        """Process a video file and generate complete directory structure.

        Args:
            video_path: Path to the input video file
            output_dir: Base directory for output (default: "output")

        Returns:
            Path to the generated output directory

        Raises:
            FileNotFoundError: If video file doesn't exist
            Exception: If processing fails
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # 1. Extract movie number from file path
        number = self.scraper.parse_number(str(video_path))
        if not number:
            raise ValueError(f"Could not extract movie number from: {video_path}")
        print("1/5 识别到媒体号码 ")

        # 2. Fetch metadata from scraper
        print("2/5 开始搜刮媒体源数据")
        metadata = self.scraper.fetch_metadata(number)

        output_path = Path(output_dir) / number
        output_path.mkdir(parents=True, exist_ok=True)

        # 3. Download and save images
        print("3/5 开始下载图片资源")
        self._download_images(metadata, output_path, number)

        # 4. Generate NFO file
        print("4/5 开始生成元数据文件.nfo")
        self._generate_nfo(metadata, output_path, number)

        # 5. Validate output integrity before copying video
        print("5/6 检查输出数据完整性")
        self._validate_output(output_path, number)

        # 6. Copy video file
        print("6/6 开始复制媒体文件，从" + str(video_path) + "复制到" + str(output_path))
        self._copy_video(video_path, output_path, number)

        return str(output_path)

    def _copy_video(self, video_path: Path, output_dir: Path, number: str) -> None:
        """Copy video file to output directory.

        Args:
            video_path: Source video file path
            output_dir: Target directory
            number: Movie number for filename
        """
        output_file = output_dir / f"{number}.mp4"
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

        if metadata.thumb.url:
            ImageDownloader.download(metadata.thumb, output_dir / f"{number}-thumb.jpg")

        if metadata.fanart.url:
            ImageDownloader.download(metadata.fanart, output_dir / f"{number}-fanart.jpg")

        # Extra fanart screenshots
        if metadata.extrafanart:
            extra_dir = output_dir / "extrafanart"
            extra_dir.mkdir(exist_ok=True)

            for i, image in enumerate(metadata.extrafanart, start=1):
                ImageDownloader.download(image, extra_dir / f"extrafanart-{i}.jpg")

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

        poster_file = output_dir / f"{number}-poster.jpg"
        if not poster_file.exists():
            missing.append(f"{number}-poster.jpg")

        fanart_file = output_dir / f"{number}-fanart.jpg"
        if not fanart_file.exists():
            missing.append(f"{number}-fanart.jpg")

        thumb_file = output_dir / f"{number}-thumb.jpg"
        if not thumb_file.exists():
            missing.append(f"{number}-thumb.jpg")

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
