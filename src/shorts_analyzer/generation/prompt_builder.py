"""Build prompts for script-writing AI from channel profiles."""

from __future__ import annotations

from typing import Any

_TITLE_LENGTH_LABELS = {
    "short": "短め（20文字以内）",
    "medium": "中程度（21〜30文字）",
    "long": "長め（30文字超）",
}


def build_script_prompt(channel_profile: dict[str, Any], topic: str) -> str:
    """Generate a detailed Japanese prompt for a script-writing AI.

    Args:
        channel_profile: Summarized channel profile from analysis results.
        topic: Video topic for the script.

    Returns:
        A single prompt string in Japanese.
    """
    recommended_style = channel_profile.get("recommended_style", {})
    average_duration = float(channel_profile.get("average_duration", 0.0))
    best_title_length = str(channel_profile.get("best_title_length", "medium"))
    average_hashtags = float(channel_profile.get("average_hashtags", 0.0))
    best_posting_period = str(channel_profile.get("best_posting_period", "Unknown"))
    top_keywords = channel_profile.get("top_keywords", [])
    top_hashtags = channel_profile.get("top_hashtags", [])

    title_style = _TITLE_LENGTH_LABELS.get(best_title_length, best_title_length)
    channel_style = recommended_style.get(
        "summary",
        "このチャンネルの成功パターンに合わせて作成してください。",
    )
    keyword_list = "、".join(top_keywords[:10]) if top_keywords else "なし"
    hashtag_list = " ".join(f"#{tag}" for tag in top_hashtags[:10]) if top_hashtags else "なし"
    posting_style = recommended_style.get(
        "posting",
        f"{best_posting_period} の投稿が効果的です。",
    )

    return f"""あなたはYouTube Shorts向けの台本を書くプロの脚本家です。
以下のチャンネル分析結果と指定トピックに基づき、視聴維持率を最大化する台本を作成してください。

## トピック
{topic}

## チャンネルスタイル
{channel_style}

## 推奨動画尺
約 {average_duration:.0f} 秒
- 冒頭3秒で視聴者の興味を引く
- 最後まで離脱させないテンポ感を意識する
- 尺に収まるよう冗長な説明は避ける

## 推奨タイトルスタイル
{title_style}
- タイトルは簡潔でインパクトのある表現にする
- 数字や意外性を使うと効果的
- タイトル案を3つ提案する

## 推奨ハッシュタグ
平均 {average_hashtags:.1f} 個を目安に使用する
推奨タグ: {hashtag_list}

## よく使われるキーワード
{keyword_list}
- 可能であれば自然な形で台本に取り入れる

## 投稿スタイル
{posting_style}
- 想定視聴者が見やすい時間帯を意識した内容構成にする

## 出力形式
以下を日本語で出力してください。

1. タイトル案（3つ）
2. 推奨ハッシュタグ
3. 台本本文（ナレーション形式）
4. 画面演出メモ（任意）

## 注意事項
- 事実関係は正確に、誤情報を含めない
- 雑学系Shortsらしい「驚き」「学び」「テンポ」を重視する
- 専門用語は必要に応じて短く補足する
"""
