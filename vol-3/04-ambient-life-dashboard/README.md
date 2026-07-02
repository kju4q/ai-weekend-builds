# 04: Ambient Life Dashboard

A calm, beautiful surface for an old tablet or a second screen. Today's calendar,
the weather, and what's on your mind, rendered as a serene scene that shifts with
the real time of day — sun by day, moon and stars by night — quietly refreshing
itself. Not another app you open. A surface you glance at.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 5-8 hours | Python (standard library) + a single HTML page |

## What you'll build

A single-page web app and a tiny local server. The server pulls your calendar
(from an `.ics` file for the simple path, or Google Calendar for the connected
path), the weather (free, no key), and your tasks, and serves them as JSON. The
page renders it all as a lofi, animated scene with a day/night cycle. Prop up an
old tablet, point it at `localhost`, and you have an ambient life display.

## What you'll learn

- Wiring several real personal data sources into one calm surface
- Connectors: reading calendar data two ways (a local file, and a real API/MCP)
- Serving an API and static files from ~120 lines of standard-library Python
- Design that's genuinely serene — restraint, not another admin panel
- Time-driven UI: letting the real hour drive color, light, and mood

## Prerequisites

- Python 3.10+ (no pip installs for the simple path)
- A browser, and optionally an old tablet or spare monitor
- Optional: a Google account for the connected-calendar path

## Local vs API

| Part | Runs where |
|---|---|
| The dashboard page + animation | 100% local |
| Calendar via `.ics` file | 100% local |
| Weather (Open-Meteo) | Free public API, **no key, no account** |
| Tasks (`tasks.json`) | 100% local |
| Calendar via Google Calendar | Your Google account (OAuth) — see below |

There is **no Anthropic API key required** for this project. The optional "what
matters today" line in `prompts.md` is the only place Claude would come in, and
it's entirely opt-in.

## How it works

```
sample.ics ──┐
tasks.json ──┼──▶ server.py  ──/api/data──▶  index.html
Open-Meteo ──┘     (Python stdlib)            (day/night scene, auto-refresh)
```

## Build it

### Step 1: Run the simple path

```
python server.py
```

Open <http://localhost:8500>. You'll see the clock, today's events from
`sample.ics`, live weather, and your tasks, on a sky that matches the current
hour. Leave it open — it refreshes the data every 5 minutes and re-paints the sky
every minute, on its own.

### Step 2: Make it yours (local calendar)

- Replace `sample.ics` with a real export (most calendar apps can export `.ics`),
  or point the server at one: `ICS_FILE=/path/to/my.ics python server.py`
- Edit `tasks.json` with what's actually on your mind
- Set your location for accurate weather: `LAT=51.51 LON=-0.13 python server.py`

### Step 3: The connected path (Google Calendar)

The simple path uses a file so anyone can run it in one command. For live data,
swap `parse_ics()` for a real calendar read. Two good options:

- **Google Calendar API**: create OAuth credentials, `pip install
  google-api-python-client google-auth-oauthlib`, and fetch today's events in
  `get_events()`. Google's Python quickstart is the fastest route.
- **MCP connector**: if you drive this from an agent (like Claude), a Google
  Calendar MCP server exposes `list_events` directly — no OAuth plumbing of your
  own. This is the "wire real personal data sources into one surface" lesson: the
  dashboard doesn't care where the events came from, only their shape.

Keep the JSON shape identical (`[{time, title}]`) and the page needs no changes.

### Step 4: Make it a real ambient surface

- Put it on an old tablet in kiosk/full-screen mode, screen timeout off
- Prop it where you'll glance at it — kitchen, desk, hallway
- Tune the palette in the `SKIES` object until it's *yours*

## Verify it works

- [ ] `python server.py` serves the page at localhost:8500
- [ ] `curl localhost:8500/api/data` returns events, weather, and tasks as JSON
- [ ] The sky color changes if you compare morning vs. night (or change your clock)
- [ ] Stars fade in at night; the sun/moon sits where the hour puts it

## Extend it

- Add a subtle now-playing line from a local music source
- Show tomorrow's first event after a certain hour ("early start: 8am standup")
- Gentle weather-driven mood: rain streaks, a warmer palette on clear evenings
- A "focus" mode that dims everything but the next event
- Pull tasks from your real system (a local todo file, Things, an MCP connector)

## Common pitfalls

- **Weather looks wrong**: set `LAT`/`LON` for your city; the default is New York.
- **Calendar empty**: the parser is intentionally minimal (SUMMARY + DTSTART). Some
  `.ics` files fold long lines or use timezones — extend `parse_ics()` as needed.
- **It looks like a dashboard, not a scene**: that means you added borders and
  boxes. Resist. The calm comes from space, few elements, and slow motion.
- **Tablet keeps sleeping**: disable screen timeout and enable a full-screen/kiosk
  mode in the browser.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
