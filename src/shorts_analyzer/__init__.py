"""ShortsAnalyzer — analyze YouTube Shorts channels and extract patterns."""

from shorts_analyzer.export import save_videos_csv
from shorts_analyzer.youtube import VideoRecord, YouTubeAPIError, YouTubeClient

__all__ = [
    "VideoRecord",
    "YouTubeAPIError",
    "YouTubeClient",
    "save_videos_csv",
]
__version__ = "0.1.0"
