"""Score generated scripts against the Shorts trivia template."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TypedDict

_CHARS_PER_SECOND = 5.0
_IDEAL_DURATION_SECONDS = (45.0, 75.0)
_ACCEPTABLE_DURATION_SECONDS = (30.0, 90.0)
_PASS_THRESHOLD = 70

_SECTION_CHECKS: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    ("Hook", 15, (r"\bhook\b", r"フック", r"##\s*hook")),
    (
        "Introduction",
        15,
        (r"\bintroduction\b", r"イントロ", r"導入", r"##\s*introduction"),
    ),
    (
        "Main Story",
        20,
        (r"\bmain story\b", r"メイン", r"本編", r"本題", r"##\s*main story"),
    ),
    ("Ending", 15, (r"\bending\b", r"エンディング", r"結び", r"##\s*ending")),
    (
        "CTA",
        10,
        (
            r"\bcta\b",
            r"call to action",
            r"チャンネル登録",
            r"高評価",
            r"フォロー",
            r"コメント",
            r"##\s*cta",
        ),
    ),
)


class ScriptScoreResult(TypedDict):
    score: int
    issues: list[str]
    passed: bool


class ScriptScorer:
    """Score scripts using template structure and duration heuristics."""

    def score(self, script: str) -> ScriptScoreResult:
        """Score a script and return the result with issues."""
        if not script.strip():
            return {
                "score": 0,
                "issues": ["Script is empty."],
                "passed": False,
            }

        issues: list[str] = []
        total_score = 0.0
        sections_found = 0

        for section_name, points, patterns in _SECTION_CHECKS:
            if _has_section(script, patterns):
                total_score += points
                sections_found += 1
            else:
                issues.append(f"Missing or unclear {section_name} section.")

        duration_score, duration_issues = _score_duration(script)
        total_score += duration_score
        issues.extend(duration_issues)

        completeness_score, completeness_issues = _score_completeness(
            script,
            sections_found,
        )
        total_score += completeness_score
        issues.extend(completeness_issues)

        score = min(100, round(total_score))
        return {
            "score": score,
            "issues": issues,
            "passed": score >= _PASS_THRESHOLD,
        }


def save_script_score(result: ScriptScoreResult, output_path: Path) -> None:
    """Save a script score result to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)


def _has_section(script: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        if re.search(pattern, script, re.IGNORECASE):
            return True
    return False


def _estimate_duration_seconds(script: str) -> float:
    spoken_text = re.sub(r"\s+", "", script)
    if not spoken_text:
        return 0.0
    return len(spoken_text) / _CHARS_PER_SECOND


def _score_duration(script: str) -> tuple[float, list[str]]:
    estimated_duration = _estimate_duration_seconds(script)
    issues: list[str] = []

    ideal_min, ideal_max = _IDEAL_DURATION_SECONDS
    acceptable_min, acceptable_max = _ACCEPTABLE_DURATION_SECONDS

    if ideal_min <= estimated_duration <= ideal_max:
        return 15.0, issues

    if acceptable_min <= estimated_duration <= acceptable_max:
        issues.append(
            "Estimated duration is acceptable but outside the ideal Shorts range "
            f"({estimated_duration:.0f} sec)."
        )
        return 10.0, issues

    if estimated_duration < acceptable_min:
        issues.append(
            "Estimated duration is too short "
            f"({estimated_duration:.0f} sec)."
        )
        return 5.0, issues

    issues.append(
        "Estimated duration is too long "
        f"({estimated_duration:.0f} sec)."
    )
    return 5.0, issues


def _score_completeness(script: str, sections_found: int) -> tuple[float, list[str]]:
    issues: list[str] = []
    non_empty_lines = [line.strip() for line in script.splitlines() if line.strip()]
    line_count = len(non_empty_lines)
    char_count = len(re.sub(r"\s+", "", script))

    if sections_found == len(_SECTION_CHECKS) and line_count >= 5 and char_count >= 150:
        return 10.0, issues

    if sections_found >= 3 and char_count >= 100:
        issues.append("Script structure is partially complete.")
        return 6.0, issues

    if char_count >= 50:
        issues.append("Script lacks overall completeness for a Shorts trivia video.")
        return 3.0, issues

    issues.append("Script is too short and incomplete.")
    return 0.0, issues
