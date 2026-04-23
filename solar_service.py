"""Sunrise and sunset helpers for context-aware circadian recommendations."""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import ssl
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


API_BASE = "https://api.sunrise-sunset.org/json"


def format_local_time(value: datetime) -> str:
    return value.strftime("%-I:%M %p")


def fetch_solar_context(latitude: float, longitude: float, day_date: str, timezone_name: str) -> dict:
    query = urlencode(
        {
            "lat": latitude,
            "lng": longitude,
            "date": day_date,
            "formatted": 0,
        }
    )
    url = f"{API_BASE}?{query}"
    request = Request(url, headers={"User-Agent": "SleepSystem/0.1"})
    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as error:
        # Development fallback for environments missing local CA certs.
        if isinstance(error.reason, ssl.SSLCertVerificationError):
            insecure_context = ssl._create_unverified_context()
            with urlopen(request, timeout=5, context=insecure_context) as response:
                payload = json.loads(response.read().decode("utf-8"))
        else:
            raise

    results = payload.get("results", {})
    timezone = ZoneInfo(timezone_name)

    sunrise_utc = datetime.fromisoformat(results["sunrise"].replace("Z", "+00:00"))
    sunset_utc = datetime.fromisoformat(results["sunset"].replace("Z", "+00:00"))

    sunrise_local = sunrise_utc.astimezone(timezone)
    sunset_local = sunset_utc.astimezone(timezone)

    morning_end = sunrise_local + timedelta(minutes=60)
    evening_start = sunset_local - timedelta(minutes=30)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "sunrise_local": format_local_time(sunrise_local),
        "sunset_local": format_local_time(sunset_local),
        "morning_light_window": f"{format_local_time(sunrise_local)}-{format_local_time(morning_end)}",
        "evening_dim_window": f"{format_local_time(evening_start)}-{format_local_time(sunset_local + timedelta(minutes=60))}",
    }
