"""File utility functions."""

import re
from pathlib import Path


def extract_number_from_path(filepath: str) -> str:
    """Extract movie number from file path.

    Common patterns:
    - FSDSS-549.mp4 -> FSDSS-549
    - ADN174.mp4 -> ADN174
    - SSNI-443.mp4 -> SSNI-443
    - SSNI443.mp4 -> SSNI-443
    - /path/to/FSDSS-549/FSDSS-549.mp4 -> FSDSS-549
    - ABC-123_HD.mp4 -> ABC-123

    Args:
        filepath: Path to the video file

    Returns:
        Movie number (e.g., "FSDSS-549", "ADN174"), or empty string if not found
    """
    filename = Path(filepath).stem

    # Pattern: LETTERS-NUMBER or LETTERSNUMBER (supports various formats)
    # Matches: ADN174, SSNI-443, SSNI443, FSDSS-549, SSIS-1234
    match = re.search(r'([A-Za-z]{2,5})-?(\d{3,4})', filename)
    if match:
        number = match.group(2)
        # Preserve original format if it has a hyphen
        if '-' in filename:
            return f"{match.group(1)}-{number}"
        # For patterns without hyphen, return without hyphen
        if re.search(r'[A-Za-z]{2,5}\d{3,4}', filename):
            return f"{match.group(1)}{number}"
        return f"{match.group(1)}-{number}"

    # Pattern: Directory name might contain the number
    parent = Path(filepath).parent.name
    match = re.search(r'([A-Za-z]{2,5})-?(\d{3,4})', parent)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    return ""
