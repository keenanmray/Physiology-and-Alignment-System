"""AI coaching summary for Becoming — powered by Claude."""

from __future__ import annotations

import json
import os
from typing import Any

import anthropic


# ─────────────────────────────────────────────────────────────
# THE SYSTEM PROMPT
# This is Claude's identity inside Becoming.
# This is the most important thing in this file.
# Every word here shapes what the user receives.
# ─────────────────────────────────────────────────────────────

BECOMING_SYSTEM_PROMPT = """You are the inner voice of Becoming — a daily operating system 
for people who refuse to sleepwalk through their lives.

Your role is not to report data back at the user. Your role is to be the wisest, 
most honest coach they have ever had — one who knows their biology AND their soul, 
and speaks to both at once.

The person talking to you has told you what they are working toward (their North Star), 
why it matters to them, and how they want to show up. They have also logged the physical 
signals that shape their energy today. Your job is to bridge those two worlds.

YOUR VOICE:
- Direct and warm. Like a mentor who genuinely believes in them.
- Grounded in their actual data. Never generic.
- Forward-looking. Always about who they are becoming.
- Brief where possible. Every word earns its place.
- Never motivational-poster language. No "you've got this!" or "amazing!".
- Never clinical. You are not reading a report. You are talking to a person.
- Speak to their North Star specifically. If they want to build a company, say that.
  If they want to be a great parent, say that. Make it personal.

YOUR JOB TODAY:
1. Read the situation honestly — what does their biology and intention data actually say?
2. Name one true thing about today that they need to hear
3. Give them 3 steps grounded in BOTH their physiology AND their north star:
   - Step 1 is always biology-first (what their body needs right now to feel alive)
   - Step 2 is always direction-first (one concrete move toward their north star today)
   - Step 3 is always identity-first (how to BE the person they said they want to become)
4. Close with a single sentence that lands. Not a platitude. A truth about today.

RULES:
- Never say "great job" or "well done"
- Never use the word "optimize"
- Never give generic advice that could apply to anyone
- Always reference their actual north star in at least one step
- If their recovery is low, acknowledge it honestly — do not pretend it is fine
- If their biology is strong, tell them to use that window aggressively

Return your response as valid JSON only. No markdown. No preamble. Just the JSON object."""


# ─────────────────────────────────────────────────────────────
# THE PROMPT BUILDER
# This takes the entry data and builds the context
# we hand to Claude. Richer context = smarter response.
# ─────────────────────────────────────────────────────────────

