"""NFO XML generation and parsing."""

from xml.etree import ElementTree as ET

from jcatch.core.models import MovieMetadata


class CDATAElement(ET.Element):
    """Element that serializes as CDATA."""

    def __init__(self, tag, text=None, attrib=None):
        super().__init__(tag, attrib or {})
        self._cdata_text = text or ""

    @property
    def text(self):
        return self._cdata_text

    @text.setter
    def text(self, value):
        self._cdata_text = value or ""


def _tostring_cdata(element: ET.Element) -> str:
    """Serialize element to string with CDATA support."""
    lines = []
    _serialize_element(element, lines, 0)
    return "\n".join(lines)


def _serialize_element(element: ET.Element, lines: list[str], indent: int) -> None:
    """Serialize an element recursively."""
    prefix = "  " * indent
    attrs = "".join(f' {k}="{v}"' for k, v in element.attrib.items())
    tag = element.tag

    if isinstance(element, CDATAElement):
        # CDATA element
        lines.append(f'{prefix}<{tag}{attrs}>')
        if element.text:
            lines.append(f'{prefix}<![CDATA[{element.text}]]>')
        for child in element:
            _serialize_element(child, lines, indent + 1)
        lines.append(f'{prefix}</{tag}>')
    elif len(element) == 0:
        # Leaf element
        text = element.text or ""
        lines.append(f'{prefix}<{tag}{attrs}>{text}</{tag}>')
    else:
        # Element with children
        text = element.text or ""
        if text:
            lines.append(f'{prefix}<{tag}{attrs}>{text}')
        else:
            lines.append(f'{prefix}<{tag}{attrs}>')
        for child in element:
            _serialize_element(child, lines, indent + 1)
        lines.append(f'{prefix}</{tag}>')


def generate_nfo(metadata: MovieMetadata) -> str:
    """Generate NFO XML content from MovieMetadata.

    Args:
        metadata: Movie metadata object

    Returns:
        Formatted XML string
    """
    movie = ET.Element("movie")

    # Basic information (CDATA wrapped)
    _add_cdata_element(movie, "title", metadata.title)
    _add_cdata_element(movie, "originaltitle", metadata.originaltitle)
    _add_cdata_element(movie, "sorttitle", metadata.sorttitle)
    _add_element(movie, "customrating", metadata.customrating)
    _add_element(movie, "mpaa", metadata.mpaa)

    # Studio
    studio = ET.SubElement(movie, "studio")
    studio.text = metadata.studio

    # Year
    year = ET.SubElement(movie, "year")
    year.text = str(metadata.year) if metadata.year else ""

    # Description (CDATA wrapped)
    _add_cdata_element(movie, "outline", metadata.outline)
    _add_cdata_element(movie, "plot", metadata.plot)

    # Runtime
    runtime = ET.SubElement(movie, "runtime")
    runtime.text = str(metadata.runtime) if metadata.runtime else ""

    # Director (CDATA wrapped)
    _add_cdata_element(movie, "director", metadata.director)

    # Images (filenames only, not URLs)
    if metadata.num:
        _add_element(movie, "poster", f"{metadata.num}-poster.jpg")
        _add_element(movie, "thumb", f"{metadata.num}-thumb.jpg")
        _add_element(movie, "fanart", f"{metadata.num}-fanart.jpg")

    # Actors
    for actor in metadata.actors:
        actor_elem = ET.SubElement(movie, "actor")
        _add_element(actor_elem, "name", actor.name)

    # Maker and label (CDATA wrapped)
    _add_element(movie, "maker", metadata.maker)
    _add_element(movie, "label", metadata.label)

    for tag in metadata.tags:
        _add_element(movie, "tag", tag)

    # Genres (exactly 2 elements as in example)
    for genre in metadata.genres:
        _add_element(movie, "genre", genre)

    # Number (CDATA wrapped)
    _add_element(movie, "num", metadata.num)

    # Dates (CDATA wrapped)
    _add_element(movie, "premiered", metadata.premiered)
    _add_element(movie, "releasedate", metadata.releasedate)
    _add_element(movie, "release", metadata.release)

    # URLs (CDATA wrapped)
    _add_element(movie, "cover", metadata.cover)
    _add_element(movie, "website", metadata.website)

    # Format output with declaration and CDATA support
    xml_str = _tostring_cdata(movie)
    return f'<?xml version="1.0" encoding="UTF-8" ?>\n{xml_str}'


def _add_element(parent: ET.Element, tag: str, text: str = "") -> None:
    """Add a simple element with text content."""
    elem = ET.SubElement(parent, tag)
    elem.text = text


def _add_cdata_element(parent: ET.Element, tag: str, text: str = "") -> None:
    """Add a CDATA-wrapped element."""
    elem = CDATAElement(tag, text)
    parent.append(elem)
