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

_VISUAL_DESCRIPTIONS = {
    "Hook": (
        "Open with a bold hook graphic and fast-cut visuals that grab attention "
        "in the first 3 seconds."
    ),
    "Introduction": (
        "Show a clear title card or topic introduction that sets up what the "
        "viewer will learn."
    ),
    "Main Story": (
        "Use supporting b-roll, diagrams, or photos while presenting the core "
        "trivia narration."
    ),
    "Ending": (
        "Display a summary visual or punchline graphic that reinforces the "
        "key takeaway."
    ),
    "CTA": (
        "End with subscribe, like, and comment prompts using simple motion "
        "graphics or on-screen text."
    ),
    "Scene": "Show visuals that directly support the narration for this beat.",
}


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
    base = _VISUAL_DESCRIPTIONS.get(section_name, _VISUAL_DESCRIPTIONS["Scene"])
    preview = narration.replace("\n", " ").strip()
    if len(preview) > 40:
        preview = f"{preview[:40]}..."
    return f"{base} Narration focus: {preview}"


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
