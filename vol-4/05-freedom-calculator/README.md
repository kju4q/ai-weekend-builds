# 05: Freedom Calculator

Takes your income with its real variability, plus what you actually spend, and
simulates the next year ten thousand times. You change an input and watch how the
outcome moves. This is exploration from your own assumptions, not financial advice.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Advanced | Full day | Python 3.10+ standard library, local JSON config, local HTML report |

Everything runs on your machine. No network request is made, no external data
source is read, and no model or model key is involved anywhere.

> This is an educational simulation of user-supplied assumptions, not financial
> advice. It explores how outputs change when inputs change. It does not predict
> what will happen.

## What you'll build

A simulation of your next year, run ten thousand times from numbers you supply.
Income with its real month-to-month variance, spending as it actually is, and a
chart showing where the futures cluster and how bad the bad ones get. Change one
assumption and watch the whole distribution move.

## What you'll learn

Probabilistic thinking, volatility, percentiles, distributions.

- Modeling a number as a distribution instead of a single guess
- Volatility as an input you can state honestly
- Reading percentiles, and why the median is not the story
- Watching how one changed assumption moves the tails

## Prerequisites

- **Python 3.10 or later.** Verified on **3.14.3** and **3.12.13**, on macOS
  26.5.1, Apple M2 Pro, arm64. Standard library only, so there is no pinned wheel
  to go stale.
- **Setup:**

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  python3 -m pip install -r requirements.txt
  ```

  On Windows the activation line is `venv\Scripts\activate`. Every Python command
  here stays `python3`.

- **That install does nothing, by design.** `requirements.txt` lists no packages.
  The observed run took **6.44 seconds**, downloaded **zero packages**, and left
  the virtualenv holding only pip itself. The first simulation run downloads
  nothing: no package, no model, no data file. Nothing in this project has ever
  needed a network connection.
- **A config file** describing your assumptions. `sample-config.json` ships with
  fictional numbers and is documented field by field in Step 4.
- **A browser** to open the generated report. It is a plain file with no server
  and no external script.

## Local vs API

| Part | Runs where |
|---|---|
| Reading and validating the config | 100% local |
| Random sampling | 100% local, seeded from your config |
| Every calculation and percentile | 100% local |
| `results.json` | 100% local |
| `report.html`, including both charts | 100% local, generated HTML, CSS, and inline SVG |

There is no network call, no API key, no model, and no external data source. This
was checked two ways: `simulate.py` imports only `argparse`, `datetime`, `html`,
`json`, `math`, `pathlib`, `random`, `statistics`, and `sys`, none of which can
open a socket; and the sample run was executed again with `socket.socket`,
`socket.create_connection`, `socket.getaddrinfo`, and `socket.gethostbyname` all
replaced by functions that raise. It completed normally and produced byte-for-byte
the same median, which it could not have done if anything had reached for the
network.

## How it works

```
sample-config.json
        |
validate assumptions
        |
run N simulated years
        |
monthly balances per run
        |
percentiles + above-zero counts + histogram
        |
terminal summary + results.json + report.html
```

## Build it

### Step 1: Run it as-is on the sample

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 simulate.py sample-config.json --output sample-output
```

The sample describes a fictional independent consultant: 5,000 starting balance,
income averaging 4,100 a month with a standard deviation of 1,900, fixed expenses
of 2,900, variable expenses averaging 900, and two one-time expenses. All of it
is invented. The run took **0.24 seconds** and printed:

```
Fictional independent consultant
  10,000 runs of 12 months, seed 42
  Starting balance: USD 5,000

  Ending balance
    p10             USD -3,288
    p25                USD 622
    median           USD 5,058
    p75              USD 9,518
    p90             USD 13,454
    mean             USD 5,067
    range   USD -20,839 to USD 30,555

  Ended above zero:      7,808 of 10,000 (78.1% of simulated runs)
  Never below zero:      6,531 of 10,000 (65.3% of simulated runs)

  These are shares of simulated runs under the assumptions in the config,
  not probabilities about your actual year.

  Wrote sample-output/results.json
  Wrote sample-output/report.html
```

