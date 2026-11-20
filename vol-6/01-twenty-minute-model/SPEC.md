# SPEC: The Twenty-Minute Model

The spec this project was built from. Paste it into your assistant with the
first prompt in [prompts.md](prompts.md) if you want to rebuild it yourself, or
change it first: your machine, your time budget, your text.

## One sentence

A tiny character-level GPT, trained from scratch on a laptop in a fixed time
budget, that prints a sample from the same prompt at fixed checkpoints so you
can watch the output go from noise to words while the loss falls.

## Inputs

- A plain UTF-8 text file. Default: `sample-data/pride-and-prejudice.txt`,
  public domain, shipped in the repo
- `--minutes`: the time budget
- `--data`: any other text file

## Outputs

- `output/step-NNNNN.pt`: a checkpoint at fixed steps, including step 0 before
  any training, plus the step where the clock ran out
- `output/samples.jsonl`: per checkpoint, the step, elapsed time, train and
  validation loss, and a sample from the same prompt with the same seed
- `output/loss.csv`: step, elapsed seconds, train loss, validation loss,
  learning rate
- `output/loss.html`: the loss chart, self-contained, no network

## Out of scope

- Pretrained weights, tokenizer downloads, Hugging Face
- Instruction tuning or chat
- Multi-GPU anything

## Constraints

- Python 3.10+ and PyTorch only, plus numpy so PyTorch does not warn
- Device picked automatically: mps, then cuda, then cpu
- No network calls at all
- The learning rate schedule follows elapsed time, so the run ends cleanly at
  the budget on any machine
- Sampling uses a fixed seed on the CPU, so a checkpoint always gives the same
  sample
- Generated outputs are in `.gitignore`. One small sample checkpoint and the
  samples from a real run are tracked so `watch.py` works before training.

## Milestones

### M1: Data and tokens
- Build: load the text, build the character vocabulary, encode, decode, split
  90/10; `tokens.py` shows characters vs a hand-written BPE
- Acceptance check: `python tokens.py` prints the same sentence both ways with
  vocabulary sizes and token counts, and decoding the encoded novel gives back
  the original text

### M2: The model, untrained
- Build: `TinyGPT` with causal attention; sample from it with random weights
- Acceptance check: the step 0 sample is noise, and the step 0 loss is within
  0.2 of ln(vocabulary size)

### M3: The training loop and selftest
- Build: AdamW, warmup and cosine decay on elapsed time, gradient clipping,
  checkpoints, `samples.jsonl`, `loss.csv`, `--selftest`
- Acceptance check: `python train.py --selftest` prints `selftest ok` in under
  30 seconds, and it checks that loss fell and that a reloaded checkpoint
  reproduces its own sample

### M4: The real run, measured
- Build: choose the default model size for a twenty minute run on my machine
- Acceptance check: `python train.py` stops at the budget, the last sample is
  made of real words, and I record the device, steps, final loss and every
  checkpoint's sample in the README

### M5: Watching it
- Build: `watch.py` (side by side samples, typed out, or fresh generation from
  checkpoints), `loss.html`
- Acceptance check: `python watch.py` works on the shipped samples before any
  training, and `loss.html` opens with the network off

## Done means

- [ ] Every acceptance check passes
- [ ] Every number in the README came from a run I did
