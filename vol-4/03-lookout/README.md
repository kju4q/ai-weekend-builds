# 03: Lookout

Sweeps the sources you name every morning and compares what it finds against
every version it has saved. It stays silent while nothing moves, and reports the
diff when something changes.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 4-6 hours | Python 3.10+, cron or a scheduled workflow, local version store, OpenAI API (optional) |

Built with Codex. The runtime needs above are this project's own.

## What you'll build

A daily job that watches the pages you care about so you stop checking them
yourself. It saves every version it fetches, compares the new one against the
history, and says nothing at all on the days nothing changed.

## What you'll learn

Scheduled agents, state, and diffing.

- Storing state between runs, which is what separates an agent from a script
- Diffing versions and deciding what counts as a real change
- Scheduling a job and having it stay quiet by default
- Writing a notification worth reading, because it only arrives when it matters

## Prerequisites

> Finalized during the build. This is the starting assumption, not the final list.

- Python 3.10+
- Somewhere to run a daily job: cron, or a scheduled workflow
- A local store for saved versions
- Optional: an OpenAI API key, only for summarizing what changed

## Local vs API

> Provisional. Confirmed during the build.

| Part | Runs where |
|---|---|
| Fetching your named sources | Local process, over the network |
| Saved version history | 100% local |
| Diffing old against new | 100% local |
| Summarizing what the change means | OpenAI API (only with a key set) |

Without a key you still get the diff. You just read it yourself.

## How it works

> Provisional. The real pipeline lands with the build.

```
your list of sources
   ↓  fetch (daily)
current version
   ↓  compare against saved history
no change  →  stay silent
change     →  diff  →  summarize (optional, hosted)  →  tell you
```

## Build it

> Coming with the build. The five steps below are the shape they will follow.

### Step 1: Run it as-is on the sample

### Step 2: Read the diff logic

### Step 3: Add your own sources

### Step 4: Put it on a schedule

### Step 5: Make it yours

## The prompts

The exact Codex prompts used to build this are in [prompts.md](prompts.md).

## Verify it works

> Checklist lands with the build.

## Extend it

- Teach it which kinds of change you care about, so a reworded footer stays silent
  and a changed price does not

## Common pitfalls

> Filled in from the real build, once there are real failures to warn about.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
