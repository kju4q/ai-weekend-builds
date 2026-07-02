"""Transcribe a recording into a dated journal entry, fully locally.

    python transcribe.py recordings/2026-07-02-091500.wav
    python transcribe.py --text "typed entry for testing the pipeline"

Transcription uses faster-whisper (pip install faster-whisper) which runs a
Whisper model entirely on your machine — no cloud, no account. The --text flag
lets you create an entry without audio so you can test the rest of the pipeline.

Entries are appended to journal/YYYY-MM-DD.md. Nothing is uploaded.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib

JOURNAL_DIR = pathlib.Path(__file__).parent / "journal"


def transcribe_audio(wav_path: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit(
            "faster-whisper not installed.\n"
            "  pip install faster-whisper\n"
            "It downloads a small model once, then runs fully offline.\n"
            "To test the pipeline without audio, use: python transcribe.py --text \"...\""
        )
    print("Loading local Whisper model (first run downloads it)...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(wav_path)
    return " ".join(seg.text.strip() for seg in segments).strip()


def save_entry(text: str) -> pathlib.Path:
    JOURNAL_DIR.mkdir(exist_ok=True)
    now = dt.datetime.now()
    path = JOURNAL_DIR / f"{now:%Y-%m-%d}.md"
    header = f"\n## {now:%H:%M}\n\n" if path.exists() else f"# {now:%A, %B %d, %Y}\n\n## {now:%H:%M}\n\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(header + text.strip() + "\n")
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", nargs="?", help="path to a .wav recording")
    ap.add_argument("--text", help="create an entry from text instead of audio")
    args = ap.parse_args()

    if args.text:
        text = args.text
    elif args.wav:
        text = transcribe_audio(args.wav)
        print("\nTranscript:\n" + text + "\n")
    else:
        ap.error("give a .wav path or --text")

    path = save_entry(text)
    print(f"Saved entry to {path}")


if __name__ == "__main__":
    main()
