# 04: Personal API

A small local server with endpoints for your life. `/today` merges your calendar,
your tasks, and the weather into one response. `/idea` files a thought. Nothing
leaves localhost.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium-Advanced | 5-8 hours | Python 3.10+ standard library, local JSON and JSONL files, optional Open-Meteo weather. No web framework, no database, no model, no model key. |

That last sentence in the description is meant precisely. The server binds to
`127.0.0.1` and nothing else. Your calendar, tasks, and ideas are read from and
written to your own disk, and no response ever goes anywhere but back to the
client on your machine. The single exception is the optional weather lookup: when
you configure coordinates, those coordinates and the names of the weather fields
being requested go to Open-Meteo, and nothing else does.

## What you'll build

One local server where the parts of your life have addresses. Ask it for `/today`
and it reads your calendar, your task file, and the weather, and hands back a
single response. Post to `/idea` and the thought is filed. It binds to localhost
and stays there.

Every later tool you build can plug into this instead of parsing the same files
again. That is the point of giving your own data an address.

## What you'll learn

What an API is, by building one around your life.

- Endpoints, methods, and responses, learned by needing them rather than reading about them
- Merging several real data sources into one clean response
- Reading and writing your own state through an interface you designed
- Why localhost-only is a real security decision, not a limitation

## Prerequisites

- **Python 3.10 or later.** Verified on **3.12.13** and **3.14.3**, on macOS
  26.5.1, Apple M2 Pro, arm64. The whole build is standard library, so there is
  no version-pinned wheel to go stale. Use `python3` everywhere, including inside
  the activated virtualenv.
- **`curl`** for the endpoint examples below. Any HTTP client works.
- **Setup:**

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  python3 -m pip install -r requirements.txt
  ```

  On Windows the activation line is `venv\Scripts\activate`. Every Python
  invocation stays `python3`.

- **What that install actually does: nothing.** `requirements.txt` lists no
  packages. The observed run took **1.28 seconds**, downloaded **zero project
  packages**, and left the virtualenv holding only pip itself. There is no model,
  no weights file, and no runtime asset. The first server run downloads nothing
  either.
- **Network:** none needed for the entire local demo below. A connection is only
  used if you configure the optional weather coordinates.
- **The data files** are three small documented files in one directory:
  `calendar.json`, `tasks.json`, and `ideas.jsonl`. Their exact shapes are in
  Step 3.
- **The server has to stay running** while you use the curl commands. It runs in
  the foreground and stops when you stop it. Use two terminals: one for the
  server, one for curl.
- **The URL is always** `http://127.0.0.1:<port>`. That is IPv4 localhost.
- **Optional weather** needs a latitude and longitude. No key, no account.

## Local vs API

### The localhost server

| Part | Runs where |
|---|---|
| The server process | Local, bound to `127.0.0.1` only |
| Every endpoint and response | Local |
| `calendar.json`, `tasks.json`, `ideas.jsonl` | Local files on your disk |
| Filing an idea | Local, appended to your file |
| Date filtering and the `/today` merge | Local |
| The runtime data directory | Local |

There is no remote access, no authentication, no account, no multi-user support,
no external storage, no model, and no model key.

**Localhost is a scope decision, not a security system.** Binding to `127.0.0.1`
means another machine on your network cannot reach it. It does not mean nothing
can: any process running on this machine as your user can call these endpoints,
and there is no authentication to stop it. That is an acceptable trade for a
personal tool reading your own files, and it is exactly why the server refuses to
bind anywhere else. There is no `--host` flag and no `HOST` environment variable,
so there is no accidental path from this to a public port.

### The optional weather request

When `WEATHER_LAT` and `WEATHER_LON` are both set, one HTTPS GET goes to
Open-Meteo per `/weather` or `/today` request. This is the one part of the
project that is not local, and it is not described as local anywhere.

Exactly this is sent, and it is visible in the server log on every attempt:

```
weather: GET https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.405&current=temperature_2m%2Cweather_code&temperature_unit=celsius
```

Four query fields: `latitude`, `longitude`, `current`, and `temperature_unit`.
Your coordinates reveal your approximate location to Open-Meteo. **No task, no
idea, no calendar entry, no file path, no filename, and no other response is
ever sent with it.**

When weather is not configured, no request is attempted at all. The code returns
before a socket is opened, and the absence of that log line is the proof.

When weather is configured but fails, `/weather` reports `available: false` with
a short reason and `/today` still returns your calendar and tasks.

