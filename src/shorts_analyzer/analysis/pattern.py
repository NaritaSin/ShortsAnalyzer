"""Pattern analysis for YouTube video records."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import TypedDict

from shorts_analyzer.youtube import VideoRecord


class PatternStats(TypedDict):
    title_length_group: str
    duration_group: str
    posting_hour_group: str
    video_count: int
    average_views: float
    average_likes: float


class PatternAnalysisResult(TypedDict):
    patterns: list[PatternStats]


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


def _parse_published_at(published_at: str) -> datetime:
    """Parse a UTC ISO8601 timestamp from YouTube."""
    return datetime.fromisoformat(published_at.replace("Z", "+00:00"))


def _title_length_group(title: str) -> str:
    length = len(title)
    if length <= 20:
        return "short"
    if length <= 30:
        return "medium"
    return "long"


def _duration_group(seconds: int) -> str:
    if seconds < 45:
        return "short"
    if seconds <= 60:
        return "medium"
    return "long"


def _posting_hour_group(hour: int) -> str:
    if 5 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 17:
        return "afternoon"
    if 18 <= hour <= 23:
        return "evening"
    return "night"


def analyze_patterns(videos: list[VideoRecord]) -> PatternAnalysisResult:
    """Calculate top-performing title, duration, and posting-time patterns."""
    if not videos:
        return {"patterns": []}

    pattern_stats: dict[tuple[str, str, str], list[tuple[int, int]]] = defaultdict(
        list
    )

    for video in videos:
        published_at = video["published_at"]
        if not published_at:
            continue

        timestamp = _parse_published_at(published_at)
        duration_seconds = _parse_duration_seconds(video["duration"])
        pattern_key = (
            _title_length_group(video["title"]),
            _duration_group(duration_seconds),
            _posting_hour_group(timestamp.hour),
        )
        views = int(video["view_count"] or 0)
        likes = int(video["like_count"] or 0)
        pattern_stats[pattern_key].append((views, likes))

    patterns: list[PatternStats] = []
    for (
        title_length_group,
        duration_group,
        posting_hour_group,
    ), stats in pattern_stats.items():
        views = [value for value, _ in stats]
        likes = [value for _, value in stats]
        patterns.append(
            {
                "title_length_group": title_length_group,
                "duration_group": duration_group,
                "posting_hour_group": posting_hour_group,
                "video_count": len(stats),
                "average_views": sum(views) / len(stats),
                "average_likes": sum(likes) / len(stats),
            }
        )

    patterns.sort(key=lambda item: item["average_views"], reverse=True)
    return {"patterns": patterns[:10]}
