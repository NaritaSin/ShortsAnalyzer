"""Channel profile generation from analysis results."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, TypedDict

_HOUR_PERIODS = (
    ("morning", range(5, 12)),
    ("afternoon", range(12, 18)),
    ("evening", range(18, 24)),
    ("night", range(0, 5)),
)


class RecommendedStyle(TypedDict):
    duration: str
    posting: str
    title: str
    hashtags: str
    keywords: str
    summary: str


class ChannelProfile(TypedDict):
    average_duration: float
    best_posting_period: str
    best_title_length: str
    average_hashtags: float
    top_keywords: list[str]
    top_hashtags: list[str]
    recommended_style: RecommendedStyle


def _best_posting_period(posting: dict[str, Any]) -> str:
    by_weekday = posting.get("by_weekday", [])
    by_hour = posting.get("by_hour", [])

    best_weekday = (
        max(by_weekday, key=lambda row: row["average_views"]) if by_weekday else None
    )
    period_stats: dict[str, list[tuple[int, float]]] = defaultdict(list)

    for row in by_hour:
        hour = row["hour"]
        for period_name, hours in _HOUR_PERIODS:
            if hour in hours:
                period_stats[period_name].append(
                    (row["video_count"], row["average_views"])
                )
                break

    best_period = "morning"
    best_period_views = 0.0
    for period_name, stats in period_stats.items():
        total_videos = sum(video_count for video_count, _ in stats)
        if total_videos == 0:
            continue

        weighted_views = sum(
            video_count * average_views for video_count, average_views in stats
        ) / total_videos
        if weighted_views > best_period_views:
            best_period_views = weighted_views
            best_period = period_name

    weekday_name = best_weekday["weekday"] if best_weekday else "Unknown"
    return f"{weekday_name} {best_period} (UTC)"


def _best_title_length(patterns: dict[str, Any]) -> str:
    pattern_list = patterns.get("patterns", [])
    if not pattern_list:
        return "medium"

    title_stats: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for pattern in pattern_list:
        title_stats[pattern["title_length_group"]].append(
            (pattern["video_count"], pattern["average_views"])
        )

    best_group = "medium"
    best_views = 0.0
    for group, stats in title_stats.items():
        total_videos = sum(video_count for video_count, _ in stats)
        if total_videos == 0:
            continue

        weighted_views = sum(
            video_count * average_views for video_count, average_views in stats
        ) / total_videos
        if weighted_views > best_views:
            best_views = weighted_views
            best_group = group

    return best_group


def _build_recommended_style(
    average_duration: float,
    best_posting_period: str,
    best_title_length: str,
    average_hashtags: float,
    top_keywords: list[str],
    top_hashtags: list[str],
) -> RecommendedStyle:
    keyword_preview = ", ".join(top_keywords[:5]) if top_keywords else "N/A"
    hashtag_preview = ", ".join(f"#{tag}" for tag in top_hashtags[:5]) if top_hashtags else "N/A"

    duration = (
        f"Keep videos around {average_duration:.0f} seconds to match the channel average."
    )
    posting = f"Post on {best_posting_period} when engagement tends to be strongest."
    title = f"Prefer {best_title_length} titles based on top-performing patterns."
    hashtags = (
        f"Use about {average_hashtags:.1f} hashtags per title, "
        f"including {hashtag_preview}."
    )
    keywords = f"Lean on recurring themes such as {keyword_preview}."
    summary = (
        f"This channel performs best with {best_title_length} titles, "
        f"{average_duration:.0f}-second videos, and posting on {best_posting_period}."
    )

    return {
        "duration": duration,
        "posting": posting,
        "title": title,
        "hashtags": hashtags,
        "keywords": keywords,
        "summary": summary,
    }


def generate_channel_profile(knowledge: dict[str, Any]) -> ChannelProfile:
    """Generate a summarized channel profile from analysis results."""
    statistics = knowledge.get("statistics", {})
    title = knowledge.get("title", {})
    posting = knowledge.get("posting", {})
    patterns = knowledge.get("patterns", {})
    hashtags = knowledge.get("hashtags", {})
    keywords = knowledge.get("keywords", {})

    average_duration = float(statistics.get("average_duration_seconds", 0.0))
    average_hashtags = float(title.get("average_hashtag_count", 0.0))
    best_posting_period = _best_posting_period(posting)
    best_title_length = _best_title_length(patterns)

    top_keywords = [
        row["keyword"] for row in keywords.get("keywords", [])[:10]
    ]
    top_hashtags = [row["tag"] for row in hashtags.get("hashtags", [])[:10]]

    recommended_style = _build_recommended_style(
        average_duration,
        best_posting_period,
        best_title_length,
        average_hashtags,
        top_keywords,
        top_hashtags,
    )

    return {
        "average_duration": average_duration,
        "best_posting_period": best_posting_period,
        "best_title_length": best_title_length,
        "average_hashtags": average_hashtags,
        "top_keywords": top_keywords,
        "top_hashtags": top_hashtags,
        "recommended_style": recommended_style,
    }
