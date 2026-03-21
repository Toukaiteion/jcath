"""File utility functions."""

import re
from pathlib import Path


def extract_number_from_path(filepath: str) -> str:
    """Extract movie number from file path.

    Common patterns:
    - FSDSS-549.mp4 -> FSDSS-549
    - /path/to/FSDSS-549/FSDSS-549.mp4 -> FSDSS-549
    - ABC-123_HD.mp4 -> ABC-123
    - XYZ456.mp4 -> XYZ-456 (if format matches)

    Args:
        filepath: Path to the video file

    Returns:
        Movie number (e.g., "FSDSS-549"), or empty string if not found
    """
    filename = Path(filepath).stem

    # Pattern 1: Standard format like FSDSS-549
    # Matches: LETTERS-NUMBER (e.g., FSDSS-549, SSIS-1234)
    match = re.search(r'^([A-Z]+)-(\d+)$', filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    # Pattern 2: Letter-number format without hyphen (e.g., FSDSS549)
    match = re.search(r'^([A-Z]+)(\d+)$', filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    # Pattern 3: Directory name might contain the number
    parent = Path(filepath).parent.name
    match = re.search(r'([A-Z]+)-(\d+)$', parent)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    return ""
