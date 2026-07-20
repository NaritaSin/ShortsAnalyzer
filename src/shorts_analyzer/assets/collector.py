"""Generate asset manifests from planned scenes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

_VIDEO_KEYWORDS = (
    "footage",
    "motion",
    "b-roll",
)

_IMAGE_KEYWORDS = (
    "graphic",
    "photo",
    "image",
    "card",
    "button",
    "visual",
    "scene",
    "temple",
    "bird",
    "soldiers",
)


class AssetManifestEntry(TypedDict):
    scene_number: int
    search_query: str
    asset_type: str
    source: str
    local_path: str
    status: str


class AssetManifestResult(TypedDict):
    assets: list[AssetManifestEntry]


class AssetCollector:
    """Build asset manifests from scene plans."""

    def collect(self, scenes_path: Path) -> list[AssetManifestEntry]:
        """Generate one manifest entry for each scene in a scenes file."""
        scenes = _load_scenes(scenes_path)
        return [_build_manifest_entry(scene) for scene in scenes]


def save_assets_manifest(
    manifest: list[AssetManifestEntry],
    output_path: Path,
) -> None:
    """Save an asset manifest to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: AssetManifestResult = {"assets": manifest}
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4, ensure_ascii=False)


def _load_scenes(scenes_path: Path) -> list[dict[str, Any]]:
    with scenes_path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data.get("scenes", [])


def _build_manifest_entry(scene: dict[str, Any]) -> AssetManifestEntry:
    visual_description = str(scene.get("visual_description", "")).strip()
    search_query = visual_description or "trivia facts image"

    return {
        "scene_number": int(scene["scene_number"]),
        "search_query": search_query,
        "asset_type": _infer_asset_type(search_query),
        "source": "",
        "local_path": "",
        "status": "pending",
    }


def _infer_asset_type(search_query: str) -> str:
    lowered = search_query.lower()
    video_score = sum(keyword in lowered for keyword in _VIDEO_KEYWORDS)
    image_score = sum(keyword in lowered for keyword in _IMAGE_KEYWORDS)

    if video_score > image_score:
        return "video"
    if image_score > video_score:
        return "image"
    return "image"
