"""Command-line interface for JCatch."""

from typing import TYPE_CHECKING

import click
from pathlib import Path

from jcatch.core import MediaProcessor
from jcatch.scrapers import (
    JavBusScraper,
    Jav321Scraper,
)
from jcatch.scrapers.decorators import FanartDecorator, PosterDecorator

if TYPE_CHECKING:
    from jcatch.scrapers.base import BaseScraper


def get_scraper() -> "BaseScraper":
    """Get the configured scraper instance.

    You can combine scrapers using decorators to get metadata from one source
    and images from another.

    Examples:
        # Simple: use JavBus for everything
        return JavBusScraper()

        # Composite: metadata from JavBus, fanart from Jav321
        base = JavBusScraper()
        return FanartDecorator(base, Jav321Scraper())

        # Multi-layer: metadata from JavBus, fanart from A, poster from B
        base = JavBusScraper()
        with_fanart = FanartDecorator(base, DMMScraper())
        return PosterDecorator(with_fanart, Jav321Scraper())

    Returns:
        Configured BaseScraper instance
    """
    # Default: use JavBus for everything
    return JavBusScraper()


@click.command()
@click.argument("video_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    default="output",
    type=click.Path(path_type=Path),
    help="Output directory (default: output)",
)
@click.option(
    "--scraper",
    "-s",
    default=None,
    help="Scraper to use (e.g., jav321, dmm)",
)
def main(video_path: Path, output: Path, scraper: str | None) -> None:
    """Process a JAV video file and generate organized media directory.

    VIDEO_PATH: Path to the video file to process

    Example:
        jcatch /path/to/FSDSS-549.mp4 -o output
    """
    try:
        # Get scraper (TODO: implement scraper selection)
        scraper_instance = get_scraper()

        # Create processor
        processor = MediaProcessor(scraper_instance)

        # Process video
        click.echo(f"Processing: {video_path}")
        output_dir = processor.process(str(video_path), str(output))

        click.echo(f"✓ Done! Output: {output_dir}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
