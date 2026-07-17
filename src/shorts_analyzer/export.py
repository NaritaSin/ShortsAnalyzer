"""Export video metadata to files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from shorts_analyzer.youtube import VideoRecord

CSV_COLUMNS = (
    "video_id",
    "title",
    "published_at",
    "view_count",
    "like_count",
    "comment_count",
    "duration",
    "thumbnail_url",
)


def save_videos_csv(videos: list[VideoRecord], output_path: Path) -> None:
    """Save video metadata to a CSV file.

    Creates parent directories automatically if they do not exist.

    Args:
        videos: Video metadata returned by :meth:`YouTubeClient.get_channel_videos`.
        output_path: Destination CSV file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dataframe = pd.DataFrame(videos, columns=list(CSV_COLUMNS))
    dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")
