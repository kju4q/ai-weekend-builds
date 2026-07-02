# 01: Life Admin Brain

Drop your lease, insurance, warranties, and passport into a folder. Then ask
"when does my passport expire?" or "what does my lease say about breaking early?"
and get an answer with the source cited. Everything stays on your machine.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 4-6 hours | Python, local embeddings, Anthropic API (optional) |

## What you'll build

A local RAG (retrieval-augmented generation) assistant for your personal
documents. You put PDFs and text files in `docs/`, run an ingest script that
turns them into a searchable local index, then ask questions in plain English.
The retrieval is fully local. The final phrasing is done by Claude if you want
it, or you can read the retrieved passages directly with no API key at all.

## What you'll learn

- What RAG actually is, built from parts instead of a framework
- How embeddings turn text into vectors you can search by meaning, not keywords
- Chunking: why you split documents and how chunk size changes answers
- Retrieval: cosine similarity, top-k, and why the index is the hard part
- The difference between "the model knows this" and "the model was handed this"

## Prerequisites

- Python 3.10+
- Optional: an Anthropic API key for natural-language answers
- Optional: `pip install sentence-transformers` for real semantic embeddings
- Optional: `pip install pypdf` to read PDF files (text/markdown work with no installs)

## Local vs API

| Part | Runs where |
|---|---|
| Reading & chunking documents | 100% local |
| Embeddings (hashing fallback) | 100% local, zero installs |
| Embeddings (sentence-transformers) | 100% local, downloads model once |
| Retrieval / similarity search | 100% local |
| Final worded answer | Claude API **if** `ANTHROPIC_API_KEY` is set; otherwise local "show the passages" mode |

Your documents and the index (`index.json`) never leave your machine. Only the
retrieved snippets for a single question are sent to Claude, and only if you opt in.

## How it works

```
docs/*.pdf, *.txt, *.md
        ↓  ingest.py
   split into ~800-char chunks
        ↓
   embed each chunk into a vector (local)
        ↓
   index.json  (your local vector store)

question ──embed──▶ cosine similarity ──▶ top 4 chunks ──▶ answer
                    (all local)                          (Claude, optional)
```

## Build it

### Step 1: Run the starter as-is

The repo ships with fake sample documents (a lease, a passport, an insurance
policy, and a warranty PDF) so you can see it work immediately:

```
python ingest.py
python ask.py "when does my passport expire?"
```

With no API key you get "local mode" — the most relevant passages, which for the
sample data already contains the expiry date. This proves retrieval works.

### Step 2: Understand the three files

- `embeddings.py` — turns text into vectors. It auto-selects sentence-transformers
  if installed, else a pure-Python hashing embedding so the demo runs anywhere.
- `ingest.py` — reads `docs/`, chunks, embeds, writes `index.json`.
- `ask.py` — embeds your question, finds the closest chunks, answers.

Read them top to bottom. They are deliberately small.

### Step 3: Turn on real embeddings

```
pip install sentence-transformers
python ingest.py      # re-embeds with all-MiniLM-L6-v2
```

Ask the same questions and notice retrieval gets sharper — the hashing fallback
matches words, real embeddings match meaning ("when do I lose coverage" now finds
the renewal clause even without the word "renew").

### Step 4: Turn on Claude answers

```
export ANTHROPIC_API_KEY=sk-ant-...
python ask.py "how much is the early termination fee and what notice do I need?"
```

Now instead of raw passages you get a written answer that cites the source file.

### Step 5: Make it yours

Delete the samples, drop your real documents into `docs/`, rerun `ingest.py`.
Add `pip install pypdf` and point it at your actual lease and policies.

## Verify it works

- [ ] `python ingest.py` writes `index.json` and reports chunk counts
- [ ] `python ask.py "..."` returns the passport passage for a passport question
- [ ] With sentence-transformers installed, re-ingest changes the backend line
- [ ] With an API key set, answers are written prose that cite `[source]`

## Extend it

- Swap `index.json` for a real local vector DB (Chroma, LanceDB, sqlite-vss)
- Add a `--source lease.pdf` filter to scope questions to one document
- Show the confidence: print the cosine score next to each retrieved chunk
- Add a tiny web UI so family members can ask without the terminal
- Auto-reingest when a file in `docs/` changes (watch mode)

## Common pitfalls

- **Chunks too big**: one 5-page chunk retrieves everything and answers nothing.
  Keep chunks small enough that one covers a single idea.
- **Forgot to reingest**: edited a doc but answers are stale? Rerun `ingest.py`.
- **Expecting magic from the hashing fallback**: it matches words, not meaning.
  Install sentence-transformers before judging retrieval quality.
- **Sending whole documents to Claude**: don't. The point of RAG is you only send
  the few chunks that matter, which keeps it cheap and private.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
