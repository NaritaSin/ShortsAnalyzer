"""Basic statistics for YouTube video analysis."""

from __future__ import annotations

from statistics import median
from typing import TypedDict

from shorts_analyzer.youtube import VideoRecord


class AnalysisResult(TypedDict):
    total_videos: int
    average_views: float
    median_views: float
    max_views: int
    min_views: int
    average_likes: float
    average_comments: float
    average_duration_seconds: float


def _parse_duration_seconds(duration: str) -> int:
    """Convert a simple ISO8601 YouTube duration (PT#M#S) to seconds."""
    if not duration.startswith("PT"):
        return 0

    value = duration[2:]
    minutes = 0
    seconds = 0

    if "M" in value:
        minute_part, value = value.split("M", 1)
        minutes = int(minute_part or 0)

    if "S" in value:
        second_part = value.replace("S", "")
        seconds = int(second_part or 0)

    return minutes * 60 + seconds


def analyze_videos(videos: list[VideoRecord]) -> AnalysisResult:
    """Calculate basic statistics from video records."""
    if not videos:
        return {
            "total_videos": 0,
            "average_views": 0.0,
            "median_views": 0.0,
            "max_views": 0,
            "min_views": 0,
            "average_likes": 0.0,
            "average_comments": 0.0,
            "average_duration_seconds": 0.0,
        }

    views = [int(v["view_count"] or 0) for v in videos]
    likes = [int(v["like_count"] or 0) for v in videos]
    comments = [int(v["comment_count"] or 0) for v in videos]
    durations = [_parse_duration_seconds(v["duration"]) for v in videos]

    return {
        "total_videos": len(videos),
        "average_views": sum(views) / len(views),
        "median_views": float(median(views)),
        "max_views": max(views),
        "min_views": min(views),
        "average_likes": sum(likes) / len(likes),
        "average_comments": sum(comments) / len(comments),
        "average_duration_seconds": sum(durations) / len(durations),
    }