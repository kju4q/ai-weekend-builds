# 01: The Twenty-Minute Model

A tiny GPT, trained from scratch on your laptop, on a novel from 1813. At step 0
it prints noise. Twenty minutes later it prints sentences that sound like Jane
Austen and mean nothing. In between you watch the loss fall and the same prompt
turn into words, checkpoint by checkpoint.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 2-3h | Python, PyTorch |

## What you'll build

A character-level decoder-only transformer, the same kind of model as GPT, small
enough to read in one sitting. A trainer that runs for a fixed time budget, saves
checkpoints at fixed steps, and prints a sample from the same prompt at each one.
A replayer that shows every checkpoint side by side, a loss chart, and a script
that shows you what a token is.

The real numbers from my run, on a MacBook Pro with an Apple M2 Pro and 16 GB of
memory, macOS 26.6, PyTorch 2.15.0 on the MPS backend, with the default settings:

| Step | Minutes | Train loss | Validation loss | What it wrote after the prompt (first 110 characters) |
|---:|---:|---:|---:|---|
| 0 | 0.0 | 4.341 | 4.342 | `,f,,46SGwsnj5(m,Nvr,O:A / z44NO2b-;5SBVe'yW5?UdGUoCOUsPvThv,!njj-C2lU)f,wDDN,wUz6-Vx!6,!(Ub6M64 / SZ!PUHg(,),W...` |
| 100 | 0.8 | 2.415 | 2.429 | `, caso st tond o hathee / sin hube thedede ashe towantove t t at abl toowho hexce / d an, out in our thond ang...` |
| 250 | 2.0 | 1.843 | 1.842 | `, the ast to knothe to saided be the / exects deto to me histere able for sirdy wer a whould the / whe parmani...` |
| 500 | 3.9 | 1.303 | 1.339 | `, they were not, however / never, however, as determined him, and all for / sixter to the minute of her affaic...` |
| 1000 | 7.6 | 1.014 | 1.129 | `, and as soon as he could / not be the entertained. She was therefore for so whole day, on what / procuring fo...` |
| 1500 | 11.4 | 0.866 | 1.098 | `, and as soon as he could not be the / expectation." /  / "I have just attempted to me to be in Meryton," said...` |
| 2000 | 15.1 | 0.740 | 1.116 | `, they said no more, / with a most unreasonable solicity as they are married, and / readily be always long at...` |
| 2683 | 20.0 | 0.632 | 1.159 | `, they saw that, however, / therefore, in a short want of very extravagance in spirits, or which / would hardl...` |

The prompt every time is the novel's first line, *"It is a truth universally
acknowledged"*, sampled with the same random seed, so the only thing changing
between rows is the weights. Full samples are in `sample-data/samples.jsonl`,
and `python watch.py` shows them side by side.

Measured on that run: 2,683 steps in 20.0 minutes of training (the whole command
took 20.1 minutes, startup and the last checkpoint included), 10,799,616
parameters, final validation loss 1.159. The lowest validation loss was 1.098 at
step 1500, and the section "What the run taught me" is about why it went back
up. On another machine the step count will differ, because the budget is time,
not steps.

## What you'll learn

- **Training**: what one step actually does (predict, measure the miss, nudge
  every weight), and why it takes thousands of them
- **Tokens**: the model never sees letters or words, only integers, and how you
  cut text into those integers changes everything downstream
- **Loss**: the single number that goes down, what its value means at step 0,
  and why the validation loss matters more than the training loss
- **Reading a model's output honestly**: fluent is not the same as meaningful,
  and the samples show you the difference

## Prerequisites

- Python 3.10+ (tested on 3.12)
- `pip install -r requirements.txt` (PyTorch and numpy)
- A recent Mac with Apple silicon, or a machine with an NVIDIA GPU. A CPU works
  for the selftest, but not for the real run: on the same M2 Pro, forced onto the
  CPU with `--device cpu --minutes 1`, it got 14 steps, against about 134 a
  minute on the GPU.
- No API key. Not optional, not needed, not supported.

## Local vs API

