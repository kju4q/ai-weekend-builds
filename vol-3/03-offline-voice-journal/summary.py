"""Read the week's journal entries and surface patterns.

    python summary.py            # last 7 days of entries
    python summary.py --last 5   # last 5 entry-files
    python summary.py --all      # every entry

Reading the entries is fully local. The pattern summary is written by Claude if
ANTHROPIC_API_KEY is set; otherwise a local keyword-based summary runs so the
tool still works with no cloud and no account.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import os
import pathlib
import re

JOURNAL_DIR = pathlib.Path(__file__).parent / "journal"

DRAIN_WORDS = ["tired", "drained", "exhausted", "stressed", "anxious", "overwhelmed",
               "frustrated", "stuck", "worried", "meeting", "email"]
ENERGY_WORDS = ["energized", "excited", "proud", "clear", "focused", "good", "walk",
                "run", "built", "shipped", "learned", "grateful", "calm"]


def entry_files(last: int | None, all_: bool) -> list[pathlib.Path]:
    files = sorted(JOURNAL_DIR.glob("*.md"))
    if all_:
        return files
    if last:
        return files[-last:]
    cutoff = dt.date.today() - dt.timedelta(days=7)
    kept = []
    for f in files:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", f.stem)
        if m and dt.date(*map(int, m.groups())) >= cutoff:
            kept.append(f)
    return kept or files[-7:]  # fall back to last 7 files if none in range


def local_summary(text: str) -> str:
    words = re.findall(r"[a-z']+", text.lower())
    counts = collections.Counter(words)
    drains = [(w, counts[w]) for w in DRAIN_WORDS if counts[w]]
    energy = [(w, counts[w]) for w in ENERGY_WORDS if counts[w]]
    intentions = re.findall(r"(?:i want to|i should|i need to|tomorrow i)[^.\n]*", text.lower())
    out = ["(local summary — set ANTHROPIC_API_KEY for a richer one)\n",
           "**What showed up as draining:** " +
           (", ".join(f"{w} (x{c})" for w, c in sorted(drains, key=lambda x: -x[1])) or "nothing obvious"),
           "**What showed up as energizing:** " +
           (", ".join(f"{w} (x{c})" for w, c in sorted(energy, key=lambda x: -x[1])) or "nothing obvious"),
           "**Recurring intentions:**"]
    out += [f"- {i.strip()}" for i in dict.fromkeys(intentions)][:5] or ["- (none detected)"]
    return "\n".join(out)


def ai_summary(text: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=600,
        messages=[{"role": "user", "content": (
            "These are my voice journal entries from the past week. Read them and "
            "gently surface patterns. Cover: what drained me, what energized me, and "
            "any recurring intentions I keep mentioning. Be warm but honest and "
            "specific. Quote a few of my own phrases back to me.\n\n" + text
        )}],
    )
    return msg.content[0].text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    files = entry_files(args.last, args.all)
    if not files:
        raise SystemExit(f"No entries in {JOURNAL_DIR}. Record one first.")
    text = "\n\n".join(f.read_text(encoding="utf-8") for f in files)
    print(f"Reading {len(files)} entr{'y' if len(files)==1 else 'ies'}...\n")

    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            print(ai_summary(text))
            return
        except Exception as e:
            print(f"(Claude call failed: {e}; local summary follows)\n")
    print(local_summary(text))


if __name__ == "__main__":
    main()