## How it works

```
calendar.json    tasks.json    ideas.jsonl
      \              |              /
       \             |             /
        read fresh from disk on each request
                     |
            server.py on 127.0.0.1
                     |
    GET  /health    is it up, which port
    GET  /calendar  all events, or ?date=YYYY-MM-DD
    GET  /tasks     every task, done and not
    GET  /ideas     everything filed so far
    POST /idea      appends one line, never rewrites
    GET  /weather   optional, see below
    GET  /today     that date's events + unfinished tasks + weather
                     |
         optional outbound weather lookup
         coordinates and field names only
```

## Build it

### Step 1: Run it as-is on the sample

In the first terminal, from this folder:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
rm -rf .demo-data
python3 server.py \
  --data-dir .demo-data \
  --seed-sample \
  --port 8765
```

`--seed-sample` copies the tracked fixtures from `sample-data/` into
`.demo-data/`. It never overwrites a file that already exists and it never
touches `sample-data/` itself, so you can always start over by deleting
`.demo-data/`. Startup prints:

```
Seeding sample data into /path/to/vol-4/04-personal-api/.demo-data
  copied calendar.json
  copied tasks.json
  copied ideas.jsonl

Personal API
  URL:            http://127.0.0.1:8765
  Data directory: /path/to/vol-4/04-personal-api/.demo-data
  Weather:        not configured (weather is not configured)
  Routes:         /calendar, /health, /idea, /ideas, /tasks, /today, /weather
  Bound to 127.0.0.1 only. No remote access, no authentication.
  Running in the foreground. Stop it with Ctrl-C.
```

**Leave this terminal open.** The server exists only while this command runs.

In a second terminal, activate the same virtualenv and work through the
endpoints. Every response below was captured from a real run.

```bash
curl -s http://127.0.0.1:8765/health | python3 -m json.tool
```

```json
{
    "ok": true,
    "service": "personal-api",
    "host": "127.0.0.1",
    "port": 8765
}
```

```bash
curl -s http://127.0.0.1:8765/tasks | python3 -m json.tool
```

```json
{
    "available": true,
    "tasks": [
        {"id": "task-1", "text": "Review the Personal API response shape", "done": false},
        {"id": "task-2", "text": "Write the sample calendar fixture", "done": false},
        {"id": "task-3", "text": "Decide what /today should leave out", "done": false},
        {"id": "task-4", "text": "Archive the completed build notes", "done": true},
        {"id": "task-5", "text": "Pick a port that nothing else uses", "done": true}
    ],
    "count": 5,
    "warnings": []
}
```

All five tasks, finished and unfinished. `/today` will filter them.

```bash
curl -s http://127.0.0.1:8765/calendar | python3 -m json.tool
```

Returns all five sample events sorted by start time, from `2026-08-24T09:00:00`
through `2026-09-01T10:00:00`, with `"date_filter": null`.

```bash
curl -s "http://127.0.0.1:8765/calendar?date=2026-08-24" \
  | python3 -m json.tool
```

```json
{
    "available": true,
    "date_filter": "2026-08-24",
    "events": [
        {"id": "event-1", "title": "Project planning", "start": "2026-08-24T09:00:00", "end": "2026-08-24T09:45:00"},
        {"id": "event-2", "title": "Library run", "start": "2026-08-24T13:15:00", "end": "2026-08-24T14:00:00"},
        {"id": "event-3", "title": "Afternoon walk", "start": "2026-08-24T17:30:00"}
    ],
    "count": 3,
    "warnings": []
}
```

Three of five. The sample deliberately puts two events on other dates so the
filter has something to exclude.

```bash
curl -s http://127.0.0.1:8765/ideas | python3 -m json.tool
```

```json
{
    "available": true,
    "ideas": [
        {"id": "idea-1", "text": "Give every local tool one stable address", "created_at": "2026-08-01T12:00:00Z"}
    ],
    "count": 1,
    "warnings": []
}
```

```bash
curl -s http://127.0.0.1:8765/weather | python3 -m json.tool
```

```json
{
    "available": false,
    "reason": "weather is not configured"
}
```

No coordinates are set, so no request was made. Step 5 turns this on.

```bash
curl -s "http://127.0.0.1:8765/today?date=2026-08-24" \
  | python3 -m json.tool
