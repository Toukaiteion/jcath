"""Data models for movie metadata."""

from pydantic import BaseModel, Field


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
