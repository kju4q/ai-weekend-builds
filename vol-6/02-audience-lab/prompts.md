# Prompts: The Audience Lab

The prompts I would use with a coding assistant to build this from
[SPEC.md](SPEC.md). Each one ends by holding back the next step, for the reason
in the [build guide](../BUILD-GUIDE.md).

## Prompt 1: Design the schema before any API code

The schema decides whether the report in M3 is one SQL query or a weekend of
glue code. Run this first.

```
I am building a local SQLite database of my own social account: posts, post
stats over time, comments with replies, and DMs. Here is the spec:

{paste SPEC.md}

Here are three records from my sample data, same shape as the API:

{paste one post, one comment with a reply, one DM from sample-data/}

Design the schema. Requirements:
- Loading the same data twice must not duplicate anything
- Stats are snapshots over time, not overwritten
- I must be able to tell which replies are mine
- A comment must link to its post and to its parent comment

Show me the CREATE TABLE statements and the one query that answers "which
questions did I never reply to". Do not write the loader yet.
```

## Prompt 2: Review the clustering before you trust it

```
Here is my clustering code and its output on my sample comments:

{paste cluster.py}
{paste the printed clusters}

Act as a skeptical data scientist. Which clusters are real questions and which
are artifacts of the text cleaning, the value of k, or very short comments?
For each problem, tell me the smallest change and how I would see that it
worked. Do not change the code yet.
```

## Prompt 3: Make the webhook safe before it sends anything

```
Here is my webhook handler for the comment-to-DM flow:

{paste server.py}

Find every way this could send a DM it should not: the same event delivered
twice, a keyword inside another word, my own comments, a reply to a reply,
an old comment arriving late, a crash between sending and logging. For each,
show me the test case I should add to the replay file. Do not turn on live
sends and do not write the fix yet.
```

## Tuning

- **It reaches for a hosted vector database**: add "SQLite only. I want one
  file I can copy."
- **It wants an LLM for clustering**: add "TF-IDF and k-means first. I will add
  embeddings only if the sample clusters are wrong."
- **It writes the webhook with live sends on by default**: add "dry run is the
  default. Live requires a flag."

## A note on privacy

Comments and DMs are other people's words. These prompts only need the sample
data and your code. Never paste real DMs into an assistant to debug.
