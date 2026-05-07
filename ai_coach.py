"""LLM-powered coaching summary for Sleep System."""

from __future__ import annotations

import json
import os
import ssl
from typing import Any
from urllib import error, request

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional at dev time
    OpenAI = None  # type: ignore[assignment]


API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1-mini"


def build_coach_prompt(entry: dict[str, Any]) -> str:
    tiny_steps = entry.get("tiny_steps") or []
    gratitude_items = entry.get("gratitude_items") or []
    recommendations = entry.get("recommendations") or []
    action_steps = entry.get("action_steps") or []
    insights = entry.get("insights") or []

    parts = [
        "You are an applied AI health coach inside a behavioral performance app.",
        "Write a concise coaching note in plain English.",
        "Keep it to 3 short paragraphs or fewer.",
        "Be specific, encouraging, and practical. Avoid hype, diagnosis, or medical claims.",
        "Connect physiology, performance, and meaning alignment when relevant.",
        "",
        f"Date: {entry.get('date')}",
        f"Sleep hours: {entry.get('sleep_hours')}",
        f"Sleep quality: {entry.get('sleep_quality')}",
        f"Performance score: {entry.get('performance_score')}",
        f"Tomorrow score: {entry.get('tomorrow_score')}",
        f"ML readiness score: {entry.get('ml_prediction')}",
        f"Recovery: {entry.get('recovery')}",
        f"Circadian status: {entry.get('circadian_status')}",
        f"Stress: {entry.get('stress')}",
        f"Focus minutes: {entry.get('focus_minutes')}",
        f"Movement minutes: {entry.get('movement_minutes')}",
        f"Screen minutes: {entry.get('screen_minutes')}",
        f"Social quality: {entry.get('social_quality')}",
        f"North Star: {entry.get('north_star') or 'Not provided'}",
        f"Why it matters: {entry.get('why_it_matters') or 'Not provided'}",
        f"How they want to show up: {entry.get('show_up_style') or 'Not provided'}",
        f"Morning gratitude: {', '.join(gratitude_items) if gratitude_items else 'Not provided'}",
        f"Priority step: {entry.get('priority_step') or 'Not provided'}",
        f"Tiny steps: {', '.join(tiny_steps) if tiny_steps else 'None provided'}",
        f"Grounded action steps: {' | '.join(action_steps) if action_steps else 'None'}",
        f"Rules-based insights: {' | '.join(insights) if insights else 'None'}",
        f"Rules-based recommendations: {' | '.join(recommendations) if recommendations else 'None'}",
    ]
    return "\n".join(parts)


def request_via_http(entry: dict[str, Any], api_key: str, model: str) -> str | None:
    payload = {
        "model": model,
        "instructions": "You are a thoughtful AI health and performance coach inside a web application.",
        "input": build_coach_prompt(entry),
    }
    req = request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    allow_insecure = os.getenv("OPENAI_ALLOW_INSECURE_SSL") == "1"
    context = ssl._create_unverified_context() if allow_insecure else None
    with request.urlopen(req, timeout=20, context=context) as http_response:
        data = json.loads(http_response.read().decode("utf-8"))
    return data.get("output_text")


def generate_ai_coach_summary(entry: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "ai_coach_summary": None,
            "ai_coach_model": None,
            "ai_coach_status": "Set OPENAI_API_KEY to enable the AI coach summary.",
        }

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    try:
        if OpenAI is not None:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=model,
                instructions="You are a thoughtful AI health and performance coach inside a web application.",
                input=build_coach_prompt(entry),
            )
            summary = response.output_text
        else:
            summary = request_via_http(entry, api_key, model)
    except ssl.SSLError:
        try:
            summary = request_via_http(entry, api_key, model)
        except Exception as exc:
            return {
                "ai_coach_summary": None,
                "ai_coach_model": model,
                "ai_coach_status": (
                    "AI coach hit a local SSL certificate problem. "
                    "Set OPENAI_ALLOW_INSECURE_SSL=1 to test locally, or fix your Python certificates. "
                    f"Details: {exc}"
                ),
            }
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        return {
            "ai_coach_summary": None,
            "ai_coach_model": model,
            "ai_coach_status": f"AI coach request failed: {detail[:180] or exc.reason}",
        }
    except Exception as exc:
        return {
            "ai_coach_summary": None,
            "ai_coach_model": model,
            "ai_coach_status": f"AI coach unavailable: {exc}",
        }

    if not summary:
        return {
            "ai_coach_summary": None,
            "ai_coach_model": model,
            "ai_coach_status": "AI coach returned no text.",
        }

    return {
        "ai_coach_summary": summary.strip(),
        "ai_coach_model": model,
        "ai_coach_status": "ready",
    }
