"""Hashtag analysis for YouTube video records."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TypedDict

from shorts_analyzer.youtube import VideoRecord

_HASHTAG_PATTERN = re.compile(r"#(\S+)")


class HashtagStats(TypedDict):
    tag: str
    count: int
    average_views: float
    average_likes: float
    average_comments: float


class HashtagAnalysisResult(TypedDict):
    hashtags: list[HashtagStats]


def _extract_hashtags(title: str) -> list[str]:
    """Extract hashtag text from a video title."""
    return _HASHTAG_PATTERN.findall(title)


def analyze_hashtags(videos: list[VideoRecord]) -> HashtagAnalysisResult:
    """Calculate hashtag statistics from video records."""
    if not videos:
        return {"hashtags": []}

    stats: dict[str, list[tuple[int, int, int]]] = defaultdict(list)

    for video in videos:
        views = int(video["view_count"] or 0)
        likes = int(video["like_count"] or 0)
        comments = int(video["comment_count"] or 0)

        for tag in _extract_hashtags(video["title"]):
            stats[tag].append((views, likes, comments))

    hashtags: list[HashtagStats] = []
    for tag, entries in stats.items():
        views = [value for value, _, _ in entries]
        likes = [value for _, value, _ in entries]
        comments = [value for _, _, value in entries]
        count = len(entries)
        hashtags.append(
            {
                "tag": tag,
                "count": count,
                "average_views": sum(views) / count,
                "average_likes": sum(likes) / count,
                "average_comments": sum(comments) / count,
            }
        )

    hashtags.sort(key=lambda item: item["count"], reverse=True)
    return {"hashtags": hashtags}
