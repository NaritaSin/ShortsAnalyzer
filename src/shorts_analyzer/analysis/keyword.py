"""Keyword analysis for YouTube video records."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TypedDict

from shorts_analyzer.youtube import VideoRecord

_HASHTAG_PATTERN = re.compile(r"#\S+")
_PUNCTUATION_PATTERN = re.compile(
    r"[、。！？「」『』（）()\[\]{}.,;:\-–—…・!?#]+"
)
_SPLIT_PATTERN = re.compile(
    r"[\s]+|"
    r"(?:を|に|は|が|の|で|と|へ|から|より|も|か|"
    r"みたいな|ような|という)"
)


class KeywordStats(TypedDict):
    keyword: str
    count: int
    average_views: float
    average_likes: float
    average_comments: float


class KeywordAnalysisResult(TypedDict):
    keywords: list[KeywordStats]


def _extract_keywords(title: str) -> list[str]:
    """Extract simple keywords from a video title."""
    without_hashtags = _HASHTAG_PATTERN.sub(" ", title)
    without_punctuation = _PUNCTUATION_PATTERN.sub(" ", without_hashtags)
    tokens = _SPLIT_PATTERN.split(without_punctuation)

    keywords: list[str] = []
    for token in tokens:
        keyword = token.strip()
        if not keyword or len(keyword) < 2:
            continue
        keywords.append(keyword)

    return keywords


def analyze_keywords(videos: list[VideoRecord]) -> KeywordAnalysisResult:
    """Calculate keyword statistics from video records."""
    if not videos:
        return {"keywords": []}

    stats: dict[str, list[tuple[int, int, int]]] = defaultdict(list)

    for video in videos:
        views = int(video["view_count"] or 0)
        likes = int(video["like_count"] or 0)
        comments = int(video["comment_count"] or 0)

        for keyword in _extract_keywords(video["title"]):
            stats[keyword].append((views, likes, comments))

    keywords: list[KeywordStats] = []
    for keyword, entries in stats.items():
        views = [value for value, _, _ in entries]
        likes = [value for _, value, _ in entries]
        comments = [value for _, _, value in entries]
        count = len(entries)
        keywords.append(
            {
                "keyword": keyword,
                "count": count,
                "average_views": sum(views) / count,
                "average_likes": sum(likes) / count,
                "average_comments": sum(comments) / count,
            }
        )

    keywords.sort(key=lambda item: item["count"], reverse=True)
    return {"keywords": keywords}
