"""What is a token? The same sentence, cut up two ways.

    python tokens.py
    python tokens.py --sentence "Your own sentence here." --merges 500

1. Characters: every distinct character is one token. This is what train.py uses.
2. A tiny byte-pair encoding (BPE), written by hand below in about 40 lines and
   trained on the novel in sample-data/. BPE is the family of tokenizer that
   large models use: start from characters, then repeatedly glue together the
   pair that appears most often, until you have the vocabulary size you asked for.

No downloads, no tokenizer library, nothing leaves the machine.
"""

from __future__ import annotations

import argparse
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.join(HERE, "sample-data", "pride-and-prejudice.txt")
DEFAULT_SENTENCE = "It is a truth universally acknowledged that Elizabeth texted Darcy."

# Split text into words before merging, keeping the leading space on each word,
# so a merge can never glue the end of one word onto the start of the next.
PRE_SPLIT = re.compile(r" ?[A-Za-z]+| ?[0-9]+| ?[^A-Za-z0-9\s]+|\s+")


def train_bpe(text: str, n_merges: int) -> list[tuple[str, str]]:
    words = Counter(PRE_SPLIT.findall(text))
    # Each word starts as a tuple of single characters.
    split = {w: tuple(w) for w in words}
    merges: list[tuple[str, str]] = []
    for _ in range(n_merges):
        pairs: Counter = Counter()
        for w, count in words.items():
            parts = split[w]
            for a, b in zip(parts, parts[1:]):
                pairs[(a, b)] += count
        if not pairs:
            break
        best = max(pairs, key=pairs.get)
        merges.append(best)
        for w in words:
            split[w] = merge_pair(split[w], best)
    return merges


def merge_pair(parts: tuple[str, ...], pair: tuple[str, str]) -> tuple[str, ...]:
    out, i = [], 0
    while i < len(parts):
        if i + 1 < len(parts) and (parts[i], parts[i + 1]) == pair:
            out.append(parts[i] + parts[i + 1])
            i += 2
        else:
            out.append(parts[i])
            i += 1
    return tuple(out)


def bpe_encode(text: str, merges: list[tuple[str, str]]) -> list[str]:
    tokens: list[str] = []
    for word in PRE_SPLIT.findall(text):
        parts = tuple(word)
        for pair in merges:          # apply merges in the order they were learned
            parts = merge_pair(parts, pair)
        tokens.extend(parts)
    return tokens


def show(tokens: list[str]) -> str:
    return "|".join(t.replace(" ", "·") for t in tokens)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sentence", default=DEFAULT_SENTENCE)
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--merges", type=int, default=300)
    ap.add_argument("--train-chars", type=int, default=200_000,
                    help="how much of the text to learn merges from")
    args = ap.parse_args()

    text = open(args.data, encoding="utf-8").read()
    char_vocab = sorted(set(text))
    sentence = args.sentence

    print(f"sentence: {sentence!r}\n")
    print("1) characters, the tokenizer train.py uses")
    print(f"   vocab size {len(char_vocab)} (every distinct character in the text)")
    print(f"   {len(sentence)} tokens")
    print(f"   {show(list(sentence))}\n")

    merges = train_bpe(text[:args.train_chars], args.merges)
    tokens = bpe_encode(sentence, merges)
    bpe_vocab = len(set(text[:args.train_chars])) + len(merges)
    print(f"2) hand-written BPE, {len(merges)} merges learned from "
          f"{args.train_chars:,} characters of the novel")
    print(f"   vocab size {bpe_vocab} ({len(set(text[:args.train_chars]))} characters "
          f"+ {len(merges)} merged pieces)")
    print(f"   {len(tokens)} tokens")
    print(f"   {show(tokens)}\n")

    print("   the first 12 merges it learned, in order:")
    print("   " + "   ".join(show([a + b]) for a, b in merges[:12]))
    print()
    ratio = len(sentence) / len(tokens)
    print(f"same sentence: {len(sentence)} character tokens vs {len(tokens)} BPE tokens, "
          f"{ratio:.1f} characters per token.")
    print("a word the novel never contains still gets tokens, just more of them: "
          + show(bpe_encode(" texted", merges)))
    print("(· marks a space. It belongs to the token after it.)")


if __name__ == "__main__":
    main()
