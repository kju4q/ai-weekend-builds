# 05: Freedom Calculator

Takes your income with its real variability, plus what you actually spend, and
simulates the next year ten thousand times. You change an input and watch how the
outcome moves. This is exploration from your own assumptions, not financial advice.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Advanced | Full day | Python 3.10+ (standard library), no model key needed |

Built with Codex. The runtime needs above are this project's own.

## What you'll build

A simulation of your next year, run ten thousand times from numbers you supply.
Income with its real month-to-month variance, spending as it actually is, and a
chart showing where the futures cluster and how bad the bad ones get. Change one
assumption and watch the whole distribution move.

## What you'll learn

Probabilistic thinking, volatility, percentiles, distributions.

- Modeling a number as a distribution instead of a single guess
- Volatility as an input you can state honestly
- Reading percentiles, and why the median is not the story
- Watching how one changed assumption moves the tails

## Prerequisites

> Finalized during the build. This is the starting assumption, not the final list.

- Python 3.10+
- Your own numbers: income history and real spending
- No model key needed for the simulation itself

## Local vs API

> Provisional. Confirmed during the build.

| Part | Runs where |
|---|---|
| Reading your assumptions | 100% local |
| The ten thousand simulation runs | 100% local |
| Percentiles and the chart | 100% local |

Your income and spending never leave the machine. No hosted model runs the
simulation, and none is required to read the result.

## How it works

> Provisional. The real pipeline lands with the build.

```
your assumptions (income, variance, spending)
   ↓  sample 10,000 times
10,000 versions of next year
   ↓  percentiles + distribution
a chart you can read, and re-read after changing one input
```

## Build it

> Coming with the build. The five steps below are the shape they will follow.

### Step 1: Run it as-is on the sample

### Step 2: Read the simulation engine

### Step 3: Change one assumption and watch the tails move

### Step 4: Model your own year

### Step 5: Make it yours

## The prompts

The exact Codex prompts used to build this are in [prompts.md](prompts.md).

## Verify it works

> Checklist lands with the build.

## Extend it

- Add a second scenario and run both against the same ten thousand draws, so the
  comparison is fair rather than two separate rolls of the dice

## Common pitfalls

> Filled in from the real build, once there are real failures to warn about.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
