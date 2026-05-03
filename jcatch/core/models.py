"""Data models for movie metadata."""

from pathlib import Path
from pydantic import BaseModel, Field
from pydantic import field_validator


class Actor(BaseModel):
    """Actor information."""

    name: str


class ImageUrl(BaseModel):
    """Image URL with associated download headers."""

    url: str = Field(description="Image URL")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers for download")


class MovieMetadata(BaseModel):
    """Complete metadata for a JAV video."""

    num: str = Field(description="Movie number, e.g., FSDSS-549")
    title: str = Field(description="Main title")
    originaltitle: str = Field(default="", description="Original title")
    sorttitle: str = Field(default="", description="Title for sorting")
    customrating: str = Field(default="JP-18+", description="Custom rating")
    mpaa: str = Field(default="JP-18+", description="MPAA rating")
    studio: str = Field(default="", description="Studio/Producer")
    year: int = Field(default=0, description="Release year")
    outline: str = Field(default="", description="Brief outline")
    plot: str = Field(default="", description="Full plot description")
    runtime: int = Field(default=0, description="Runtime in minutes")
    director: str = Field(default="", description="Director name")
    maker: str = Field(default="", description="Maker/Distributor")
    label: str = Field(default="", description="Label")
    actors: list[Actor] = Field(default_factory=list, description="List of actors")
    tags: list[str] = Field(default_factory=list, description="Tags")
    genres: list[str] = Field(default_factory=list, description="Genres")
    premiered: str = Field(default="", description="Premiere date YYYY-MM-DD")
    releasedate: str = Field(default="", description="Release date")
    release: str = Field(default="", description="Release date (alternative)")
    cover: str = Field(default="", description="Cover image URL")
    website: str = Field(default="", description="Website URL")

    # Image URLs for downloading (with headers)
    fanart: ImageUrl = Field(default_factory=ImageUrl, description="Fanart image")
    poster: ImageUrl = Field(default_factory=ImageUrl, description="Poster image")
    thumb: ImageUrl = Field(default_factory=ImageUrl, description="Thumbnail image")
    extrafanart: list[ImageUrl] = Field(
        default_factory=list, description="Extra fanart/screenshot URLs"
    )


class ProcessConfiguration(BaseModel):
    """Configuration for media processing operations."""

    video_path: Path | None = Field(default=None, description="Path to input video file (optional for metadata-only mode)")
    output_dir: Path = Field(default="output", description="Base output directory")
    clean: bool = Field(default=False, description="Clean mode: delete source on success, clean output on failure")
    key: str | None = Field(default=None, description="Movie number for scraping (e.g., 'FSDSS-549')")
    metadata_only: bool = Field(default=False, description="Only generate metadata, skip video operations")
    zip_output: bool = Field(default=False, description="Zip the output directory")

    @field_validator('video_path')
    @classmethod
    def validate_video_path(cls, v):
        if v is None:
            return v
        if not v.exists():
            raise ValueError(f"Video file not found: {v}")
        if not v.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return v

    @field_validator('output_dir')
    @classmethod
    def validate_output_dir(cls, v):
        return v.resolve()

    class Config:
        arbitrary_types_allowed = True
