# Prompts: Offline Voice Journal

Recording and transcription have no prompts — that's local speech-to-text. The
only prompt is the weekly summary, and the trick is tone. This journal is private
and personal, so the prompt has to be warm without being saccharine, and honest
without being clinical.

## The weekly summary prompt

This is what's wired into `summary.py`:

```
These are my voice journal entries from the past week. Read them and gently
surface patterns. Cover: what drained me, what energized me, and any recurring
intentions I keep mentioning. Be warm but honest and specific. Quote a few of my
own phrases back to me.

{all entries, concatenated}
```

## Why "quote my own phrases back to me"

Generic reflections ("you seem to value balance") feel like a horoscope. Quoting
the person's actual words ("you wrote 'the days I move first are the days I don't
feel stuck' three times") is what makes it land. It proves the summary read *you*,
not a template.

## Tuning by tone

- **Too soft / therapist-y**: add "No platitudes. Don't reassure me — just show me
  the pattern."
- **Too clinical**: add "Write it like a close friend who's been paying attention."
- **You want action**: add "End with one small experiment I could try next week,
  based only on what's in the entries."
- **You want brevity**: add "Keep it under 150 words."

## Optional: a monthly rollup prompt

```
Here are four weekly summaries. What changed across the month? What got better,
what's still stuck, and which intention did I actually follow through on?

{paste the four weekly summaries}
```

## A privacy note

The default `summary.py` path is fully local and uses no prompt at all — it counts
draining/energizing words and pulls out lines like "I want to..." with a regex.
Use that if you'd rather this journal never touch a network. The prompt above is
strictly opt-in.
