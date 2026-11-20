# 04: The Auditor

**Status: plan and prompts.** There is no application code in this folder yet.
What is here is the spec, the prompts, and invented sample data, so you can
build it yourself with an assistant using the [build guide](../BUILD-GUIDE.md).
Nothing on this page is a result I measured, because I have not built it.

Every time your coding agent says "done", a different model that has never seen
the conversation reads the task and the result, and says where it is wrong.
Every verdict is stored, so over weeks you get a score: how often "done" was
actually done.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 4-6h | Python, git, a model API for the auditor, SQLite |

## Why a second reader with no memory

Anthropic published a study, [How AI agents shape experts' judgment
calls](https://www.anthropic.com/research/agents-judgment-calls) (October 27,
2026). Analysts did a data analysis with an agent, and each agent was given a
lean on four analytical choices at random. The page reports:

> Across the four analytical choices, analysts went with their agent's lean 86%
> of the time. If the agent's input made no difference, we'd expect about 50%.

And, on review:

> a human reviewer is only an independent check if their judgment is their own.

That study is about people working with agents, not about one model checking
another. The step from there to this project is mine: if a reviewer who reads
the agent's reasoning tends to end up agreeing with it, then the auditor should
not read the agent's reasoning at all. It gets the task as you wrote it, the
diff, and the test output. It never gets the agent's summary of what it did,
because that summary is an argument for its own lean.

## What you will build

- A hook that fires when your agent finishes, or a command you run by hand
- A packet builder that collects three things only: your original task, the
  git diff, and the output of your tests
- An auditor call to a different model, with no conversation history, that
  returns findings (file, line, what is wrong, how sure) and a score
- A SQLite log of every audit, and a chart of the score over time

## What you will learn

- **Evals**: deciding what "correct" means before you look, and scoring against
  it the same way every time
- **Verification**: why the one who did the work is the wrong one to check it,
  for agents as well as people
- **Context control**: what you leave out of a prompt matters as much as what
  you put in
- **Measuring a judge**: the auditor is a model too, so you plant known bugs and
  check whether it finds them

## Prerequisites

- Python 3.10+ and a git repo where an agent does work
- An API key for the auditor model. Use a different model from the one that did
  the work, ideally from a different provider.
- Optional: your coding agent's hook system, so the audit runs on its own when
  the agent stops

## Local vs API

| Part | Runs where |
|---|---|
| Building the packet (task, diff, tests) | 100% local |
| The audit | The auditor model's API. The packet goes there: your task text, your diff, your test output |
| The log and the chart | 100% local |

If the repo is private, the diff leaving your machine is the real cost of this
project. Decide that before you wire the hook.

## How it will work

```
agent says "done"
   │
   v
packet.py ── task.md (yours) + git diff + test output
   │          NOT the agent's summary, NOT the conversation
   v
auditor model (fresh context, different model)
   │
   v
{findings: [{file, line, problem, confidence}], score: 0-10, verdict}
   │
   v
audits.db ──> chart.html: score per task over time
```

## Build it in steps

The full spec with acceptance checks is in [SPEC.md](SPEC.md). In order:

1. **The packet.** Build it from `sample-data/tasks/` first. Read one packet
   yourself and check that nothing in it argues for the agent's work.
2. **The auditor call**, run by hand on the sample tasks. Five of the six sample
   tasks have a planted defect. One is clean.
3. **Measure the auditor.** How many planted defects did it find, and did it
   invent one in the clean task? This is the score of your judge, before you
   use it to score anything else.
4. **The log and the chart.**
5. **The hook.** Only after the auditor has passed step 3.
6. **Run it for two weeks** on real work before believing the trend.

## Verify checklist

- [ ] No packet contains the agent's own summary or chat history (grep for it)
- [ ] The auditor finds the planted defect in at least 4 of the 5 sample tasks
- [ ] The auditor does not report a serious finding on the clean sample task
- [ ] Running the same packet twice gives the same verdict, or you know how
      often it does not
- [ ] Every audit row stores the auditor model name, so a model change shows up
      in the chart

## Extend it

- Two auditors from different providers, and flag only what both find
- Feed confirmed findings back to the agent as a fix-up task
- Track which kinds of task fail the audit most, and write those specs more
  carefully
- Audit your own work with it, without telling it who wrote the diff

## Common pitfalls

- **Leaking the agent's summary into the packet.** Commit messages, PR
  descriptions and code comments the agent wrote can all carry its argument.
  Decide what counts and strip it consistently.
- **Trusting the auditor because it sounds sure.** It is a model. Step 3 exists
  so you know its hit rate on bugs you planted.
- **Scoring against a vague task.** If your task said "make it better", there is
  nothing to audit against. Write the acceptance checks in the task first (see
  the [build guide](../BUILD-GUIDE.md)).
- **Reading the trend too early.** A handful of audits is anecdote.

## Files

- [SPEC.md](SPEC.md): paste-ready spec with milestones and acceptance checks
- [prompts.md](prompts.md): the prompts for your coding assistant, and the
  auditor prompt itself
- [sample-data/](sample-data): six invented tasks with diffs, five of them with
  a planted defect, and the answer key

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