```

```json
{
    "date": "2026-08-24",
    "calendar": {
        "available": true,
        "events": [
            {"id": "event-1", "title": "Project planning", "start": "2026-08-24T09:00:00", "end": "2026-08-24T09:45:00"},
            {"id": "event-2", "title": "Library run", "start": "2026-08-24T13:15:00", "end": "2026-08-24T14:00:00"},
            {"id": "event-3", "title": "Afternoon walk", "start": "2026-08-24T17:30:00"}
        ],
        "count": 3,
        "warnings": []
    },
    "tasks": {
        "available": true,
        "tasks": [
            {"id": "task-1", "text": "Review the Personal API response shape", "done": false},
            {"id": "task-2", "text": "Write the sample calendar fixture", "done": false},
            {"id": "task-3", "text": "Decide what /today should leave out", "done": false}
        ],
        "count": 3,
        "warnings": []
    },
    "weather": {
        "available": false,
        "reason": "weather is not configured"
    },
    "partial": true,
    "warnings": [
        "weather is not configured"
    ]
}
```

Three tasks, not five: `/today` shows only what is unfinished. `partial` is true
because one source, weather, is unavailable, and the reason is named. The
calendar and tasks are there regardless.

`?date=2026-08-24` is used throughout because the tracked sample has fixed dates.
Without it, `/today` uses the system's current date and the sample will look
empty.

Now prove that filing an idea appends rather than replaces.

```bash
wc -l .demo-data/ideas.jsonl
```

```
       1 .demo-data/ideas.jsonl
```

```bash
curl -s \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"Build a local status endpoint"}' \
  http://127.0.0.1:8765/idea \
  | python3 -m json.tool
```

```json
{
    "id": "idea-27f6175446e6",
    "text": "Build a local status endpoint",
    "created_at": "2026-08-24T19:55:33Z"
}
```

```bash
curl -s \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"Connect the next weekend build to this API"}' \
  http://127.0.0.1:8765/idea \
  | python3 -m json.tool
