# Prompts: Freedom Calculator

> These are AI-assisted build prompts: a recommended path a reader can follow with
> ChatGPT Chat, ChatGPT Work, and Codex. They are not presented as the exact
> prompts used to produce this repository implementation, and they must not claim
> those tools performed this build.

The project can be built by hand from the README alone. These are optional.

## AI-assisted build prompts

### 1. ChatGPT Chat: clarify the implementation

```
I am building a project called Freedom Calculator. Treat the concept and this
description as locked:

  Takes your income with its real variability, plus what you actually spend, and
  simulates the next year ten thousand times. You change an input and watch how
  the outcome moves. This is exploration from your own assumptions, not financial
  advice.

Do not redesign or reposition it. No web app, no server, no database, no account
system, no network calls, no external data source, no model and no model key. The
Python standard library is enough. It is a weekend project: one script, one JSON
config, one generated report.

Framing matters more than usual here, so hold this line throughout: this is an
educational simulation of user-supplied assumptions. It is not financial advice,
not affordability advice, not a prediction, and not a decision tool. Refuse
phrasing like "can you afford it", "a percentage you can trust", "the best
option", "the right answer", or anything with "guaranteed" in it. If I drift
toward advice framing, say so.

Help me define the smallest complete runnable implementation. Work through:

- The config fields, which are required, and what each one means.
- Which distributions to support, and what parameters each needs.
- What validation must reject outright rather than guess. I would rather the tool
  refuse a config than invent a missing standard deviation.
- The metrics worth reporting, and which of them are objective outputs of the
  code rather than interpretations.
- The difference between a run ending above zero and a run never falling below
  zero, and why reporting only the first one would be misleading.
- How to describe both numbers honestly, given they are shares of simulated runs
  under made-up assumptions and not probabilities about a real year.
- What the model deliberately does not include: taxes, inflation, investment
  returns, debt interest, correlation between income and expenses, currency
  changes, unexpected events, behavioral changes, real market data.
- The exact disclaimer wording for the terminal, the report, and the README.
- How to verify the thing works, including a change that should produce an
  arithmetically predictable shift in the output.

Ask only the implementation questions you actually need answered. Do not write
code and do not produce a plan until I have approved the decisions.
```

### 2. ChatGPT Work: turn decisions into a checklist

```
Here are the decisions I approved:

[paste the decision list from step 1]

Convert them into a build checklist for a single weekend project. Produce:

1. Five README build steps in this order: run it as-is on the sample, read the
   simulation engine, change one assumption and rerun, use your own assumptions,
   make it yours. Exact python3 commands for each.
2. The minimal file list. Nothing beyond what those steps need.
3. The config schema: every field, whether it is required, its type, and its
   validation rule.
4. The outputs: the terminal summary, results.json, and a self-contained
   report.html with no server and no external script.
5. The validation cases that must fail with a clear message and a non-zero exit,
   including malformed JSON, zero and negative runs, zero months, unknown
   distributions, invalid standard deviations, reversed ranges, and one-time
   expenses outside the simulated period.
6. The verification checks, including reproducibility with a fixed seed and one
   changed assumption whose effect on the median can be predicted by hand.
7. Where the disclaimer appears and what it says.

Rules for your output:
- Do not create extra repository planning files. No build plan, no build log, no
  architecture document. The checklist goes into the README and nowhere else.
- No advice framing, no prediction framing, no guarantee language.
- Standard library only unless something genuinely cannot be done without a
  dependency.
- Use python3 in every command.
- Do not use em dashes.

Return a concise checklist I can copy into the README and hand to Codex.
```

### 3. Codex: implement the project

