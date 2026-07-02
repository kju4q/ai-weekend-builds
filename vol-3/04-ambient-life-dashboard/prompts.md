# Prompts: Ambient Life Dashboard

Most of this build is design and plumbing, not prompting — the calendar, weather,
and tasks are real data, not generated. But there are two places an LLM makes the
surface feel alive. Both are optional; the dashboard is fully functional without them.

## Prompt 1: "What matters today" (optional AI line)

Add a single, quiet line under the clock that reads the day and says the one true
thing. Feed it the same JSON the page already has:

```
Here is my day as JSON:
{ "events": [...], "weather": {...}, "tasks": [...] }

Write ONE short, calm line (max 12 words) naming the single thing that matters
most today. No emoji, no exclamation, no "don't forget". Sound like a calm friend,
not an assistant. If the day is genuinely open, say something gentle about the space.
```

Wire it into `server.py` as `/api/whatmatters`, call it once per morning (not every
refresh — it doesn't change minute to minute), and render it in the footer.

## Prompt 2: Natural language → calendar (the connector lesson)

The point of #4 is wiring real personal data in. If you drive this from an agent
with calendar access (Google Calendar API or an MCP connector), you can also write
*to* the calendar in plain language:

```
Add "Dentist, 2pm next Tuesday, 45 minutes" to my calendar. Confirm the exact
date and time you scheduled before creating it.
```

The dashboard reads the same calendar back on its next refresh — one surface,
sources flowing both directions.

## Design prompts (for the look, not the code)

If you generate palette or scene ideas, anchor them hard or you'll get neon:

```
Suggest 4 background gradient palettes for an ambient home dashboard: dawn, day,
dusk, night. Muted, low-saturation, calm — think lofi album art and Rothko, not a
weather app. Give hex stops top-to-bottom for each.
```

## Tuning

- **AI line too chatty**: lower the word cap to 8 and add "No verbs like 'remember'
  or 'make sure'."
- **It states the obvious**: add "Skip anything I'd already know by looking. Say the
  non-obvious thing or say nothing."
- **Palettes too bright**: add "Maximum 40% saturation. If in doubt, go dimmer."

## A note on keys

Prompts 1 and 2 need an Anthropic API key (and, for #2, calendar access). The core
dashboard — page, server, weather, `.ics` calendar, tasks — needs **no keys at all**.
