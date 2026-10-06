# 04: Motion Studio

Set your brand once, write a three-line brief, and get a branded animation you can
critique, fix, and render to a real video file. The generator, the critic, and the
renderer all run on your machine, and the output is a single self-contained HTML
file with no build step and no dependencies.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium-Advanced | 5-8 hours | Python (standard library), ffmpeg, Chrome, Anthropic API (optional) |

## What you'll build

A four-step studio. `generate.py` composes a canvas animation from your
`brand.json` and a three-line `brief.txt`. `critique.py` reviews that animation
against motion principles and tells you what to fix, with numbers. You iterate.
Then `render.py` captures the finished page into an mp4 or webm.

The sample brand and brief produce a 6.00 second, 1280x720, 144 frame h264 file in
about 16 seconds on an M-series Mac. That number is from a real run, not an
estimate.

## What you'll learn

- **Directing instead of prompting**: the generate, critique, iterate loop, and
  why the second round is where the quality arrives
- **Motion craft as code**: easing functions, anticipation, per-word stagger, and
  a held final frame, written out so you can see what each one does
- **A deterministic contract between tools**: the generator embeds its timeline as
  JSON so the critic and the renderer can read the piece instead of guessing
- **Checking creative work mechanically**: what a checklist can catch (a linear
  tween, a missing hold) and what it structurally cannot (whether it is any good)
- **A real render pipeline**: headless browser capture, the filmstrip trick that
  makes it fast, and ffmpeg's `untile` filter

## Prerequisites

- Python 3.10+. No pip installs for the whole local path.
- **ffmpeg**, for rendering. `brew install ffmpeg`. Not needed to generate or critique.
- **A Chromium-family browser** for rendering: Google Chrome, Chromium, Brave, or
  Edge. Detected, not assumed.
- Optional: an Anthropic API key, for a model-written animation (`--ai` on
  generate) or a written critique (`--ai` on critique). Neither is required and
  both have a local path that is the default.

## Local vs API

| Part | Runs where |
|---|---|
| Reading `brand.json` and `brief.txt` | 100% local |
| Generating the animation (default) | 100% local |
| Generating with `--ai` | Claude API (only with `--ai` **and** a key) |
| The critique checklist (default) | 100% local |
| The written critique with `--ai` | Claude API (only with `--ai` **and** a key) |
| Rendering to video | 100% local (your own ffmpeg and browser) |

Without `--ai`, nothing leaves the machine, and the rendering step never does
regardless. When you pass `--ai` to `generate.py`, your brand values and your
three lines of brief are sent. When you pass `--ai` to `critique.py`, the
generated page source and its timeline are sent, which contains those same brand
values and lines. Nothing else is uploaded in either case, and no video frame ever
is.

## How it works

```
brand.json  (colors, fonts, pace, canvas)        set once
brief.txt   (three lines + duration + logo)      the only thing you change
   |
   v  generate.py        pace preset -> timeline, cues get easings, text gets stagger
out/animation.html       self-contained. CFG block holds the timeline as JSON.
   |
   v  critique.py        parses CFG + source, tests 10 principles, names the numbers
your director's notes    edit brief.txt or the template, regenerate
   |
   v  render.py          ?strip=1 packs 21 frames per screenshot, one Chrome launch each
   |                     ffmpeg untile=1x21 unstacks them into frames
out/animation.mp4        1280x720, h264, exactly the duration the brief asked for
```

## Build it

### Step 1: Generate from the sample

```
python generate.py sample-data/brand.json sample-data/brief.txt
open out/animation.html
```

It prints the timeline it built: each cue, when it starts, how long it runs, and
which easing it got. Watch the page a few times. The headline pulls back before it
moves, the words arrive one at a time, and the logo holds alone for the last
second.

### Step 2: Run the critique

```
python critique.py out/animation.html --brief sample-data/brief.txt
```

