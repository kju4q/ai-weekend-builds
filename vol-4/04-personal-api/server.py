"""Personal API: a small local server that gives your own files stable addresses.

    python3 server.py --data-dir .demo-data --seed-sample --port 8765

It binds to 127.0.0.1 and nothing else. There is no host option, no environment
host override, no authentication, and no remote access, because remote access is
deliberately outside the scope of this build.

The server runs in the foreground for exactly as long as this command runs. It
does not daemonize, does not schedule anything, and does not survive Ctrl-C.

Standard library only. No web framework, no database, no model, no API key. The
one optional outbound request is a weather lookup, and it carries nothing but the
coordinates you configured and the names of the weather fields being requested.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import signal
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Bound here and nowhere else. 127.0.0.1 is IPv4 localhost: only this machine can
# reach it. This is a constant on purpose, so that no flag and no environment
# variable can widen it by accident.
HOST = "127.0.0.1"

DEFAULT_PORT = 8765
DEFAULT_DATA_DIR = ".personal-api-data"

MAX_BODY_BYTES = 16 * 1024   # 16 KB request body ceiling
MAX_IDEA_CHARS = 2000

DEFAULT_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_WEATHER_TIMEOUT = 5.0
WEATHER_PROVIDER = "Open-Meteo"
USER_AGENT = "personal-api/1.0 (local weekend build)"

SAMPLE_FILES = ("calendar.json", "tasks.json", "ideas.jsonl")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# One writer at a time, because ThreadingHTTPServer will happily run two POSTs at
# once and a torn append would corrupt a line for good.
_IDEA_LOCK = threading.Lock()


# ---------------------------------------------------------------- helpers

def parse_iso(value: str) -> dt.datetime:
    """Parse an ISO 8601 timestamp. A trailing Z becomes +00:00 for 3.10.

    Offsets are preserved exactly as written in the response. Nothing here
    converts between timezones.
    """
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    return dt.datetime.fromisoformat(text)


def wall_clock(value: dt.datetime) -> dt.datetime:
    """The datetime as written, with any offset dropped.

    Used for sorting and for date matching only. Comparing an aware datetime with
    a naive one raises TypeError, and a calendar file may legitimately hold both,
    so ordering is done on the clock time a human would read off the entry. This
    is not a timezone conversion and is not presented as one.
    """
    return value.replace(tzinfo=None)


def now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json_file(path: pathlib.Path, filename: str) -> tuple[object, list[str], bool]:
    """Return (data, warnings, available). Never raises for ordinary file trouble."""
    if not path.exists():
        return None, [f"{filename} was not found"], False
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, [f"{filename} could not be read ({type(e).__name__})"], False
    if not raw.strip():
        return None, [f"{filename} is empty"], False
    try:
        return json.loads(raw), [], True
    except json.JSONDecodeError as e:
        return None, [f"{filename} is not valid JSON (line {e.lineno}, column {e.colno})"], False


# ---------------------------------------------------------------- loaders

def load_tasks(data_dir: pathlib.Path) -> dict:
    """Every valid task in the file, plus a warning for each entry skipped."""
    data, warnings, available = read_json_file(data_dir / "tasks.json", "tasks.json")
    if not available:
        return {"available": False, "tasks": [], "count": 0, "warnings": warnings}
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        return {"available": False, "tasks": [], "count": 0,
                "warnings": ["tasks.json must be an object with a \"tasks\" list"]}

    tasks, skipped = [], []
    for i, entry in enumerate(data["tasks"]):
        if not isinstance(entry, dict):
            skipped.append(f"task {i + 1} is not an object")
            continue
        tid, text, done = entry.get("id"), entry.get("text"), entry.get("done")
        problems = []
        if not isinstance(tid, str) or not tid.strip():
            problems.append("id must be a non-empty string")
        if not isinstance(text, str) or not text.strip():
            problems.append("text must be a non-empty string")
        if not isinstance(done, bool):
            problems.append("done must be true or false")
        if problems:
            label = tid if isinstance(tid, str) and tid.strip() else f"entry {i + 1}"
            skipped.append(f"task {label} skipped: {', '.join(problems)}")
            continue
        tasks.append({"id": tid, "text": text, "done": done})
    return {"available": True, "tasks": tasks, "count": len(tasks), "warnings": skipped}


def load_calendar(data_dir: pathlib.Path, date_filter: str | None = None) -> dict:
    """Valid events, sorted by start. Filtered to one date when asked."""
    data, warnings, available = read_json_file(data_dir / "calendar.json", "calendar.json")
    if not available:
        return {"available": False, "date_filter": date_filter, "events": [],
                "count": 0, "warnings": warnings}
    if not isinstance(data, dict) or not isinstance(data.get("events"), list):
        return {"available": False, "date_filter": date_filter, "events": [], "count": 0,
                "warnings": ["calendar.json must be an object with an \"events\" list"]}

    events, skipped = [], []
    for i, entry in enumerate(data["events"]):
        if not isinstance(entry, dict):
            skipped.append(f"event {i + 1} is not an object")
            continue
        eid, title, start = entry.get("id"), entry.get("title"), entry.get("start")
        problems = []
        if not isinstance(eid, str) or not eid.strip():
            problems.append("id must be a non-empty string")
        if not isinstance(title, str) or not title.strip():
            problems.append("title must be a non-empty string")
        parsed_start = None
        if not isinstance(start, str):
            problems.append("start must be an ISO 8601 string")
        else:
            try:
                parsed_start = parse_iso(start)
            except ValueError:
                problems.append(f"start {start!r} is not an ISO 8601 datetime")
        end = entry.get("end")
        if end is not None:
            if not isinstance(end, str):
                problems.append("end must be an ISO 8601 string when present")
            else:
                try:
                    parse_iso(end)
                except ValueError:
                    problems.append(f"end {end!r} is not an ISO 8601 datetime")
        if problems:
            label = eid if isinstance(eid, str) and eid.strip() else f"entry {i + 1}"
            skipped.append(f"event {label} skipped: {', '.join(problems)}")
            continue
        record = {"id": eid, "title": title, "start": start}
        if end is not None:
            record["end"] = end
        record["_sort"] = wall_clock(parsed_start)
        events.append(record)

    if date_filter:
        events = [e for e in events if e["_sort"].date().isoformat() == date_filter]
    events.sort(key=lambda e: e["_sort"])
    for e in events:
        del e["_sort"]
    return {"available": True, "date_filter": date_filter, "events": events,
            "count": len(events), "warnings": skipped}


def load_ideas(data_dir: pathlib.Path) -> dict:
    """Ideas in file order. A missing file is a valid empty collection, because
    you have simply not filed an idea yet."""
    path = data_dir / "ideas.jsonl"
    if not path.exists():
        return {"available": True, "ideas": [], "count": 0, "warnings": []}
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        return {"available": False, "ideas": [], "count": 0,
                "warnings": [f"ideas.jsonl could not be read ({type(e).__name__})"]}

    ideas, skipped = [], []
    for number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            skipped.append(f"ideas.jsonl line {number} is not valid JSON, skipped")
            continue
        if not isinstance(entry, dict):
            skipped.append(f"ideas.jsonl line {number} is not an object, skipped")
            continue
        missing = [k for k in ("id", "text", "created_at")
                   if not isinstance(entry.get(k), str) or not entry[k].strip()]
        if missing:
            skipped.append(f"ideas.jsonl line {number} is missing {', '.join(missing)}, skipped")
            continue
        ideas.append({"id": entry["id"], "text": entry["text"],
                      "created_at": entry["created_at"]})
    return {"available": True, "ideas": ideas, "count": len(ideas), "warnings": skipped}


def append_idea(data_dir: pathlib.Path, text: str) -> dict:
    """Append exactly one JSON object and one newline. Never rewrites the file."""
    record = {"id": f"idea-{uuid.uuid4().hex[:12]}", "text": text,
              "created_at": now_utc_iso()}
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with _IDEA_LOCK:
        data_dir.mkdir(parents=True, exist_ok=True)
        with (data_dir / "ideas.jsonl").open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
    return record


# ---------------------------------------------------------------- weather

class WeatherConfig:
    """Read once at startup from the environment. Never from an HTTP request."""

    def __init__(self) -> None:
        self.base_url = os.getenv("WEATHER_API_BASE_URL", DEFAULT_WEATHER_URL).strip() \
            or DEFAULT_WEATHER_URL
        self.timeout = DEFAULT_WEATHER_TIMEOUT
        self.lat: float | None = None
        self.lon: float | None = None
        self.reason = "weather is not configured"
        self.configured = False
        self._load()

    def _load(self) -> None:
        raw_timeout = os.getenv("WEATHER_TIMEOUT_SECONDS", "").strip()
        if raw_timeout:
            try:
                value = float(raw_timeout)
                if value > 0:
                    self.timeout = value
                else:
                    print("WEATHER_TIMEOUT_SECONDS must be positive, "
                          f"using {DEFAULT_WEATHER_TIMEOUT}", file=sys.stderr)
            except ValueError:
                print(f"WEATHER_TIMEOUT_SECONDS is not a number, "
                      f"using {DEFAULT_WEATHER_TIMEOUT}", file=sys.stderr)

        scheme = urllib.parse.urlparse(self.base_url).scheme
        if scheme not in ("http", "https"):
            self.reason = "weather base URL must be http or https"
            return

        lat_raw = os.getenv("WEATHER_LAT", "").strip()
        lon_raw = os.getenv("WEATHER_LON", "").strip()
        if not lat_raw and not lon_raw:
            return
        if not lat_raw or not lon_raw:
            self.reason = "weather needs both WEATHER_LAT and WEATHER_LON"
            return
        try:
            lat, lon = float(lat_raw), float(lon_raw)
        except ValueError:
            self.reason = "weather coordinates are not numbers"
            return
        if not -90.0 <= lat <= 90.0:
            self.reason = "WEATHER_LAT must be between -90 and 90"
            return
        if not -180.0 <= lon <= 180.0:
            self.reason = "WEATHER_LON must be between -180 and 180"
            return
        self.lat, self.lon, self.configured = lat, lon, True
        self.reason = ""

    def provider_label(self) -> str:
        """Name the host actually being contacted.

        Reporting "Open-Meteo" while WEATHER_API_BASE_URL points somewhere else
        would be a small lie in the one field a reader uses to check where their
        coordinates went.
        """
        if self.base_url == DEFAULT_WEATHER_URL:
            return WEATHER_PROVIDER
        host = urllib.parse.urlparse(self.base_url).netloc
        return host or self.base_url

    def describe(self) -> str:
        if self.configured:
            return (f"configured for {self.lat}, {self.lon} via {self.base_url} "
                    f"(timeout {self.timeout}s)")
        return f"not configured ({self.reason})"


def fetch_weather(cfg: WeatherConfig) -> dict:
    """One outbound request, carrying coordinates and field names only.

    Nothing local goes with it: no task, no idea, no calendar entry, no filename,
    no path, no previous response. When it is not configured, no request is made
    at all and this returns before any socket is opened.
    """
    if not cfg.configured:
        return {"available": False, "reason": cfg.reason}

    query = urllib.parse.urlencode({
        "latitude": cfg.lat,
        "longitude": cfg.lon,
        "current": "temperature_2m,weather_code",
        "temperature_unit": "celsius",
    })
    url = f"{cfg.base_url}?{query}"
    # Printed every time a request is actually attempted, so "no request was made"
    # is something you can see in the log rather than something you take on trust.
    print(f"weather: GET {url}", file=sys.stderr)

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=cfg.timeout) as resp:
            if resp.status != 200:
                return {"available": False,
                        "reason": f"weather lookup failed (HTTP {resp.status})",
                        "provider": cfg.provider_label()}
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"available": False, "reason": f"weather lookup failed (HTTP {e.code})",
                "provider": cfg.provider_label()}
    except urllib.error.URLError as e:
        return {"available": False,
                "reason": f"weather lookup failed ({type(e.reason).__name__ if e.reason else 'URLError'})",
                "provider": cfg.provider_label()}
    except TimeoutError:
        return {"available": False, "reason": "weather lookup timed out",
                "provider": cfg.provider_label()}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {"available": False, "reason": "weather response was not valid JSON",
                "provider": cfg.provider_label()}
    except OSError as e:
        return {"available": False, "reason": f"weather lookup failed ({type(e).__name__})",
                "provider": cfg.provider_label()}

    current = payload.get("current")
    if not isinstance(current, dict):
        return {"available": False, "reason": "weather response was missing current values",
                "provider": cfg.provider_label()}
    temperature = current.get("temperature_2m")
    code = current.get("weather_code")
    if not isinstance(temperature, (int, float)):
        return {"available": False, "reason": "weather response was missing temperature_2m",
                "provider": cfg.provider_label()}
    return {"available": True, "provider": cfg.provider_label(),
            "temperature_c": float(temperature),
            "weather_code": code if isinstance(code, int) else None,
            "fetched_at": now_utc_iso()}


# ---------------------------------------------------------------- today

def build_today(data_dir: pathlib.Path, cfg: WeatherConfig, date: str) -> dict:
    calendar = load_calendar(data_dir, date)
    tasks = load_tasks(data_dir)
    weather = fetch_weather(cfg)

    unfinished = [t for t in tasks["tasks"] if not t["done"]]
    tasks_block = {"available": tasks["available"], "tasks": unfinished,
                   "count": len(unfinished), "warnings": tasks["warnings"]}

    warnings = list(calendar["warnings"]) + list(tasks["warnings"])
    if not calendar["available"]:
        warnings.append("calendar is unavailable")
    if not tasks["available"]:
        warnings.append("tasks are unavailable")
    if not weather["available"]:
        warnings.append(weather.get("reason", "weather is unavailable"))

    partial = not (calendar["available"] and tasks["available"] and weather["available"])
    return {"date": date,
            "calendar": {k: calendar[k] for k in ("available", "events", "count", "warnings")},
            "tasks": tasks_block, "weather": weather,
            "partial": partial, "warnings": warnings}


# ---------------------------------------------------------------- http

class Handler(BaseHTTPRequestHandler):
    server_version = "PersonalAPI/1.0"
    sys_version = ""

    data_dir: pathlib.Path
    weather: WeatherConfig
    port: int

    # path -> {method: attribute name}
    ROUTES = {
        "/health": {"GET": "r_health"},
        "/today": {"GET": "r_today"},
        "/calendar": {"GET": "r_calendar"},
        "/tasks": {"GET": "r_tasks"},
        "/ideas": {"GET": "r_ideas"},
        "/weather": {"GET": "r_weather"},
        "/idea": {"POST": "r_post_idea"},
    }

    # -------------------------------------------------- plumbing

    def _send(self, status: int, payload: dict, extra_headers: dict | None = None) -> None:
        body = json.dumps(payload, indent=1, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _error(self, status: int, message: str, extra_headers: dict | None = None) -> None:
        self._send(status, {"error": message, "status": status}, extra_headers)

    def send_error(self, code, message=None, explain=None):
        """Override so that even framework-level failures answer in JSON.

        Without this, a malformed request line returns the stock HTML error page,
        which is a surprising thing for a JSON API to hand back.
        """
        try:
            self._error(int(code), message or "request failed")
        except Exception:
            pass

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{self.log_date_time_string()}  {fmt % args}\n")

    def _dispatch(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        routes = self.ROUTES.get(path)
        if routes is None:
            self._error(404, f"no route for {path}. Known routes: "
                             f"{', '.join(sorted(self.ROUTES))}")
            return
        attr = routes.get(self.command)
        if attr is None:
            allowed = ", ".join(sorted(routes))
            self._error(405, f"{self.command} is not allowed on {path}, use {allowed}",
                        {"Allow": allowed})
            return
        try:
            getattr(self, attr)(urllib.parse.parse_qs(parsed.query))
        except Exception as e:  # a bug here must not take the server down
            self.log_message("unhandled error on %s: %s: %s", path, type(e).__name__, e)
            self._error(500, "the server hit an unexpected error, see its log")

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_HEAD = _dispatch

    def _date_param(self, query: dict, default_today: bool) -> tuple[str | None, bool]:
        """Return (date, ok). Rejects anything that is not a real YYYY-MM-DD."""
        values = query.get("date")
        if not values:
            return (dt.date.today().isoformat() if default_today else None), True
        raw = values[0].strip()
        if not _DATE_RE.match(raw):
            self._error(400, f"date must look like YYYY-MM-DD, got {raw!r}")
            return None, False
        try:
            return dt.date.fromisoformat(raw).isoformat(), True
        except ValueError:
            self._error(400, f"{raw!r} is not a real calendar date")
            return None, False

    # -------------------------------------------------- routes

    def r_health(self, query: dict) -> None:
        self._send(200, {"ok": True, "service": "personal-api",
                         "host": HOST, "port": self.port})

    def r_tasks(self, query: dict) -> None:
        self._send(200, load_tasks(self.data_dir))

    def r_calendar(self, query: dict) -> None:
        date, ok = self._date_param(query, default_today=False)
        if not ok:
            return
        self._send(200, load_calendar(self.data_dir, date))

    def r_ideas(self, query: dict) -> None:
        self._send(200, load_ideas(self.data_dir))

    def r_weather(self, query: dict) -> None:
        self._send(200, fetch_weather(self.weather))

    def r_today(self, query: dict) -> None:
        date, ok = self._date_param(query, default_today=True)
        if not ok:
            return
        self._send(200, build_today(self.data_dir, self.weather, date))

    def r_post_idea(self, query: dict) -> None:
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            self._error(415, "Content-Type must be application/json")
            return

        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self._error(411, "Content-Length is required")
            return
        try:
            length = int(raw_length)
        except ValueError:
            self._error(400, "Content-Length is not a number")
            return
        if length < 0:
            self._error(400, "Content-Length cannot be negative")
            return
        if length > MAX_BODY_BYTES:
            self._error(413, f"request body is larger than {MAX_BODY_BYTES} bytes",
                        {"Connection": "close"})
            return

        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._error(400, "request body is not valid JSON")
            return
        if not isinstance(payload, dict):
            self._error(400, "request body must be a JSON object")
            return

        text = payload.get("text")
        if text is None:
            self._error(400, "\"text\" is required")
            return
        if not isinstance(text, str):
            self._error(400, "\"text\" must be a string")
            return
        text = text.strip()
        if not text:
            self._error(400, "\"text\" cannot be empty")
            return
        if len(text) > MAX_IDEA_CHARS:
            self._error(400, f"\"text\" is longer than {MAX_IDEA_CHARS} characters")
            return

        extra = sorted(set(payload) - {"text"})
        try:
            record = append_idea(self.data_dir, text)
        except OSError as e:
            self.log_message("could not append idea: %s: %s", type(e).__name__, e)
            self._error(500, "the idea could not be written, see the server log")
            return
        response = dict(record)
        if extra:
            response["ignored_fields"] = extra
        self._send(201, response)


# ---------------------------------------------------------------- startup

def seed_sample(data_dir: pathlib.Path) -> None:
    """Copy the tracked fixtures in, without ever overwriting live data."""
    source = pathlib.Path(__file__).parent / "sample-data"
    if not source.is_dir():
        print(f"No sample-data directory next to server.py, nothing to seed.",
              file=sys.stderr)
        return
    data_dir.mkdir(parents=True, exist_ok=True)
    for name in SAMPLE_FILES:
        src, dest = source / name, data_dir / name
        if not src.exists():
            print(f"  sample {name} is missing from sample-data, skipped")
        elif dest.exists():
            print(f"  {name} already exists, left unchanged")
        else:
            shutil.copyfile(src, dest)
            print(f"  copied {name}")


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="server.py",
        description="A local HTTP server for your calendar file, task file, and "
                    "ideas file. Binds to 127.0.0.1 only and runs in the "
                    "foreground until you stop it with Ctrl-C.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n"
               "  python3 server.py --data-dir .demo-data --seed-sample --port 8765\n"
               "  python3 server.py --data-dir ~/personal-api-data\n"
               "\n"
               "environment (used when the matching option is absent):\n"
               "  PERSONAL_API_DATA_DIR   data directory\n"
               "  PERSONAL_API_PORT       port\n"
               "  WEATHER_LAT             latitude, optional\n"
               "  WEATHER_LON             longitude, optional\n"
               "  WEATHER_TIMEOUT_SECONDS request timeout, default 5\n"
               "  WEATHER_API_BASE_URL    weather endpoint, default Open-Meteo\n"
               "\n"
               "There is no host option. The server always binds to 127.0.0.1.\n",
    )


def main() -> int:
    parser = build_parser()
    parser.add_argument("--data-dir", default=None,
                        help="directory holding calendar.json, tasks.json, and "
                             "ideas.jsonl (default: PERSONAL_API_DATA_DIR, "
                             f"otherwise {DEFAULT_DATA_DIR})")
    parser.add_argument("--port", type=int, default=None,
                        help=f"port to listen on (default: PERSONAL_API_PORT, "
                             f"otherwise {DEFAULT_PORT})")
    parser.add_argument("--seed-sample", action="store_true",
                        help="copy the tracked sample-data files into the data "
                             "directory, without overwriting anything already there")
    args = parser.parse_args()

    data_dir = pathlib.Path(
        args.data_dir or os.getenv("PERSONAL_API_DATA_DIR") or DEFAULT_DATA_DIR
    ).expanduser()
    if not data_dir.is_absolute():
        data_dir = (pathlib.Path.cwd() / data_dir).resolve()

    raw_port = args.port if args.port is not None else os.getenv("PERSONAL_API_PORT")
    try:
        port = int(raw_port) if raw_port not in (None, "") else DEFAULT_PORT
    except (TypeError, ValueError):
        print(f"Port {raw_port!r} is not a number.", file=sys.stderr)
        return 2
    if not 1 <= port <= 65535:
        print(f"Port {port} is outside the range 1 to 65535.", file=sys.stderr)
        return 2

    if args.seed_sample:
        print(f"Seeding sample data into {data_dir}")
        seed_sample(data_dir)
        sys.stdout.flush()

    weather = WeatherConfig()

    Handler.data_dir = data_dir
    Handler.weather = weather
    Handler.port = port

    try:
        httpd = ThreadingHTTPServer((HOST, port), Handler)
    except OSError as e:
        print(f"Could not bind {HOST}:{port} ({type(e).__name__}: {e}).", file=sys.stderr)
        print("Another process may already be using that port. Try --port 8766.",
              file=sys.stderr)
        return 2

    print()
    print("Personal API")
    print(f"  URL:            http://{HOST}:{port}")
    print(f"  Data directory: {data_dir}")
    print(f"  Weather:        {weather.describe()}")
    print(f"  Routes:         {', '.join(sorted(Handler.ROUTES))}")
    print("  Bound to 127.0.0.1 only. No remote access, no authentication.")
    print("  Running in the foreground. Stop it with Ctrl-C.")
    print()
    # Flushed explicitly: stdout is block-buffered when this is redirected to a
    # log file, and a startup banner that appears minutes later is no use.
    sys.stdout.flush()

    # Ctrl-C raises KeyboardInterrupt. A plain `kill` sends SIGTERM, which would
    # otherwise end the process without the shutdown below ever running, so it is
    # routed to the same path.
    def on_sigterm(signum, frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, on_sigterm)
    except ValueError:
        pass  # not the main thread, which cannot happen from __main__

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        httpd.shutdown()
        httpd.server_close()
    print("Stopped. The server is no longer listening.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