def build_becoming_prompt(entry: dict[str, Any]) -> str:
    """
    Build the user-facing prompt from today's entry.
    
    We pull both sides of the Becoming equation:
    - Identity side: north star, why, how to show up, gratitude, steps
    - Biology side: sleep, light, caffeine, movement, stress, focus
    """

    # Identity inputs
    north_star = entry.get("north_star") or "Not provided"
    why_it_matters = entry.get("why_it_matters") or "Not provided"
    show_up_style = entry.get("show_up_style") or "Not provided"
    priority_step = entry.get("priority_step") or "Not provided"

    tiny_steps = entry.get("tiny_steps") or []
    gratitude_items = entry.get("gratitude_items") or []
    action_steps = entry.get("action_steps") or []
    insights = entry.get("insights") or []
    recommendations = entry.get("recommendations") or []

    # Biology inputs
    sleep_hours = entry.get("sleep_hours", "unknown")
    sleep_quality = entry.get("sleep_quality", "unknown")
    performance_score = entry.get("performance_score", "unknown")
    recovery = entry.get("recovery", "unknown")
    tomorrow_score = entry.get("tomorrow_score", "unknown")
    circadian_status = entry.get("circadian_status", "unknown")
    stress = entry.get("stress", "unknown")
    focus_minutes = entry.get("focus_minutes", 0)
    movement_minutes = entry.get("movement_minutes", 0)
    screen_minutes = entry.get("screen_minutes", 0)
    social_quality = entry.get("social_quality", "unknown")
    caffeine_mg = entry.get("caffeine_mg", 0)
    light_minutes = entry.get("light_minutes", 0)

    # Solar context (if available)
    sunrise = entry.get("sunrise_local") or "unknown"
    morning_window = entry.get("morning_light_window") or "unknown"

    prompt = f"""TODAY'S BECOMING ENTRY

=== WHO THEY ARE BECOMING ===
North Star: {north_star}
Why it matters to them: {why_it_matters}
How they choose to show up today: {show_up_style}
What they are grateful for: {', '.join(gratitude_items) if gratitude_items else 'Nothing logged'}
Tiny steps they set this morning: {', '.join(tiny_steps) if tiny_steps else 'None set'}
Priority step (the one that matters most): {priority_step}

=== THEIR BIOLOGY TODAY ===
Performance score: {performance_score}/100
Recovery score: {recovery}/100
Tomorrow readiness: {tomorrow_score}/100
Circadian status: {circadian_status}
Sleep: {sleep_hours} hours, quality rated as "{sleep_quality}"
Morning light exposure: {light_minutes} minutes
Caffeine: {caffeine_mg}mg
Focus work completed: {focus_minutes} minutes
Movement: {movement_minutes} minutes
Screen time: {screen_minutes} minutes
Stress level: {stress}/5
Social quality: {social_quality}/5
Sunrise today: {sunrise}
Optimal morning light window: {morning_window}

=== WHAT OUR SYSTEM NOTICED ===
Key insights: {' | '.join(insights) if insights else 'None'}
Action steps suggested: {' | '.join(action_steps) if action_steps else 'None'}
Recommendations: {' | '.join(recommendations) if recommendations else 'None'}

=== YOUR TASK ===
Generate today's Becoming readout for this person.
Their North Star is: "{north_star}"
Make every step specific to that direction and grounded in today's biology.
Return valid JSON only, exactly matching this schema:

{{
  "headline": "2-6 word phrase capturing today's real situation",
  "honest_read": "2-3 sentences. What does today's data actually say? Name reality honestly.",
  "step_1": {{
    "label": "Biology",
    "action": "Specific action based on their physiological state right now",
    "why": "One sentence on how this affects how alive they feel today"
  }},
  "step_2": {{
    "label": "Direction",
    "action": "One specific move toward their north star today — tangible and doable",
    "why": "One sentence connecting this to their larger goal"
  }},
  "step_3": {{
    "label": "Identity",
    "action": "One way to BE the person they said they want to become today",
    "why": "One sentence anchoring this to who they are becoming"
  }},
  "closing_truth": "One sentence. Make it land. Not a platitude — a truth about today.",
  "energy_window": "Their peak performance window today based on sleep and circadian data (e.g. 9am-12pm)",
  "pattern_note": "If there is a meaningful pattern to flag, one brief sentence. Otherwise null."
}}"""

    return prompt


# ─────────────────────────────────────────────────────────────
# THE MAIN FUNCTION
# This is what app.py calls. Same interface as before
# so nothing else in your codebase needs to change.
# ─────────────────────────────────────────────────────────────

def generate_ai_coach_summary(entry: dict[str, Any]) -> dict[str, Any]:
    """
    Generate the Becoming readout using Claude.
    
    Called from app.py exactly like before:
        entry_payload.update(generate_ai_coach_summary(entry_payload))
    
    Returns a dict that gets merged into the entry and passed to the template.
    """

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return {
            "ai_coach_summary": None,
            "ai_coach_model": None,
            "ai_coach_status": "Set ANTHROPIC_API_KEY to enable the Becoming AI readout.",
            "becoming_readout": None,
        }

    try:
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
            system=BECOMING_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": build_becoming_prompt(entry)}
            ],
            timeout=30,
        )

        raw = message.content[0].text.strip()
        print(f"CLAUDE RAW RESPONSE: {raw[:100]}")
        # Strip markdown code fences if Claude wrapped the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        readout = json.loads(raw)
        # Build the plain-text summary for backward compatibility
        # (your template currently uses ai_coach_summary as a text block)
        plain_summary = _readout_to_plain_text(readout)

        return {
            "ai_coach_summary": plain_summary,
            "ai_coach_model": "claude-sonnet-4-6",
            "ai_coach_status": "ready",
            "becoming_readout": readout,  # structured version for future UI upgrade
        }

    except json.JSONDecodeError:
        # Claude returned something we couldn't parse — use raw text
        return {
            "ai_coach_summary": raw if "raw" in dir() else "Readout unavailable.",
            "ai_coach_model": "claude-sonnet-4-6",
            "ai_coach_status": "ready",
            "becoming_readout": None,
        }

    except Exception as exc:
        import traceback
        traceback.print_exc()  # This will show in Render logs
        return {
            "ai_coach_summary": None,
            "ai_coach_model": "claude-sonnet-4-6",
            "ai_coach_status": f"AI readout unavailable: {exc}",
            "becoming_readout": None,
        }


