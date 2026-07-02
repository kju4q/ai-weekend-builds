"""Record audio from your laptop mic to recordings/DATE-TIME.wav.

    python record.py            # records 120 seconds
    python record.py 30         # records 30 seconds

Uses `sounddevice` if installed (pip install sounddevice). If it isn't, this
prints the exact ffmpeg command to record on your OS instead. Either way the
audio is written locally and never leaves the machine.
"""

from __future__ import annotations

import datetime as dt
import pathlib
import sys

REC_DIR = pathlib.Path(__file__).parent / "recordings"
SAMPLE_RATE = 16000  # what whisper expects


def outfile() -> pathlib.Path:
    REC_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return REC_DIR / f"{stamp}.wav"


def record(seconds: int) -> None:
    path = outfile()
    try:
        import sounddevice as sd
        import wave

        print(f"Recording {seconds}s... speak now. (Ctrl-C to stop early)")
        audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                       channels=1, dtype="int16")
        sd.wait()
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(audio.tobytes())
        print(f"Saved {path}")
        print(f"Next: python transcribe.py {path}")
    except ImportError:
        print("sounddevice not installed. Two options:\n")
        print("  1) pip install sounddevice   (then rerun this script)\n")
        print("  2) record with ffmpeg directly:")
        print("     macOS:  ffmpeg -f avfoundation -i \":0\" -t "
              f"{seconds} -ar {SAMPLE_RATE} -ac 1 {path}")
        print("     Linux:  ffmpeg -f alsa -i default -t "
              f"{seconds} -ar {SAMPLE_RATE} -ac 1 {path}")
        print(f"\n  Then: python transcribe.py {path}")


if __name__ == "__main__":
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    record(secs)
