"""Entry point for ShortsAnalyzer."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from shorts_analyzer import YouTubeAPIError, YouTubeClient
from shorts_analyzer.analysis.duration import analyze_duration
from shorts_analyzer.analysis.hashtag import analyze_hashtags
from shorts_analyzer.analysis.keyword import analyze_keywords
from shorts_analyzer.analysis.pattern import analyze_patterns
from shorts_analyzer.analysis.posting import analyze_posting
from shorts_analyzer.analysis.title import analyze_titles
from shorts_analyzer.analysis.trend import analyze_trends
from shorts_analyzer.ai.openai_provider import OpenAIProvider
from shorts_analyzer.export import save_videos_csv
from shorts_analyzer.generation.idea_generator import Idea, generate_ideas, save_ideas
from shorts_analyzer.generation.prompt_builder import build_script_prompt
from shorts_analyzer.generation.script_generator import ScriptGenerator
from shorts_analyzer.generation.script_scorer import ScriptScorer, save_script_score
from shorts_analyzer.knowledge.exporter import export_knowledge
from shorts_analyzer.knowledge.profile import generate_channel_profile
from shorts_analyzer.statistics import analyze_videos

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_ROOT / "output" / "videos.csv"
GENERATED_PATH = PROJECT_ROOT / "generated"
SCRIPT_PROMPT_PATH = GENERATED_PATH / "script_prompt.txt"
SCRIPT_PATH = GENERATED_PATH / "script.txt"
SCRIPT_SCORE_PATH = GENERATED_PATH / "script_score.json"
IDEAS_PATH = GENERATED_PATH / "ideas.json"
KNOWLEDGE_PATH = PROJECT_ROOT / "knowledge"
CHANNEL_PROFILE_PATH = KNOWLEDGE_PATH / "channel_profile.json"
TEST_TOPIC = "エミュー戦争"
CHANNEL_HANDLE = "@雑学をまとめる犬"
MAX_RESULTS = 100


def _load_env() -> None:
    """Load environment variables from common dotenv file locations."""
    for path in (PROJECT_ROOT / ".env", PROJECT_ROOT / ".env" / "env"):
        if path.is_file():
            load_dotenv(path)
            return

    load_dotenv()


def main() -> None:
    """Fetch channel videos and save them to CSV."""
    _load_env()

    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        print("Set YOUTUBE_API_KEY in .env", file=sys.stderr)
        sys.exit(1)

    client = YouTubeClient(api_key)

    try:
        videos = client.get_channel_videos(CHANNEL_HANDLE, max_results=MAX_RESULTS)
    except YouTubeAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    save_videos_csv(videos, OUTPUT_PATH)

    analysis = analyze_videos(videos)
    title_analysis = analyze_titles(videos)
    posting_analysis = analyze_posting(videos)
    duration_analysis = analyze_duration(videos)
    hashtag_analysis = analyze_hashtags(videos)
    keyword_analysis = analyze_keywords(videos)
    pattern_analysis = analyze_patterns(videos)
    trend_analysis = analyze_trends(videos)

    knowledge = {
        "statistics": analysis,
        "title": title_analysis,
        "posting": posting_analysis,
        "duration": duration_analysis,
        "hashtags": hashtag_analysis,
        "keywords": keyword_analysis,
        "patterns": pattern_analysis,
        "trend": trend_analysis,
    }
    knowledge["channel_profile"] = generate_channel_profile(knowledge)
    export_knowledge(knowledge, KNOWLEDGE_PATH)

    with CHANNEL_PROFILE_PATH.open(encoding="utf-8") as file:
        channel_profile = json.load(file)

    script_prompt = build_script_prompt(channel_profile, TEST_TOPIC)
    SCRIPT_PROMPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCRIPT_PROMPT_PATH.write_text(script_prompt, encoding="utf-8")

    ideas = generate_ideas(
        channel_profile,
        keyword_analysis,
        hashtag_analysis,
        trend_analysis,
        script_prompt,
    )
    save_ideas(ideas, IDEAS_PATH)

    selected_idea: Idea = ideas["ideas"][0]
    script_generator = ScriptGenerator(OpenAIProvider())
    script_text = script_generator.generate_script(
        selected_idea,
        SCRIPT_PROMPT_PATH,
        SCRIPT_PATH,
    )
    script_score = ScriptScorer().score(script_text)
    save_script_score(script_score, SCRIPT_SCORE_PATH)

    print(f"Fetched {len(videos)} videos")
    print(f"Saved to {OUTPUT_PATH}")
    print(f"Exported knowledge to {KNOWLEDGE_PATH}")
    print(f"Prompt saved to {SCRIPT_PROMPT_PATH}")
    print(f"Ideas saved to {IDEAS_PATH}")
    print(f"Script saved to {SCRIPT_PATH}")
    print(f"Script score saved to {SCRIPT_SCORE_PATH}")

    print()
    print("===== Analysis =====")
    print(f"Videos: {analysis['total_videos']}")
    print(f"Average Views: {analysis['average_views']:,.0f}")
    print(f"Median Views: {analysis['median_views']:,.0f}")
    print(f"Max Views: {analysis['max_views']:,}")
    print(f"Min Views: {analysis['min_views']:,}")
    print(f"Average Likes: {analysis['average_likes']:,.0f}")
    print(f"Average Comments: {analysis['average_comments']:,.0f}")
    print(f"Average Duration: {analysis['average_duration_seconds']:.1f} sec")

    print()
    print("===== Title Analysis =====")
    print(f"Average Title Length: {title_analysis['average_title_length']:.1f}")
    print(f"Longest Title Length: {title_analysis['longest_title_length']}")
    print(f"Shortest Title Length: {title_analysis['shortest_title_length']}")
    print(f"Titles with Numbers: {title_analysis['titles_with_numbers']}")
    print(f"Titles with Question Mark: {title_analysis['titles_with_question_mark']}")
    print(
        f"Titles with Exclamation Mark: {title_analysis['titles_with_exclamation_mark']}"
    )
    print(f"Average Hashtag Count: {title_analysis['average_hashtag_count']:.2f}")

    print()
    print("===== Posting Analysis (UTC) =====")
    print("By Weekday:")
    for row in posting_analysis["by_weekday"]:
        print(
            f"  {row['weekday']}: "
            f"{row['video_count']} videos, "
            f"avg views {row['average_views']:,.0f}, "
            f"avg likes {row['average_likes']:,.0f}"
        )

    print("By Hour:")
    for row in posting_analysis["by_hour"]:
        print(
            f"  {row['hour']:02d}:00: "
            f"{row['video_count']} videos, "
            f"avg views {row['average_views']:,.0f}, "
            f"avg likes {row['average_likes']:,.0f}"
        )

    print()
    print("===== Duration Analysis =====")
    print(
        f"Average Duration: {duration_analysis['average_duration_seconds']:.1f} sec"
    )
    print(
        f"Longest Duration: {duration_analysis['longest_duration_seconds']} sec"
    )
    print(
        f"Shortest Duration: {duration_analysis['shortest_duration_seconds']} sec"
    )
    print("Duration Groups:")
    for row in duration_analysis["duration_groups"]:
        print(
            f"  {row['group']} sec: "
            f"{row['video_count']} videos, "
            f"avg views {row['average_views']:,.0f}, "
            f"avg likes {row['average_likes']:,.0f}"
        )

    print()
    print("===== Hashtag Analysis =====")
    print("Top 10 Hashtags:")
    for row in hashtag_analysis["hashtags"][:10]:
        print(
            f"  #{row['tag']}: "
            f"{row['count']} uses, "
            f"avg views {row['average_views']:,.0f}, "
            f"avg likes {row['average_likes']:,.0f}, "
            f"avg comments {row['average_comments']:,.0f}"
        )

    print()
    print("===== Keyword Analysis =====")
    print("Top 20 Keywords:")
    for row in keyword_analysis["keywords"][:20]:
        print(
            f"  {row['keyword']}: "
            f"{row['count']} uses, "
            f"avg views {row['average_views']:,.0f}, "
            f"avg likes {row['average_likes']:,.0f}, "
            f"avg comments {row['average_comments']:,.0f}"
        )

    print()
    print("===== Pattern Analysis =====")
    print("Top 10 Patterns:")
    for row in pattern_analysis["patterns"]:
        print(
            f"  title={row['title_length_group']}, "
            f"duration={row['duration_group']}, "
            f"hour={row['posting_hour_group']}: "
            f"{row['video_count']} videos, "
            f"avg views {row['average_views']:,.0f}, "
            f"avg likes {row['average_likes']:,.0f}"
        )

    print()
    print("===== Trend Analysis =====")
    print("Older Dataset")
    print(f"  Average Views: {trend_analysis['older']['average_views']:,.0f}")
    print(f"  Average Likes: {trend_analysis['older']['average_likes']:,.0f}")
    print(f"  Average Comments: {trend_analysis['older']['average_comments']:,.0f}")
    print(
        f"  Average Duration: {trend_analysis['older']['average_duration']:.1f} sec"
    )

    print("Newer Dataset")
    print(f"  Average Views: {trend_analysis['newer']['average_views']:,.0f}")
    print(f"  Average Likes: {trend_analysis['newer']['average_likes']:,.0f}")
    print(f"  Average Comments: {trend_analysis['newer']['average_comments']:,.0f}")
    print(
        f"  Average Duration: {trend_analysis['newer']['average_duration']:.1f} sec"
    )

    print("Differences")
    print(
        "  Views Change: "
        f"{trend_analysis['differences']['views_change_percent']:+.1f}%"
    )
    print(
        "  Likes Change: "
        f"{trend_analysis['differences']['likes_change_percent']:+.1f}%"
    )
    print(
        "  Comments Change: "
        f"{trend_analysis['differences']['comments_change_percent']:+.1f}%"
    )
    print(
        "  Duration Change: "
        f"{trend_analysis['differences']['duration_change_seconds']:+.1f} sec"
    )

    print()
    print("===== Idea Generation =====")
    print("Top 10 Ideas:")
    for row in ideas["ideas"][:10]:
        print(
            f"  [{row['estimated_score']}] {row['title']} "
            f"({row['theme']})"
        )

    print()
    print("===== Script Generation =====")
    print(f"Selected Idea: {selected_idea['title']} ({selected_idea['theme']})")

    print()
    print("===== Script Score =====")
    print(f"Score: {script_score['score']}/100")
    print(f"Passed: {script_score['passed']}")
    if script_score["issues"]:
        print("Issues:")
        for issue in script_score["issues"]:
            print(f"  - {issue}")


if __name__ == "__main__":
    main()