```

```json
{
    "id": "idea-f65ec9cc61cd",
    "text": "Connect the next weekend build to this API",
    "created_at": "2026-08-24T19:55:33Z"
}
```

`id` and `created_at` are generated by the server, so yours will differ. The id
is a random hex suffix and the timestamp is UTC at the moment of the write.

```bash
wc -l .demo-data/ideas.jsonl
cat .demo-data/ideas.jsonl
```

```
       3 .demo-data/ideas.jsonl
{"id":"idea-1","text":"Give every local tool one stable address","created_at":"2026-08-01T12:00:00Z"}
{"id": "idea-27f6175446e6", "text": "Build a local status endpoint", "created_at": "2026-08-24T19:55:33Z"}
{"id": "idea-f65ec9cc61cd", "text": "Connect the next weekend build to this API", "created_at": "2026-08-24T19:55:33Z"}
```

One line became three. The original sample idea is untouched, the first new idea
was not overwritten by the second, and each line is its own JSON object.

```bash
curl -s http://127.0.0.1:8765/ideas | python3 -m json.tool
```

Returns `"count": 3` with all three in file order.

### Step 2: Read the request handler

One file, `server.py`, standard library only.

**Startup.** `main()` parses three flags with `argparse`, then falls back to
`PERSONAL_API_DATA_DIR` and `PERSONAL_API_PORT` when a flag is absent. The flag
always wins. The port is validated against 1 to 65535 and a bad value exits with
code 2 before anything binds. `--seed-sample` calls `seed_sample()`, which copies
each of the three fixtures only if the destination does not already exist.

**The binding.** `HOST` is a module constant set to `127.0.0.1`, used directly in
`ThreadingHTTPServer((HOST, port), Handler)`. There is no flag, no environment
variable, and no code path that changes it. A bind failure prints the reason and
exits 2, which is what you see when the port is already in use.

**Routing.** `Handler.ROUTES` is a dict of path to method to handler name. Every
HTTP verb is wired to one `_dispatch()`, which looks up the path, then the
method. An unknown path is a 404 that lists the routes that do exist; a known
path with the wrong method is a 405 carrying an `Allow` header. `_dispatch()`
also wraps every handler in a try block, so a bug in one route returns a 500 and
leaves the server running.

**Responses.** `_send()` writes JSON with `Content-Type: application/json;
charset=utf-8` and an explicit `Content-Length`. `_error()` wraps it for the
error shape, `{"error": ..., "status": ...}`. `send_error()` is overridden so
that even a framework-level failure answers in JSON rather than the stock HTML
error page, which is a strange thing for a JSON API to hand back.

**The loaders.** `load_tasks()`, `load_calendar()`, and `load_ideas()` each
return an `available` flag, the rows they could parse, a count, and a `warnings`
list naming what was skipped and why. One invalid entry is skipped with a
warning, never an exception. `read_json_file()` centralizes the missing, empty,
unreadable, and malformed cases so the three loaders answer consistently.

**Why the files are read on every request.** No caching. Editing `tasks.json` in
your editor changes the very next response, with no restart, which is exactly
what you want from a personal tool. A cache would need invalidation, and at this
scale a file read costs nothing worth optimizing.

**The append.** `append_idea()` builds the record, serializes one line, takes a
module-level lock, opens the file in `"a"` mode, writes, flushes, and calls
`os.fsync()`. Append mode means the existing lines are never read, rewritten, or
at risk. The lock matters because `ThreadingHTTPServer` will happily run two
POSTs at once, and a torn line would be corrupt permanently.

**The POST validation** in `r_post_idea()` runs in order: content type must be
`application/json`, `Content-Length` must be present and a number, a body over
16 KB is a 413 before it is read, the body must parse as a JSON object, `text`
must exist and be a string, it is trimmed, an empty result is rejected, and over
2000 characters is rejected. Unknown fields are not stored, and the response
lists them under `ignored_fields` so a typo does not vanish silently.

**Weather.** `WeatherConfig` reads the environment once at startup and validates
it: both coordinates or neither, real numbers, latitude within 90, longitude
within 180, and an `http` or `https` base URL. `fetch_weather()` returns
immediately when unconfigured, before any socket is opened. Otherwise it logs the
full URL it is about to request, then makes one `urllib.request` call with a
timeout. Every failure mode, refused connection, DNS failure, timeout, non-200,
unparseable body, missing field, returns `available: false` with a short reason
and never a traceback.

**`/today`.** `build_today()` calls the calendar loader with the date filter, the
task loader, and the weather fetch, then keeps only tasks where `done` is false,
collects warnings from each source, and sets `partial` when any source is
unavailable. It never fails as a whole because one part failed.

**Shutdown.** `serve_forever()` runs until `KeyboardInterrupt`. SIGTERM is routed
to the same path so a plain `kill` also shuts down cleanly instead of dropping
the process mid-request. Both print `Stopped.` and exit 0.

### Step 3: Point it at your own calendar and tasks

Two ways to configure it. The command line wins over the environment.

**CLI path:**

```bash
python3 server.py \
  --data-dir ~/personal-api-data \
  --port 8765
