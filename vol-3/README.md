# Vol 3: 5 Life-First Local Builds (July 2026)

5 projects that are tools you build yourself and own. Not workflow hacks — life
stuff: your documents, your money, your voice, your day, your decisions. And
local-first wherever it's possible, so your data never leaves your machine. Each
one teaches a different core concept you'll reuse for years.

| # | Project | Difficulty | Time | What you get |
|---|---------|---|---|---|
| 01 | [Life Admin Brain](01-life-admin-brain) | Medium | 4-6h | Drop in your lease + policies → ask them anything, locally |
| 02 | [Money Map](02-money-map) | Easy-Medium | 3-5h | Bank CSV → where it went + the subscriptions you forgot |
| 03 | [Offline Voice Journal](03-offline-voice-journal) | Medium | 4-6h | Talk 2 min → local transcript → weekly patterns, no cloud |
| 04 | [Ambient Life Dashboard](04-ambient-life-dashboard) | Medium | 5-8h | An old tablet → a calm scene of your day, quietly refreshing |
| 05 | [Decision Simulator](05-decision-simulator) | Advanced | Full day | A big decision → 10,000 simulated futures in one chart |

## Each project teaches a different concept

- **RAG (#1)**: retrieval-augmented generation built from parts — chunking,
  embeddings, and retrieval — so answers come from *your* documents, not the model.
- **Classification (#2)**: turning messy, human-written real-world data (a bank
  CSV) into clean categories, with rules for speed and an LLM for the long tail.
- **Local models (#3)**: running a real speech model (Whisper) on your own
  hardware — the whole game for anything genuinely private.
- **Connectors (#4)**: wiring several real personal data sources — calendar,
  weather, tasks — into one surface, via files or a live API/MCP connector.
- **Simulation (#5)**: Monte Carlo — simulating ten thousand futures instead of
  guessing one, and reading a distribution instead of a point estimate.

Build all 5 and you've covered retrieval, classification, on-device models,
connectors, and simulation — five patterns that show up everywhere.

## Local vs API, at a glance

Every project runs its core **fully locally** — your documents, money, voice, and
decisions never leave your machine. An Anthropic API key is **optional** in every
one, used only for the nicest-phrasing layer (a written answer, warmer advice, a
richer summary), and each has a local fallback so nothing breaks without a key.
Each project's README has the exact breakdown.

## Pick one

If you drown in life admin: start with **#1 Life Admin Brain**. Ask your lease a
question and get an answer — the "why did I not have this" moment.

If you want value in one sitting: **#2 Money Map**. Point it at a CSV, find the
gym you forgot you're paying for.

If you want the most private thing you'll ever build: **#3 Offline Voice Journal**.
A real model on your machine, wifi off.

If you want something beautiful you'll actually keep around: **#4 Ambient Life
Dashboard**. Prop up an old tablet and glance at your day.

If you're facing a real decision right now: **#5 Decision Simulator**. Stop
guessing one future — see ten thousand.

## Want vol 1 or vol 2?

[Go back to the root](../README.md) — vol 2 and vol 1 are linked there.