| Part | Runs where |
|---|---|
| The training text | Ships in `sample-data/`, read from disk |
| Training | 100% local, on your GPU or CPU |
| Sampling, replaying, the loss chart | 100% local |
| Tokens demo | 100% local, the tokenizer is written in the file |

Everything is local: no network calls, no downloads, no key. `loss.html` is one
self-contained file with no external scripts or fonts.

## The training text

`sample-data/pride-and-prejudice.txt` is *Pride and Prejudice* by Jane Austen,
first published in 1813. It is in the public domain because Austen died in 1817,
so the copyright expired long ago everywhere, and the work was published before
1931, so it is public domain in the United States as well.

I took the text from Project Gutenberg's eBook #1342, kept only the novel from
"It is a truth universally acknowledged" to the last line, removed the
illustration captions, the publisher's lines and every Project Gutenberg header
and license line, and turned curly quotes and accented letters into plain ASCII.
The result is 684,920 characters with 70 distinct characters, which is also the
model's whole vocabulary. Austen's own double hyphens are left in, as
she wrote them.

To train on your own text instead:

```
python train.py --data path/to/your-text.txt
```

Any plain UTF-8 file works. On a small file, watch the gap between train and
validation loss: when train keeps falling and validation stops, the model is
memorizing your text rather than learning it.

## How it works

```
pride-and-prejudice.txt
   │  every distinct character gets an integer: 70 of them
   v
[ 27, 63, 1, 52, 62, 1, 44, ... ]   "It is a", 90% train, last 10% held out for validation
   │
   │  take 64 random windows of 256 characters
   v
TinyGPT  ──  embed each character + its position
   │         6 blocks of: causal attention (look back) -> MLP (think)
   │         a score for every possible next character, at every position
   v
cross-entropy loss: how surprised was it by the real next character?
   │
   v
backprop + AdamW: nudge all 10,799,616 weights to be less surprised
   │
   └── repeat until the clock runs out (20 minutes by default)

checkpoints at steps 0, 100, 250, 500, 1000, 1500, 2000, 3000 and up, and the step
where the clock runs out:
   save the weights, print a sample from the same prompt with the same seed
```

## Build it

### Step 1: Check the setup

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python train.py --selftest
```

It trains a 2-layer model for 60 steps on the CPU, checks that the loss fell,
that the first checkpoint is the untrained one, and that reloading a checkpoint
reproduces its own sample exactly. It prints `selftest ok` in a few seconds.

### Step 2: Watch a finished run before you start one

```
python watch.py
```

Before you have trained anything this replays `sample-data/samples.jsonl`, the
samples from the run in the table above, side by side. This is the target.
`python watch.py --type` types each one out, which is the version to film.

### Step 3: See what a token is

```
python tokens.py
```

The same sentence as characters (what this model uses) and as a tiny BPE written
by hand in the file and trained on the novel in a couple of seconds. Here is what
it printed for me:

```
sentence: 'It is a truth universally acknowledged that Elizabeth texted Darcy.'

1) characters, the tokenizer train.py uses
   vocab size 70 (every distinct character in the text)
   67 tokens
   I|t|·|i|s|·|a|·|t|r|u|t|h|·|u|n|i|v|e|r|s|a|l|l|y|·|a|c|k|n|o|w|l|e|d|g|e|d|·|t|h|a|t|·|E|l|i|z|a|b|e|t|h|·|t|e|x|t|e|d|·|D|a|r|c|y|.

2) hand-written BPE, 300 merges learned from 200,000 characters of the novel
   vocab size 367 (67 characters + 300 merged pieces)
   30 tokens
   I|t|·is|·a|·t|r|ut|h|·un|i|ver|s|all|y|·ac|k|now|l|ed|g|ed|·that|·Elizabeth|·t|e|x|t|ed|·Darcy|.

   the first 12 merges it learned, in order:
   ·t   he   ·a   in   ·s   ·w   re   ·o   er   ou   ha   ·the

