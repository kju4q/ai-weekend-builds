"""Train a tiny character-level GPT from scratch, on your laptop, and watch it learn.

    python train.py                     the full run: twenty minutes of training
    python train.py --minutes 5         a five minute budget instead
    python train.py --data my-notes.txt train on your own text instead
    python train.py --selftest          a 30 second check that everything works

Every checkpoint step (including step 0, before any training) it saves the model,
prints a sample from the same prompt with the same random seed, and appends the
sample to output/samples.jsonl. Loss goes to output/loss.csv and output/loss.html.

No network calls, no downloads, no API key. The training text ships in
sample-data/, and everything written goes to output/.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass

import torch
import torch.nn as nn
from torch.nn import functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.join(HERE, "sample-data", "pride-and-prejudice.txt")
DEFAULT_PROMPT = "It is a truth universally acknowledged"
CHECKPOINT_STEPS = [0, 100, 250, 500, 1000, 1500, 2000, 3000, 4000, 6000, 8000]
SAMPLE_CHARS = 240
SAMPLE_SEED = 1337


@dataclass
class Config:
    vocab_size: int = 0
    block_size: int = 256    # how many characters the model can look back at
    n_layer: int = 6         # transformer blocks stacked on top of each other
    n_head: int = 6          # attention heads per block
    n_embd: int = 384        # width of every vector inside the model
    dropout: float = 0.2


# ==== the model

class Block(nn.Module):
    """One transformer block: attention (look back), then an MLP (think)."""

    def __init__(self, c: Config):
        super().__init__()
        self.ln1 = nn.LayerNorm(c.n_embd)
        self.attn = nn.Linear(c.n_embd, 3 * c.n_embd)
        self.proj = nn.Linear(c.n_embd, c.n_embd)
        self.ln2 = nn.LayerNorm(c.n_embd)
        self.mlp = nn.Sequential(
            nn.Linear(c.n_embd, 4 * c.n_embd),
            nn.GELU(),
            nn.Linear(4 * c.n_embd, c.n_embd),
            nn.Dropout(c.dropout),
        )
        self.n_head = c.n_head
        self.dropout = c.dropout
        self.resid_drop = nn.Dropout(c.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.shape
        q, k, v = self.attn(self.ln1(x)).split(C, dim=2)
        q, k, v = (t.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
                   for t in (q, k, v))
        # is_causal=True is the whole trick: position t may only look at 0..t,
        # so the model can never cheat by reading the character it must predict.
        y = F.scaled_dot_product_attention(
            q, k, v, is_causal=True,
            dropout_p=self.dropout if self.training else 0.0)
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        x = x + self.resid_drop(self.proj(y))
        return x + self.mlp(self.ln2(x))


class TinyGPT(nn.Module):
    def __init__(self, c: Config):
        super().__init__()
        self.config = c
        self.tok_emb = nn.Embedding(c.vocab_size, c.n_embd)
        self.pos_emb = nn.Embedding(c.block_size, c.n_embd)
        self.drop = nn.Dropout(c.dropout)
        self.blocks = nn.Sequential(*[Block(c) for _ in range(c.n_layer)])
        self.ln_f = nn.LayerNorm(c.n_embd)
        self.head = nn.Linear(c.n_embd, c.vocab_size, bias=False)
        self.apply(self._init)

    @staticmethod
    def _init(m: nn.Module) -> None:
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
        if isinstance(m, nn.Linear) and m.bias is not None:
            nn.init.zeros_(m.bias)

    def n_params(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.drop(self.tok_emb(idx) + self.pos_emb(pos))
        logits = self.head(self.ln_f(self.blocks(x)))
        if targets is None:
            return logits, None
        # Cross-entropy: how surprised the model was by the real next character.
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx: torch.Tensor, n: int, gen: torch.Generator,
                 temperature: float = 0.8) -> torch.Tensor:
        for _ in range(n):
            logits, _ = self(idx[:, -self.config.block_size:])
            probs = F.softmax(logits[:, -1, :] / temperature, dim=-1)
            # Sample on the CPU with our own generator, so the same seed gives
            # the same draw on every device.
            nxt = torch.multinomial(probs.float().cpu(), 1, generator=gen)
            idx = torch.cat([idx, nxt.to(idx.device)], dim=1)
        return idx


# ==== data

class CharData:
    """Every distinct character in the text is one token. That is the tokenizer."""

    def __init__(self, text: str, device: str):
        self.chars = sorted(set(text))
        self.stoi = {ch: i for i, ch in enumerate(self.chars)}
        data = torch.tensor(self.encode(text), dtype=torch.long)
        cut = int(0.9 * len(data))
        self.train, self.val = data[:cut], data[cut:]
        self.device = device

    def encode(self, s: str) -> list[int]:
        return [self.stoi[c] for c in s if c in self.stoi]

    def decode(self, ids) -> str:
        return "".join(self.chars[i] for i in ids)

    def batch(self, split: str, batch_size: int, block: int, gen: torch.Generator):
        data = self.train if split == "train" else self.val
        ix = torch.randint(len(data) - block - 1, (batch_size,), generator=gen)
        x = torch.stack([data[i:i + block] for i in ix])
        y = torch.stack([data[i + 1:i + 1 + block] for i in ix])  # shifted by one
        return x.to(self.device), y.to(self.device)


def pick_device(requested: str | None) -> str:
    if requested:
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def sync(device: str) -> None:
    if device == "mps":
        torch.mps.synchronize()
    elif device == "cuda":
        torch.cuda.synchronize()


# ==== training

@torch.no_grad()
def estimate_loss(model, data, batch_size, block, iters, gen) -> dict:
    model.eval()
    out = {}
    for split in ("train", "val"):
        losses = [model(*data.batch(split, batch_size, block, gen))[1].item()
                  for _ in range(iters)]
        out[split] = sum(losses) / len(losses)
    model.train()
    return out


def sample(model, data, prompt: str, n: int) -> str:
    model.eval()
    gen = torch.Generator().manual_seed(SAMPLE_SEED)
    idx = torch.tensor([data.encode(prompt)], dtype=torch.long, device=data.device)
    out = data.decode(model.generate(idx, n, gen)[0].tolist())
    model.train()
    return out


def save_checkpoint(path, model, data, step, losses, half=False) -> None:
    state = model.state_dict()
    if half:
        state = {k: v.half() for k, v in state.items()}
    torch.save({"config": asdict(model.config), "chars": data.chars,
                "step": step, "losses": losses,
                "state": {k: v.cpu() for k, v in state.items()}}, path)


def load_checkpoint(path: str, device: str):
    ck = torch.load(path, map_location="cpu", weights_only=False)
    model = TinyGPT(Config(**ck["config"]))
    model.load_state_dict({k: v.float() for k, v in ck["state"].items()})
    return model.to(device).eval(), ck


def lr_at(step: int, progress: float, peak: float, warmup: int = 100) -> float:
    """Warm up over the first steps, then a cosine decay over the time budget.
    progress is the fraction of the budget used, so the schedule ends when the
    clock does, on a fast machine or a slow one."""
    if step < warmup:
        return peak * (step + 1) / warmup
    return peak * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, progress))))


def train(args) -> dict:
    torch.manual_seed(args.seed)
    device = pick_device(args.device)
    with open(args.data, encoding="utf-8") as f:
        text = f.read()
    data = CharData(text, device)
    c = Config(vocab_size=len(data.chars), block_size=args.block,
               n_layer=args.layers, n_head=args.heads, n_embd=args.width,
               dropout=args.dropout)
    model = TinyGPT(c).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.1,
                            betas=(0.9, 0.95))
    os.makedirs(args.out, exist_ok=True)
    gen = torch.Generator().manual_seed(args.seed)
    eval_gen = torch.Generator().manual_seed(args.seed + 1)

    max_steps = args.max_steps or 10**9
    checkpoints = [s for s in CHECKPOINT_STEPS if s < max_steps]
    if args.max_steps:
        checkpoints.append(args.max_steps)
    print(f"device {device} | text {len(text):,} chars | vocab {c.vocab_size} characters")
    print(f"model {model.n_params():,} parameters | {c.n_layer} layers, "
          f"{c.n_head} heads, width {c.n_embd}, context {c.block_size}")
    print(f"budget {args.minutes:g} minutes"
          + (f" or {args.max_steps} steps, whichever comes first" if args.max_steps else "")
          + f" | checkpoints at steps {checkpoints} and wherever the clock stops")
    print(f"prompt: {args.prompt!r}\n")

    loss_path = os.path.join(args.out, "loss.csv")
    samples_path = os.path.join(args.out, "samples.jsonl")
    open(samples_path, "w").close()
    rows: list[dict] = []
    t0 = time.time()
    budget = args.minutes * 60
    step = 0
    last_train = float("nan")

    def checkpoint(step: int, w, lr: float) -> None:
        sync(device)
        elapsed = time.time() - t0
        losses = estimate_loss(model, data, args.batch, c.block_size, args.eval_iters, eval_gen)
        text_out = sample(model, data, args.prompt, args.sample_chars)
        save_checkpoint(os.path.join(args.out, f"step-{step:05d}.pt"),
                        model, data, step, losses)
        rec = {"step": step, "elapsed_s": round(elapsed, 1),
               "train_loss": round(losses["train"], 4),
               "val_loss": round(losses["val"], 4), "sample": text_out}
        with open(samples_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        # Checkpoints get a row in loss.csv too, measured over eval_iters batches,
        # so the chart starts at step 0 and ends on the same numbers as the samples.
        w.writerow([step, rec["elapsed_s"], rec["train_loss"], rec["val_loss"], f"{lr:.2e}"])
        print(f"\n=== step {step:5d} | {elapsed/60:5.1f} min | train {losses['train']:.3f}"
              f" | val {losses['val']:.3f} ===")
        print(text_out)
        print("=" * 60 + "\n", flush=True)

    with open(loss_path, "w", newline="") as lf:
        w = csv.writer(lf)
        w.writerow(["step", "elapsed_s", "train_loss", "val_loss", "lr"])
        while True:
            out_of_time = time.time() - t0 > budget
            if step in checkpoints or out_of_time or step == max_steps:
                checkpoint(step, w, lr_at(step, (time.time() - t0) / budget, args.lr))
                if out_of_time or step >= max_steps:
                    break
            if args.max_steps:
                progress = max(step / args.max_steps, (time.time() - t0) / budget)
            else:
                progress = (time.time() - t0) / budget
            lr = lr_at(step, progress, args.lr)
            for g in opt.param_groups:
                g["lr"] = lr
            x, y = data.batch("train", args.batch, c.block_size, gen)
            _, loss = model(x, y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            step += 1
            if step % args.log_every == 0 and step not in checkpoints:
                last_train = loss.item()   # .item() waits for the GPU, so only now and then
                elapsed = time.time() - t0
                row = {"step": step, "elapsed_s": round(elapsed, 1),
                       "train_loss": round(last_train, 4), "val_loss": "", "lr": f"{lr:.2e}"}
                if step % args.eval_every == 0:
                    row["val_loss"] = round(estimate_loss(
                        model, data, args.batch, c.block_size, args.eval_iters,
                        eval_gen)["val"], 4)
                w.writerow(row.values())
                lf.flush()
                rows.append(row)
                if step % (args.log_every * 10) == 0:
                    print(f"step {step:5d} | {elapsed/60:5.1f} min | loss {last_train:.3f}"
                          + (f" | val {row['val_loss']:.3f}" if row["val_loss"] != "" else ""),
                          flush=True)

    total = time.time() - t0
    write_loss_html(os.path.join(args.out, "loss.html"), loss_path)
    summary = {"device": device, "params": model.n_params(), "steps": step,
               "minutes": round(total / 60, 2), "final_train": last_train}
    print(f"done: {step} steps in {total/60:.1f} minutes on {device}, "
          f"{model.n_params():,} parameters")
    print(f"wrote loss.csv, samples.jsonl, loss.html and the checkpoints to {args.out}")
    return summary


# ==== loss chart

def write_loss_html(path: str, csv_path: str) -> None:
    """Rebuild loss.html around the rows in csv_path. The template is the tracked
    loss.html next to this file, so the chart code lives in exactly one place."""
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    template = os.path.join(HERE, "loss.html")
    with open(template) as f:
        html = f.read()
    start = html.index("/*DATA*/") + len("/*DATA*/")
    end = html.index("/*END*/")
    html = html[:start] + json.dumps(rows) + html[end:]
    with open(path, "w") as f:
        f.write(html)


# ==== selftest

def selftest() -> None:
    t0 = time.time()
    tmp = tempfile.mkdtemp(prefix="tinygpt-")
    text = open(DEFAULT_DATA, encoding="utf-8").read()[:60_000]
    data_path = os.path.join(tmp, "data.txt")
    open(data_path, "w").write(text)
    args = build_parser().parse_args([
        "--data", data_path, "--out", tmp, "--device", "cpu", "--max-steps", "60",
        "--layers", "2", "--heads", "2", "--width", "64", "--block", "64",
        "--batch", "16", "--eval-iters", "4", "--log-every", "10",
        "--eval-every", "30", "--sample-chars", "40", "--lr", "3e-3"])
    print("selftest: training a 2-layer model for 60 steps on the CPU\n")
    summary = train(args)

    recs = [json.loads(l) for l in open(os.path.join(tmp, "samples.jsonl"))]
    assert recs[0]["step"] == 0, "first checkpoint must be the untrained model"
    assert recs[-1]["val_loss"] < recs[0]["val_loss"] - 0.5, "loss did not fall"
    assert all(r["sample"].startswith(DEFAULT_PROMPT) for r in recs)

    model, ck = load_checkpoint(os.path.join(tmp, "step-00060.pt"), "cpu")
    data = CharData(text, "cpu")
    assert sample(model, data, DEFAULT_PROMPT, 40) == recs[-1]["sample"], \
        "reloaded checkpoint does not reproduce its own sample"
    rows = list(csv.DictReader(open(os.path.join(tmp, "loss.csv"))))
    assert [r["step"] for r in rows] == ["0", "10", "20", "30", "40", "50", "60"] and os.path.exists(os.path.join(tmp, "loss.html"))
    print(f"\nuntrained val loss {recs[0]['val_loss']:.3f}, "
          f"ln(vocab {len(data.chars)}) = {math.log(len(data.chars)):.3f}")
    print(f"after 60 steps     {recs[-1]['val_loss']:.3f}")
    print(f"checkpoint reload reproduces the sample: yes")
    full = open(DEFAULT_DATA, encoding="utf-8").read()
    whole = CharData(full, "cpu")
    assert whole.decode(whole.encode(full)) == full, "encode then decode lost text"
    print(f"encode then decode gives back all {len(full):,} characters: yes")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"selftest ok in {time.time() - t0:.1f}s")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Train a tiny character-level GPT.")
    ap.add_argument("--data", default=DEFAULT_DATA, help="any plain UTF-8 text file")
    ap.add_argument("--out", default=os.path.join(HERE, "output"))
    ap.add_argument("--minutes", type=float, default=20,
                    help="the time budget: training stops here and the schedule fits it")
    ap.add_argument("--max-steps", type=int, default=0,
                    help="optional step cap, 0 means the clock alone decides")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--device", default=None, help="mps, cuda or cpu (auto if unset)")
    ap.add_argument("--layers", type=int, default=Config.n_layer)
    ap.add_argument("--heads", type=int, default=Config.n_head)
    ap.add_argument("--width", type=int, default=Config.n_embd)
    ap.add_argument("--block", type=int, default=Config.block_size)
    ap.add_argument("--dropout", type=float, default=Config.dropout)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--eval-iters", type=int, default=20)
    ap.add_argument("--log-every", type=int, default=25)
    ap.add_argument("--eval-every", type=int, default=250)
    ap.add_argument("--sample-chars", type=int, default=SAMPLE_CHARS)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    return ap


if __name__ == "__main__":
    a = build_parser().parse_args()
    if a.selftest:
        selftest()
    else:
        train(a)
