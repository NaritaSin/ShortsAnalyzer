"""Download images from Pexels for asset manifest entries."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

import requests

from shorts_analyzer.assets.collector import (
    AssetManifestEntry,
    save_assets_manifest,
)

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
DEFAULT_TIMEOUT_SECONDS = 30


class PexelsAPIError(Exception):
    """Raised when the Pexels API returns an error response."""


class PexelsDownloader:
    """Download images from Pexels based on an asset manifest."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        key = api_key if api_key is not None else os.environ.get("PEXELS_API_KEY", "")
        if not key.strip():
            msg = "PEXELS_API_KEY must be set in the environment"
            raise ValueError(msg)
        self._api_key = key
        self._timeout = timeout

    def download(
        self,
        manifest_path: Path,
        images_dir: Path,
        *,
        project_root: Path | None = None,
    ) -> list[AssetManifestEntry]:
        """Download manifest assets and update the manifest file."""
        root = project_root or manifest_path.parent.parent
        manifest = _load_manifest(manifest_path)

        updated_assets: list[AssetManifestEntry] = []
        for entry in manifest:
            updated_assets.append(self._download_entry(entry, images_dir, root))

        save_assets_manifest(updated_assets, manifest_path)
        return updated_assets

    def _download_entry(
        self,
        entry: AssetManifestEntry,
        images_dir: Path,
        project_root: Path,
    ) -> AssetManifestEntry:
        existing_path = entry.get("local_path", "")
        if existing_path:
            resolved_path = project_root / existing_path
            if resolved_path.is_file():
                return entry

        if entry["asset_type"] != "image":
            return entry

        image_url = self._search_image(entry["search_query"])
        extension = _extension_from_url(image_url)
        filename = f"scene_{entry['scene_number']}{extension}"
        saved_path = images_dir / filename
        images_dir.mkdir(parents=True, exist_ok=True)
        self._download_file(image_url, saved_path)

        relative_path = saved_path.relative_to(project_root).as_posix()
        return {
            **entry,
            "status": "downloaded",
            "source": image_url,
            "local_path": relative_path,
        }

    def _search_image(self, query: str) -> str:
        response = requests.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": self._api_key},
            params={"query": query, "per_page": 1},
            timeout=self._timeout,
        )
        if not response.ok:
            msg = (
                f"Pexels search failed with status {response.status_code}: "
                f"{response.text}"
            )
            raise PexelsAPIError(msg)

        photos = response.json().get("photos", [])
        if not photos:
            msg = f"No Pexels images found for query: {query}"
            raise PexelsAPIError(msg)

        sources = photos[0].get("src", {})
        image_url = sources.get("large") or sources.get("original") or sources.get(
            "medium"
        )
        if not image_url:
            msg = f"Pexels image URL missing for query: {query}"
            raise PexelsAPIError(msg)

        return str(image_url)

    def _download_file(self, url: str, output_path: Path) -> None:
        response = requests.get(url, timeout=self._timeout)
        if not response.ok:
            msg = (
                f"Image download failed with status {response.status_code}: "
                f"{url}"
            )
            raise PexelsAPIError(msg)
        output_path.write_bytes(response.content)


def _load_manifest(manifest_path: Path) -> list[AssetManifestEntry]:
    with manifest_path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data.get("assets", [])


def _extension_from_url(url: str) -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    return ".jpg"
