"""YouTube Data API v3 client for fetching channel uploads."""

from __future__ import annotations

from typing import Any, TypedDict

import requests

BASE_URL = "https://www.googleapis.com/youtube/v3"
DEFAULT_TIMEOUT_SECONDS = 30


class YouTubeAPIError(Exception):
    """Raised when the YouTube Data API returns an error response."""


class VideoRecord(TypedDict):
    """Video metadata returned by :meth:`YouTubeClient.get_channel_videos`."""

    video_id: str
    title: str
    published_at: str
    view_count: str
    like_count: str
    comment_count: str
    duration: str
    thumbnail_url: str


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

    def get_channel_videos(
        self,
        channel_handle: str,
        max_results: int = 10,
    ) -> list[VideoRecord]:
        """Return the latest uploads for a YouTube channel handle.

        Resolves the handle to a channel ID, then fetches playlist items
        in reverse chronological order (newest first).

        Args:
            channel_handle: Channel handle with or without ``@`` (e.g. ``@example``).
            max_results: Maximum number of videos to return (1–50).

        Returns:
            A list of video metadata dicts, newest first.

        Raises:
            ValueError: If the handle is empty or ``max_results`` is out of range.
            YouTubeAPIError: If the API returns an error or the request fails.
        """
        handle = channel_handle.strip().lstrip("@")
        if not handle:
            msg = "channel_handle must be a non-empty string"
            raise ValueError(msg)
        if not 1 <= max_results <= 50:
            msg = "max_results must be between 1 and 50"
            raise ValueError(msg)

        channel_id = self._resolve_channel_id(handle)
        uploads_playlist_id = self._get_uploads_playlist_id(channel_id)
        return self._get_playlist_videos(uploads_playlist_id, max_results=max_results)

    def _resolve_channel_id(self, handle: str) -> str:
        """Return the channel ID for a handle."""
        data = self._request(
            "channels",
            {
                "part": "id",
                "forHandle": handle,
            },
        )

        items = data.get("items", [])
        if not items:
            msg = f"Channel not found for handle: @{handle}"
            raise YouTubeAPIError(msg)

        channel_id = items[0].get("id")
        if not isinstance(channel_id, str) or not channel_id:
            msg = f"Invalid channel response for handle: @{handle}"
            raise YouTubeAPIError(msg)

        return channel_id

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
    ) -> list[VideoRecord]:
        """Return videos from a playlist."""
        data = self._request(
            "playlistItems",
            {
                "part": "snippet",
                "playlistId": playlist_id,
                "maxResults": max_results,
            },
        )

        collected: list[dict[str, str]] = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            resource_id = snippet.get("resourceId", {})
            video_id = resource_id.get("videoId")
            if not isinstance(video_id, str) or not video_id:
                continue

            collected.append(
                {
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail_url": _pick_thumbnail_url(snippet.get("thumbnails", {})),
                }
            )

        if not collected:
            return []

        details_by_id = self._get_video_details(
            [video["video_id"] for video in collected]
        )

        videos: list[VideoRecord] = []
        for video in collected:
            details = details_by_id.get(video["video_id"], {})
            videos.append(
                {
                    "video_id": video["video_id"],
                    "title": video["title"],
                    "published_at": video["published_at"],
                    "view_count": details.get("view_count", ""),
                    "like_count": details.get("like_count", ""),
                    "comment_count": details.get("comment_count", ""),
                    "duration": details.get("duration", ""),
                    "thumbnail_url": video["thumbnail_url"],
                }
            )

        return videos

    def _get_video_details(self, video_ids: list[str]) -> dict[str, dict[str, str]]:
        """Return statistics and duration keyed by video ID."""
        data = self._request(
            "videos",
            {
                "part": "statistics,contentDetails",
                "id": ",".join(video_ids),
            },
        )

        details: dict[str, dict[str, str]] = {}
        for item in data.get("items", []):
            video_id = item.get("id")
            if not isinstance(video_id, str) or not video_id:
                continue

            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            details[video_id] = {
                "view_count": _as_string(statistics.get("viewCount")),
                "like_count": _as_string(statistics.get("likeCount")),
                "comment_count": _as_string(statistics.get("commentCount")),
                "duration": _as_string(content_details.get("duration")),
            }

        return details

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


def _as_string(value: object) -> str:
    """Return a string value for API fields that may be missing."""
    if value is None:
        return ""
    return str(value)


def _pick_thumbnail_url(thumbnails: dict[str, Any]) -> str:
    """Return the best available thumbnail URL from a snippet."""
    for quality in ("maxres", "high", "medium", "default"):
        url = thumbnails.get(quality, {}).get("url")
        if isinstance(url, str) and url:
            return url
    return ""
