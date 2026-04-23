# Sleep System V3

`Sleep System V3` is a portfolio-ready Python project that models how daily behaviors shape recovery, energy, circadian alignment, and next-day performance.

This project is intentionally positioned as a **behavioral performance engine**, not a generic sleep tracker. The goal is to show how physiological signals like sleep timing, caffeine timing, light exposure, stress, movement, and screens can be translated into practical recommendations.

## Why this is a strong portfolio project

- It demonstrates object-oriented design with clear domain models.
- It turns health knowledge into a working decision engine.
- It stores multi-day data and reads patterns over time.
- It creates explainable recommendations instead of just showing raw numbers.
- It can grow into a future AI-assisted product without losing its rule-based foundation.

## Current feature set

- Sleep duration and sleep debt modeling
- Circadian shift estimation from light, screens, and late caffeine
- Recovery and energy scoring
- Performance score for the current day
- Tomorrow score for next-day readiness
- Personalized recommendations
- Previous-day comparison
- Weekly pattern detection using historical logs
- SQLite-backed persistence for the web app
- History page and trend snapshots
- Sunrise/sunset-aware circadian timing recommendations
- Learned ML readiness prediction layered on top of the rule-based engine
- Next-day feedback loop for calibrating predictions against reality
- Daily alignment layer for purpose, tiny steps, and evening reflection
- Morning setup and evening reflection framing for a more natural daily rhythm
- Human-readable clock-time inputs instead of decimal-hour sleep entry

## Project angle

One-line pitch:

> A behavioral operating system that helps students and high-performers understand how today's choices shape tomorrow's energy, focus, and recovery.

## Files

- `sleep_engine.py`: shared domain logic for scoring, recommendations, and trend analysis
- `database.py`: SQLite persistence and legacy log import
- `history_helpers.py`: chart and history presentation helpers
- `solar_service.py`: sunrise/sunset integration for location-aware timing
- `ml_model.py`: trainable regression model for readiness-score prediction
- `app.py`: Flask web app for logging and analyzing daily behavior
- `templates/index.html`: app interface
- `templates/history.html`: history and trend view
- `templates/feedback.html`: next-day outcome entry flow
- `static/styles.css`: visual design for the web app
- `Sleep System V3.py`: main portfolio version
- `Sleep System Dashboard.py`: generates a lightweight HTML dashboard from log data
- `dashboard.html`: generated visual report
- `sleep_system.db`: SQLite database used by the web app
- `log.json`: historical behavior/performance log
- `Sleep System V2.py`: earlier simplified version
- `Sleep System .py`: earlier exploratory version

## How to run

From the project folder:

```bash
python3 "Sleep System V3.py"
```

Then edit the `DayInput(...)` block inside the script to log a new day.

To run the web app:

```bash
python3 app.py
```

Then open `http://127.0.0.1:8000`.

The web app now uses `sleep_system.db` as its main data store. On first run, it seeds the database from `log.json` so your older entries still appear in the new history flow.
It also supports automatic sunrise/sunset timing based on latitude and longitude entered in the form.
The app now includes a feedback loop: after a prediction is made, you can return in the evening and log actual energy, focus, readiness, and reflection.
It also includes a daily alignment layer so users can define what matters each morning, choose three tiny steps, and reflect on what made them feel alive or drained.
Sleep, caffeine timing, and light timing can be entered using normal clock times like `10:00 PM` or `6:30 AM` rather than decimal-hour math.

## Make It Public

Fastest public path:

1. Push this project to GitHub.
2. Create a Render web service from the repo.
3. Use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Deploy and share the generated public URL.

Important:

- This repo includes `render.yaml` and `gunicorn` so it is ready for a basic Render deployment.
- The current app uses `sleep_system.db` (SQLite). On many hosts, local filesystem storage is ephemeral unless you configure persistent storage.
- For a real public beta, the next infrastructure upgrade should be Postgres.

To generate the HTML dashboard:

```bash
python3 "Sleep System Dashboard.py"
```

Then open `dashboard.html` in your browser.

## Example questions this project answers

- Did late caffeine hurt my circadian alignment?
- Which behavior most likely reduced my recovery today?
- Are my recent inputs improving or hurting my projected tomorrow score?
- What is the highest-leverage behavior change I should make next?

## How this differs from Whoop, Apple Watch, or Oura

- Those products are primarily sensors and dashboards for physiological measurement.
- This project is built as an explainable behavior engine that connects choices to outcomes.
- The value is not raw tracking alone. The value is identifying the highest-leverage behavior change for tomorrow.
- It can also incorporate self-reported context like focus, stress, and social quality, which many wearables infer only indirectly.

## Architecture choice

- The scoring and recommendation logic lives in `sleep_engine.py`.
- The Flask app stores entries in SQLite through `database.py`.
- The app can enrich a daily entry with sunrise/sunset context through `solar_service.py`.
- The app can also train an ML model on historical entries and show a learned readiness prediction.
- The feedback loop lets the system compare predictions to actual outcomes and improve over time.
- The alignment layer connects performance with purpose instead of treating health as only a score.
- The CLI runner, dashboard generator, and Flask app all reuse the same engine.
- This separation is intentional: it shows product thinking and keeps the domain model independent from the interface.

## Next steps for expansion

- Add user authentication and multi-user support
- Replace raw latitude/longitude entry with city search and saved user preferences
- Add richer charts directly in the Flask dashboard
- Compare rule-based and ML predictions over time with explicit calibration metrics
- Use actual feedback as the primary target for future personalization
- Swap SQLite for Postgres when you deploy
- Add real predictive modeling from accumulated personal data
- Layer in AI-generated explanations on top of the rule-based engine
