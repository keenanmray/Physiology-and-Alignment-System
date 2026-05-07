"""Simple local diagnostic for the AI coach connection."""

from __future__ import annotations

import os

from ai_coach import generate_ai_coach_summary


def main() -> None:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY is not set in this Terminal session.")
        return

    print(f"OPENAI_API_KEY detected: {key[:8]}...{key[-4:]}")
    if os.getenv("OPENAI_ALLOW_INSECURE_SSL") == "1":
        print("OPENAI_ALLOW_INSECURE_SSL=1 is enabled for local testing.")

    sample_entry = {
        "date": "test",
        "sleep_hours": 8.0,
        "sleep_quality": "good",
        "performance_score": 78,
        "tomorrow_score": 80,
        "ml_prediction": 79,
        "recovery": 76,
        "circadian_status": "aligned",
        "stress": 1,
        "focus_minutes": 120,
        "movement_minutes": 35,
        "screen_minutes": 40,
        "social_quality": 4,
        "north_star": "Build something that helps people",
        "why_it_matters": "I want my work to improve lives",
        "show_up_style": "Present, warm, and grounded",
        "gratitude_items": ["family", "health", "opportunity"],
        "priority_step": "Ship one useful improvement",
        "tiny_steps": ["Go outside", "Work deeply", "Reflect honestly"],
        "insights": ["Sleep and focus looked strong today."],
        "recommendations": ["Keep screens lower tonight."],
    }

    result = generate_ai_coach_summary(sample_entry)

    if result.get("ai_coach_summary"):
        print("AI coach connection works.")
        print()
        print(result["ai_coach_summary"])
        return

    print("AI coach connection failed.")
    print(result.get("ai_coach_status", "Unknown error"))


if __name__ == "__main__":
    main()