same sentence: 67 character tokens vs 30 BPE tokens, 2.2 characters per token.
a word the novel never contains still gets tokens, just more of them: ·t|e|x|t|ed
(· marks a space. It belongs to the token after it.)
```

Real tokenizers are this idea with a far bigger vocabulary. The character
version is why this model needs 70 outputs instead of tens of thousands.

### Step 4: See the untrained output first

Start training and look at the very first sample before it learns anything:

```
python train.py
```

Step 0 is printed before a single weight has been updated. My step 0:

```
It is a truth universally acknowledged,f,,46SGwsnj5(m,Nvr,O:A
z44NO2b-;5SBVe'yW5?UdGUoCOUsPvThv,!njj-C2lU)f,wDDN,wUz6-Vx!6,!(Ub6M64
SZ!PUHg(,),W6H!kBgjmKu
FuZKG)Dj(V6iGU,jL'TFy"8J6Xi'wNy)wlipp,Wv5?
sOmAueTW6.BlOUgb-(.,!ls:VEs)ss:XuwSN6dCawUB4,JO.h'iybxnX"M!jSai)LmI)bmoBdSyfSb-U
```

That is what random weights produce. Also look at the loss on that line: 4.342
on validation text. If every one of the 70 characters were equally likely, the
loss would be ln(70) = 4.248. An untrained model is a guesser, and the
loss says exactly how good a guesser.

### Step 5: Let it run, and watch the loss

The trainer prints the loss every 250 steps and a sample at every checkpoint.
When it finishes, open the chart:

```
open output/loss.html
```

`loss.html` in this folder is the chart from my run. Yours is written to
`output/loss.html`. Both work with the network off, and either can open any
`loss.csv` with the file picker at the bottom.

### Step 6: Replay your own run

```
python watch.py
python watch.py --rows
python watch.py --prompt "Mr. Darcy"
```

The last one loads every checkpoint you saved and generates from a new prompt,
so you can see whether the model learned the text or just the first line.

## Verify it works

- [ ] `python train.py --selftest` prints `selftest ok`
- [ ] `python tokens.py` prints the same sentence as 70-character tokens and
      as fewer BPE tokens
- [ ] `python watch.py` shows the shipped samples before you train
- [ ] `python train.py` prints the step 0 sample as noise and a loss close to
      ln(70) = 4.248
- [ ] The run stops at the time budget and writes `output/loss.csv`,
      `output/samples.jsonl`, `output/loss.html` and one `.pt` per checkpoint
- [ ] `python watch.py` now shows your run, and the last checkpoint is made of
      real words
- [ ] `output/loss.html` opens with wifi off

## Same idea as GPT, and what is not the same

What is genuinely the same:

- **Next-token prediction.** The only thing this model is trained to do is
  predict the next token from the ones before it. That is the training objective
  of GPT-style models too.
- **Cross-entropy loss.** The same number, computed the same way: how much
  probability the model gave to the token that actually came next.
- **A decoder-only transformer.** Embeddings, causal self-attention, MLPs,
  residual connections, layer norm. The `Block` class in `train.py` is the same
  shape as a block in a large model, just narrower and with fewer of them.
- **Sampling.** Generation is the same loop: predict a distribution, draw one
  token, append it, repeat.

What is emphatically **not** the same:

- **Scale.** This model has 10,799,616 parameters. GPT-2, from 2019, had 1.5
  billion in its largest version, about 140 times as many, and it is small next
  to the models people chat with today. Scale is not a detail: it is most of why
  big models can do things this one cannot.
- **Data.** One novel, about 685,000 characters. Large models train on far
  more text: web pages, books and code, in many languages.
- **Tokenizer.** One token per character, 70 of them. Large models use a
  learned subword tokenizer, the idea in `tokens.py`, with a vocabulary in the
  tens of thousands or more (GPT-2's had 50,257). Each token carries more text,
  so the same context window sees far more of it.
- **Instruction tuning.** This model only continues text. It has never been
  trained to follow an instruction, answer a question, or refuse one. Chat
  models get further training on examples of conversations and on human
  preferences. Ask this model a question and it writes the next line of a novel.

So: the same objective and the same architecture, without the scale, the data,
the tokenizer or the tuning that make a chat assistant. Which is the right
thing to understand in twenty minutes, as long as nobody tells you that you
just trained GPT.

## What the run taught me

Every item below is something I saw in the run above, not a general lesson I
looked up.

**Untrained is slightly worse than guessing.** If the model gave all 70
characters equal odds, the loss would be ln(70) = 4.248. At step 0 it was 4.342.
Random weights are not neutral: they are a little confident, about the wrong
characters. Loss is a good ruler from the very first step.

**Spelling came before sense, and both came fast.** At step 100 (0.8 minutes)
the sample is word-shaped: "caso st tond o hathee". At step 500 (3.9 minutes),
37 of the 44 words in the sample are words that appear in the novel. At step
1000 (7.6 minutes) it was 48 of 48, and at step 1500 it was writing dialogue,
opening and closing quotes and "said Mr. Bennet". Not one of those sentences
means anything. The model learned what Austen's text looks like long before it
could have learned what it says, and in twenty minutes at this size it did not
get there.

**My best model was at minute 11, not minute 20.** Validation loss, measured on
the last 10% of the novel that the model never trains on, was lowest at step
1500: 1.098. After that it rose, to 1.116 at step 2000 and 1.159 at the end,
while the training loss kept falling, from 0.866 to 0.632. That gap is the
model getting better at the 90% it trains on and worse at text it has not seen.
It has 10.8 million parameters and about 616,000 training characters. The last
eight and a half minutes of my twenty-minute run made the model worse at the
thing I actually care about, and the training loss alone would never have told
me.

**The samples did not show it.** To me, the step 2683 sample reads no worse
than the step 1500 one. If I had judged the run by reading output, I would have
called those last minutes progress. The validation loss is the only place the
problem was visible.

**It did not memorize the line it was prompted with.** The novel continues
"that a single man in possession of a good fortune". None of the eight
checkpoints wrote that. I checked every sample against the novel: the longest
run of characters copied exactly was 26 characters ("Lady Catherine had been
r", at step 2000). The model learned the style, not the text, even while it was
starting to overfit.

**Ask it a question and it writes a novel.** I gave the final checkpoint the
prompt "What is the capital of France?". It closed the quotation mark and wrote
a reply in a drawing room: *"My dear Jane, I think: I have no reason for your
power..."*. Next-token prediction on one book gives you a continuation machine,
not an assistant. That gap is instruction tuning, the last item in the section
above.

## Extend it

- Train on your own writing with `--data` and see which of your habits it picks
  up first
- Stop at the best point: try `--minutes 12`, or raise `--dropout`, and see
  whether the final validation loss beats my 1.159
- Try `--width 192 --layers 4` and compare the final loss and samples at the
  same twenty minutes: smaller and faster, or bigger and slower?
- Replace the character tokenizer with the BPE from `tokens.py` and compare the
  samples at the same budget
- Plot attention: for one sample, which earlier characters does each position
  look at?
- Add a temperature flag to `watch.py` and see what 0.3 and 1.5 do to the same
  checkpoint

## Common pitfalls

- **Judging it at the first checkpoints.** Step 100 is word-shaped nonsense. Wait.
- **Reading the train loss as the real number.** The train loss in the progress
  lines is one batch and noisy. The validation loss is measured on text the model
  never trains on, and it is the honest one.
- **A prompt from the training text.** The default prompt is the novel's first
  line, and the model has read it. Use `watch.py --prompt` with something new to
  see what it does when it cannot remember.
- **Comparing runs on different machines by step.** The budget is time, so a
  faster machine gets more steps in the same twenty minutes. Compare final loss
  at equal minutes, or pass `--max-steps` to fix the step count.
- **Out of memory on a smaller GPU.** Lower `--batch` first, then `--block`.
- **Checkpoints filling your disk.** Each one is 43 MB, and my run wrote 8 of
  them. `output/` is in `.gitignore` so they never get committed.

## Files

- `train.py`: the model, the trainer, the loss chart writer, and `--selftest`
- `tokens.py`: characters vs a hand-written BPE, on the same sentence
- `watch.py`: replays every checkpoint's sample, or generates fresh from them
- `loss.html`: the loss chart from my run, and the template `train.py` fills in
- [SPEC.md](SPEC.md): the spec this was built from, with acceptance checks
- [prompts.md](prompts.md): the prompts for your coding assistant
- `sample-data/`: the training text, `samples.jsonl` and `loss.csv` from my run,
  and `final.pt`, the last checkpoint of that run in half precision

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
