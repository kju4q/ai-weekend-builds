"""Motion Studio, critique: review an animation against motion principles.

    python critique.py out/animation.html
    python critique.py out/animation.html --brief sample-data/brief.txt
    python critique.py out/animation.html --ai       # Claude writes the critique

The local path is the default and it is a real check, not a printout. It parses
the CFG block that generate.py embeds in the page, plus the page source, and
tests each principle against the actual numbers in the file. Every line it prints
names the value it found, so a FAIL tells you what to change and a PASS is
something you could verify by hand.

What it cannot do is tell you whether the piece is any good. A checklist catches
a linear tween and a missing hold; it cannot see that your headline is boring.
That is what --ai, and your own eyes on the page, are for.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Easing names generate.py may use. "linear" is deliberately not in here: it is
# the one easing that counts as a finding rather than a feature.
NONLINEAR = {
    "easeOutCubic", "easeInOutCubic", "easeOutQuint",
    "easeOutBack", "easeOutElastic", "anticipate",
}


class Finding:
    """One checklist row. ok=True pass, ok=False fail, ok=None not applicable."""

    def __init__(self, name: str, ok: bool | None, detail: str) -> None:
        self.name = name
        self.ok = ok
        self.detail = detail

    def line(self) -> str:
        mark = "PASS" if self.ok else ("FAIL" if self.ok is False else "n/a ")
        return f"  [{mark}]  {self.name}\n           {self.detail}"


def load_cfg(html: str) -> dict:
    """Pull the CFG object generate.py embeds. It is strict JSON, by contract."""
    m = re.search(r"const CFG = (\{.*?\n\});", html, re.S)
    if not m:
        raise SystemExit(
            "critique.py: no CFG block found. This file was not written by "
            "generate.py, or the generator's contract changed."
        )
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"critique.py: CFG block is not valid JSON: {exc}")


def brief_duration(path: str | None) -> float | None:
    """The duration the brief asked for, if it asked for one."""
    if not path or not Path(path).exists():
        return None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*duration:\s*([0-9.]+)\s*s?\s*$", raw, re.I)
        if m:
            return float(m.group(1))
    return None


def check(cfg: dict, html: str, brief: str | None) -> list[Finding]:
    out: list[Finding] = []
    tl = cfg.get("timeline", [])
    dur = float(cfg.get("duration", 0))
    hold = float(cfg.get("hold", 0))

    # 1. Easing helpers actually defined in the page.
    defined = set(re.findall(r"function (ease[A-Za-z]+|anticipate)\s*\(", html))
    out.append(Finding(
        "Non-linear easing is available",
        len(defined & NONLINEAR) >= 3,
        f"{len(defined & NONLINEAR)} non-linear helpers defined: "
        f"{', '.join(sorted(defined & NONLINEAR)) or 'none'}",
    ))

    # 2. Nothing moves linearly. The real test: no cue is assigned linear.
    linear_cues = [c["id"] for c in tl if c.get("ease") == "linear"]
    out.append(Finding(
        "Nothing moves linearly",
        not linear_cues,
        "no cue uses linear easing" if not linear_cues
        else f"linear easing on: {', '.join(linear_cues)}",
    ))

    # 3. Anticipation: something pulls back before it moves.
    antic = [c["id"] for c in tl if c.get("ease") == "anticipate"]
    out.append(Finding(
        "Anticipation before a move",
        bool(antic),
        f"anticipate on: {', '.join(antic)}" if antic
        else "no cue uses anticipation. The first entrance is the one to fix.",
    ))

    # 4. A breath before the first move.
    first = min((c["start"] for c in tl), default=0.0)
    out.append(Finding(
        "A breath before the first move",
        first >= 0.15,
        f"first cue starts at {first:.2f}s",
    ))

    # 5. Stagger: entrances are spread, not simultaneous.
    starts = sorted(round(float(c["start"]), 3) for c in tl)
    gaps = [b - a for a, b in zip(starts, starts[1:])]
    staggered = len(set(starts)) == len(starts) and all(g > 0.05 for g in gaps)
    out.append(Finding(
        "Entrances are staggered",
        staggered if len(starts) > 1 else None,
        f"{len(starts)} cues, gaps "
        f"{', '.join(f'{g:.2f}s' for g in gaps) if gaps else 'n/a'}",
    ))

    # 6. Per-word stagger inside a cue, which is a text-specific craft point.
    out.append(Finding(
        "Per-word stagger inside the text",
        "perWord" in html,
        "found a per-word offset in the draw loop" if "perWord" in html
        else "text animates as one block. Stagger the words.",
    ))

    # 7. A held final frame: dead air at the end, nothing entering.
    last_end = max(((c["start"] + c["dur"]) for c in tl), default=0.0)
    tail = dur - last_end
    out.append(Finding(
        "The final frame is held",
        hold > 0.3 and tail > 0.1,
        f"hold {hold:.2f}s declared, {tail:.2f}s of dead air after the last cue ends "
        f"at {last_end:.2f}s of {dur:.2f}s",
    ))

    # 8. Nothing runs past the end of the piece.
    over = [c["id"] for c in tl if c["start"] + c["dur"] > dur + 1e-6]
    out.append(Finding(
        "Every cue finishes inside the duration",
        not over,
        "all cues land before the end" if not over
        else f"running past the end: {', '.join(over)}",
    ))

    # 9. The duration the brief asked for.
    want = brief_duration(brief)
    if want is None:
        out.append(Finding("Duration matches the brief", None,
                           "the brief set no duration, so nothing to match"))
    else:
        out.append(Finding(
            "Duration matches the brief",
            abs(dur - want) < 0.05,
            f"brief asked for {want:.2f}s, the file is {dur:.2f}s",
        ))

    # 10. It is actually animated and self-contained.
    raf = html.count("requestAnimationFrame")
    external = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    out.append(Finding(
        "Self-contained and animating",
        raf > 0 and not external,
        f"{raf} requestAnimationFrame call(s), "
        f"{len(external)} external resource(s)"
        + (f": {', '.join(external[:3])}" if external else ""),
    ))

    return out


def ai_critique(html: str, cfg: dict) -> str:
    """Optional. Sends the page source to Claude for a real critique."""
    import anthropic  # lazy, so the local path needs nothing installed

    client = anthropic.Anthropic()
    prompt = (
        "You are a senior motion designer reviewing a colleague's work. Below is "
        "a self-contained HTML/canvas animation: its timeline config and its "
        "source.\n\nCritique it on timing, easing, hierarchy, and anticipation. "
        "Say what feels rushed, what deserves a pause, and where the typography "
        "fights the motion. Be specific and reference real cues and numbers from "
        "the timeline. Then give exactly three director's notes I could act on, "
        "each about a specific moment, not a principle.\n\n"
        f"TIMELINE:\n{json.dumps(cfg.get('timeline', []), indent=2)}\n\n"
        f"SOURCE:\n{html[:60000]}"
    )
    msg = client.messages.create(
        model="claude-opus-5",
        max_tokens=1600,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("html", help="the animation HTML from generate.py")
    ap.add_argument("--brief", default=None,
                    help="brief.txt, to check the duration it asked for")
    ap.add_argument("--ai", action="store_true",
                    help="also get a written critique from Claude (needs a key)")
    args = ap.parse_args()

    path = Path(args.html)
    if not path.exists():
        raise SystemExit(f"critique.py: no such file: {path}. Run generate.py first.")
    html = path.read_text(encoding="utf-8")
    cfg = load_cfg(html)

    print(f"\nCritique of {path}")
    print(f"{cfg.get('brand', 'unknown brand')}, {cfg.get('duration', 0):.2f}s "
          f"at {cfg.get('fps', 0)}fps, pace {cfg.get('pace', '?')}\n")

    findings = check(cfg, html, args.brief)
    for f in findings:
        print(f.line())

    failed = [f for f in findings if f.ok is False]
    passed = [f for f in findings if f.ok is True]
    print(f"\n{len(passed)} passed, {len(failed)} to fix, "
          f"{len(findings) - len(passed) - len(failed)} not applicable")

    if failed:
        print("\nWhat to change first:")
        for f in failed:
            print(f"  - {f.name}: {f.detail}")
    else:
        print("\nThe mechanics are sound. What a checklist cannot tell you is "
              "whether it reads well,\nso open it in a browser and watch it three "
              "times before you call it done.")

    if args.ai:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("\n--ai needs ANTHROPIC_API_KEY set. The checklist above ran "
                  "regardless.", file=sys.stderr)
        else:
            try:
                print("\n" + "=" * 70)
                print("Claude's critique\n")
                print(ai_critique(html, cfg))
            except Exception as exc:  # the local critique already printed
                print(f"\n--ai failed ({exc.__class__.__name__}: {exc}). "
                      "The checklist above still stands.", file=sys.stderr)

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
