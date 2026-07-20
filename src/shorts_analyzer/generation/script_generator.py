"""Generate scripts from selected ideas using an AI provider."""

from __future__ import annotations

from pathlib import Path

from shorts_analyzer.ai.provider import AIProvider
from shorts_analyzer.generation.idea_generator import Idea

_DEFAULT_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3] / "templates" / "shorts_trivia.md"
)


class ScriptGenerator:
    """Generate and save scripts from prompts and selected ideas."""

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    def generate_script(
        self,
        idea: Idea,
        prompt_path: Path,
        output_path: Path,
        template_path: Path | None = None,
    ) -> str:
        """Read a template and prompt, append the selected idea, and generate a script.

        Args:
            idea: Selected video idea to append to the prompt.
            prompt_path: Path to the base script prompt file.
            output_path: Path where the generated script will be saved.
            template_path: Path to the script structure template file.

        Returns:
            The generated script text.
        """
        template_text = self._load_template(template_path)
        prompt_text = prompt_path.read_text(encoding="utf-8")
        full_prompt = self._build_prompt(template_text, prompt_text, idea)
        script = self._provider.generate(full_prompt)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(script, encoding="utf-8")
        return script

    def _load_template(self, template_path: Path | None) -> str:
        path = template_path or _DEFAULT_TEMPLATE_PATH
        return path.read_text(encoding="utf-8")

    def _build_prompt(self, template_text: str, prompt_text: str, idea: Idea) -> str:
        idea_section = (
            "## 採用アイデア\n"
            f"タイトル: {idea['title']}\n"
            f"テーマ: {idea['theme']}\n"
            f"選定理由: {idea['reason']}\n"
            f"推定スコア: {idea['estimated_score']}\n"
        )
        return (
            f"{template_text.rstrip()}\n\n"
            f"{prompt_text.rstrip()}\n\n"
            f"{idea_section}"
        )