Two files land in `sample-output/`: `results.json` (4.6 KB, every number the run
computed, including the full monthly bands and histogram) and `report.html`
(17 KB, the same thing with charts). Open the report directly:

```bash
open sample-output/report.html
```

On Linux use `xdg-open`, on Windows `start`. There is no server involved.

**The two headline percentages are different questions.** 78.1% of runs finished
above zero on month 12. Only 65.3% got there without dipping below zero at some
point along the way. The 12.8 point gap is the share of runs that went negative
and recovered. A single "ended above zero" number hides that entirely, which is
why both are reported.

Neither is a probability you can apply to your actual year. They are the share of
simulated runs under these assumptions, and the assumptions are made up.

### Step 2: Read the simulation engine

One file, `simulate.py`, standard library only.

**Validation runs before anything else.** `load_config()` reads and parses the
JSON, then `validate_config()` checks it. `validate_amount()` handles the three
money fields, accepting either a plain number as shorthand for a fixed amount or
an object naming a distribution. Every failure raises `ConfigError` with the
field name and what was wrong, and `main()` turns that into exit code 2. Nothing
is guessed: a missing standard deviation is an error, not a default, because a
silently invented assumption would change every number downstream while looking
authoritative.

**Sampling.** `sample()` draws one value from a spec, supporting `fixed`,
`normal`, `uniform`, and `triangular`, then applies the optional `minimum` and
`maximum` clamps. It always consumes the same number of draws from the generator
for a given distribution, which is what makes Step 3 work.

**The simulation loop.** `simulate()` seeds a `random.Random` from the config, and
for each run walks month by month: sample income, sample fixed, sample variable,
subtract any one-time expense for that month, update the balance, and record it.
Two things are tracked per run: the ending balance, and whether the balance was
ever negative at any month end.

**Percentiles.** `percentile()` interpolates linearly between the two closest
ranks of the sorted values. Monthly bands are computed the same way per month,
across runs. Worth knowing: those bands are percentiles computed independently at
each month, not a single run's path. No individual run traces the median line.

**Never below zero** is the stricter of the two counters, and it is computed
inside the loop rather than from the ending balances, because by definition it
depends on the months in between.

**The report.** `histogram()` buckets the ending balances into 40 bins.
`svg_histogram()` and `svg_bands()` generate inline SVG as strings, and
`render_report()` assembles the page with inline CSS. There is no plotting
library and no JavaScript, which is why the report opens from the filesystem with
nothing else installed.

### Step 3: Change one assumption and rerun

Same seed, same run count, one input moved:

```bash
cp sample-config.json changed-config.json

python3 - <<'PY'
import json

path = "changed-config.json"
with open(path, encoding="utf-8") as file:
    config = json.load(file)

config["name"] = "Fictional consultant with higher fixed expenses"
config["monthly_fixed_expenses"] += 1000

with open(path, "w", encoding="utf-8") as file:
    json.dump(config, file, indent=2)
    file.write("\n")
PY

python3 simulate.py changed-config.json --output changed-output
```

Observed result:

```
    p10            USD -15,288
    p25            USD -11,378
    median          USD -6,942
    p75             USD -2,482
    p90              USD 1,454

  Ended above zero:      1,447 of 10,000 (14.5% of simulated runs)
  Never below zero:      930 of 10,000 (9.3% of simulated runs)
```

Every order statistic moved by exactly **-12,000**, verified across all of them:

| Statistic | Baseline | Higher expenses | Shift |
|---|---:|---:|---:|
| p10 | -3,287.52 | -15,287.52 | -12,000.00 |
| p25 | 622.42 | -11,377.58 | -12,000.00 |
| median | 5,058.12 | -6,941.88 | -12,000.00 |
| p75 | 9,518.30 | -2,481.70 | -12,000.00 |
| p90 | 13,453.71 | 1,453.71 | -12,000.00 |
| mean | 5,067.10 | -6,932.90 | -12,000.00 |
| lowest run | -20,839.12 | -32,839.12 | -12,000.00 |
| highest run | 30,555.37 | 18,555.37 | -12,000.00 |

