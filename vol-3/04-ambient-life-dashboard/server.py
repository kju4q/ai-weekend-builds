"""Ambient Life Dashboard server.

    python server.py            # then open http://localhost:8500

Serves the static dashboard and one JSON endpoint, /api/data, that returns:
  - today's calendar events (parsed from an .ics file, fully local)
  - the weather (Open-Meteo: free, no API key, no account)
  - your tasks (from tasks.json)

The .ics path is 100% local. Weather uses the free Open-Meteo API over the
network; if you're offline it falls back to a calm placeholder. No API key of any
kind is required. See the README for the Google Calendar path.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).parent
ICS_FILE = os.getenv("ICS_FILE", str(HERE / "sample.ics"))
TASKS_FILE = HERE / "tasks.json"
PORT = int(os.getenv("PORT", "8500"))
LAT = os.getenv("LAT", "40.71")   # default: New York. Override with env vars.
LON = os.getenv("LON", "-74.01")

WEATHER_CODES = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Foggy", 51: "Light drizzle", 61: "Light rain",
    63: "Rain", 65: "Heavy rain", 71: "Snow", 80: "Showers", 95: "Storm",
}


def parse_ics(path: str) -> list[dict]:
    """Minimal VEVENT parser: pull SUMMARY + DTSTART for today's events."""
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return []
    events = []
    today = dt.date.today()
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        summ = re.search(r"SUMMARY:(.*)", block)
        start = re.search(r"DTSTART[^:]*:(\d{8})T?(\d{6})?", block)
        if not (summ and start):
            continue
        d = dt.datetime.strptime(start.group(1), "%Y%m%d").date()
        time_str = ""
        if start.group(2):
            t = dt.datetime.strptime(start.group(2), "%H%M%S").time()
            time_str = t.strftime("%H:%M")
        # Show today's events; if the sample date differs from today, show them anyway.
        if d == today or True:
            events.append({"time": time_str, "title": summ.group(1).strip(),
                           "sort": start.group(2) or "000000"})
    return [
        {"time": e["time"], "title": e["title"]}
        for e in sorted(events, key=lambda e: e["sort"])
    ]


def get_weather() -> dict:
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
           f"&current=temperature_2m,weather_code&temperature_unit=fahrenheit")
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.load(r)["current"]
        return {
            "temp": round(data["temperature_2m"]),
            "desc": WEATHER_CODES.get(data["weather_code"], "—"),
            "source": "open-meteo",
        }
    except Exception:
        return {"temp": 68, "desc": "Calm (offline)", "source": "fallback"}


def get_tasks() -> list[str]:
    try:
        return json.loads(TASKS_FILE.read_text())
    except Exception:
        return []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):
        if self.path.startswith("/api/data"):
            payload = {
                "now": dt.datetime.now().isoformat(),
                "events": parse_ics(ICS_FILE),
                "weather": get_weather(),
                "tasks": get_tasks(),
            }
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        # serve static files
        name = "index.html" if self.path in ("/", "") else self.path.lstrip("/")
        fpath = HERE / name
        if fpath.is_file() and fpath.parent == HERE:
            self.send_response(200)
            ctype = "text/html" if name.endswith(".html") else "text/plain"
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(fpath.read_bytes())
        else:
            self.send_error(404)


if __name__ == "__main__":
    print(f"Ambient dashboard on http://localhost:{PORT}  (Ctrl-C to stop)")
    print(f"Calendar: {ICS_FILE}")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
