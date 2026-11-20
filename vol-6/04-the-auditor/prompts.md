# Prompts: The Auditor

Two kinds of prompt live here: the ones for your coding assistant while you
build this from [SPEC.md](SPEC.md), and the auditor prompt itself, which is
part of the product. The build prompts end by holding back the next step, for
the reason in the [build guide](../BUILD-GUIDE.md).

## Prompt 1: Decide what the auditor sees before any code

```
I am building an auditor: when my coding agent says it is done, a different
model with no memory of the conversation reviews the work. Here is the spec:

{paste SPEC.md}

Here is one sample task folder:

{paste task.md, diff.patch, tests.txt from sample-data/tasks/01-*}

List every source of text that could end up in the packet in a real repo
(commit messages, PR descriptions, code comments, changelog entries, test
names). For each one, tell me whether it carries the agent's own argument that
the work is correct, and whether to include it, strip it, or include it marked
as written by the agent. Do not write packet.py yet.
```

## Prompt 2: The auditor prompt (this one runs in the product)

```
You are reviewing a code change. You did not write it and you have not seen
any conversation about it. You are given the task as the person wrote it, the
diff, and the test output. Nothing else.

TASK:
{task.md}

DIFF:
{diff.patch}

TEST OUTPUT:
{tests.txt}

Check the change against every acceptance check in the task, one by one. Then
look for anything the task requires that the diff does not do, and anything the
diff does that the task did not ask for.

Return only JSON:
{"findings": [{"file": "...", "line": 0, "problem": "...", "confidence": "high|medium|low"}],
 "score": 0-10,
 "verdict": "done" | "not done" | "unclear"}

If the work is correct, return an empty findings list. Do not invent problems
to have something to say.
```

The last line matters. A reviewer asked to find problems will find some. The
clean sample task is there to catch that.

## Prompt 3: Read the auditor's misses with me

```
Here is my auditor's score on the sample tasks, compared with the answer key:

{paste the output of score_auditor.py}
{paste the verdict for each task it got wrong}

For each miss and each false alarm, tell me whether the cause is the packet
(it did not have the information), the prompt (it was not asked to look), or
the model (it had both and still missed it). Propose the single change most
likely to fix the largest group. Do not change the prompt yet.
```

## Tuning

- **It returns prose around the JSON**: add "the first character of your reply
  is { and the last is }".
- **Every verdict is a 7**: ask for findings first and compute the score from
  them in code, instead of asking the model for a number.
- **It flags style instead of correctness**: add "only report something that
  breaks an acceptance check or the task's intent. Ignore style."

## A note on privacy

The packet holds your task, your diff and your test output, and it goes to the
auditor model's provider. Nothing else in this project leaves the machine.
