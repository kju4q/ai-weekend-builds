"""Replay what the model wrote at every checkpoint, side by side, same prompt.

    python watch.py                       the samples from your run (or the shipped one)
    python watch.py --rows                one checkpoint per row instead of columns
    python watch.py --type                type each sample out character by character
    python watch.py --prompt "Mr. Darcy"  generate fresh from every saved checkpoint
    python watch.py --checkpoint sample-data/final.pt --prompt "Mr. Darcy"

Before you train anything this reads sample-data/samples.jsonl, the samples from
the run described in the README, so you can see the target first. After you
train it reads output/samples.jsonl, which train.py writes.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys
import textwrap
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "output")
SHIPPED = os.path.join(HERE, "sample-data")


def load_samples(path: str | None) -> tuple[str, list[dict]]:
    if path is None:
        mine = os.path.join(OUTPUT, "samples.jsonl")
        path = mine if os.path.exists(mine) else os.path.join(SHIPPED, "samples.jsonl")
    with open(path) as f:
        return path, [json.loads(line) for line in f if line.strip()]


def generate_from_checkpoints(paths: list[str], prompt: str, n: int) -> list[dict]:
    import torch  # only needed for this mode
    from train import CharData, load_checkpoint, pick_device, SAMPLE_SEED

    device = pick_device(None)
    out = []
    for p in paths:
        model, ck = load_checkpoint(p, device)
        data = CharData.__new__(CharData)        # rebuild the vocab, no text needed
        data.chars = ck["chars"]
        data.stoi = {c: i for i, c in enumerate(data.chars)}
        data.device = device
        gen = torch.Generator().manual_seed(SAMPLE_SEED)
        idx = torch.tensor([data.encode(prompt)], dtype=torch.long, device=device)
        text = data.decode(model.generate(idx, n, gen)[0].tolist())
        out.append({"step": ck["step"], "val_loss": ck["losses"]["val"], "sample": text})
    return out


def label(r: dict) -> str:
    return f"step {r['step']}  loss {r['val_loss']:.2f}"


def columns(recs: list[dict], width: int) -> None:
    per_row = max(1, min(len(recs), (width + 3) // 34))
    col = (width - 3 * (per_row - 1)) // per_row
    for start in range(0, len(recs), per_row):
        group = recs[start:start + per_row]
        blocks = [[label(r), "-" * col] + textwrap.wrap(
            r["sample"].replace("\n", " / "), col) for r in group]
        height = max(len(b) for b in blocks)
        for i in range(height):
            print(" | ".join((b[i] if i < len(b) else "").ljust(col) for b in blocks).rstrip())
        print()


def rows(recs: list[dict], width: int, typed: bool, delay: float) -> None:
    for r in recs:
        print(f"== {label(r)} " + "=" * max(0, width - len(label(r)) - 4))
        body = textwrap.fill(r["sample"].replace("\n", " / "), width)
        if typed:
            for ch in body:
                sys.stdout.write(ch)
                sys.stdout.flush()
                time.sleep(delay)
            print("\n")
        else:
            print(body + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Watch the model go from noise to words.")
    ap.add_argument("--samples", help="a samples.jsonl file (default: yours, else the shipped one)")
    ap.add_argument("--rows", action="store_true", help="one checkpoint per row")
    ap.add_argument("--type", action="store_true", help="type the samples out, implies --rows")
    ap.add_argument("--delay", type=float, default=0.012, help="seconds per typed character")
    ap.add_argument("--prompt", help="generate fresh text from this prompt at every checkpoint")
    ap.add_argument("--checkpoint", nargs="*", help="specific .pt files for --prompt")
    ap.add_argument("--chars", type=int, default=240)
    args = ap.parse_args()
    width = min(shutil.get_terminal_size((120, 40)).columns, 160)

    if args.prompt:
        paths = args.checkpoint or sorted(glob.glob(os.path.join(OUTPUT, "step-*.pt")))
        if not paths:
            paths = [os.path.join(SHIPPED, "final.pt")]
            print("no checkpoints in output/ yet, using the shipped sample-data/final.pt\n")
        recs = generate_from_checkpoints(paths, args.prompt, args.chars)
        print(f"prompt {args.prompt!r}, {len(recs)} checkpoint(s)\n")
    else:
        path, recs = load_samples(args.samples)
        print(f"{os.path.relpath(path, HERE)}: {len(recs)} checkpoints, same prompt, "
              f"same random seed\n")

    if args.rows or args.type:
        rows(recs, width, args.type, args.delay)
    else:
        columns(recs, width)


if __name__ == "__main__":
    main()
