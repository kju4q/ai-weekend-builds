# 02: Pattern Mirror

Reads years of your camera roll and shows you the shape of your life: what you
photograph when you're happy, the months the pictures stop, the people who appear
and fade. It all runs locally.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Easy-Medium | 3-5 hours | Python 3.10+, a vision model (local or hosted), OpenAI API (optional) |

Built with Codex. The runtime needs above are this project's own.

## What you'll build

A local pass over your camera roll that reads the images in bulk and renders the
timeline as something you can look at. Not a photo browser. A report that tells
you which subjects cluster in your good months, where the gaps are, and who
recurs across years.

## What you'll learn

Vision models and timeline analysis.

- Running a vision model over thousands of images without paying for every one
- Reading dates and metadata as the spine of the analysis
- Turning a timeline into a shape you can read at a glance
- Recognizing that absence in the data is itself a finding

## Prerequisites

> Finalized during the build. This is the starting assumption, not the final list.

- Python 3.10+
- An export of your camera roll, or a folder of photos with their dates intact
- A vision model, local or hosted
- Optional: an OpenAI API key if you use the hosted path

## Local vs API

> Provisional. Confirmed during the build.

| Part | Runs where |
|---|---|
| Reading files, dates, and metadata | 100% local |
| Grouping into months and clusters | 100% local |
| Describing what is in an image | Local model, or OpenAI API if you choose the hosted path |
| Rendering the report | 100% local |

Choose the local vision path and no photo ever leaves the machine.

## How it works

> Provisional. The real pipeline lands with the build.

```
folder of photos
   ↓  read dates + metadata
timeline
   ↓  describe images (local or hosted vision)
tags per photo
   ↓  group by month, cluster subjects, find gaps
a report you can look at
```

## Build it

> Coming with the build. The five steps below are the shape they will follow.

### Step 1: Run it as-is on the sample

### Step 2: Read the timeline builder

### Step 3: Turn on the vision pass

### Step 4: Point it at your own camera roll

### Step 5: Make it yours

## The prompts

The exact Codex prompts used to build this are in [prompts.md](prompts.md).

## Verify it works

> Checklist lands with the build.

## Extend it

- Run it once a year and diff the two reports, so the thing you're looking at is
  the change rather than the snapshot

## Common pitfalls

> Filled in from the real build, once there are real failures to warn about.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
