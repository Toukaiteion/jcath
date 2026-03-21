"""Command-line interface for JCatch."""

import click
from pathlib import Path

from .core import MediaProcessor
from .scrapers.base import BaseScraper


def get_scraper() -> BaseScraper:
    """Get the configured scraper instance.

    TODO: Implement scraper selection logic.
    You can:
    1. Use a default scraper
    2. Allow configuration via config file
    3. Allow CLI option to specify scraper

    For now, you'll need to import your concrete scraper implementation
    and return it here.
    """
    # TODO: Import and return your actual scraper implementation
    # from .scrapers.jav321 import Jav321Scraper
    # return Jav321Scraper()

    raise NotImplementedError(
        "No scraper configured. Please implement get_scraper() "
        "in jcatch/main.py with your concrete scraper implementation."
    )


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
