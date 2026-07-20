"""Duration analysis for YouTube video records."""

from __future__ import annotations

from collections import defaultdict
from typing import TypedDict

from shorts_analyzer.youtube import VideoRecord

_DURATION_GROUPS = (
    ("0-30", 0, 30),
    ("30-45", 30, 45),
    ("45-60", 45, 60),
    ("60+", 60, None),
)


class DurationGroupStats(TypedDict):
    group: str
    video_count: int
    average_views: float
    average_likes: float


class DurationAnalysisResult(TypedDict):
    average_duration_seconds: float
    longest_duration_seconds: int
    shortest_duration_seconds: int
    duration_groups: list[DurationGroupStats]


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


def _duration_group(seconds: int) -> str:
    for label, lower, upper in _DURATION_GROUPS:
        if upper is None:
            if seconds >= lower:
                return label
            continue

        if lower <= seconds < upper:
            return label

    return "60+"


def analyze_duration(videos: list[VideoRecord]) -> DurationAnalysisResult:
    """Calculate duration statistics from video records."""
    if not videos:
        return {
            "average_duration_seconds": 0.0,
            "longest_duration_seconds": 0,
            "shortest_duration_seconds": 0,
            "duration_groups": [],
        }

    durations = [_parse_duration_seconds(video["duration"]) for video in videos]
    group_stats: dict[str, list[tuple[int, int]]] = defaultdict(list)

    for video, duration_seconds in zip(videos, durations, strict=True):
        views = int(video["view_count"] or 0)
        likes = int(video["like_count"] or 0)
        group_stats[_duration_group(duration_seconds)].append((views, likes))

    duration_groups: list[DurationGroupStats] = []
    for label, _, _ in _DURATION_GROUPS:
        stats = group_stats.get(label)
        if not stats:
            continue

        views = [value for value, _ in stats]
        likes = [value for _, value in stats]
        duration_groups.append(
            {
                "group": label,
                "video_count": len(stats),
                "average_views": sum(views) / len(stats),
                "average_likes": sum(likes) / len(stats),
            }
        )

    return {
        "average_duration_seconds": sum(durations) / len(durations),
        "longest_duration_seconds": max(durations),
        "shortest_duration_seconds": min(durations),
        "duration_groups": duration_groups,
    }
