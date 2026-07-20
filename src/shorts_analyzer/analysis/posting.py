"""Posting time analysis for YouTube video records."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import TypedDict

from shorts_analyzer.youtube import VideoRecord

_WEEKDAY_ORDER = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


class WeekdayStats(TypedDict):
    weekday: str
    video_count: int
    average_views: float
    average_likes: float


class HourStats(TypedDict):
    hour: int
    video_count: int
    average_views: float
    average_likes: float


class PostingAnalysisResult(TypedDict):
    by_weekday: list[WeekdayStats]
    by_hour: list[HourStats]


def _parse_published_at(published_at: str) -> datetime:
    """Parse a UTC ISO8601 timestamp from YouTube."""
    return datetime.fromisoformat(published_at.replace("Z", "+00:00"))


def analyze_posting(videos: list[VideoRecord]) -> PostingAnalysisResult:
    """Calculate posting-time statistics from video records."""
    if not videos:
        return {"by_weekday": [], "by_hour": []}

    weekday_groups: dict[str, list[tuple[int, int]]] = defaultdict(list)
    hour_groups: dict[int, list[tuple[int, int]]] = defaultdict(list)

    for video in videos:
        published_at = video["published_at"]
        if not published_at:
            continue

        timestamp = _parse_published_at(published_at)
        views = int(video["view_count"] or 0)
        likes = int(video["like_count"] or 0)

        weekday_groups[timestamp.strftime("%A")].append((views, likes))
        hour_groups[timestamp.hour].append((views, likes))

    by_weekday: list[WeekdayStats] = []
    for weekday in _WEEKDAY_ORDER:
        stats = weekday_groups.get(weekday)
        if not stats:
            continue

        views = [value for value, _ in stats]
        likes = [value for _, value in stats]
        by_weekday.append(
            {
                "weekday": weekday,
                "video_count": len(stats),
                "average_views": sum(views) / len(stats),
                "average_likes": sum(likes) / len(stats),
            }
        )

    by_hour: list[HourStats] = []
    for hour in sorted(hour_groups):
        stats = hour_groups[hour]
        views = [value for value, _ in stats]
        likes = [value for _, value in stats]
        by_hour.append(
            {
                "hour": hour,
                "video_count": len(stats),
                "average_views": sum(views) / len(stats),
                "average_likes": sum(likes) / len(stats),
            }
        )

    return {"by_weekday": by_weekday, "by_hour": by_hour}
