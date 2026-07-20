"""Plan visual scenes from generated scripts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TypedDict

_CHARS_PER_SECOND = 5.0

_SECTION_ORDER = (
    "Hook",
    "Introduction",
    "Main Story",
    "Ending",
    "CTA",
)

_SECTION_PATTERNS: dict[str, tuple[str, ...]] = {
    "Hook": (r"^##\s*hook\b", r"^hook\s*:?", r"^#\s*hook\b", r"^フック\s*:?"),
    "Introduction": (
        r"^##\s*introduction\b",
        r"^introduction\s*:?",
        r"^イントロ\s*:?",
        r"^導入\s*:?",
    ),
    "Main Story": (
        r"^##\s*main story\b",
        r"^main story\s*:?",
        r"^メイン\s*:?",
        r"^本編\s*:?",
        r"^本題\s*:?",
    ),
    "Ending": (
        r"^##\s*ending\b",
        r"^ending\s*:?",
        r"^エンディング\s*:?",
        r"^結び\s*:?",
    ),
    "CTA": (r"^##\s*cta\b", r"^cta\s*:?", r"^call to action"),
}

_SECTION_DEFAULT_NOUNS: dict[str, tuple[str, ...]] = {
    "Hook": ("attention", "hook", "graphic"),
    "Introduction": ("topic", "introduction", "card"),
    "Main Story": ("trivia", "story", "scene"),
    "Ending": ("summary", "fact", "visual"),
    "CTA": ("subscribe", "like", "button"),
    "Scene": ("short", "video", "scene"),
}

_JP_NOUN_MAP: tuple[tuple[str, str], ...] = (
    ("オーストラリア", "australian"),
    ("エミュー", "emu"),
    ("エミュ", "emu"),
    ("大統領", "president"),
    ("ウサギ", "rabbit"),
    ("火山", "volcano"),
    ("噴火", "eruption"),
    ("ローマ", "roman"),
    ("寺院", "temple"),
    ("兵士", "soldiers"),
    ("戦争", "war"),
    ("カタツムリ", "snail"),
    ("ネコ", "cat"),
    ("犬", "dog"),
    ("ペンギン", "penguin"),
    ("ホッキョクグマ", "polar bear"),
    ("菌類", "mushroom"),
    ("ゴルフボール", "golf ball"),
    ("カエル", "frog"),
    ("ハムスター", "hamster"),
    ("貝", "shell"),
    ("昆虫", "insect"),
    ("鳥", "bird"),
    ("魚", "fish"),
    ("歴史", "history"),
    ("科学", "science"),
    ("雑学", "trivia"),
)

_ENGLISH_STOPWORDS = frozenset(
    {
        "openai",
        "placeholder",
        "youtube",
        "shorts",
        "script",
        "template",
        "response",
        "for",
        "the",
        "and",
        "with",
        "from",
        "this",
        "that",
    }
)


class Scene(TypedDict):
    scene_number: int
    narration: str
    visual_description: str
    estimated_duration_seconds: float


class ScenePlanResult(TypedDict):
    scenes: list[Scene]


class ScenePlanner:
    """Split a generated script into timed scenes."""

    def plan_scenes(self, script: str) -> list[Scene]:
        """Split a script into scenes with narration and visual notes."""
        sections = _split_script(script)
        scenes: list[Scene] = []

        for index, (section_name, narration) in enumerate(sections, start=1):
            cleaned_narration = narration.strip()
            if not cleaned_narration:
                continue

            scenes.append(
                {
                    "scene_number": index,
                    "narration": cleaned_narration,
                    "visual_description": _visual_description(
                        section_name,
                        cleaned_narration,
                    ),
                    "estimated_duration_seconds": _estimate_duration_seconds(
                        cleaned_narration
                    ),
                }
            )

        return scenes


def save_scenes(scenes: list[Scene], output_path: Path) -> None:
    """Save planned scenes to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: ScenePlanResult = {"scenes": scenes}
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4, ensure_ascii=False)


def _estimate_duration_seconds(narration: str) -> float:
    spoken_text = re.sub(r"\s+", "", narration)
    if not spoken_text:
        return 0.0
    return round(len(spoken_text) / _CHARS_PER_SECOND, 1)


def _visual_description(section_name: str, narration: str) -> str:
    nouns = _extract_nouns(narration)
    defaults = list(
        _SECTION_DEFAULT_NOUNS.get(section_name, _SECTION_DEFAULT_NOUNS["Scene"])
    )

    if len(nouns) >= 2:
        return _format_noun_phrase(nouns)

    combined = _dedupe_preserve_order(nouns + defaults)
    return _format_noun_phrase(combined)


def _extract_nouns(narration: str) -> list[str]:
    cleaned = re.sub(r"\[[^\]]*\]?", " ", narration)
    nouns: list[str] = []

    for word in re.findall(r"[a-zA-Z]+", cleaned):
        lowered = word.lower()
        if len(lowered) >= 3 and lowered not in _ENGLISH_STOPWORDS:
            nouns.append(lowered)

    for japanese, english in _JP_NOUN_MAP:
        if japanese in cleaned:
            nouns.extend(english.split())

    return _dedupe_preserve_order(nouns)


def _format_noun_phrase(words: list[str]) -> str:
    unique_words = _dedupe_preserve_order(words)
    if not unique_words:
        return "trivia facts image"

    phrase_words = unique_words[:6]
    if len(phrase_words) < 2:
        phrase_words.append("image")

    return " ".join(phrase_words[:6])


def _dedupe_preserve_order(words: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_words: list[str] = []
    for word in words:
        if word in seen:
            continue
        seen.add(word)
        unique_words.append(word)
    return unique_words


def _split_script(script: str) -> list[tuple[str, str]]:
    if not script.strip():
        return []

    sections: list[tuple[str, str]] = []
    current_name = "Scene"
    current_lines: list[str] = []

    for line in script.splitlines():
        stripped = line.strip()
        section_name = _match_section_header(stripped)
        if section_name:
            if current_lines:
                sections.append((current_name, "\n".join(current_lines)))
            current_name = section_name
            current_lines = []
            continue

        if stripped:
            current_lines.append(stripped)

    if current_lines:
        sections.append((current_name, "\n".join(current_lines)))

    if len(sections) > 1 or sections and sections[0][0] != "Scene":
        return sections

    return _split_paragraphs(script)


def _match_section_header(line: str) -> str | None:
    for section_name in _SECTION_ORDER:
        for pattern in _SECTION_PATTERNS[section_name]:
            if re.search(pattern, line, re.IGNORECASE):
                return section_name
    return None


def _split_paragraphs(script: str) -> list[tuple[str, str]]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", script) if part.strip()]
    if len(paragraphs) > 1:
        return [(f"Scene {index + 1}", paragraph) for index, paragraph in enumerate(paragraphs)]

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[。！？!?])\s*", script)
        if sentence.strip()
    ]
    if len(sentences) <= 1:
        return [("Scene", script.strip())]

    grouped: list[tuple[str, str]] = []
    chunk: list[str] = []
    for sentence in sentences:
        chunk.append(sentence)
        if len(chunk) >= 2:
            grouped.append((f"Scene {len(grouped) + 1}", " ".join(chunk)))
            chunk = []

    if chunk:
        grouped.append((f"Scene {len(grouped) + 1}", " ".join(chunk)))

    return grouped