That is not a coincidence and it is a useful thing to understand. 1,000 a month
across 12 months is 12,000, and because the seed is unchanged and fixed expenses
consume no random draws, every single simulated run saw identical income and
variable-expense samples. The whole distribution slid sideways by exactly that
amount without changing shape at all.

The counts are the part that did change shape: runs ending above zero fell from
78.1% to 14.5%, and runs that never dipped fell from 65.3% to 9.3%. The
distribution moved rigidly; how much of it sits above the zero line did not.

Clean up when you are done, since neither file belongs in the repository:

```bash
rm -rf changed-config.json changed-output
```

### Step 4: Use your own assumptions

```bash
cp sample-config.json my-config.json
python3 simulate.py my-config.json --output my-output
```

`my-config.json` and `my-output/` are already gitignored.

Every field:

| Field | Required | Meaning |
|---|---|---|
| `name` | no | Label shown in the summary and report. Defaults to `unnamed scenario`. |
| `currency` | no | A label only. No conversion happens. Defaults to `USD`. |
| `months` | yes | How many months one run covers. At least 1. |
| `runs` | yes | How many independent runs to simulate. At least 1. |
| `seed` | no | Same seed plus same config gives identical output. Defaults to 0. |
| `starting_balance` | yes | Balance before month 1. May be negative. |
| `monthly_income` | yes | A number, or a distribution object. |
| `monthly_fixed_expenses` | yes | A number, or a distribution object. |
| `monthly_variable_expenses` | yes | A number, or a distribution object. |
| `one_time_expenses` | no | List of `{month, amount, label}`. Month must be within the period. |

The three money fields accept a plain number as shorthand for a fixed amount, or
an object:

```json
{"distribution": "fixed", "amount": 2900}
{"distribution": "normal", "mean": 4100, "sd": 1900, "minimum": 0}
{"distribution": "uniform", "low": 3000, "high": 6000}
{"distribution": "triangular", "low": 3000, "high": 6000, "mode": 4200}
```

`minimum` and `maximum` are optional clamps on any distribution. `minimum: 0` on
income matters more than it looks: a normal distribution with a wide spread will
otherwise sample negative income, which is not a thing. All four distributions
were verified to run.

**Use consistent monthly units.** Everything is per month except `starting_balance`
and one-time amounts. An annual figure dropped into a monthly field is the easiest
way to get a confidently wrong answer.

**The assumptions are yours.** The model does exactly what your numbers say, so
the output is only as honest as the inputs. If you widen the standard deviation
until the result looks acceptable, you have not learned anything about your year,
only about the config file. The useful move is the opposite: put in ranges you
would defend out loud, then see what falls out.

### Step 5: Make it yours

- **Change the run count:** `--runs 50000`, or edit `runs`. More runs means
  steadier percentiles and a longer wait.
- **Change the seed:** `--seed 7`. Verified: seed 42 gives a median of 5,058.12
  and 78.1% above zero, seed 7 gives 5,052.99 and 77.7%. Same assumptions,
  different draws, which is a good way to see how much of a small difference is
  just noise.
- **Add another one-time expense** to the list, with its month and label.
- **Change a distribution,** for example income from `normal` to `triangular`
  when you have a floor, a ceiling, and a most-likely value in mind.
- **Extend the number of months** past 12 for a longer horizon. Everything scales.
- **Add a reported percentile:** add it to `PERCENTILES` near the top of
  `simulate.py`, and to the table rows in `render_report()`.
- **Compare two saved result files:** both runs write a full `results.json`, so a
  short script that loads two of them and prints the difference per percentile is
  an afternoon's work, and is exactly what Step 3 did by hand.

## How to build this with ChatGPT, Work, and Codex

> Frame this as the workflow a reader follows, not as a record of how this specific
> implementation was produced. Do not claim these tools performed this build.

This project can be built manually from the README alone. The prompts in
[prompts.md](prompts.md) provide an optional AI-assisted path.

- **ChatGPT Chat:** clarifies assumptions, config fields, simplifications, and
  which outputs are objective enough to report.
- **ChatGPT Work:** turns approved decisions into the five-step checklist this
  README reflects.
- **Codex:** implements, runs, and verifies the simulator against that checklist.

## Verify it works

