"""Title analysis for YouTube video records."""

from __future__ import annotations

from typing import TypedDict

from shorts_analyzer.youtube import VideoRecord


class TitleAnalysisResult(TypedDict):
    average_title_length: float
    longest_title_length: int
    shortest_title_length: int
    titles_with_numbers: int
    titles_with_question_mark: int
    titles_with_exclamation_mark: int
    average_hashtag_count: float


def analyze_titles(videos: list[VideoRecord]) -> TitleAnalysisResult:
    """Calculate title statistics from video records."""
    if not videos:
        return {
            "average_title_length": 0.0,
            "longest_title_length": 0,
            "shortest_title_length": 0,
            "titles_with_numbers": 0,
            "titles_with_question_mark": 0,
            "titles_with_exclamation_mark": 0,
            "average_hashtag_count": 0.0,
        }

    titles = [v["title"] for v in videos]
    lengths = [len(title) for title in titles]

    return {
        "average_title_length": sum(lengths) / len(lengths),
        "longest_title_length": max(lengths),
        "shortest_title_length": min(lengths),
        "titles_with_numbers": sum(
            1 for title in titles if any(char.isdigit() for char in title)
        ),
        "titles_with_question_mark": sum(1 for title in titles if "?" in title),
        "titles_with_exclamation_mark": sum(1 for title in titles if "!" in title),
        "average_hashtag_count": sum(title.count("#") for title in titles)
        / len(titles),
    }