def _readout_to_plain_text(readout: dict) -> str:
    """
    Convert the structured JSON readout into plain text
    for your existing template that expects ai_coach_summary as a string.
    
    Once you upgrade your template to use the structured readout,
    you can remove this function.
    """
    parts = []

    headline = readout.get("headline", "")
    if headline:
        parts.append(headline.upper())
        parts.append("")

    honest_read = readout.get("honest_read", "")
    if honest_read:
        parts.append(honest_read)
        parts.append("")

    for step_key in ["step_1", "step_2", "step_3"]:
        step = readout.get(step_key, {})
        if step:
            label = step.get("label", "")
            action = step.get("action", "")
            why = step.get("why", "")
            parts.append(f"{label}: {action}")
            if why:
                parts.append(f"  → {why}")

    parts.append("")

    energy_window = readout.get("energy_window", "")
    if energy_window:
        parts.append(f"Peak window: {energy_window}")

    closing = readout.get("closing_truth", "")
    if closing:
        parts.append("")
        parts.append(closing)

    pattern = readout.get("pattern_note")
    if pattern:
        parts.append("")
        parts.append(f"Pattern: {pattern}")

    return "\n".join(parts)

# ─────────────────────────────────────────────────────────────
# EVENING REFLECTION
# Called after the user submits their evening check-in.
# Compares morning intention with evening reality.
# ─────────────────────────────────────────────────────────────

EVENING_SYSTEM_PROMPT = """You are the evening voice of Becoming.

The day is done. Your job is not to judge it — it's to help the person
see it clearly, learn from it honestly, and carry the right thing into tomorrow.

YOUR VOICE:
- Calm and clear. The day is over. No urgency.
- Honest without being harsh. Name what happened.
- Forward-looking. Always end facing tomorrow.
- Brief. This is a closing note, not a report.
- Never say "great job" or praise effort generically.
- If they fell short of their intention, say so gently but directly.
- If they showed up well, name specifically what that looked like.

Return valid JSON only. No markdown. No preamble."""


def build_evening_prompt(entry: dict[str, Any]) -> str:
    # Morning intention
    north_star = entry.get("north_star") or "Not provided"
    show_up_style = entry.get("show_up_style") or "Not provided"
    priority_step = entry.get("priority_step") or "Not provided"
    tiny_steps = entry.get("tiny_steps") or []

    # Evening reality
    actual_energy = entry.get("actual_energy")
    actual_focus = entry.get("actual_focus")
    alive_moment = entry.get("alive_moment") or "Not logged"
    drained_moment = entry.get("drained_moment") or "Not logged"
    alignment_score = entry.get("alignment_score")
    evening_lesson = entry.get("evening_lesson") or "Not logged"

    # Biology context
    performance_score = entry.get("performance_score")
    recovery = entry.get("recovery")

    prompt = f"""EVENING REFLECTION — {entry.get('date', 'today')}

=== WHAT THEY INTENDED THIS MORNING ===
North Star: {north_star}
How they planned to show up: {show_up_style}
Priority step: {priority_step}
Tiny steps: {', '.join(tiny_steps) if tiny_steps else 'None set'}

=== WHAT ACTUALLY HAPPENED ===
Actual energy (0-100): {actual_energy if actual_energy is not None else 'Not logged'}
Actual focus (0-100): {actual_focus if actual_focus is not None else 'Not logged'}
What made them feel alive: {alive_moment}
What drained them: {drained_moment}
Self-reported alignment (0-100): {alignment_score if alignment_score is not None else 'Not logged'}
Lesson from today: {evening_lesson}

=== BIOLOGY CONTEXT ===
Morning performance score: {performance_score}/100
Morning recovery score: {recovery}/100

=== YOUR TASK ===
Compare morning intention with evening reality.
Their north star is: "{north_star}"
Return valid JSON only, matching this schema exactly:

{{
  "headline": "2-5 words capturing what today actually was",
  "reflection": "2-3 sentences comparing intention vs reality. Specific and honest.",
  "highlight": "The one thing worth carrying forward — what went right or what was learned.",
  "tomorrow_seed": "One specific thing to bring into tomorrow morning."
}}"""

    return prompt


def generate_evening_reflection(entry: dict[str, Any]) -> dict[str, Any]:
    """
    Generate the evening reflection using Claude.
    Called from app.py after the evening form is saved.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return {
            "evening_reflection": None,
            "evening_status": "No API key set.",
        }

    try:
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=EVENING_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": build_evening_prompt(entry)}
            ],
            timeout=30,
        )

        raw = message.content[0].text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        reflection = json.loads(raw)

        return {
            "evening_reflection": reflection,
            "evening_status": "ready",
        }

    except json.JSONDecodeError:
        return {
            "evening_reflection": None,
            "evening_status": "Parse error",
        }

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return {
            "evening_reflection": None,
            "evening_status": f"Unavailable: {exc}",
        }