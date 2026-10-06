# Prompts: Motion Studio

The default path uses no prompts. `generate.py` composes the animation from your
brand and brief deterministically, and `critique.py` checks it against ten
mechanical tests. These prompts power the optional `--ai` paths, and the third
section is the part worth your attention even if you never set a key: directing is
a skill, and the notes you write are the whole job.

## Prompt 1: Generate the animation

This is the one wired into `generate.py --ai`. The constraints are not decoration.
Every one of them exists so that `critique.py` and `render.py` still work on the
model's output.

```
You are a senior motion designer. Write a self-contained HTML file containing a
15-second canvas animation. No external resources of any kind: no CDN scripts, no
web fonts, no images. Everything inline.

BRAND
{paste brand.json}

BRIEF
{paste brief.txt, the three lines}

HARD REQUIREMENTS
- One <script> block must begin exactly `const CFG = {` and contain strict JSON
  with keys: brand, pace, width, height, fps, duration, hold, beats, logo,
  colors, fonts, and timeline. timeline is an array of
  {id, label, start, dur, ease}.
- The page must accept ?strip=1&from=N&count=M&fps=F and render M frames stacked
  vertically, deterministically, for frame capture. Without those params, animate
  in real time on requestAnimationFrame.
- Time must be derived from a single t value, never from accumulated deltas, so
  frame N is identical whether it was reached by playing or by seeking.
- No easing may be linear. Define at least three non-linear easings.
- The first cue starts after a deliberate pause, not at 0.
- Text enters word by word, staggered.
- The final frame holds with nothing moving for at least 0.8s.

CRAFT
Anticipation before every significant move. Vary the easing by cue, and make the
large moves slower than the small ones. The typography and the camera must not
both lead at once.
```

## Prompt 2: Critique the animation

This is the one wired into `critique.py --ai`. The local checklist has already
caught the mechanical faults by the time this runs, so the prompt is deliberately
pointed at what a checklist cannot see.

```
You are a senior motion designer reviewing a colleague's work. Below is a
self-contained HTML/canvas animation: its timeline config and its source.

Critique it on timing, easing, hierarchy, and anticipation. Say what feels
rushed, what deserves a pause, and where the typography fights the motion. Be
specific and reference real cues and numbers from the timeline. Then give exactly
three director's notes I could act on, each about a specific moment, not a
principle.

TIMELINE
{the timeline array}

SOURCE
{the page source}
```

## Three example director's notes

Round two is where a piece stops looking generated, and these are the shape that
works. Each one names a moment and asks for one change.

```
The opening feels rushed. The headline starts moving before the eye has settled
on the frame. Give it a breath first, about a third of a second of nothing, then
bring it in.
```

```
The logo and the wordmark arrive almost together, at 3.58s and 3.95s, so they
read as one event and the lockup loses its moment. Hold the mark alone, let it
settle, then contract the wordmark in.
```

```
The three lines all enter the same way at the same speed, so the third one has no
more weight than the first even though it is the line that lands the idea. Slow
the last entrance down and let the two above it sit still while it arrives.
```

Notice what none of them say: nothing about "improving the easing" or "better
timing". A note you can act on names a moment, a problem, and a direction.

## Why the deterministic CFG contract matters

It would be easier to let the model write whatever HTML it likes. The reason
Prompt 1 is so prescriptive is that three tools have to read the same file.
`critique.py` parses the `CFG` block to test easings and timings against real
numbers, and `render.py` needs `?strip=1` frame seeking to capture 21 frames in
one screenshot instead of launching a browser 144 times. A model that writes a
beautiful animation driven by accumulated frame deltas produces a file that
cannot be critiqued mechanically and renders with stuttering, because seeking to
frame 63 no longer gives the same image as playing to it. Pinning the contract is
what keeps the model's creativity inside a pipeline.

## Tuning

- **It loads a font or a library**: add "any external resource makes the output
  unusable. Inline everything, and end every font stack in a generic family."
- **The CFG block comes back as JavaScript, not JSON**: add "no comments, no
  trailing commas, no expressions, no template literals inside CFG. It must pass
  JSON.parse unchanged."
- **The render stutters**: the animation is using accumulated time. Add "frame N
  must be a pure function of N. Never add up deltas."
- **Everything moves at once**: add "no two cues may start within 0.2s of each
  other."
- **The critique is generic praise**: add "do not tell me what works. Only what to
  change, with the timestamp."
- **The critique invents problems**: add "every claim must cite a cue id and a
  number from the timeline I gave you."

## A note on privacy

Prompt 1 sends your brand values and your three lines of brief. Prompt 2 sends the
generated page source, which contains those same values plus the timeline. That is
the entire payload in both cases. No video frame, no rendered image, and no file
from `out/` is ever uploaded, and rendering is local in every configuration. If
your brief is confidential before launch, stay on the default path: the local
generator and the local checklist are the ones that ship in this project, and they
need no key at all.
