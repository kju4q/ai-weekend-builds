# Vol 6: 5 Builds That Show You How the Machine Works (November 2026)

5 projects about what is underneath: a model you train yourself, the audience
data you already own, the bill for every model call, a second reader for
everything your agent calls done, and a map of everything you know. One is built
and measured. Four are plans, with a spec, prompts and sample data, so you can
build them with an assistant using the [build guide](BUILD-GUIDE.md).

| # | Project | Status | Difficulty | Time | What you get |
|---|---------|---|---|---|---|
| 01 | [The Twenty-Minute Model](01-twenty-minute-model) | Built | Medium | 2-3h | A tiny GPT trained from scratch on your laptop, going from noise to words while you watch |
| 02 | [The Audience Lab](02-audience-lab) | Plan and prompts | Medium-Advanced | 5-8h | Every post, comment and DM in your own database, and the questions people keep asking |
| 03 | [The Router](03-the-router) | Plan and prompts | Medium | 4-6h | One door for every model request, local or cloud per task, with the bill logged |
| 04 | [The Auditor](04-the-auditor) | Plan and prompts | Medium | 4-6h | A second model checks every "done" from your agent, with a score over time |
| 05 | [The Graph of Everything You Know](05-the-graph) | Plan and prompts | Advanced | Full day | Your notes, reading and projects as one connected graph you can ask questions |

**Built** means the code is in the folder and I ran it: the README has the
numbers from that run. **Plan and prompts** means a paste-ready spec, the prompts
I would use, and invented sample data, with no application code yet. The times
for the plans are estimates.

## Start here: the build guide

[BUILD-GUIDE.md](BUILD-GUIDE.md) is how to turn any of these plans into a
working project with an AI assistant: write the spec first, ask for a plan and
not code, build one milestone at a time, run the acceptance check after each
one, commit what passes, and always run on the sample data before your own.

## Each project teaches a different concept

- **Training, tokens and loss (#1)**: what actually happens when a model
  learns, on a model small enough to train in twenty minutes and read in one
  sitting.
- **Platform APIs and clustering (#2)**: tokens, pagination, rate limits and
  webhooks, then turning hundreds of comments into a short list of questions.
- **Inference and spending less on the model (#3)**: tokens in, tokens out, what
  each call costs, and measuring which requests a small local model can handle.
- **Evals and verification (#4)**: deciding what correct means before you look,
  and why the reviewer should not read the author's argument.
- **Knowledge graphs (#5)**: extraction, entity resolution, and answering by
  walking connections instead of searching text.

## Local vs API, at a glance

**#1 The Twenty-Minute Model** is local only: no key, no network calls, not even
optional. The training text ships in the folder. The four plans each have a
table in their README saying which part touches which service: #2 talks to your
social platform's API, #3 and #4 call a cloud model by design, and #5 can run
fully local if you choose a local extraction model.

## Pick one

If you have never seen a model learn: start with **#1 The Twenty-Minute Model**.
Watch step 0 print noise and the last step print sentences.

If your comments are full of the same five questions: **#2 The Audience Lab**.

If your model bill surprised you this month: **#3 The Router**.

If your agent says "done" and you have stopped believing it: **#4 The Auditor**.

If you read a lot and remember little of it: **#5 The Graph of Everything You
Know**.

## Want an earlier volume?

[Go back to the root](../README.md), where vol 5 through vol 1 are linked.
