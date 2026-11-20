# Prompts: The Twenty-Minute Model

This project has no model API in it, so no prompts are wired into the code. What
it has is the set of prompts worth using on your coding assistant while you
build it, because a training loop is easy to get subtly wrong: it runs, the loss
goes down, and it is still broken.

Use these with Claude Code, Codex, or whatever you build in.

## Prompt 1: Design the model size and time budget before writing the trainer

This decides whether you get words in twenty minutes or noise in two hours. Run
it before you write a line of `train.py`.

```
I want to train a character-level decoder-only transformer from scratch on my
laptop, in PyTorch. Here is my setup:

- Machine: {your laptop, chip, memory}
- Device: {mps, cuda or cpu}
- Training text: {size in characters, number of distinct characters}
- Time budget: {minutes}

Propose the model size: layers, heads, embedding width, context length, batch
size, learning rate. For each choice, tell me what it costs in time per step and
what it buys. Estimate the parameter count, and how many steps I will get in my
budget if one step takes {measure one and paste the number}. Tell me the
smallest model that will still produce real words in the budget, and the point
where a bigger model stops helping because the text is too small. Do not write
the trainer yet.
```

The last sentence is the one that matters. An assistant asked for a model size
will happily hand you a trainer too, and then you are debugging speed and
correctness at the same time.

Measure one step before you trust any estimate. `python train.py --minutes 1`
prints the step count, and the step count divided by sixty is your real speed.

## Prompt 2: Review the training loop for silent bugs

```
Here is my training script:

{paste train.py}

Act as a reviewer looking for bugs that do not crash and do not stop the loss
falling. Check specifically:
- Are targets the inputs shifted by exactly one position?
- Is attention causal, so position t cannot see position t+1?
- Is the validation text really held out from training?
- Is dropout off during evaluation and sampling, and back on after?
- Is the loss averaged correctly over batch and positions?
- Is the learning rate schedule doing what I think at every step?
- Will the same seed give the same sample on every checkpoint?

For each, quote the line that answers it. If you find a bug, tell me the
smallest experiment that proves it before you tell me the fix. Do not change
the code yet.
```

A non-causal mask is the classic one: the loss falls beautifully because the
model reads the answer, and the samples are garbage. That is why `watch.py`
exists. Loss alone cannot catch it.

## Prompt 3: Explain a loss curve from the real numbers

Paste the numbers, not a description of them. These are from my run.

```
Character-level transformer, {params} parameters, trained for {minutes} minutes
on {device}. Vocabulary is {vocab} characters. Here is loss.csv at every
checkpoint:

{paste step, train loss, validation loss for each checkpoint}

Walk me through this curve: why the loss at step 0 is what it is, what the
model has learned at each drop, and whether the gap between train and
validation loss tells me anything yet. Then tell me the single cheapest
experiment that would tell me whether more training time or a bigger model
would help more. Do not change my settings yet.
```

For the record, these were my numbers. Validation loss went 4.342 at step 0,
2.429 at 100, 1.842 at 250, 1.339 at 500, 1.129 at 1000, 1.098 at 1500, 1.116
at 2000 and 1.159 at the end, step 2683, while the training loss kept falling to
0.632. The question worth asking an assistant about that curve is the one in
"What the run taught me" in the [README](README.md): why the validation loss
turned around at step 1500, and what that means for the twenty minute default.

## Why "do not write the next layer yet" earns its place

All three prompts end by holding back the next step. With training code the
failures stack up: a model too big for the budget produces a curve you cannot
interpret, which produces hyperparameter changes that are guesses. One layer at
a time, checked against something you measured, is the difference between an
evening and a weekend.

## Tuning

- **It reaches for Hugging Face**: add "PyTorch only, no transformers library.
  I want to read every line of the model."
- **It suggests a pretrained tokenizer**: add "character-level, the vocabulary
  is the set of characters in my text. No downloads."
- **It ignores the time budget**: add "the run must stop at my time budget. Tie
  the learning rate schedule to elapsed time, not a step count."
- **It explains transformers at you**: add "I know the architecture. Answer only
  the specific question about my code."

## A note on privacy

Nothing in this project sends anything anywhere. The prompts on this page go to
whatever assistant you paste them into, carrying your code and your loss
numbers. If you train on your own text with `--data`, never paste that text
into a prompt. The prompts never need it, only the numbers.
