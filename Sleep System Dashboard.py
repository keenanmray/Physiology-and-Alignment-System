"""Generate a lightweight HTML dashboard for Sleep System log data."""

from __future__ import annotations

import json
import math
import os
from statistics import mean


LOG_FILE = "log.json"
OUTPUT_FILE = "dashboard.html"


def load_logs(path: str = LOG_FILE) -> list[dict]:
    if not os.path.exists(path):
        return []

    logs = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return logs


def sleep_hours(entry: dict) -> float | None:
    if "sleep_hours" in entry and isinstance(entry["sleep_hours"], (int, float)):
        return round(float(entry["sleep_hours"]), 2)

    start = entry.get("sleep_start")
    end = entry.get("sleep_end")
    if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
        return None
    if end >= start:
        return round(end - start, 2)
    return round((24 - start) + end, 2)


def numeric_series(logs: list[dict], key: str) -> list[float | None]:
    series = []
    for entry in logs:
        value = entry.get(key)
        if isinstance(value, (int, float)):
            series.append(float(value))
        else:
            series.append(None)
    return series


def sleep_series(logs: list[dict]) -> list[float | None]:
    return [sleep_hours(entry) for entry in logs]


def average(values: list[float | None]) -> str:
    clean = [value for value in values if value is not None]
    if not clean:
        return "N/A"
    return f"{round(mean(clean), 1)}"


def latest_value(values: list[float | None], suffix: str = "") -> str:
    clean = [value for value in values if value is not None]
    if not clean:
        return "N/A"
    return f"{round(clean[-1], 1)}{suffix}"


def trend_delta(values: list[float | None], suffix: str = "") -> str:
    clean = [value for value in values if value is not None]
    if len(clean) < 2:
        return "No trend yet"
    delta = round(clean[-1] - clean[-2], 1)
    if delta == 0:
        return "Flat vs last entry"
    direction = "up" if delta > 0 else "down"
    return f"{direction} {abs(delta)}{suffix} vs last entry"


def polyline_svg(values: list[float | None], color: str, label: str) -> str:
    width = 640
    height = 220
    padding = 24
    clean = [value for value in values if value is not None]
    if len(clean) < 2:
        return f"""
        <div class="chart-card">
          <h3>{label}</h3>
          <p class="empty">Not enough data to draw this chart yet.</p>
        </div>
        """

    minimum = min(clean)
    maximum = max(clean)
    if math.isclose(minimum, maximum):
        minimum -= 1
        maximum += 1

    step_x = (width - padding * 2) / (len(values) - 1)
    points = []
    last_valid_index = None

    for index, value in enumerate(values):
        if value is None:
            continue
        x = padding + index * step_x
        normalized = (value - minimum) / (maximum - minimum)
        y = height - padding - normalized * (height - padding * 2)
        points.append(f"{round(x, 1)},{round(y, 1)}")
        last_valid_index = index

    grid_lines = []
    for row in range(4):
        y = padding + row * ((height - padding * 2) / 3)
        grid_lines.append(
            f'<line x1="{padding}" y1="{round(y,1)}" x2="{width - padding}" y2="{round(y,1)}" class="grid" />'
        )

    return f"""
    <div class="chart-card">
      <div class="chart-head">
        <h3>{label}</h3>
        <span>{round(clean[-1], 1)} latest</span>
      </div>
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="{label} trend line">
        {''.join(grid_lines)}
        <polyline fill="none" stroke="{color}" stroke-width="4" points="{' '.join(points)}" />
      </svg>
      <div class="chart-range">
        <span>Min {round(min(clean), 1)}</span>
        <span>Max {round(max(clean), 1)}</span>
      </div>
    </div>
    """


def recent_recommendations(logs: list[dict]) -> list[str]:
    if not logs:
        return ["No recommendations yet. Log more days to generate guidance."]

    latest = logs[-1]
    flags = latest.get("behavior_flags", [])
    recommendations = []

    if "short_sleep" in flags:
        recommendations.append("Short sleep showed up in the latest entry. Protect a longer sleep window tonight.")
    if "late_caffeine" in flags:
        recommendations.append("Late caffeine is present. Move stimulants earlier to protect circadian timing.")
    if "high_screen" in flags:
        recommendations.append("Screen load is elevated. Tighten evening screen exposure to support recovery.")
    if "high_stress" in flags:
        recommendations.append("Stress is elevated. Add a deliberate downshift ritual before bed.")

    if not recommendations:
        recommendations.append("Your latest entry looks stable. Use consistency as the current performance strategy.")

    return recommendations[:3]


