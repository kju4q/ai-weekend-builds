# 01: Past-You Searcher

Your notes, journals, old posts, and exported conversations become one queryable
memory. You ask it a question and it answers in your own words, with receipts
pointing back at what you actually wrote. It all runs locally.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 4-6 hours | Python 3.10+, local embedding model, local vector store, OpenAI API (optional) |

Built with Codex. The runtime needs above are this project's own.

## What you'll build

A local index over everything you have ever written, and a way to ask it
questions. Point it at a folder of notes, journal files, and exported chats, ask
"what did I keep saying about work in 2023", and get an answer in your own
phrasing with the source passages cited underneath.

## What you'll learn

RAG and embeddings over your own data.

- Chunking long personal writing so a passage still makes sense on its own
- Embeddings and similarity search, built from parts rather than called as a service
- Citing sources, so an answer is checkable instead of merely plausible
- Keeping retrieval fully local while a hosted model only phrases the result

## Prerequisites

> Finalized during the build. This is the starting assumption, not the final list.

- Python 3.10+
- A local embedding model and a local vector store
- Your own text to point it at: notes, journal files, exported conversations
- Optional: an OpenAI API key, only for the layer that phrases the final answer

## Local vs API

> Provisional. Confirmed during the build.

| Part | Runs where |
|---|---|
| Reading and chunking your files | 100% local |
| Embeddings and the index | 100% local |
| Retrieving the passages that answer a question | 100% local |
| Phrasing the final answer in your voice | OpenAI API (only with a key set) |

Without a key, retrieval still works and you read the passages directly. Your
writing never leaves the machine.

## How it works

> Provisional. The real pipeline lands with the build.

```
your notes, journals, exported chats
   ↓  chunk
passages
   ↓  embed  →  local index
question
   ↓  retrieve the closest passages
   ↓  phrase the answer (optional, hosted)
answer + the passages it came from
```

## Build it

> Coming with the build. The five steps below are the shape they will follow.

### Step 1: Run it as-is on the sample

### Step 2: Read the indexer

### Step 3: Point it at your own writing

### Step 4: Turn on cited answers

### Step 5: Make it yours

## The prompts

The exact Codex prompts used to build this are in [prompts.md](prompts.md).

## Verify it works

> Checklist lands with the build.

## Extend it

- Add a time filter, so you can ask the same question of what you wrote in 2019
  and what you wrote last month, and read the two answers side by side

## Common pitfalls

> Filled in from the real build, once there are real failures to warn about.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
