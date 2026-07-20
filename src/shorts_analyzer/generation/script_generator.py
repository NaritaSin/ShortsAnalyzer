"""Generate scripts from selected ideas using an AI provider."""

from __future__ import annotations

from pathlib import Path

from shorts_analyzer.ai.provider import AIProvider
from shorts_analyzer.generation.idea_generator import Idea


class ScriptGenerator:
    """Generate and save scripts from prompts and selected ideas."""

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    def generate_script(
        self,
        idea: Idea,
        prompt_path: Path,
        output_path: Path,
    ) -> str:
        """Read a prompt, append the selected idea, and generate a script.

        Args:
            idea: Selected video idea to append to the prompt.
            prompt_path: Path to the base script prompt file.
            output_path: Path where the generated script will be saved.

        Returns:
            The generated script text.
        """
        prompt_text = prompt_path.read_text(encoding="utf-8")
        full_prompt = self._build_prompt(prompt_text, idea)
        script = self._provider.generate(full_prompt)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(script, encoding="utf-8")
        return script

    def _build_prompt(self, prompt_text: str, idea: Idea) -> str:
        return (
            f"{prompt_text.rstrip()}\n\n"
            "## 採用アイデア\n"
            f"タイトル: {idea['title']}\n"
            f"テーマ: {idea['theme']}\n"
            f"選定理由: {idea['reason']}\n"
            f"推定スコア: {idea['estimated_score']}\n"
        )