```

**Environment path:**

```bash
cp .env.example .env
# edit the values
set -a
source .env
set +a
python3 server.py
```

Copying `.env.example` does nothing by itself. The server reads ordinary
environment variables, so the file has to be sourced or the variables exported.
The `set -a` around it is what exports everything the file defines.

Keep your real data outside the repository. `~/personal-api-data` is a good
default, and the generated directories used by this README are already
gitignored.

**`tasks.json`:**

```json
{
  "tasks": [
    {"id": "task-1", "text": "Review the Personal API response shape", "done": false},
    {"id": "task-2", "text": "Archive the completed build notes", "done": true}
  ]
}
```

`id` and `text` are non-empty strings, `done` is a boolean. All three are
required. `/tasks` returns every valid task; `/today` returns only those with
`done: false`. There are no due dates, priorities, tags, or projects, and there
is no endpoint that edits a task. Adding one is Step 5 work.

**`calendar.json`:**

```json
{
  "events": [
    {"id": "event-1", "title": "Project planning", "start": "2026-08-24T09:00:00", "end": "2026-08-24T09:45:00"},
    {"id": "event-2", "title": "Afternoon walk", "start": "2026-08-24T17:30:00"}
  ]
}
```

`id`, `title`, and `start` are required; `end` is optional. Dates are ISO 8601
strings that `datetime.fromisoformat` accepts, and a trailing `Z` is handled.
Events come back sorted by start time.

**On timezones, precisely:** an offset you write is preserved exactly as written
in the response. Nothing converts between zones. Sorting and date matching use
the clock time as written, with any offset ignored, because a file may mix naive
and offset-aware entries and comparing the two directly raises an error. So
`2026-08-24T09:00:00+02:00` is filed under `2026-08-24` and sorts at 09:00. If
you need real timezone conversion, that is an extension, and this build does not
claim it.

Recurring events are not supported. There is no `.ics` parsing, no Google
Calendar, no Apple Calendar, and no phone sync. This reads the one JSON shape
documented above. Live calendar connections are listed under Extend it.

**`ideas.jsonl`,** one JSON object per line:

```json
{"id":"idea-1","text":"Give every local tool one stable address","created_at":"2026-08-01T12:00:00Z"}
```

You do not have to create this file. A missing `ideas.jsonl` is a valid empty
collection, `GET /ideas` returns `"count": 0` with no warning, and the first
successful `POST /idea` creates the directory and the file. `id` and `created_at`
are always generated by the server, never taken from your request.

**When something is wrong with a file,** the server keeps serving:

- **Missing** `tasks.json` or `calendar.json`: that endpoint returns
  `"available": false` with `"tasks.json was not found"`, and `/today` returns
  whatever else it has and marks itself partial.
- **Empty or malformed JSON**: `"available": false` with the parse position, for
  example `"tasks.json is not valid JSON (line 1, column 25)"`.
- **One bad entry among good ones**: the good ones are returned and each skipped
  entry gets its own warning naming what was wrong, for example
  `"event bad-2 skipped: start 'not-a-datetime' is not an ISO 8601 datetime"`.
- **A malformed line in `ideas.jsonl`**: that line is skipped with a warning
  giving its line number, and the valid lines are still returned.

Responses name the file, never the full path, so pasting a response into a chat
does not leak your directory layout. The startup banner does print the resolved
data directory, because that is for you, on your machine.

**Edit a file and see it immediately.** With the server still running, change a
task in `.demo-data/tasks.json`, save, and run the curl command again. The new
text is there. No restart, because files are read on every request. Restarting is
only needed when startup configuration changes: the port, the data directory, or
the weather variables.

### Step 4: Add an endpoint of your own

This is an exercise for you, not something the shipped code includes. `/counts`
is not implemented in this repository and is not in the route list or the
verification checklist.

A good first endpoint is deterministic and reuses what already exists. Say
`GET /counts` returning how many events, tasks, unfinished tasks, and ideas you
have.

Add the route to `Handler.ROUTES`:

```python
"/counts": {"GET": "r_counts"},
```

Then a handler beside the others, reusing the loaders rather than reading files
itself:

```python
def r_counts(self, query: dict) -> None:
    calendar = load_calendar(self.data_dir)
    tasks = load_tasks(self.data_dir)
    ideas = load_ideas(self.data_dir)
    self._send(200, {
        "events": calendar["count"],
        "tasks": tasks["count"],
        "tasks_unfinished": sum(1 for t in tasks["tasks"] if not t["done"]),
        "ideas": ideas["count"],
    })
```

That is the whole shape of the exercise: no new file format, no dependency, no
model, no remote access, no authentication. The loaders already handle missing
and malformed files, so your endpoint inherits that for free. Restart the server
and `curl -s http://127.0.0.1:8765/counts` to try it.

### Step 5: Make it yours

- **Change the port:** `--port 8790`, or `PERSONAL_API_PORT=8790`.
- **Move the data outside the repo:** `--data-dir ~/personal-api-data`, so your
  real calendar is nowhere near a git working tree.
- **Add a field to your tasks,** for example a `project` string. Add it to the
  validation in `load_tasks()` and to the record it builds, and document the
  shape where you keep your notes. Validation and documentation move together or
  the format quietly rots.
- **Add another local source.** A `notes.json` beside the others, with its own
  loader following the same `available` and `warnings` shape, is an afternoon.
- **Change what `/today` includes.** It deliberately leaves out ideas, because a
  morning glance is about what is scheduled and what is unfinished. If you
  disagree, `build_today()` is eight lines.
- **Add a launch script** so you do not retype the flags:

  ```bash
  #!/bin/sh
  cd "$(dirname "$0")" && exec ./venv/bin/python3 server.py --data-dir ~/personal-api-data
  ```

- **Turn weather on:**

  ```bash
  export WEATHER_LAT=52.52
  export WEATHER_LON=13.405
  python3 server.py --data-dir .demo-data --port 8765
  ```

  The startup banner then reads `configured for 52.52, 13.405 via
  https://api.open-meteo.com/v1/forecast (timeout 5.0s)`, and `/weather` returns
  a real reading. Verified live: `{"available": true, "provider": "Open-Meteo",
  "temperature_c": 18.4, "weather_code": 0, "fetched_at":
  "2026-08-24T19:58:20Z"}`.
