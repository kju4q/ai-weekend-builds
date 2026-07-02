# 05: Decision Simulator

You're about to make a big decision — rent vs. buy, Job A vs. Job B — and you're
guessing at one future. This tool runs ten thousand. It finds the uncertain
variables, simulates 10,000 versions of how it could go, and shows you where the
futures cluster and how bad the worst cases really get, as a chart you can read
in five seconds.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Advanced | Full day | Python (standard library) + a single HTML chart |

## What you'll build

A Monte Carlo simulation engine, a small config format for describing a decision
in real numbers, and a genuinely good interactive visualization. You define a
decision as a set of variables (some fixed, some uncertain distributions) and one
formula per option. The engine samples the uncertain variables 10,000 times,
evaluates every option each time, and renders overlapping outcome distributions
with medians, typical ranges, worst cases, and head-to-head win rates.

## What you'll learn

- Monte Carlo simulation from scratch — the single most useful modeling technique
- Why simulating ten thousand futures beats agonizing over one point estimate
- Modeling uncertainty with distributions (normal, uniform, triangular, bernoulli)
- Reading a distribution: median vs. tail risk, "usually fine" vs. "how bad is bad"
- Turning a raw array of numbers into a chart that actually informs a decision

## Prerequisites

- Python 3.10+ (standard library only — nothing to install)
- Comfort reading a JSON config and a math expression
- Optional: an Anthropic API key, only if you want plain-English → config

## Local vs API

| Part | Runs where |
|---|---|
| The entire simulation | 100% local, standard library, no network |
| The chart (`results.html`) | 100% local, opens in any browser |
| Plain-English → config (optional) | Claude API — see `prompts.md` |

There is **no API key required** to run any simulation. Claude is only useful for
the convenience of describing a decision in words instead of writing the config.

## How it works

```
decision.json  (variables + one formula per option)
      ↓  identify uncertain variables (the distributions)
      ↓  10,000 times: sample each variable, evaluate every option
outcome arrays per option
      ↓  summarize: median, 10–90% range, worst 5%, win rate
results.json  +  results.html  (overlapping histograms)
```

## The config format

```json
{
  "title": "...",
  "runs": 10000,
  "goal": "max",                          // "max" = higher outcome is better
  "variables": {
    "home_price":   { "dist": "normal", "mean": 500000, "sd": 15000 },
    "rent_growth":  { "dist": "uniform", "low": 0.01, "high": 0.05 },
    "upkeep":       { "dist": "triangular", "low": 4000, "high": 12000, "mode": 7000 },
    "b_succeeds":   { "dist": "bernoulli", "p": 0.35 },
    "years":        { "fixed": 5 }         // fixed = certain, not simulated
  },
  "options": {
    "Buy":  "home_price*(1+appreciation)**years - ...",
    "Rent": "home_price*0.2*(1+invest_return)**years - ..."
  }
}
```

Any variable with a `dist` is treated as **uncertain** and gets sampled. Anything
with `fixed` is certain. Each option is a formula over the variable names.

## Build it

### Step 1: Run the samples

```
python simulate.py rent-vs-buy.json
python simulate.py job-a-vs-b.json
open results.html
```

You'll get a printed summary and a chart: two outcome distributions overlaid,
with median lines, and cards showing each option's win rate and worst 5%.

### Step 2: Read the engine

`simulate.py` is small. Follow it top to bottom: `sample()` draws one value from a
variable spec, the main loop in `run()` does 10,000 draws, `summarize()` turns each
outcome array into percentiles. The whole idea fits on one screen.

### Step 3: Change an assumption and watch the tails move

Bump `rent-vs-buy.json`'s `appreciation` sd from `0.025` to `0.05`. Rerun. Notice
the median barely moves but the worst-5% gets much worse — that's the entire value
of simulating: it shows you the risk, not just the expected case.

### Step 4: Model your own decision

Copy a sample, rename the options, and write formulas in your real numbers. Start
with a couple of uncertain variables; add more as you trust the model.

### Step 5: (Optional) describe it in words

Use the prompt in `prompts.md` to have Claude draft the config from a paragraph.
Always read the generated config — you own the assumptions, not the model.

## Verify it works

- [ ] `python simulate.py rent-vs-buy.json` prints medians and win rates
- [ ] `results.html` opens and shows two overlapping distributions with a legend
- [ ] Hovering the chart shows per-bin counts for each option
- [ ] `job-a-vs-b.json` shows the startup option's long right tail (rare big wins)

## Extend it

- Add correlated variables (interest rates and home prices don't move independently)
- Add a third and fourth option — the engine already supports N options
- Show the probability each option clears a threshold you care about ("beats $0")
- Sensitivity analysis: which single variable moves the outcome most?
- Export a one-paragraph plain-English readout of what the simulation implies

## Common pitfalls

- **Garbage in**: a simulation is only as good as your distributions. Wide, honest
  ranges beat confident wrong point estimates.
- **Reading only the median**: the whole point is the tails. A higher median with a
  brutal worst-5% can be the worse choice.
- **Expression errors**: option formulas are evaluated in a sandbox with only your
  variables and a few math functions (`min`, `max`, `sqrt`, `exp`, `log`). Typos in
  a variable name surface as a clear error.
- **Treating output as truth**: these are illustrative models. They sharpen thinking;
  they don't predict the future.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
