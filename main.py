"""Entry point for ShortsAnalyzer."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from shorts_analyzer import YouTubeAPIError, YouTubeClient

PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    """Fetch and print the latest uploads for a channel."""
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    channel_id = os.environ.get("YOUTUBE_CHANNEL_ID", "")

    if not api_key or not channel_id:
        print(
            "Set YOUTUBE_API_KEY and YOUTUBE_CHANNEL_ID environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = YouTubeClient(api_key)

    try:
        videos = client.get_latest_videos(channel_id, max_results=5)
    except YouTubeAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"ShortsAnalyzer v0.1.0 — latest uploads for {channel_id}\n")
    for index, video in enumerate(videos, start=1):
        print(f"{index}. {video.title}")
        print(f"   ID: {video.video_id}")
        print(f"   Published: {video.published_at}\n")


if __name__ == "__main__":
    main()
