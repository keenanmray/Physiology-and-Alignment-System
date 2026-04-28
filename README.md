# Becoming

`Becoming` is a beta daily alignment and physiology app. It helps people set clear intentions, log a few key body-and-behavior inputs, and get a simple performance score out of 100 with grounded next steps.

Project link:

https://github.com/keenanmray/Physiology-and-Alignment-System

## What the user does

1. Set a morning intention.
2. Choose how to show up.
3. Log gratitude, sleep, stress, light, caffeine, movement, and focus.
4. Get a performance score out of 100.
5. Read a short explanation and follow the 3 next steps.
6. Come back later and reflect on how the day actually felt.

## What the app gives back

- Performance score out of 100
- Recovery score out of 100
- Tomorrow score out of 100
- 3 grounded action steps tied to the user's goals and physiology
- Circadian guidance
- Top recommendations based on the day
- Morning intention snapshot
- Simple history view for tracking change over time

## Core idea

`Becoming` is not trying to be another passive health dashboard. It is a daily system that helps people connect:

- who they want to become
- how they want to show up
- what their physiology is telling them
- what actions matter most today

## How to run

From the project folder:

```bash
python3 app.py
```

Then open `http://127.0.0.1:8000`.

The web app uses `sleep_system.db` as its main data store. On first run, it seeds the database from `log.json` so older entries still appear in the history view.

## Behind the scenes in plain English

- The app uses a rules engine to turn daily inputs into scores and recommendations.
- Sleep, stress, screens, caffeine timing, light, movement, and focus all push the score up or down.
- The recommendations are not random. They come from the specific inputs that looked most important that day.
- The 3 next steps are grounded in both the user's stated direction and the physiology signals from that day.
- The app stores entries over time so users can compare today with previous days.
- There is also a lightweight ML layer in the background that can learn patterns from history, but the user-facing beta is intentionally kept simple.

## What makes it different

Most competitors focus mainly on measurement.

`Becoming` focuses on:

- identity and intention, not just metrics
- grounded next steps, not just scores
- physiology plus meaning, not physiology alone
- helping users move toward the person they want to become

## Share it with others

To give other people one link they can open, deploy it to the web.

Fastest path:

1. Push this project to GitHub.
2. Create a Render web service from the repo.
3. Use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Deploy and share the generated Render URL.

Important:

- This repo includes `render.yaml` and `gunicorn` so it is ready for a basic Render deployment.
- The current app uses `sleep_system.db` (SQLite). On many hosts, local filesystem storage is temporary unless you configure persistent storage.
- For a real public beta, the next infrastructure upgrade should be Postgres and user accounts.

## Next steps

- Add user authentication and private per-user data
- Replace raw latitude/longitude entry with city search
- Improve the 3-step engine with stronger goal parsing
- Add richer trend views
- Expand reflection and feedback loops