def build_html(logs: list[dict]) -> str:
    dates = [entry.get("date", "Unknown") for entry in logs]
    performance = numeric_series(logs, "performance_score")
    tomorrow = numeric_series(logs, "tomorrow_score")
    recovery = numeric_series(logs, "recovery")
    circadian_shift = numeric_series(logs, "circadian_shift")
    sleep = sleep_series(logs)

    latest_date = dates[-1] if dates else "No data"
    recommendations = recent_recommendations(logs)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sleep System Dashboard</title>
  <style>
    :root {{
      --bg: #f4efe5;
      --panel: #fffaf2;
      --ink: #1e1d1a;
      --muted: #6a655b;
      --accent: #0b6e4f;
      --accent-2: #d17b0f;
      --accent-3: #235789;
      --line: #d8cfbf;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, rgba(209,123,15,0.14), transparent 24%),
        radial-gradient(circle at top right, rgba(35,87,137,0.12), transparent 22%),
        var(--bg);
      color: var(--ink);
    }}
    .wrap {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 40px 20px 72px;
    }}
    .hero {{
      display: grid;
      gap: 18px;
      padding: 28px;
      border: 1px solid var(--line);
      background: linear-gradient(135deg, rgba(255,250,242,0.96), rgba(246,239,228,0.94));
      border-radius: 24px;
      box-shadow: 0 12px 40px rgba(44, 36, 24, 0.08);
    }}
    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-size: 12px;
      color: var(--muted);
      margin: 0;
    }}
    h1, h2, h3, p {{ margin: 0; }}
    h1 {{
      font-size: clamp(2.2rem, 4vw, 4rem);
      line-height: 0.95;
      max-width: 10ch;
    }}
    .sub {{
      max-width: 60ch;
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.5;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 12px;
      background: rgba(255,255,255,0.6);
      font-size: 0.95rem;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-top: 18px;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
    }}
    .stat .label {{
      color: var(--muted);
      font-size: 0.9rem;
      margin-bottom: 6px;
    }}
    .stat .value {{
      font-size: 2rem;
      line-height: 1;
      margin-bottom: 6px;
    }}
    .stat .delta {{
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .section {{
      margin-top: 26px;
    }}
    .charts {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-top: 12px;
    }}
    .chart-card, .notes {{
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--panel);
      padding: 18px;
    }}
    .chart-head {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }}
    .chart-head span, .chart-range, .empty {{
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .chart-range {{
      display: flex;
      justify-content: space-between;
      margin-top: 10px;
    }}
    svg {{
      width: 100%;
      height: auto;
      display: block;
      overflow: visible;
    }}
    .grid {{
      stroke: #e9dfd0;
      stroke-width: 1;
    }}
    .notes ul {{
      margin: 12px 0 0;
      padding-left: 18px;
    }}
    .notes li {{
      margin-bottom: 10px;
      line-height: 1.4;
    }}
    @media (max-width: 640px) {{
      .wrap {{
        padding: 20px 14px 40px;
      }}
      .hero {{
        padding: 20px;
      }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <p class="eyebrow">Sleep System Dashboard</p>
      <h1>Behavior drives tomorrow.</h1>
      <p class="sub">
        This dashboard reframes your project away from generic sleep tracking and toward
        a behavioral performance engine: a system that links daily choices to recovery,
        energy, circadian alignment, and next-day readiness.
      </p>
      <div class="meta">
        <span class="pill">Latest entry: {latest_date}</span>
        <span class="pill">Tracked days: {len(logs)}</span>
        <span class="pill">Portfolio angle: explainable decision engine</span>
      </div>
      <div class="stats">
        <article class="stat">
          <div class="label">Latest Performance</div>
          <div class="value">{latest_value(performance)}</div>
          <div class="delta">{trend_delta(performance, ' pts')}</div>
        </article>
        <article class="stat">
          <div class="label">Avg Sleep Hours</div>
          <div class="value">{average(sleep)}</div>
          <div class="delta">{trend_delta(sleep, ' hrs')}</div>
        </article>
        <article class="stat">
          <div class="label">Latest Tomorrow Score</div>
          <div class="value">{latest_value(tomorrow)}</div>
          <div class="delta">{trend_delta(tomorrow, ' pts')}</div>
        </article>
        <article class="stat">
          <div class="label">Latest Recovery</div>
          <div class="value">{latest_value(recovery)}</div>
          <div class="delta">{trend_delta(recovery, ' pts')}</div>
        </article>
      </div>
    </section>

    <section class="section">
      <h2>Trends</h2>
      <div class="charts">
        {polyline_svg(performance, '#0b6e4f', 'Performance Score')}
        {polyline_svg(sleep, '#d17b0f', 'Sleep Duration')}
        {polyline_svg(circadian_shift, '#235789', 'Circadian Shift')}
        {polyline_svg(tomorrow, '#7a4b94', 'Tomorrow Score')}
      </div>
    </section>

    <section class="section charts">
      <article class="notes">
        <h3>Why this is different from wearables</h3>
        <ul>
          <li>Wearables mostly measure physiology. This project explains which behaviors likely caused the signal.</li>
          <li>Wearables often focus on scores and passive monitoring. This system focuses on decisions and behavior changes.</li>
          <li>Your wedge is contextual reasoning: sleep, caffeine, screens, stress, movement, and focus all live in one behavioral model.</li>
        </ul>
      </article>
      <article class="notes">
        <h3>Current recommendations</h3>
        <ul>
          {''.join(f'<li>{item}</li>' for item in recommendations)}
        </ul>
      </article>
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    logs = load_logs()
    html = build_html(logs)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        handle.write(html)
    print(f"Dashboard written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
