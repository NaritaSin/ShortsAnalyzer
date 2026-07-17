"""YouTube Data API v3 client for fetching channel uploads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

BASE_URL = "https://www.googleapis.com/youtube/v3"
DEFAULT_TIMEOUT_SECONDS = 30


class YouTubeAPIError(Exception):
    """Raised when the YouTube Data API returns an error response."""


@dataclass(frozen=True, slots=True)
class Video:
    """Metadata for a single YouTube video."""

    video_id: str
    title: str
    published_at: str
    description: str


class YouTubeClient:
    """Client for the YouTube Data API v3.

    Fetches channel uploads via the official REST API using ``requests``.
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize the client.

        Args:
            api_key: YouTube Data API v3 key.
            timeout: HTTP request timeout in seconds.
        """
        if not api_key.strip():
            msg = "api_key must be a non-empty string"
            raise ValueError(msg)

        self._api_key = api_key
        self._timeout = timeout
        self._session = requests.Session()

    def get_latest_videos(
        self,
        channel_id: str,
        *,
        max_results: int = 10,
    ) -> list[Video]:
        """Return the latest uploads for a YouTube channel.

        Resolves the channel's uploads playlist, then fetches playlist items
        in reverse chronological order (newest first).

        Args:
            channel_id: YouTube channel ID (e.g. ``UC...``).
            max_results: Maximum number of videos to return (1–50).

        Returns:
            A list of :class:`Video` objects, newest first.

        Raises:
            ValueError: If ``channel_id`` is empty or ``max_results`` is out of range.
            YouTubeAPIError: If the API returns an error or the request fails.
        """
        if not channel_id.strip():
            msg = "channel_id must be a non-empty string"
            raise ValueError(msg)
        if not 1 <= max_results <= 50:
            msg = "max_results must be between 1 and 50"
            raise ValueError(msg)

        uploads_playlist_id = self._get_uploads_playlist_id(channel_id)
        return self._get_playlist_videos(uploads_playlist_id, max_results=max_results)

    def _get_uploads_playlist_id(self, channel_id: str) -> str:
        """Return the uploads playlist ID for a channel."""
        data = self._request(
            "channels",
            {
                "part": "contentDetails",
                "id": channel_id,
            },
        )

        items = data.get("items", [])
        if not items:
            msg = f"Channel not found: {channel_id}"
            raise YouTubeAPIError(msg)

        uploads_raw = (
            items[0]
            .get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )
        if not isinstance(uploads_raw, str) or not uploads_raw:
            msg = f"No uploads playlist found for channel: {channel_id}"
            raise YouTubeAPIError(msg)

        return uploads_raw

    def _get_playlist_videos(
        self,
        playlist_id: str,
        *,
        max_results: int,
    ) -> list[Video]:
        """Return videos from a playlist."""
        data = self._request(
            "playlistItems",
            {
                "part": "snippet",
                "playlistId": playlist_id,
                "maxResults": max_results,
            },
        )

        videos: list[Video] = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            resource_id = snippet.get("resourceId", {})
            video_id = resource_id.get("videoId")
            if not video_id:
                continue

            videos.append(
                Video(
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    published_at=snippet.get("publishedAt", ""),
                    description=snippet.get("description", ""),
                )
            )

        return videos

    def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Perform a GET request against the YouTube Data API.

        Args:
            endpoint: API resource name (e.g. ``channels``, ``playlistItems``).
            params: Query parameters (``key`` is added automatically).

        Returns:
            Parsed JSON response body.

        Raises:
            YouTubeAPIError: On HTTP failures or API error payloads.
        """
        url = f"{BASE_URL}/{endpoint}"
        query = {**params, "key": self._api_key}

        try:
            response = self._session.get(url, params=query, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            msg = f"YouTube API request failed: {exc}"
            raise YouTubeAPIError(msg) from exc

        try:
            data: dict[str, Any] = response.json()
        except ValueError as exc:
            msg = "YouTube API returned invalid JSON"
            raise YouTubeAPIError(msg) from exc

        if "error" in data:
            error = data["error"]
            message = error.get("message", "Unknown API error")
            code = error.get("code", "unknown")
            msg = f"YouTube API error ({code}): {message}"
            raise YouTubeAPIError(msg)

        return data
