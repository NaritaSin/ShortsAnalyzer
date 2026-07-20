"""Generate narration audio using a local VOICEVOX Engine."""

from __future__ import annotations

import os
import re
from pathlib import Path

import requests

DEFAULT_VOICEVOX_URL = "http://127.0.0.1:50021"
DEFAULT_SPEAKER_ID = 1
DEFAULT_TIMEOUT_SECONDS = 120


class VoiceVoxError(Exception):
    """Raised when the VOICEVOX Engine returns an error response."""


class VoiceVoxGenerator:
    """Generate narration audio from a script via VOICEVOX Engine."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        speaker_id: int = DEFAULT_SPEAKER_ID,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        url = base_url if base_url is not None else os.environ.get(
            "VOICEVOX_URL",
            DEFAULT_VOICEVOX_URL,
        )
        self._base_url = url.rstrip("/")
        self._speaker_id = speaker_id
        self._timeout = timeout

    def generate(self, script_path: Path, output_path: Path) -> Path:
        """Read a script and save synthesized narration audio."""
        script_text = script_path.read_text(encoding="utf-8")
        narration = _prepare_narration_text(script_text)
        if not narration.strip():
            msg = f"No narration text found in script: {script_path}"
            raise VoiceVoxError(msg)

        audio_query = self._create_audio_query(narration)
        wav_bytes = self._synthesize(audio_query)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(wav_bytes)
        return output_path

    def _create_audio_query(self, text: str) -> dict[str, object]:
        try:
            response = requests.post(
                f"{self._base_url}/audio_query",
                params={"speaker": self._speaker_id, "text": text},
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            msg = f"Failed to connect to VOICEVOX Engine at {self._base_url}: {exc}"
            raise VoiceVoxError(msg) from exc

        if not response.ok:
            msg = (
                f"VOICEVOX audio_query failed with status {response.status_code}: "
                f"{response.text}"
            )
            raise VoiceVoxError(msg)

        payload = response.json()
        if not isinstance(payload, dict):
            msg = "VOICEVOX audio_query returned an invalid response"
            raise VoiceVoxError(msg)
        return payload

    def _synthesize(self, audio_query: dict[str, object]) -> bytes:
        try:
            response = requests.post(
                f"{self._base_url}/synthesis",
                params={"speaker": self._speaker_id},
                json=audio_query,
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            msg = f"Failed to synthesize audio with VOICEVOX Engine: {exc}"
            raise VoiceVoxError(msg) from exc

        if not response.ok:
            msg = (
                f"VOICEVOX synthesis failed with status {response.status_code}: "
                f"{response.text}"
            )
            raise VoiceVoxError(msg)

        return response.content


def _prepare_narration_text(script: str) -> str:
    """Extract narration text from a generated script."""
    lines: list[str] = []
    for line in script.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("["):
            continue
        if re.match(r"^\d+\.\s", stripped):
            continue
        if stripped.startswith("## "):
            continue
        lines.append(stripped)

    return "\n".join(lines)
