# 03: Offline Voice Journal

Talk to your laptop for two minutes. It transcribes you with a model running on
your own hardware, saves the entry as a dated markdown file, and once a week it
reads everything back and gently tells you what drained you, what energized you,
and the intentions you keep repeating. No cloud. No account. No one else ever
hears it.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 4-6 hours | Python, faster-whisper (local), Anthropic API (optional) |

## What you'll build

Three small scripts: one records audio from your mic, one transcribes it with a
local Whisper model, and one reads the week's entries and surfaces patterns. The
recording and transcription are the point — you'll run a real speech model on your
own machine and watch your voice become text with nothing leaving the laptop.

## What you'll learn

- Running a real ML model (Whisper) locally instead of calling an API
- Why local models are the whole game for anything genuinely private
- Capturing and writing audio (sample rate, mono, 16-bit — what Whisper wants)
- Turning a pile of freeform text into a weekly reflection
- The difference between "AI as a service" and "AI on hardware you own"

## Prerequisites

- Python 3.10+
- For real recording: `pip install sounddevice` (or use the printed ffmpeg command)
- For real transcription: `pip install faster-whisper` (downloads a model once)
- Optional: an Anthropic API key for a richer weekly summary

## Local vs API

| Part | Runs where |
|---|---|
| Recording audio | 100% local |
| Transcription (faster-whisper) | 100% local — the model runs on your CPU |
| Saving dated markdown entries | 100% local |
| Weekly summary (default) | 100% local, keyword-based |
| Weekly summary (richer) | Claude API **only** if `ANTHROPIC_API_KEY` is set |

The recordings and entries live in `recordings/` and `journal/` on your disk. The
only thing that can ever go to the cloud is the text you choose to summarize with
the optional AI path — and even that has a full local fallback.

## How it works

```
mic ──record.py──▶ recordings/DATE.wav
                        │
                 transcribe.py  (local Whisper)
                        ▼
              journal/YYYY-MM-DD.md   ◀── one file per day, appended
                        │
                  summary.py  (reads the week)
                        ▼
        "what drained you / energized you / kept intending"
```

## Build it

### Step 1: See the pipeline without a mic

The repo ships three sample entries. Prove the summary works first:

```
python summary.py --all
```

You'll get a local reflection: draining words, energizing words, and the
recurring intentions pulled from the entries.

### Step 2: Create an entry from text

Test the write path with no audio:

```
python transcribe.py --text "today felt scattered but the evening walk helped"
```

That appends a timestamped entry to today's file in `journal/`.

### Step 3: Turn on real recording

```
pip install sounddevice
python record.py 120        # records two minutes
```

If you'd rather not install anything, `record.py` prints the exact ffmpeg command
for your OS. Either way you get a `.wav` in `recordings/`.

### Step 4: Transcribe locally

```
pip install faster-whisper
python transcribe.py recordings/<your-file>.wav
```

The first run downloads a small model (~140MB), then runs entirely offline. Watch
your voice turn into text with the network unplugged if you want to prove it.

### Step 5: Make it a weekly habit

Record a couple of minutes most days. On Sunday:

```
python summary.py            # last 7 days
export ANTHROPIC_API_KEY=... # optional, for a warmer summary
python summary.py
```

## Verify it works

- [ ] `python summary.py --all` prints a reflection from the sample entries
- [ ] `python transcribe.py --text "..."` appends to today's journal file
- [ ] With faster-whisper installed, a real `.wav` produces a transcript
- [ ] The whole thing works with wifi off (except the optional AI summary)

## Extend it

- Swap faster-whisper for whisper.cpp if you want zero Python in the hot path
- Add sentiment/mood tracking and chart it over months
- Detect the same intention repeated across weeks and nudge you about it
- Encrypt the `journal/` folder at rest
- A monthly summary that compares this month to last

## Common pitfalls

- **Wrong sample rate**: Whisper wants 16kHz mono. `record.py` sets this; if you
  record elsewhere, resample first (`-ar 16000 -ac 1`).
- **Model download on a plane**: the first transcription needs internet to fetch
  the model. Run it once at home, then it's fully offline forever.
- **Empty summary**: `summary.py` looks at the last 7 days by filename date. Use
  `--all` or `--last N` if your entries are older than a week.
- **Expecting the local summary to be poetic**: it counts words. The warmth comes
  from the optional AI path — the local one is the honest, private baseline.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
