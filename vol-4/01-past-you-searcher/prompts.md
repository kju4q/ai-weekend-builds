# Prompts: Past-You Searcher

Two different things live in this file.

**The AI-assisted build prompts** are the path a reader follows to build this
project with help: clarify in ChatGPT Chat, plan in ChatGPT Work, implement and
review in Codex. They are reusable templates, not a record of how this particular
copy was produced. The project can also be built by hand from the README alone.

**The runtime prompt** is the real one, the exact system prompt `ask.py` sends
when the optional answer layer is enabled.

Retrieval itself needs no prompt. It is math on vectors.

## AI-assisted build path

### 1. ChatGPT Chat: clarify the implementation

```
I am building a project called Past-You Searcher. The concept is locked and I do
not want it redesigned:

  Personal writing (notes, journals, old posts, exported conversations) becomes
  one local index I can ask questions of. Answers come back as passages from my
  own writing with a source receipt on each one. Retrieval and indexing are
  fully local. A hosted model may optionally phrase a short answer from the
  retrieved passages, nothing more.

Do not propose a different product, a web interface, a vector database service,
or a framework. It is a weekend project: a few Python files and a command line.

Help me pin down the smallest version that actually runs, end to end:

- Inputs: which file formats, and what the one supported conversation JSON shape
  should be. I want one documented format, not a universal importer.
- Dates: writing has inconsistent dates. Propose a strict fallback order and
  tell me which cases are honest guesses I should label as such.
- Chunking: chunk size and overlap for personal writing, and why.
- Index: the smallest sensible local format. No separate database service.
- Outputs: exactly what a result line shows so a claim is checkable.
- The local/API boundary: what runs locally always, what is sent when the
  optional layer is on, and what must never be sent.
- Failure cases I have to handle: no index, empty folder, unsupported files,
  malformed conversation JSON, re-running ingestion, retrieval finding nothing
  relevant.
- Verification: the objective checks that prove each of the above.

Ask me the implementation questions you actually need answered. Do not write the
code yet. End with the decisions we settled, as a list.
```

### 2. ChatGPT Work: turn decisions into a checklist

```
Here are the decisions from our discussion:

[paste the decision list from step 1]

Turn them into a build checklist for a single weekend project. Produce:

1. Five build steps, in this order and no other: run it as-is on the sample,
   read the indexer, point it at your own writing, turn on cited answers, make
   it yours. Each step gets exact commands.
2. The minimal file list. Nothing beyond what the five steps need.
3. Dependencies, with the reason each one exists and what breaks without it.
4. The install sequence, starting from a clean clone and a fresh virtualenv.
5. Acceptance checks: objective, runnable, one per requirement, including the
   no-key path and the case where the writing does not support an answer.
6. Privacy checks: what must never be committed, what must never be sent to an
   API, and how each is enforced rather than merely promised.

Do not create any extra repository documents: no build plan, no build log, no
architecture file, no agent instructions. The checklist goes into the project
README and nowhere else.
```

### 3. Codex: implement the project

```
Read this project's README and everything currently in this folder before
changing anything.

Implement the project in small stages. After each stage, run it and show me the
real output:

1. embeddings.py: local embeddings with a documented fallback when the embedding
   library is not installed. The index must record which backend produced it,
   because vectors from two backends are not comparable.
2. ingest.py: folder to chunks to embeddings to a local index file. Skip hidden
   and unsupported files by name in the output. Support the one documented
   conversation JSON format. Apply the agreed date fallback order and store how
   each date was found. Make re-running safe and incremental, and write the
   index atomically.
3. sample-data/: four to six short synthetic files across different sources and
   dates, sharing deliberate repeated themes and at least one changed opinion,
   so retrieval has something real to find. All fictional and safe to publish.
   Never use my real writing.
4. ask.py: embed the question locally, rank, print the top passages each with
   filename, date, and chunk number. Then the optional answer layer, off unless
   both the key and the model variables are set.

Constraints:
- Do not rename the project or rewrite its opening description.
- Keep the local/API boundary exactly as documented. Only the retrieved passages
  for the current question may be sent.
- Do not hardcode a model name. Read it from the environment.
- No web interface, no framework, no database service, no test directory.
- Every error path prints what to do next.
- Touch no other project in this repository.

Run every command you write in the README. If something fails, fix it and show
the passing output.
```

