# Prompts: The Router

The prompts I would use with a coding assistant to build this from
[SPEC.md](SPEC.md). Each one ends by holding back the next step, for the reason
in the [build guide](../BUILD-GUIDE.md).

## Prompt 1: Write the rules before the router

```
I am building a router that sends each model request to a small local model or
a big cloud model. Here is the spec:

{paste SPEC.md}

Here are my 30 sample requests with the route I expect for each:

{paste sample-data/requests.jsonl}

Propose routing rules as data (rules.json), not code. For every rule, tell me
which sample requests it decides and why. List the requests no rule decides
confidently: those become "unsure". Tell me which rule you trust least. Do not
write the router yet.
```

## Prompt 2: Review the cost math for silent errors

```
Here is my logging and cost code, and five rows from my log:

{paste log.py}
{paste 5 rows}
{paste prices.json}

Check the cost math by hand for each row. Look for: per-token vs per-million
mixups, input and output prices swapped, local calls being charged, escalated
requests counted once instead of twice, and token counts that are estimated
instead of returned by the backend. Show the arithmetic for each row. Do not
change the code yet.
```

## Prompt 3: Read a week of logs with me

```
Here is my router's report for one week and the 20 most expensive log rows:

{paste report.md}
{paste rows}

Which rule is costing me the most money, and which local routes am I least sure
were good enough? Propose one change to rules.json and the experiment that
would tell me whether it made answers worse. Do not change the rules yet.
```

## Tuning

- **It writes a framework**: add "one file per milestone, no classes unless
  there is state to hold."
- **It routes on prompt length alone**: add "length is one signal. The task
  type and the private flag come first."
- **It hard-codes prices**: add "prices come from prices.json with a date. If
  the file is older than 30 days, print a warning."

## A note on privacy

The router decides where your prompts go, which makes it a privacy tool as much
as a cost tool. The `private` flag is enforced below the router on purpose:
test it by trying to break it.