```
Read the README and everything in this folder before writing anything. Preserve
the existing title and opening description exactly.

Standard library first. Do not add a plotting library: the report chart can be
inline SVG generated as strings.

Implement in checkpoints, and after each one run it and show me the real output.

1. Config loading and validation. Every rejection names the field and what was
   wrong, and exits non-zero. Nothing is guessed or defaulted silently.
2. Sampling for fixed, normal, uniform, and triangular, with optional minimum and
   maximum clamps. Seed everything from one random.Random so a run is reproducible
   from the config alone.
3. The simulation loop: month by month per run, tracking the ending balance and
   whether the balance was ever negative along the way.
4. Statistics: percentiles by interpolation, monthly bands, both above-zero
   counters, and a histogram of ending balances.
5. The terminal summary and results.json.
6. A self-contained report.html with inline CSS and inline SVG. No server, no
   external script, no external stylesheet, no absolute local paths.
7. README and prompts completed from behavior you actually ran.

Constraints:
- No network code, no model, no API key, no environment variables.
- Synthetic config numbers only. Nothing real.
- Report only metrics the code computes. Do not add an interpretation layer.
- Keep the advice framing out: shares of simulated runs, never probabilities
  about a real year.
- Every documented command uses python3.
- Make no unrelated changes to the repository.
- Do not commit or push.
```

### 4. Codex: verify and review

```
Review this project as if you had just cloned it.

1. Create a fresh virtual environment and install from requirements.txt. Record
   whether pip downloaded anything and how long it took.
2. Run python3 -m py_compile simulate.py and python3 simulate.py --help.
3. Run the exact README commands in order. Record the run time and the output
   file sizes.
4. Run the same config and seed twice and confirm the results are identical.
5. Run with a different seed and confirm the sampled results differ.
6. Do the changed-assumption test: add 1000 to monthly fixed expenses with the
   same seed and run count, and confirm the median ending balance drops by
   exactly 12000 over 12 months. Check the other percentiles too, and explain why
   the shift is exact rather than approximate.
7. Test every invalid config case and confirm each exits non-zero with a message
   naming the problem.
8. Confirm results.json is valid JSON, the percentiles are ordered, the counts
   are within the run count, and the histogram sums to the run count.
9. Open report.html and confirm it renders with no server, contains no script
   tag, no external URL, and no absolute local path.
10. Review the source for any network, model, or key code. If the environment
    allows it, run the sample with network access blocked and report the result.
    If it does not, say so plainly rather than implying you tested it.
11. Compare every claim in the README against actual behavior, especially any
    number quoted in the text.
12. Confirm generated outputs, personal configs, caches, and virtual environments
    are ignored by Git, and that the tracked sample config is not.

Fix only confirmed problems. Do not refactor working code and do not add
features. Report clearly what you could not test and why. Use python3
consistently. Do not use em dashes. Do not commit or push.
```

## No runtime AI prompt

This project has no runtime AI prompt. Config validation, distribution sampling,
the month-by-month simulation, percentiles, the above-zero counters, the
histogram, and the generated HTML report are all deterministic Python behavior.
No model is involved at any point, and the project reads no API key because there
is nothing for one to authenticate against.

## Tuning

- **Runs**: `runs` in the config, or `--runs`. More runs steady the percentiles,
  and the tails settle last, since p10 and p90 each rest on a tenth of the
  sample. 10,000 runs of 12 months completes in about a quarter of a second, so
  there is rarely a reason to run fewer.
- **Seed**: `seed` in the config, or `--seed`. Same seed plus same config gives
  identical output. Changing only the seed shows you how much of a small
  difference between two scenarios is just sampling noise.
- **Months**: `months`. Everything scales, and the monthly bands table grows with
  it. One-time expenses must fall inside the period or the config is rejected.
- **Distribution means and spreads**: the `mean` and `sd` of a normal, or the
  `low` and `high` of a uniform or triangular. The mean moves the whole
  distribution; the spread changes its width, which is the more interesting
  experiment of the two. Widening a spread until the result looks acceptable
  teaches you nothing except what the config says.
- **Minimum bounds**: `minimum` on any distribution. `minimum: 0` on income is
  usually right, because a wide normal will otherwise sample negative income.
  `maximum` exists too, for a genuine cap such as a contract ceiling.
- **One-time expenses**: the `one_time_expenses` list. Each needs a `month` inside
  the period and an `amount`. A negative amount works as a one-time inflow if you
  want to model a rebate, though the label says expense.
- **Histogram bins**: `HISTOGRAM_BINS` near the top of `simulate.py`, 40 by
  default. Fewer bins smooth the shape, more bins expose the noise in the tails.
- **Report percentiles**: `PERCENTILES` near the top of `simulate.py`. Adding a
  value there puts it in `results.json`, and adding a matching row in
  `render_report()` puts it in the HTML table.
