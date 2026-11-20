# 03: The Router

**Status: plan and prompts.** There is no application code in this folder yet.
What is here is the spec, the prompts, and invented sample data, so you can
build it yourself with an assistant using the [build guide](../BUILD-GUIDE.md).
Nothing on this page is a result I measured, because I have not built it.

One door for every model request you make. Behind it, a router decides per task
whether a small model on your laptop can handle it or whether it needs a big
cloud model, and logs every request with its tokens and cost. At the end of a
week you know what you spend, on what, and how much of it a local model could
have done.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 4-6h | Python, a local model runner such as Ollama, one cloud model API, SQLite |

## What you will build

- `ask`: one command (and one Python function) that takes a prompt and returns
  an answer, wherever it came from
- A router that picks local or cloud per request, using rules you can read
  first, and a measured quality check second
- A log of every request: which model, input tokens, output tokens, latency,
  cost, and why the router chose it
- A weekly report: total spend, spend by task type, and what the bill would have
  been if everything had gone to the big model

## What you will learn

- **Inference**: what actually happens when you call a model, tokens in and
  tokens out, and why output tokens usually cost more than input tokens
- **Spending less on the model**: most requests do not need the biggest model,
  and the only way to know which ones is to measure
- **Routing**: rules first, because you can read them, then a check that the
  rules are not quietly making answers worse
- **Running a model locally**: a small model on a laptop, its speed, and where
  it falls over

## Prerequisites

- Python 3.10+
- A local model runner with one small model pulled. Ollama is the easy path on
  a Mac.
- One cloud model API key. Any provider works: the router only needs a function
  that sends a prompt and returns text plus token counts.
- The current prices for the cloud models you use, from the provider's pricing
  page, typed into `prices.json`. The sample `prices.json` has invented round
  numbers marked as examples. Do not trust a price you did not look up.

## Local vs API

| Part | Runs where |
|---|---|
| The router itself | 100% local |
| Requests routed local | 100% local, your laptop does the work |
| Requests routed cloud | The cloud API, the full prompt goes there |
| The log and the report | 100% local, one SQLite file |

A rule worth adding early: anything tagged private never routes to the cloud,
whatever the router thinks.

## How it will work

```
ask("summarize this email")
   │
   v
router.py ── rules: task type, prompt length, private tag, needs tools?
   │              │
   │        unsure? ──> try local, check the answer, escalate if it fails
   v
local model  or  cloud model
   │
   v
log.db: model, tokens in, tokens out, ms, cost, reason
   │
   v
report.py ──> this week: spent, by task, and the all-cloud counterfactual
```

## Build it in steps

The full spec with acceptance checks is in [SPEC.md](SPEC.md). In order:

1. **One function per backend.** `local(prompt)` and `cloud(prompt)`, each
   returning text, input tokens, output tokens and milliseconds. Nothing else.
2. **The log.** Every call writes one row. Cost is computed from `prices.json`.
3. **Rules-only router.** Run it on `sample-data/requests.jsonl`, 30 invented
   requests each labeled with the route I would expect. Compare.
4. **Measure quality on the disagreements.** For the requests where local and
   cloud would differ, run both and compare the answers side by side. This is
   where you find out whether the rules are right.
5. **Escalation.** For the unsure middle, try local first and escalate to cloud
   when a cheap check fails (empty answer, refused, wrong format).
6. **The report**, then point your real tools at `ask` for a week.

## Verify checklist

- [ ] Every request in the sample writes exactly one log row (two if escalated,
      both marked)
- [ ] The rules-only router agrees with the expected route on the sample, and
      you have read every disagreement
- [ ] A request tagged private never reaches the cloud backend, even when the
      rules say it should
- [ ] The report's all-cloud counterfactual is computed from the same token
      counts, not estimated

## Extend it

- Replace the rules with a tiny classifier trained on your own log
- Cache identical requests
- Add a third tier: a mid-sized cloud model
- Count the time saved as well as the money

## Common pitfalls

- **Trusting a router you have not checked.** The cheap route always looks good
  on a bill. Step 4 is the only thing that tells you if answers got worse.
- **Estimating tokens.** Use the token counts the backend returns, not a
  characters divided by four guess, or your cost log is fiction.
- **Prices drift.** Put the date you copied them next to them in `prices.json`.
- **Comparing a cold local model to a warm cloud one.** The first local call
  loads the model. Do not judge local speed on it.

## Files

- [SPEC.md](SPEC.md): paste-ready spec with milestones and acceptance checks
- [prompts.md](prompts.md): the prompts for your coding assistant
- [sample-data/](sample-data): 30 invented requests with expected routes, and an
  example prices file

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
