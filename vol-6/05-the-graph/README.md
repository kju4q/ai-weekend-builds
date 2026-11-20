# 05: The Graph of Everything You Know

**Status: plan and prompts.** There is no application code in this folder yet.
What is here is the spec, the prompts, and invented sample data, so you can
build it yourself with an assistant using the [build guide](../BUILD-GUIDE.md).
Nothing on this page is a result I measured, because I have not built it.

Point it at what you have read, built and written: notes, saved articles,
project READMEs, drafts. It pulls out the people, ideas and projects in them,
connects them, and answers questions that no single document can, like "which
ideas from what I read in the spring ended up in something I built?"

| Difficulty | Time | Suggested stack |
|---|---|---|
| Advanced | Full day | Python, SQLite, a model for extraction (local or API) |

## What you will build

- An ingest step that reads a folder of markdown and text files
- An extractor that pulls out entities (person, idea, project, source) and
  relations between them, each one pointing back to the sentence it came from
- A merge step that decides "Mira Okafor", "Okafor" and "M. Okafor" are
  one node
- The graph, stored as two tables in SQLite: nodes and edges
- A question answerer that finds the relevant part of the graph, walks it, and
  answers with the sentences it used
- A small self-contained HTML view of the graph

## What you will learn

- **Knowledge graphs**: nodes, edges, and why "who connects to what" answers
  questions that search cannot
- **Extraction**: turning prose into structured facts with a model, and
  checking that it did not make facts up
- **Entity resolution**: the unglamorous merge step that decides whether the
  graph is useful or a pile of duplicates
- **Graph retrieval**: answering by walking connections, compared with plain
  similarity search over chunks

## Prerequisites

- Python 3.10+
- A model for extraction. A local model keeps every note on your machine; a
  cloud model will extract better but reads every document. Decide per folder.
- A folder of your own writing. Start with `sample-data/` instead.

## Local vs API

| Part | Runs where |
|---|---|
| Reading files | 100% local |
| Extracting entities and relations | Local model, or a cloud API that reads every document you ingest |
| Merging, storing, walking the graph | 100% local |
| Writing the final answer | Local model, or a cloud API that reads the sentences retrieved for that question |
| The graph view | 100% local, one HTML file |

## How it will work

```
notes/, reading/, projects/
   │
   v
extract.py ── per paragraph: entities + relations + the source sentence
   │
   v
merge.py ── one node per real thing (aliases kept)
   │
   v
graph.db: nodes(id, type, name, aliases)  edges(src, rel, dst, source_file, sentence)
   │
   ├──> ask.py "what did I build that came from something I read?"
   │      find start nodes ──> walk 1-2 hops ──> answer citing sentences
   │
   └──> view.html
```

## Build it in steps

The full spec with acceptance checks is in [SPEC.md](SPEC.md). In order:

1. **Fix the schema of a fact.** Entity types and relation types, written down,
   before any extraction. A short closed list beats an open one.
2. **Extract from one sample file** and read every fact by hand against the
   text. Count the ones that are not in the text.
3. **Extract from all of `sample-data/`** and look at the duplicates.
4. **Merge.** The sample has the same person written three ways on purpose.
5. **Ask.** `sample-data/questions.md` has five questions and the answer each
   one should reach, with the files that support it.
6. **Your own folder.** Small first: one month of notes, not ten years.

## Verify checklist

- [ ] Every edge in the graph has a source file and a sentence, and the sentence
      is really in that file
- [ ] On the first sample file, you counted the extracted facts that are not in
      the text, and you know the number
- [ ] The three spellings of the same person in the sample merge into one node
- [ ] At least 4 of the 5 sample questions reach the expected answer, citing the
      right files
- [ ] `view.html` opens with the network off

## Extend it

- Add dates to edges and ask "what changed my mind, and when"
- Compare graph answers with plain chunk search on the same questions
- Re-ingest only files that changed since last time
- Let it suggest connections you have not made yet, and mark them as guesses

## Common pitfalls

- **An open list of relation types.** Let the model invent relations and you get
  hundreds that mean the same thing. Close the list.
- **Facts without sources.** If an edge does not point at a sentence, you cannot
  check it, and an unchecked graph is a confident one.
- **Skipping the merge.** Without it, every question finds half the answer
  because the other half is under a different spelling.
- **Ingesting everything on day one.** Extraction costs time or money per
  document. Prove it on the sample, then one month of notes.

## Files

- [SPEC.md](SPEC.md): paste-ready spec with milestones and acceptance checks
- [prompts.md](prompts.md): the prompts for your coding assistant
- [sample-data/](sample-data): invented notes, reading highlights and project
  READMEs that connect, plus five questions with expected answers

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
