# Prompts: The Graph of Everything You Know

The prompts I would use with a coding assistant to build this from
[SPEC.md](SPEC.md). Each one ends by holding back the next step, for the reason
in the [build guide](../BUILD-GUIDE.md).

## Prompt 1: Fix the types before extracting anything

```
I am building a personal knowledge graph from my notes, reading highlights and
project READMEs. Here is the spec:

{paste SPEC.md}

Here are two sample files:

{paste sample-data/notes/2026-03-attention.md}
{paste sample-data/projects/tiny-model/README.md}

By hand, list every fact you would extract from these two files using only the
closed entity and relation types in the spec, each with the exact sentence it
comes from. Then tell me which facts did not fit the types, and whether the fix
is a new type or leaving that fact out. Do not write the extractor yet.
```

Doing it by hand first gives you the answer key for M1.

## Prompt 2: Catch made-up facts

```
Here is my extractor's output on one file, and the file:

{paste the JSON}
{paste the file}

For every fact, check whether its sentence appears in the file word for word,
and whether the sentence actually states the fact or only suggests it. List the
facts that fail either test. Then tell me what in my extraction prompt invited
them. Do not change the prompt yet.
```

## Prompt 3: Debug a question the graph got wrong

```
My graph answered this question wrong:

Question: {question}
Expected: {expected answer and files from questions.md}
Got: {the answer}
Nodes it started from: {...}
Edges it walked: {...}

Tell me where it went wrong: wrong start nodes, a missing edge, an edge under
an unmerged duplicate, or a correct walk with a bad final answer. Show me the
query I can run on graph.db to confirm it. Do not change any code yet.
```

## Tuning

- **It wants a graph database server**: add "SQLite, two tables. I want one
  file."
- **It extracts every noun**: add "only the entity types in the spec. A thing
  that is not a person, idea, project or source is not a node."
- **Answers are fluent but cite nothing**: add "answer only from the sentences
  you were given, and quote the one each claim came from."

## A note on privacy

This project reads everything you point it at. With a local extraction model,
nothing leaves the machine. With a cloud model, every document you ingest is
sent. Start with the sample data, then a folder you would be comfortable
pasting into a chat.