- **Turn weather off:** unset both coordinates. No request is made, `/weather`
  says so, and `/today` still works and marks itself partial.

## How to build this with ChatGPT, Work, and Codex

> Frame this as the workflow a reader follows, not as a record of how this specific
> implementation was produced. Do not claim these tools performed this build.

This project can be built manually from the README alone. The prompts in
[prompts.md](prompts.md) provide an optional AI-assisted path.

- **ChatGPT Chat:** helps you clarify the local file formats, the endpoint
  contracts, the localhost boundary, the weather boundary, the failure behavior,
  and the smallest runnable version, before any code exists.
- **ChatGPT Work:** turns your approved decisions into the ordered five-step
  checklist that this README reflects.
- **Codex:** helps you implement each step, run the server, exercise the
  endpoints with curl, inspect failures, and verify that the code matches what
  the README claims.

## Verify it works

Static and startup:

- [ ] `python3 -m py_compile server.py` is clean
- [ ] `python3 server.py --help` lists exactly `--data-dir`, `--port`, and
      `--seed-sample`, and no host, daemon, model, or key option
- [ ] `grep -n '^HOST = ' server.py` shows `127.0.0.1`, and `0.0.0.0` appears
      nowhere in the file
- [ ] Startup prints the URL `http://127.0.0.1:8765`, the resolved data
      directory, the weather state, and how to stop it
- [ ] `lsof -nP -iTCP:8765 -sTCP:LISTEN` shows the listener on IPv4
      `127.0.0.1:8765`
- [ ] The server starts with no model key of any kind set, and with weather
      unconfigured
- [ ] `--port 99999` and `PERSONAL_API_PORT=70000` each exit with code 2
- [ ] Starting a second server on a port already in use exits 2 with a readable
      message
- [ ] `--port` on the command line overrides `PERSONAL_API_PORT`

Endpoints, with the sample seeded:

- [ ] `GET /health` returns `ok: true` and the configured port
- [ ] `GET /tasks` returns all 5 sample tasks
- [ ] `GET /calendar` returns all 5 events sorted by start
- [ ] `GET /calendar?date=2026-08-24` returns exactly 3 events
- [ ] `GET /ideas` returns the 1 seeded idea
- [ ] `GET /weather` returns `available: false`, reason `weather is not configured`
- [ ] `GET /today?date=2026-08-24` returns 3 events, 3 unfinished tasks,
      `partial: true`, and a weather warning
- [ ] No response contains an absolute path

Append behavior:

- [ ] `wc -l .demo-data/ideas.jsonl` is 1 before posting
- [ ] The first `POST /idea` returns 201 with a generated `id` and `created_at`
- [ ] The second `POST /idea` returns 201 with a different `id`
- [ ] `wc -l` is now 3, exactly two more than before
- [ ] `cat` shows the original line first, then both new lines in order
- [ ] Each line parses as JSON on its own
- [ ] `GET /ideas` returns `count: 3` in the same order

Graceful degradation, using a separate empty data directory:

- [ ] Missing `tasks.json` returns `available: false` and the server keeps running
- [ ] Missing `calendar.json` returns `available: false` and the server keeps running
- [ ] Missing `ideas.jsonl` returns `available: true` with `count: 0`
- [ ] `/today` still answers, marked partial, naming every missing source
- [ ] `POST /idea` into that empty directory creates `ideas.jsonl`

Malformed data, using another separate directory:

- [ ] Malformed `tasks.json` reports the parse position and does not crash
- [ ] A calendar with one valid and four broken events returns the valid one and
      four warnings naming each problem
- [ ] `ideas.jsonl` with a broken line among good ones returns the good ones and
      warns with the line number
- [ ] `/today` remains usable on that directory
- [ ] No response contains a Python traceback

Invalid HTTP input:

- [ ] `?date=not-a-date` returns 400 JSON
- [ ] `?date=2026-02-30` returns 400 JSON
- [ ] Malformed POST JSON returns 400
- [ ] `{}` returns 400 for a missing `text`
- [ ] `{"text":42}` returns 400
- [ ] `{"text":"   "}` returns 400
- [ ] `Content-Type: text/plain` returns 415
- [ ] A 17 KB body returns 413
- [ ] Text over 2000 characters returns 400
- [ ] An unknown route returns 404 JSON listing the real routes
- [ ] `DELETE /idea` returns 405 JSON with an `Allow` header
- [ ] No error response is HTML

