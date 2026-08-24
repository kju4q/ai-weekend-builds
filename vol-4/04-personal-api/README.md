# 04: Personal API

A small local server with endpoints for your life. `/today` merges your calendar,
your tasks, and the weather into one response. `/idea` files a thought. Nothing
leaves localhost.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium-Advanced | 5-8 hours | Python 3.10+ (standard library), a free weather source, no model key needed |

Built with Codex. The runtime needs above are this project's own.

## What you'll build

One local server where the parts of your life have addresses. Ask it for `/today`
and it reads your calendar, your task file, and the weather, and hands back a
single response. Post to `/idea` and the thought is filed. It binds to localhost
and stays there.

## What you'll learn

What an API is, by building one around your life.

- Endpoints, methods, and responses, learned by needing them rather than reading about them
- Merging several real data sources into one clean response
- Reading and writing your own state through an interface you designed
- Why localhost-only is a real security decision, not a limitation

## Prerequisites

> Finalized during the build. This is the starting assumption, not the final list.

- Python 3.10+
- A calendar export and a task file for it to read
- A free weather source, no key required
- No model key needed for the core server

## Local vs API

> Provisional. Confirmed during the build.

| Part | Runs where |
|---|---|
| The server itself | 100% local, bound to localhost |
| Calendar and tasks | 100% local, read from your files |
| Weather | Free public source, over the network |
| Filing an idea | 100% local, written to your disk |

No hosted model is involved anywhere in this project.

## How it works

> Provisional. The real pipeline lands with the build.

```
calendar export  +  tasks file  +  weather source
   ↓
local server on localhost
   ↓
GET  /today   →  one merged response
POST /idea    →  thought filed to disk
```

## Build it

> Coming with the build. The five steps below are the shape they will follow.

### Step 1: Run it as-is on the sample

### Step 2: Read the request handler

### Step 3: Point it at your own calendar and tasks

### Step 4: Add an endpoint of your own

### Step 5: Make it yours

## The prompts

The exact Codex prompts used to build this are in [prompts.md](prompts.md).

## Verify it works

> Checklist lands with the build.

## Extend it

- Point the other projects in this volume at it, so they read your day from one
  place instead of each parsing their own files

## Common pitfalls

> Filled in from the real build, once there are real failures to warn about.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
