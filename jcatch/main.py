"""Command-line interface for JCatch."""

from typing import TYPE_CHECKING

import click
from pathlib import Path

from jcatch.core import MediaProcessor
from jcatch.core.models import ProcessConfiguration
from jcatch.scrapers import (
    JavBusScraper, PosterDecorator, JavWineScraper, Www324JavScraper,
)

if TYPE_CHECKING:
    from jcatch.scrapers.base import BaseScraper


def get_scraper(headless: bool = True) -> "BaseScraper":
    """Get the configured scraper instance.

    You can combine scrapers using decorators to get metadata from one source
    and images from another.

    Examples:
        # Simple: use JavBus for everything
        return JavBusScraper(headless=headless)

        # Composite: metadata from JavBus, fanart from Jav321
        base = JavBusScraper(headless=headless)
        return FanartDecorator(base, Jav321Scraper())

        # Multi-layer: metadata from JavBus, fanart from A, poster from B
        base = JavBusScraper(headless=headless)
        with_fanart = FanartDecorator(base, DMMScraper())
        return PosterDecorator(with_fanart, Jav321Scraper())

    Args:
        headless: Whether to run Chrome in headless mode (default: True)

    Returns:
        Configured BaseScraper instance
    """
    # Default: use JavBus for everything
    base = JavBusScraper(headless=headless)
    with_poster = PosterDecorator(base, Www324JavScraper())
    with_poster = PosterDecorator(with_poster, JavWineScraper())
    return with_poster


def find_largest_video(directory: Path) -> Path:
    """Find the largest video file in a directory (non-recursive).

    Args:
        directory: Directory to search

    Returns:
        Path to the largest video file

    Raises:
        FileNotFoundError: If no video files found
    """
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.webm'}
    videos = []

    for item in directory.iterdir():
        if item.is_file() and item.suffix.lower() in video_extensions:
            videos.append((item, item.stat().st_size))

    if not videos:
        raise FileNotFoundError(f"No video files found in: {directory}")

    videos.sort(key=lambda x: x[1], reverse=True)
    return videos[0][0]


@click.command()
@click.option(
    "--video-path",
    "-v",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to the video file (optional)",
)
@click.option(
    "--key",
    "-k",
    default=None,
    help="Movie number for scraping (e.g., 'ADN174', 'SSNI-443')",
)
@click.option(
    "--output",
    "-o",
    default=lambda: Path.cwd(),
    type=click.Path(path_type=Path),
    help="Output directory (default: current directory)",
)
@click.option(
    "--headless",
    "-H",
    is_flag=True,
    default=True,
    show_default=True,
    help="Headless browser mode (default: enabled)",
)
@click.option(
    "--delete-source",
    "-d",
    is_flag=True,
    default=False,
    help="Delete source video file after successful processing",
)
def main(
    video_path: Path | None,
    key: str | None,
    output: Path,
    headless: bool,
    delete_source: bool = False,
) -> None:
    """Process a JAV video file and generate organized media directory.

    The script processes videos in these ways:
    1. Specify video file directly: jcatch -v /path/to/video.mp4
    2. Use current directory's largest video: jcatch
    3. Override the movie number: jcatch -v video.mp4 -k ADN-174

    Examples:
        jcatch
        jcatch -v /path/to/FSDSS-549.mp4 -o output
        jcatch -k SSNI-443 -d
        jcatch -v video.mp4 -o . --headless
    """
    # Print all parameters before execution
    click.echo("=" * 50)
    click.echo("执行参数:")
    click.echo(f"  video_path: {video_path if video_path else '(自动检测)'}")
    click.echo(f"  key: {key if key else '(从文件名解析)'}")
    click.echo(f"  output: {output.resolve()}")
    click.echo(f"  headless: {headless}")
    click.echo(f"  delete_source: {delete_source}")
    click.echo("=" * 50)

    try:
        # Resolve video path: provided or find largest in current directory
        if video_path is None:
            video_path = find_largest_video(Path.cwd())
            click.echo(f"Auto-detected video: {video_path}")

        # Resolve key: provided or extract from filename
        if key is None:
            from jcatch.utils.file import extract_number_from_path
            extracted = extract_number_from_path(str(video_path))
            if not extracted:
                raise ValueError(
                    f"Could not extract movie number from filename: {video_path.name}. "
                    f"Use --key to specify manually."
                )
            key = extracted

        # Get scraper
        scraper_instance = get_scraper(headless=headless)

        # Create processor
        processor = MediaProcessor(scraper_instance)

        # Create configuration object
        config = ProcessConfiguration(
            video_path=video_path,
            output_dir=output,
            delete_source=delete_source,
            key=key
        )

        # Process with config object
        click.echo(f"Processing: {video_path}")
        output_dir = processor.process(config)

        click.echo(f"✓ Done! Output: {output_dir}")

    except FileNotFoundError as e:
        click.echo(f"✗ Error: {e}", err=True)
        click.echo(
            "Please specify a video file with --video-path, "
            "or ensure a video file exists in the current directory.",
            err=True,
        )
        raise click.ClickException(str(e))
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