Weather:

- [ ] Unconfigured: `/weather` says so and the server log contains no
      `weather: GET` line, which is the proof no request was attempted
- [ ] Unreachable, via `WEATHER_API_BASE_URL=http://127.0.0.1:9/forecast`:
      `/weather` returns `available: false` with a short reason, `/today` still
      returns 3 events and 3 tasks, and the server keeps running
- [ ] Live, with real coordinates: `/weather` returns a temperature and the
      log line shows only `latitude`, `longitude`, `current`, and
      `temperature_unit` were sent
- [ ] With live weather succeeding, `/today` includes it and `partial` is false

Shutdown and hygiene:

- [ ] Ctrl-C prints `Stopping.` then `Stopped.` and exits 0
- [ ] No server process and no listener remains afterwards
- [ ] Nothing was installed as a service and no startup item was created
- [ ] `python3 -m pip install -r requirements.txt` downloads zero packages
- [ ] The first run downloads no model and no runtime asset
- [ ] `git status` shows no `.demo-data/`, no `.env`, no caches, and no personal data
- [ ] `sample-data/` is still tracked and unmodified

## Extend it

- **Point the other projects in this volume at it,** so they read your day from
  one place instead of each parsing their own files

Future extensions, none of them included here:

- Read an `.ics` calendar export and map it into the `calendar.json` shape
- Add a local endpoint for something else you track, like reading or music
- Connect to a task application through its official API
- Add a Google Calendar connector
- Add a local token, if you ever deliberately expose this beyond localhost.
  That changes the security model completely and is a different project
- Add a launch agent or system service so it starts with your machine
- Add write endpoints for tasks, not just ideas

## Common pitfalls

Everything here was observed during verification on macOS 26.5.1 with Python
3.14.3 and 3.12.13.

- **`localhost` is not always `127.0.0.1`.** On many systems `localhost` resolves
  to IPv6 `::1` first, and this server binds IPv4 only. `lsof` confirms the
  listener is on `127.0.0.1:8765`. Use `127.0.0.1` in your URLs, as every command
  here does, and the ambiguity never comes up.
- **A relative `--data-dir` follows your current directory.** `.demo-data` means
  `.demo-data` relative to wherever you ran the command. The startup banner
  prints the resolved absolute path, so check that line if the data looks wrong.
- **The port may already be taken.** Binding fails with
  `[Errno 48] Address already in use` and exit code 2. Pick another port.
- **Copying `.env.example` does nothing on its own.** It is not read
  automatically. Source it with `set -a` or export the variables by hand.
- **Curl quoting differs between shells.** The single-quoted `-d '{"text":"..."}'`
  form here works in bash and zsh. In PowerShell the quoting rules are different
  and the JSON will arrive mangled, which shows up as a 400 for invalid JSON.
- **The sample dates are fixed,** so `/today` with no `?date=` looks empty unless
  you happen to be running this on 2026-08-24. Use `?date=2026-08-24` with the
  sample, and drop it when you point the server at your own data.
- **A malformed file gives you a partial answer, not an error page.** That is
  intentional, and it means a broken `tasks.json` is easy to miss if you do not
  read the `warnings` array.
- **`ideas.jsonl` only appears after the first successful POST.** Before that,
  `GET /ideas` returning `count: 0` is correct, not a bug.
- **Weather stays unavailable until both coordinates are set.** Setting only one
  reports `weather needs both WEATHER_LAT and WEATHER_LON` rather than guessing.
- **A short `WEATHER_TIMEOUT_SECONDS` turns a slow provider into a failure.**
  That is the point of the setting, and the failure is graceful: `/today` keeps
  working. The live lookup took about 1.2 seconds from this machine, so a 1
  second timeout would fail here.
- **A restricted network makes weather unreachable,** and the response says so
  with a short reason rather than a stack trace.
- **The server stops when the command stops.** Closing the terminal, or letting
  the shell exit, ends it. Nothing runs in the background, nothing restarts it,
  and Step 4 of the Lookout project is where scheduling lives, not here.
- **There is no authentication.** Do not put this behind a tunnel or a port
  forward. Any process on this machine running as you can already call it, which
  is fine for a personal tool and not fine for anything exposed.
- **The install genuinely downloads nothing.** If pip prints package downloads,
  you are in the wrong directory or the wrong `requirements.txt`.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
