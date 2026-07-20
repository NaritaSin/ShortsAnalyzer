"""Generate asset search requests from planned scenes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, TypedDict

_VIDEO_KEYWORDS = (
    "b-roll",
    "motion",
    "fast-cut",
    "animation",
    "subscribe",
    "like",
)

_IMAGE_KEYWORDS = (
    "graphic",
    "title card",
    "photo",
    "diagram",
    "summary visual",
    "overlay",
    "text",
)


class AssetRequest(TypedDict):
    scene_number: int
    search_query: str
    asset_type: str


class AssetRequestResult(TypedDict):
    asset_requests: list[AssetRequest]


class AssetCollector:
    """Build asset search requests from scene plans."""

    def collect(self, scenes_path: Path) -> list[AssetRequest]:
        """Generate one asset request for each scene in a scenes file."""
        scenes = _load_scenes(scenes_path)
        return [_build_request(scene) for scene in scenes]


def save_asset_requests(requests: list[AssetRequest], output_path: Path) -> None:
    """Save asset requests to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: AssetRequestResult = {"asset_requests": requests}
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4, ensure_ascii=False)


def _load_scenes(scenes_path: Path) -> list[dict[str, Any]]:
    with scenes_path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data.get("scenes", [])


def _build_request(scene: dict[str, Any]) -> AssetRequest:
    visual_description = str(scene.get("visual_description", ""))
    narration = str(scene.get("narration", ""))
    search_query = _infer_search_query(visual_description, narration)
    asset_type = _infer_asset_type(visual_description)

    return {
        "scene_number": int(scene["scene_number"]),
        "search_query": search_query,
        "asset_type": asset_type,
    }


def _infer_search_query(visual_description: str, narration: str) -> str:
    focus_match = re.search(
        r"Narration focus:\s*(.+?)(?:\.\.\.|$)",
        visual_description,
        re.IGNORECASE,
    )
    if focus_match:
        focus = _clean_query(focus_match.group(1))
        if focus:
            return focus

    visual_terms = _extract_visual_terms(visual_description)
    narration_terms = _clean_query(narration)
    if visual_terms and narration_terms:
        return _clean_query(f"{narration_terms} {visual_terms}")

    if narration_terms:
        return narration_terms

    cleaned_visual = _clean_query(visual_description)
    return cleaned_visual or "youtube shorts trivia visual"


def _extract_visual_terms(visual_description: str) -> str:
    description = visual_description.split("Narration focus:", 1)[0]
    keywords: list[str] = []

    for term in (
        "hook graphic",
        "title card",
        "b-roll",
        "diagram",
        "photos",
        "summary visual",
        "motion graphics",
        "subscribe",
        "like",
        "comment prompts",
    ):
        if term in description.lower():
            keywords.append(term)

    if keywords:
        return " ".join(keywords)

    return _clean_query(description)


def _infer_asset_type(visual_description: str) -> str:
    lowered = visual_description.lower()
    video_score = sum(keyword in lowered for keyword in _VIDEO_KEYWORDS)
    image_score = sum(keyword in lowered for keyword in _IMAGE_KEYWORDS)

    if video_score > image_score:
        return "video"
    if image_score > video_score:
        return "image"
    return "video" if "b-roll" in lowered else "image"


def _clean_query(text: str) -> str:
    cleaned = re.sub(r"\[[^\]]*\]?", " ", text)
    cleaned = re.sub(r"[#*_]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.")
    return cleaned[:120]
