# 03. Lookout

**Difficulty**: Medium | **Time**: 4-6h

## What it is

Sweeps the sources you name every morning and compares what it finds against
every version it has saved. It stays silent while nothing moves, and reports the
diff when something changes.

## What you'll learn

Scheduled agents, state, and diffing.

## What you'll need

> Finalized during the build. The list below is the starting assumption, not the
> final one.

- Python 3.10+
- Somewhere to run a daily job, cron or a scheduled workflow
- A local store for saved versions
- An OpenAI API key, only for summarizing what changed

## Build steps

> Coming with the build. This section will hold the real step-by-step once the
> project is built.

## What to build next

Teach it which kinds of change you care about, so a reworded footer stays silent
and a changed price does not.
