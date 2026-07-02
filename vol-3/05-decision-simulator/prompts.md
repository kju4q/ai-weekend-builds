# Prompts: Decision Simulator

The simulation needs no prompt — it's math and `random`. The one place an LLM
helps is the hardest part for a human: turning a fuzzy real decision into honest
distributions. That's what these prompts do. All of it is optional; you can write
the config by hand.

## Prompt 1: Plain-English decision → config

```
Turn this decision into a Monte Carlo config JSON for my simulator.

Decision: {describe it in plain words, with whatever real numbers you have —
e.g. "Rent vs buy a $500k house over 5 years. Rent is about $2,200/mo now. I'm
unsure about home appreciation and what I'd earn investing the down payment."}

Rules:
- Output ONLY valid JSON with this shape:
  { "title", "runs": 10000, "goal": "max" | "min",
    "variables": { name: {"dist": "normal"|"uniform"|"triangular"|"bernoulli"| ...} or {"fixed": n} },
    "options": { "OptionName": "a math expression over the variable names" } }
- Anything I'm uncertain about becomes a distribution; anything I stated as a fact
  becomes "fixed".
- Choose distributions honestly: normal for "around X", uniform for "somewhere
  between", triangular when there's a most-likely value, bernoulli for a yes/no.
- Make the option expressions compute the thing I actually care about (net worth,
  total cost, total comp). State in the title what higher/lower means.
- After the JSON, in a comment-free separate message, list every assumption you made
  so I can correct it.
```

## Prompt 2: Sanity-check my distributions

```
Here is my decision config:
{paste config}

Play skeptic. For each uncertain variable: is the spread realistic, or am I being
overconfident? Which variable's uncertainty probably matters most to the outcome?
Is anything that should be uncertain marked "fixed"? Don't rewrite it — just point
at what to reconsider.
```

## Prompt 3: Read the result back to me

```
Here is the summary from 10,000 simulations:
{paste the printed summary or results.json "summary" + "win_rate"}

In plain language: which option is better and why, what the realistic range is,
and specifically how bad the worst cases get. Name the tradeoff between the safe
option and the high-variance one. 5 sentences, no hedging beyond what the numbers
support.
```

## Why the LLM does NOT run the simulation

Language models are bad at arithmetic over 10,000 draws and would just make up a
plausible answer. The whole point is that the *engine* computes the futures
deterministically and locally. Claude is for translating words to a model and
model back to words — never for doing the sampling. Keep that line and you keep
results you can trust.

## Tuning

- **Config won't parse**: add "Return only the JSON object, no markdown fence."
- **Distributions too confident**: add "Assume I'm overconfident. Widen the ranges."
- **Wrong goal direction**: state it explicitly ("lower total cost is better → goal: min").
