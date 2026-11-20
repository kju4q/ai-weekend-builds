# SPEC: The Router

Paste this into your assistant with the first prompt in [prompts.md](prompts.md).
Edit it first: name your local model, your cloud model, and your prices.

## One sentence

One function that every model request goes through, which picks a small local
model or a big cloud model per task and logs tokens and cost for every call.

## Inputs

- A prompt, an optional task type, and an optional `private` flag
- `prices.json`: price per million input tokens and per million output tokens
  for each model, with the date I copied them
- `rules.json`: the routing rules
- Sample data: `sample-data/requests.jsonl`, 30 invented requests, each with
  `task`, `prompt`, `private`, and `expected_route`

## Outputs

- The answer text
- `log.db`: one row per backend call with `ts`, `request_id`, `route`, `model`,
  `tokens_in`, `tokens_out`, `ms`, `cost`, `reason`, `escalated_from`
- `report.md`: spend this week, spend by task type, local share, and the cost if
  every request had gone to the cloud model

## Out of scope

- Streaming
- Tool use and agents
- A web UI

## Constraints

- Python 3.10+. One small local model through a local runner, one cloud model
  through its official SDK
- The cloud key lives in `.env`, which is in `.gitignore`
- A request with `private: true` never reaches the cloud backend. This is
  enforced in one place, below the router, so a router bug cannot break it.
- Cost uses the token counts the backend returns

## Milestones

### M1: Two backends
- Build: `backends.py` with `local(prompt)` and `cloud(prompt)`, each returning
  `{text, tokens_in, tokens_out, ms, model}`
- Acceptance check: `python backends.py --test` prints one line per backend with
  non-zero token counts

### M2: The log
- Build: `log.py` and cost from `prices.json`
- Acceptance check: after 3 calls, `log.db` has 3 rows, and cost for each row
  equals tokens times price, which I check by hand for one row

### M3: Rules-only router
- Build: `router.py`, `ask(prompt, task=None, private=False)`
- Acceptance check: `python router.py --sample` prints a table of expected
  route vs chosen route for all 30 sample requests, with the agreement count,
  and does not call any backend (`--dry`)

### M4: Quality on the disagreements
- Build: `compare.py` runs both backends on chosen requests and writes the
  answers side by side to `compare.md`
- Acceptance check: `compare.md` exists for every sample request where the
  router chose local, and I have marked each one acceptable or not

### M5: Escalation
- Build: try local first for `route: unsure`, escalate on a failed check
- Acceptance check: a sample request whose local answer is forced empty (a
  `--force-empty-local` flag) produces two log rows, the second with
  `escalated_from` set

### M6: Report
- Build: `report.py`
- Acceptance check: the all-cloud counterfactual in `report.md` equals the sum
  of every request's tokens priced at the cloud model's prices

## Done means

- [ ] Every acceptance check passes on sample-data/
- [ ] The private rule holds in a test that tries to break it
- [ ] One real week of my requests went through `ask`, and I have read the report
