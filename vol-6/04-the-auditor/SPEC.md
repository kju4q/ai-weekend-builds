# SPEC: The Auditor

Paste this into your assistant with the first prompt in [prompts.md](prompts.md).
Edit it first: name your auditor model and your test command.

## One sentence

When my coding agent says it is done, a different model with no memory of the
conversation reads my task, the diff and the test output, says where the work is
wrong, and every verdict is logged so I can see a score over time.

## Inputs

- `task.md`: the task as I wrote it, with its acceptance checks
- The git diff of the agent's work against the commit before it started
- The output of my test command
- Sample data: `sample-data/tasks/*/`, six invented tasks, each with `task.md`,
  `diff.patch`, `tests.txt`, and `agent-summary.txt` (which the auditor must
  never see), plus `sample-data/answer-key.json` listing the planted defect per
  task, or none for the clean one

## Outputs

- One JSON verdict per audit: `{findings: [{file, line, problem, confidence}],
  score: 0-10, verdict: "done" | "not done" | "unclear"}`
- `audits.db`: one row per audit with timestamp, task id, auditor model, score,
  verdict, and the findings JSON
- `chart.html`: score over time, self-contained, no network

## Out of scope

- Fixing the problems it finds
- Reading the agent's conversation, summary, or reasoning. Never, by design.

## Constraints

- Python 3.10+. The auditor is a different model from the one that did the work.
- The packet builder is the only code that decides what the auditor sees, and it
  has a test that fails if the agent's summary gets in
- The auditor key lives in `.env`, which is in `.gitignore`
- The auditor returns JSON that is validated against a schema. Invalid JSON is
  logged as an error, not as a score.

## Milestones

### M1: Packet builder
- Build: `packet.py <task-dir>` prints the packet
- Acceptance check: `python packet.py sample-data/tasks/01-slugify` prints the
  task, the diff and the test output, and `python packet.py --check` builds all
  six packets and fails if any of them contains text from that task's
  `agent-summary.txt` (what the agent said when it finished)

### M2: Auditor call
- Build: `audit.py <task-dir>` sends the packet and prints the validated verdict
- Acceptance check: running it on all six sample tasks prints six verdicts

### M3: Judge the judge
- Build: `score_auditor.py` compares verdicts to `sample-data/answer-key.json`
- Acceptance check: it prints planted defects found (target: at least 4 of 5)
  and false alarms on the clean task (target: no finding with confidence high)

### M4: Log and chart
- Build: audits written to `audits.db`, `chart.py` writes `chart.html`
- Acceptance check: after M3, `audits.db` has 6 rows and `chart.html` opens with
  the network off

### M5: Hook
- Build: wire `audit.py` to the agent's stop event, or a `done` command
- Acceptance check: one real task ends, and one new row appears in `audits.db`
  without me running anything

## Done means

- [ ] Every acceptance check passes on sample-data/
- [ ] I know my auditor's hit rate on planted defects before trusting its score
- [ ] Two weeks of real audits in the chart