### 4. Codex: verify and review

```
Review this project as if you had just cloned it and never seen it before.

1. Follow the README exactly, from a fresh virtualenv. Every command, in order,
   copied as written. Report anything that does not work as documented.
2. Run the sample ingestion and at least three of the sample questions. Confirm
   the passages returned are actually relevant and each carries a receipt.
3. Ask something the sample writing does not cover. Confirm nothing is invented.
4. Test the error paths: missing index, empty folder, unsupported file types,
   malformed conversation JSON, a second ingestion run, a changed file.
5. Confirm the no-key path is genuinely useful rather than a degraded stub.
6. Compare every claim in the README against the code. Flag anything the docs
   promise that the code does not do, especially about what leaves the machine.
7. Confirm secrets and personal writing cannot be committed: check .gitignore
   covers the generated index, the personal writing folder, the virtualenv, and
   .env. Confirm no real key is present anywhere.
8. Confirm the dependency versions listed are the ones actually installed.

Fix only confirmed problems. Do not refactor working code, do not add features,
and do not create planning documents. Report what you changed and what you chose
to leave.
```

## Runtime prompt

This is the exact system prompt in `ask.py`, sent only when both
`OPENAI_API_KEY` and `OPENAI_MODEL` are set:

```
You answer questions about the user's own past writing using ONLY the passages
provided. Every factual claim must end with a receipt in the form
[filename #chunk]. Never invent a memory, a date, an opinion, or a change over
time that is not present in the passages. If the passages do not support an
answer, say exactly that and stop. Do not pad the answer. Two to five sentences
unless the question needs a short list.
```

The user turn is the retrieved passages, then the question:

```
Passages:
[old-post.md #1] (dated 2022-08-09)
...Building products on top of a system that cannot cite itself feels like
building on sand, and I have done enough of that already.

[2024-01-20-reflection.md #0] (dated 2024-01-20)
...What actually changed my mind was retrieval...

Question: How did my thinking about AI workflows change?
```

Every clause in that system prompt is doing a job:

- **"ONLY the passages provided"** is the whole point of retrieval. Without it
  the model answers from training data, and a fluent paragraph about how people
  generally change their minds about AI is worse than useless: it reads exactly
  like a memory of yours. Test it by asking something absent from your writing.
- **"Every factual claim must end with a receipt"** makes the answer checkable in
  seconds. An answer you cannot check costs as much to verify as it would have
  cost to write.
- **"If the passages do not support an answer, say exactly that and stop"** is
  the honest failure mode. This is the sentence that keeps a thin retrieval hit
  from turning into a confident fabrication.
- **"Never invent a memory, a date, an opinion, or a change over time"** names
  the four specific fabrications this tool invites. Questions like "how did my
  thinking change" actively tempt a model to narrate an arc that the passages do
  not show. Naming the failure is more effective than a general warning.
- **"Do not pad"** because you asked your own archive a question, not a model for
  an essay.

## Tuning

- **Number of retrieved passages**: `TOP_K` in `ask.py`, 5 by default. Raise to
  8 for broad questions across years, drop to 3 for specific ones. More passages
  means more context sent to the API when that layer is on.
- **Chunk size and overlap**: `CHUNK_CHARS` (700) and `CHUNK_OVERLAP` (150) in
  `ingest.py`. Smaller chunks match more precisely but lose the surrounding
  context that makes a passage readable. Larger chunks cover several topics at
  once and match everything weakly. Re-ingest after changing either, since
  existing chunks are already stored.
- **Answer length**: change the last line of the system prompt. "Two to five
  sentences" is deliberately short. "One sentence" makes a good quick-answer mode.
- **Citation strictness**: strengthen to "Every sentence must end with a receipt"
  if claims are arriving unattributed. That reads worse and verifies better.
- **When retrieval is weak**: `WEAK_SCORE` in `ask.py` is 0.20, set by hand
  against the sample. Below it, `ask.py` warns that the closest passage is
  probably unrelated. Raise it if you are getting confident answers built on
  thin matches; lower it if real hits are being flagged. Note the two embedding
  backends score on different scales, so retune it if you switch backends.
- **A weak result is usually a retrieval problem, not a prompt problem.** Before
  editing the prompt, raise `TOP_K`, shrink `CHUNK_CHARS`, or confirm you are on
  the sentence-transformers backend rather than the fallback.
