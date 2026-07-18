"""Entry point for ShortsAnalyzer."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from shorts_analyzer import YouTubeAPIError, YouTubeClient
from shorts_analyzer.export import save_videos_csv
from shorts_analyzer.statistics import analyze_videos

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_ROOT / "output" / "videos.csv"
CHANNEL_HANDLE = "@雑学をまとめる犬"
MAX_RESULTS = 100


def _load_env() -> None:
    """Load environment variables from common dotenv file locations."""
    for path in (PROJECT_ROOT / ".env", PROJECT_ROOT / ".env" / "env"):
        if path.is_file():
            load_dotenv(path)
            return

    load_dotenv()


def main() -> None:
    """Fetch channel videos and save them to CSV."""
    _load_env()

    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        print("Set YOUTUBE_API_KEY in .env", file=sys.stderr)
        sys.exit(1)

    client = YouTubeClient(api_key)

    try:
        videos = client.get_channel_videos(CHANNEL_HANDLE, max_results=MAX_RESULTS)
    except YouTubeAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    save_videos_csv(videos, OUTPUT_PATH)

    analysis = analyze_videos(videos)

    print(f"Fetched {len(videos)} videos")
    print(f"Saved to {OUTPUT_PATH}")

    print()
    print("===== Analysis =====")
    print(f"Videos: {analysis['total_videos']}")
    print(f"Average Views: {analysis['average_views']:,.0f}")
    print(f"Median Views: {analysis['median_views']:,.0f}")
    print(f"Max Views: {analysis['max_views']:,}")
    print(f"Min Views: {analysis['min_views']:,}")
    print(f"Average Likes: {analysis['average_likes']:,.0f}")
    print(f"Average Comments: {analysis['average_comments']:,.0f}")
    print(f"Average Duration: {analysis['average_duration_seconds']:.1f} sec")


if __name__ == "__main__":
    main()