Ten checks against the real file. On the shipped sample all ten pass, which is a
fair question to ask of a checklist, so prove it bites: copy the HTML, set a cue's
`"ease"` to `"linear"` and `"hold"` to `0`, and run it again. It will fail six
checks and exit non-zero. That is the test I ran before trusting it.

### Step 3: Make it yours

Copy the samples up a level and edit them:

```
cp sample-data/brand.json brand.json
cp sample-data/brief.txt brief.txt
python generate.py brand.json brief.txt
```

In `brand.json`, the `pace` field is the one that changes the feel most: `calm`,
`brisk`, or `snappy`. They are three sets of four timings (lead, gap, beat, hold)
and they are the whole personality of the piece. In `brief.txt`, three lines is
the format. The first is the headline, the second supports it, the third lands it.

### Step 4: Direct it

Watch, write notes about specific moments, change the brief or the pace, and
regenerate. `prompts.md` has three example director's notes to copy the shape of.
The notes that work name a moment ("the opening feels rushed"), not a principle
("improve the timing").

### Step 5: Render it

```
python render.py out/animation.html --dry-run    # see the pipeline first
python render.py out/animation.html              # about 16 seconds
```

`--dry-run` prints every command it would run, which is worth reading once because
the filmstrip trick is the interesting part of this project. A naive renderer
launches a headless browser per frame, and Chrome costs about six seconds to
start, so 144 frames is fifteen minutes. Instead the page accepts
`?strip=1&from=0&count=21&fps=24`, which stacks 21 frames vertically in one tall
screenshot. Seven browser launches instead of 144, then `ffmpeg -vf untile=1x21`
unstacks them into a video.

```
python render.py out/animation.html --format webm
python render.py out/animation.html --keep-frames    # inspect the strips
```

## Verify it works

- [ ] `python generate.py sample-data/brand.json sample-data/brief.txt` prints a
      6 cue timeline and writes `out/animation.html`
- [ ] `out/animation.html` opens in a browser and animates, with no network access
- [ ] `python critique.py out/animation.html --brief sample-data/brief.txt` prints
      10 PASS lines and exits 0
- [ ] A copy with `"ease": "linear"` and `"hold": 0` fails that same check and exits 1
- [ ] `python render.py out/animation.html --dry-run` prints the Chrome and ffmpeg
      commands and captures nothing
- [ ] `python render.py out/animation.html` writes `out/animation.mp4`, and
      `ffprobe` reports 1280x720, 144 frames, duration 6.000000

## Extend it

- Add a fourth pace preset of your own and feel what changing only `lead` does
- Add an audio track: generate at a bpm, put the beat entrances on the beat, and
  mux the audio in with ffmpeg in `render.py`
- Add a second scene and a transition between them, which is where timing gets
  genuinely hard
- Teach `critique.py` to check contrast ratios between your brand colors, so the
  checklist covers legibility and not only motion
- Render a square and a vertical crop from the same timeline for different platforms
- Have `--ai` write only the draw function while the timeline stays deterministic,
  so the critic and renderer never break on a model's output

## Common pitfalls

- **Everything eases the same way**: the template varies easing per cue on
  purpose. If you add cues, vary them, and make the big move slower than the
  small ones.
- **No breath at the start**: a cue starting at 0.00s reads as a jump cut. The
  `lead` value exists for this and the checklist tests for it.
- **Fonts you do not have**: `brand.json` font stacks must end in a real fallback,
  because the headless browser that renders your video may not have your font.
- **The strip is too tall**: Chromium's surface limit is 16384px, so
  `render.py` caps strips at 15600px and splits accordingly. A very large canvas
  means fewer frames per strip and a slower render, not a failure.
- **Rendering with no browser or no ffmpeg**: `render.py` detects both and prints
  the exact commands it would have run, then exits non-zero. It does not pretend
  to have rendered anything.
- **Trusting the checklist**: ten passes means the mechanics are sound, not that
  the piece is good. Open it and watch it.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
