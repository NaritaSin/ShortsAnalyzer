"""Trend analysis for YouTube video records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypedDict

from shorts_analyzer.youtube import VideoRecord


class TrendGroupStats(TypedDict):
    average_views: float
    average_likes: float
    average_comments: float
    average_duration: float


class TrendDifferences(TypedDict):
    views_change_percent: float
    likes_change_percent: float
    comments_change_percent: float
    duration_change_seconds: float


class TrendAnalysisResult(TypedDict):
    older: TrendGroupStats
    newer: TrendGroupStats
    differences: TrendDifferences


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


def _empty_group_stats() -> TrendGroupStats:
    return {
        "average_views": 0.0,
        "average_likes": 0.0,
        "average_comments": 0.0,
        "average_duration": 0.0,
    }


def _calculate_group_stats(videos: list[VideoRecord]) -> TrendGroupStats:
    if not videos:
        return _empty_group_stats()

    views = [int(video["view_count"] or 0) for video in videos]
    likes = [int(video["like_count"] or 0) for video in videos]
    comments = [int(video["comment_count"] or 0) for video in videos]
    durations = [_parse_duration_seconds(video["duration"]) for video in videos]
    count = len(videos)

    return {
        "average_views": sum(views) / count,
        "average_likes": sum(likes) / count,
        "average_comments": sum(comments) / count,
        "average_duration": sum(durations) / count,
    }


def _percent_change(old_value: float, new_value: float) -> float:
    if old_value == 0:
        return 0.0
    return (new_value - old_value) / old_value * 100


def _sort_key(video: VideoRecord) -> datetime:
    published_at = video["published_at"]
    if not published_at:
        return datetime.min.replace(tzinfo=UTC)
    return _parse_published_at(published_at)


def analyze_trends(videos: list[VideoRecord]) -> TrendAnalysisResult:
    """Compare metrics between the older and newer halves of a video dataset."""
    if not videos:
        empty = _empty_group_stats()
        return {
            "older": empty,
            "newer": empty,
            "differences": {
                "views_change_percent": 0.0,
                "likes_change_percent": 0.0,
                "comments_change_percent": 0.0,
                "duration_change_seconds": 0.0,
            },
        }

    sorted_videos = sorted(videos, key=_sort_key)
    midpoint = len(sorted_videos) // 2
    older_videos = sorted_videos[:midpoint]
    newer_videos = sorted_videos[midpoint:]

    older = _calculate_group_stats(older_videos)
    newer = _calculate_group_stats(newer_videos)

    return {
        "older": older,
        "newer": newer,
        "differences": {
            "views_change_percent": _percent_change(
                older["average_views"], newer["average_views"]
            ),
            "likes_change_percent": _percent_change(
                older["average_likes"], newer["average_likes"]
            ),
            "comments_change_percent": _percent_change(
                older["average_comments"], newer["average_comments"]
            ),
            "duration_change_seconds": (
                newer["average_duration"] - older["average_duration"]
            ),
        },
    }
