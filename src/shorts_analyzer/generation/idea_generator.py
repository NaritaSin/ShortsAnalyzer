"""Generate video ideas from channel analysis without calling AI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

_IDEA_TEMPLATES = (
    "{keyword}の正体",
    "知られざる{keyword}",
    "なぜ{keyword}？",
    "{keyword}の衝撃事実",
    "{keyword}って何？",
    "{keyword}の裏側",
    "意外な{keyword}",
    "{keyword}の真実",
)


class Idea(TypedDict):
    title: str
    theme: str
    reason: str
    estimated_score: int


class IdeaGenerationResult(TypedDict):
    ideas: list[Idea]


def _extract_topic_from_prompt(prompt_text: str) -> str | None:
    lines = prompt_text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "## トピック" and index + 1 < len(lines):
            topic = lines[index + 1].strip()
            return topic or None
    return None


def _title_length_score(title: str, best_title_length: str) -> float:
    length = len(title)
    if best_title_length == "short":
        if length <= 20:
            return 20.0
        return max(0.0, 20.0 - (length - 20) * 2)

    if best_title_length == "medium":
        if 21 <= length <= 30:
            return 20.0
        distance = min(abs(length - 21), abs(length - 30))
        return max(0.0, 20.0 - distance * 2)

    if length > 30:
        return 20.0
    return max(0.0, 20.0 - (30 - length) * 2)


def _trend_score(trend: dict[str, Any]) -> float:
    differences = trend.get("differences", {})
    views_change = float(differences.get("views_change_percent", 0.0))
    likes_change = float(differences.get("likes_change_percent", 0.0))
    trend_signal = (views_change + likes_change) / 2
    return min(20.0, max(0.0, 10.0 + trend_signal / 5.0))


def _hashtag_score(hashtags: dict[str, Any]) -> float:
    hashtag_rows = hashtags.get("hashtags", [])
    if not hashtag_rows:
        return 10.0

    top_tag = hashtag_rows[0]
    count = int(top_tag.get("count", 0))
    return min(15.0, 10.0 + count / 20.0)


def _keyword_score(
    keyword_row: dict[str, Any],
    rank: int,
    keyword_count: int,
    max_views: float,
) -> float:
    average_views = float(keyword_row.get("average_views", 0.0))
    usage_count = int(keyword_row.get("count", 0))
    view_ratio = average_views / max_views if max_views else 0.0
    usage_ratio = min(usage_count / 3.0, 1.0)
    rank_ratio = 1.0 - (rank / max(keyword_count, 1)) * 0.4
    return 35.0 * view_ratio * usage_ratio * rank_ratio


def _estimate_score(
    keyword_row: dict[str, Any] | None,
    rank: int,
    keyword_count: int,
    max_views: float,
    channel_profile: dict[str, Any],
    hashtags: dict[str, Any],
    trend: dict[str, Any],
    title: str,
) -> int:
    score = 0.0
    score += _trend_score(trend)
    score += _hashtag_score(hashtags)
    score += _title_length_score(
        title,
        str(channel_profile.get("best_title_length", "medium")),
    )

    if keyword_row is not None:
        score += _keyword_score(keyword_row, rank, keyword_count, max_views)
    else:
        score += 20.0

    recommended_style = channel_profile.get("recommended_style", {})
    if recommended_style.get("summary"):
        score += 10.0

    return min(100, round(score))


def _build_reason(
    keyword: str,
    channel_profile: dict[str, Any],
    hashtags: dict[str, Any],
    trend: dict[str, Any],
) -> str:
    top_hashtags = channel_profile.get("top_hashtags", [])
    hashtag_text = " ".join(f"#{tag}" for tag in top_hashtags[:2])
    views_change = float(trend.get("differences", {}).get("views_change_percent", 0.0))
    trend_text = "上昇傾向" if views_change >= 0 else "調整が必要"

    return (
        f"「{keyword}」はチャンネルの上位キーワードに合致し、"
        f"{hashtag_text} の雑学系フォーマットに適しています。"
        f"推奨スタイル（{channel_profile.get('best_title_length', 'medium')}タイトル、"
        f"約{channel_profile.get('average_duration', 0):.0f}秒）と相性が良く、"
        f"直近トレンドは{trend_text}（視聴数 {views_change:+.1f}%）です。"
    )


def _make_idea(
    title: str,
    theme: str,
    keyword_row: dict[str, Any] | None,
    rank: int,
    keyword_count: int,
    max_views: float,
    channel_profile: dict[str, Any],
    hashtags: dict[str, Any],
    trend: dict[str, Any],
) -> Idea:
    keyword = keyword_row["keyword"] if keyword_row else theme
    return {
        "title": title,
        "theme": theme,
        "reason": _build_reason(keyword, channel_profile, hashtags, trend),
        "estimated_score": _estimate_score(
            keyword_row,
            rank,
            keyword_count,
            max_views,
            channel_profile,
            hashtags,
            trend,
            title,
        ),
    }


def generate_ideas(
    channel_profile: dict[str, Any],
    keywords: dict[str, Any],
    hashtags: dict[str, Any],
    trend: dict[str, Any],
    prompt_text: str,
) -> IdeaGenerationResult:
    """Generate ranked video ideas from channel analysis data."""
    keyword_rows = keywords.get("keywords", [])
    max_views = max(
        (float(row.get("average_views", 0.0)) for row in keyword_rows),
        default=0.0,
    )
    keyword_count = len(keyword_rows)
    ideas: list[Idea] = []
    seen_titles: set[str] = set()

    topic = _extract_topic_from_prompt(prompt_text)
    if topic:
        title = topic if len(topic) <= 20 else topic[:20]
        idea = _make_idea(
            title=title,
            theme=topic,
            keyword_row=None,
            rank=0,
            keyword_count=keyword_count,
            max_views=max_views,
            channel_profile=channel_profile,
            hashtags=hashtags,
            trend=trend,
        )
        ideas.append(idea)
        seen_titles.add(title)

    for rank, keyword_row in enumerate(keyword_rows):
        keyword = str(keyword_row.get("keyword", "")).strip()
        if not keyword:
            continue

        template = _IDEA_TEMPLATES[rank % len(_IDEA_TEMPLATES)]
        title = template.format(keyword=keyword)
        if title in seen_titles:
            continue

        ideas.append(
            _make_idea(
                title=title,
                theme=keyword,
                keyword_row=keyword_row,
                rank=rank,
                keyword_count=keyword_count,
                max_views=max_views,
                channel_profile=channel_profile,
                hashtags=hashtags,
                trend=trend,
            )
        )
        seen_titles.add(title)

        if len(ideas) >= 20:
            break

    for rank, keyword_row in enumerate(keyword_rows):
        if len(ideas) >= 20:
            break

        keyword = str(keyword_row.get("keyword", "")).strip()
        if not keyword:
            continue

        combo_title = f"{keyword}の雑学"
        if combo_title in seen_titles:
            continue

        ideas.append(
            _make_idea(
                title=combo_title,
                theme=f"{keyword}をテーマにした雑学ショート",
                keyword_row=keyword_row,
                rank=rank,
                keyword_count=keyword_count,
                max_views=max_views,
                channel_profile=channel_profile,
                hashtags=hashtags,
                trend=trend,
            )
        )
        seen_titles.add(combo_title)

    ideas.sort(key=lambda idea: idea["estimated_score"], reverse=True)
    return {"ideas": ideas[:20]}


def save_ideas(ideas: IdeaGenerationResult, output_path: Path) -> None:
    """Save generated ideas to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(ideas, file, indent=4, ensure_ascii=False)
