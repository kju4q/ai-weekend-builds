# 04: Content Repurposer

One post becomes five platform-native versions. Saves hours every week.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 4-6 hours | Node.js or Python, Anthropic API |

## What you'll build

A tool that takes one piece of long-form content (blog post, newsletter, video script) and outputs platform-native versions for Instagram, TikTok, X, LinkedIn, and YouTube. Voice preserved across formats. Each output respects platform-specific rules (length, tone, hashtag conventions, CTA style).

Drop in a long post, get back 5 ready-to-post pieces.

## What you'll learn

- Prompt chaining with shared context (each platform sees the source plus platform rules)
- Voice preservation: keeping an author's tone across drastic format changes
- Encoding platform-specific writing rules as instructions
- Parallel API calls for speed
- Building a tool you'll actually use every week

## Prerequisites

- Node.js 18+ or Python 3.10+
- An Anthropic API key
- A clear sense of your own voice (you'll capture it in a `voice.md` file)
- Comfort with async/await and Promise.all (or asyncio)

## How it works

```
source content (one long post)
                +
voice.md (your tone, banned phrases, examples)
                ↓
        shared context built once
                ↓
  ┌──────┬──────┬──────┬──────┬──────┐
  ↓      ↓      ↓      ↓      ↓      ↓
 IG    TikTok   X    LinkedIn  YT  Newsletter
(parallel Claude calls, each with the shared context plus platform-specific instructions)
  ↓      ↓      ↓      ↓      ↓      ↓
output files written: ig.md, tiktok.md, x.md, linkedin.md, youtube.md, newsletter.md
```

The shared context (source + voice) is the same across all calls. Each call adds its own platform rules. Run all calls in parallel.

## Build it

### Step 1: Scaffold

Make a new project. Install:

- The Anthropic SDK
- A way to read/write markdown files (built-in)
- Optionally a CLI library (commander for Node, click for Python)

Set up `.env` with `ANTHROPIC_API_KEY`.

### Step 2: Build your voice.md

This is the most important file in the project. It encodes:

- Past lines that worked (5-10 examples)
- Openers that pulled readers in
- Closers that earned the save
- Banned phrases ("In today's fast-paced world...", "game-changing", whatever your specific dislikes are)
- Tone rules ("short paragraphs," "no em dashes," etc.)

Don't paste examples from people you admire. Use your own. The point is YOUR voice, not a generic "good content voice."

### Step 3: Build the shared context

Write a function `buildContext(source, voice)` that returns a string with the source content and the voice file embedded. This block gets prepended to every platform call.

### Step 4: Build platform calls

Write one function per platform. Each one:

1. Takes the shared context
2. Adds the platform-specific instructions (see `prompts.md`)
3. Calls Claude
4. Returns the platform-native version

Start with one platform (Instagram is the easiest). Get it working. Then duplicate the pattern for the others.

### Step 5: Run them in parallel

Wrap all platform functions in `Promise.all` (Node) or `asyncio.gather` (Python). All 5-6 calls run at the same time. Total time = max of any single call (usually 5-15 seconds).

### Step 6: Write the outputs

For each platform's result, write to `./output/{platform}.md`. Done.

### Step 7: Add a review step (optional but recommended)

After generating all platform versions, run one more Claude call that reviews all of them against your voice rules. Flags any that broke a hard rule. Re-runs the bad ones with the violation pointed out.

## The prompts

The shared context format and per-platform repurposing prompts are in [`prompts.md`](prompts.md).

## Verify it works

- [ ] Each platform's output respects that platform's character limits and tone
- [ ] No output is just a copy of another (TikTok and IG can match, but X and LinkedIn must differ)
- [ ] No output uses banned phrases from your voice.md
- [ ] The voice across all 5 outputs feels like the same person, just speaking to different rooms

## Extend it

- Add a "save the platform versions to a Notion page" step
- Add a tone variant flag (sharp, friendly, professional)
- Generate the trendy-video text overlay version too
- Wire it into your CMS so publishing the source auto-generates the platform versions
- Track which platform versions actually performed and feed that back into voice.md

## Common pitfalls

- **Voice drifts toward generic**: the voice.md is too thin. Add 5-10 more concrete examples.
- **All platforms produce similar output**: the platform-specific rules in `prompts.md` aren't strong enough. Add specific banned and required patterns per platform.
- **LinkedIn output is too casual or X output is too long**: each platform has length constraints in the prompt. If they get violated, repeat the constraint at the start of the platform's instructions.
- **Hashtag spam**: cap hashtag count in each platform's prompt. 2-3 max for IG, 0 for X unless trending, 3-5 for LinkedIn.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
