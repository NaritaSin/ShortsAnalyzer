"""Export analysis results to JSON knowledge files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_EXPORT_FILES = {
    "statistics": "statistics.json",
    "title": "title.json",
    "posting": "posting.json",
    "duration": "duration.json",
    "hashtags": "hashtags.json",
    "keywords": "keywords.json",
    "patterns": "patterns.json",
    "trend": "trend.json",
    "channel_profile": "channel_profile.json",
}


def export_knowledge(data: dict[str, Any], output_dir: Path) -> None:
    """Save each analysis result into an individual JSON file.

    Creates the output directory automatically if it does not exist.

    Args:
        data: Analysis results keyed by analysis name.
        output_dir: Destination directory for JSON files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for key, filename in _EXPORT_FILES.items():
        output_path = output_dir / filename
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(data[key], file, indent=4, ensure_ascii=False)