- [ ] `python3 -m py_compile simulate.py` is clean
- [ ] `python3 simulate.py --help` lists `config`, `--output`, `--runs`, `--seed`
- [ ] `python3 simulate.py sample-config.json --output sample-output` completes
      and reports 10,000 runs of 12 months
- [ ] `sample-output/results.json` is valid JSON
- [ ] `sample-output/report.html` opens directly in a browser with no server, and
      contains no `<script>` tag, no `src=`, and no external URL
- [ ] The reported run count equals `runs` in the config
- [ ] Percentiles are ordered: p10 <= p25 <= p50 <= p75 <= p90
- [ ] The lowest observed run is at or below p10, and p90 at or below the highest
- [ ] Both above-zero counts are between 0 and the run count
- [ ] The never-below-zero count is at or below the ended-above-zero count
- [ ] The histogram bin counts sum to the run count
- [ ] Running the same config and seed twice gives identical results
- [ ] `--seed 7` produces a different median than seed 42
- [ ] Adding 1,000 to `monthly_fixed_expenses` over 12 months lowers the median
      ending balance by exactly 12,000, and shifts every other percentile by the
      same amount
- [ ] All four distributions run: `fixed`, `normal`, `uniform`, `triangular`
- [ ] Malformed JSON, zero runs, negative runs, zero months, an unknown
      distribution, a negative standard deviation, a zero standard deviation, a
      reversed uniform range, an out-of-range triangular mode, a one-time expense
      outside the period, a missing required field, a non-numeric amount, and a
      missing distribution parameter each exit 2 with a specific message
- [ ] A missing config file exits 2
- [ ] `simulate.py` imports no module capable of opening a socket
- [ ] The sample run completes with all socket functions replaced by ones that
      raise, producing the same median
- [ ] `python3 -m pip install -r requirements.txt` downloads zero packages
- [ ] `git status` shows no generated output directories, no `my-config.json`,
      and no `changed-config.json`

## Extend it

- **Add a second scenario and run both against the same ten thousand draws,** so
  the comparison is fair rather than two separate rolls of the dice. Step 3 is the
  manual version of this: same seed, one input changed.

Further small extensions:

- A `--compare` flag that reads two `results.json` files and prints the shift per
  percentile
- Quarterly or annual aggregation of the monthly bands
- A per-month breakdown of how often the balance dipped, rather than one count
  for the whole year

## Common pitfalls

Everything here was observed during verification on macOS 26.5.1 with Python
3.14.3.

- **Changing the seed changes the sampled outcomes.** Seed 42 gave a median of
  5,058.12 and seed 7 gave 5,052.99 from identical assumptions. If a difference
  between two runs is smaller than the difference a seed change produces, it is
  noise, not signal.
- **Too few runs give unstable percentiles.** The tails move most: p10 and p90 are
  each estimated from a tenth of the sample, so at 100 runs they wobble
  substantially between seeds. 10,000 runs of 12 months takes 0.24 seconds, so
  there is little reason to run fewer.
- **A normal distribution needs a `minimum` to stay physical.** Income with a
  mean of 4,100 and a standard deviation of 1,900 samples negative values a bit
  under 2% of the time. `minimum: 0` clamps those. Without it the model quietly
  includes months where you were paid a negative amount.
- **Units have to be consistent.** Every money field except `starting_balance`
  and one-time amounts is per month.
- **The output reflects only what you configured.** A quiet result is a statement
  about the config, not about your year.
- **Reusing one output directory overwrites the previous report.** `results.json`
  and `report.html` are replaced without warning. Use a different `--output` for
  each scenario you want to keep.
- **A rigid shift is not a change in risk shape.** In Step 3 the entire
  distribution moved by exactly 12,000 without changing width, because the seed
  and the random draws were identical. Changing a standard deviation instead
  changes the shape, and that is a different kind of experiment.
- **Taxes, inflation, investment returns, debt interest, correlation between
  income and expenses, currency changes, unexpected events beyond the one-time
  items you configured, behavioral changes, and real market data are not
  modeled.** Version 1 does none of these. Leaving them out does not make them
  unimportant; it makes this a small model with a boundary you can see. The
  report repeats this list.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
