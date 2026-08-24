# 01: Past-You Searcher

Your notes, journals, old posts, and exported conversations become one queryable
memory. You ask it a question and it answers in your own words, with receipts
pointing back at what you actually wrote. It all runs locally.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 4-6 hours | Python 3.10+, sentence-transformers (local), OpenAI API (optional) |

Built with Codex. The runtime needs above are this project's own.

## What you'll build

A local index over everything you have ever written, and a way to ask it
questions. Point it at a folder of notes, journal files, and exported chats, ask
"what did I keep saying about building products", and get back the passages that
answer it, each stamped with the file, the date, and the passage number it came
from.

## What you'll learn

RAG and embeddings over your own data.

- Chunking long personal writing so a passage still makes sense on its own
- Embeddings and similarity search, built from parts rather than called as a service
- Citing sources, so an answer is checkable instead of merely plausible
- Keeping retrieval fully local while a hosted model only phrases the result

## Prerequisites

- **Python 3.10 or later.** Verified on 3.12.13 (macOS, arm64). Use `python3`,
  since plain `python` does not exist on current macOS.
- **Install:**

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

  That installs `sentence-transformers==6.0.0` and `openai==3.3.1`.
  sentence-transformers pulls in torch, which is a **multi-GB download** and
  takes a few minutes on a normal connection.

- **Supported input formats:** `.md`, `.txt`, and `.json` conversation exports
  in the one format documented under [Step 3](#step-3-point-it-at-your-own-writing).
  Anything else in the folder is skipped and named in the output.
- **Optional: an OpenAI API key.** Only for phrasing an answer. Everything else
  works without it.
- **First run downloads the embedding model.** The first `ingest.py` fetches
  `all-MiniLM-L6-v2` (about 90MB) from Hugging Face and caches it under
  `~/.cache/huggingface`. Later runs are offline and take about a second on the
  sample. You may see a one-line Hugging Face notice about unauthenticated
  requests; it is harmless.

### Running without installing anything

If you skip the install, `embeddings.py` falls back to a pure-Python hashing
embedding and the whole pipeline still runs. It matches on shared words rather
than meaning, so results are noticeably weaker. On the sample question "what did
I keep saying about building products", the correct top passage scores 0.609 with
sentence-transformers and 0.340 with the fallback. Use it to see the shape of the
thing; install the real backend to actually use it.

## Local vs API

| Part | Runs where |
|---|---|
| Reading your files | 100% local |
| Chunking | 100% local |
| Embeddings (model runs on your machine) | 100% local |
| The index (`index.json`) | 100% local, never uploaded |
| Search and ranking | 100% local |
| Phrasing a final answer | OpenAI API, only when you set both variables |

With no `OPENAI_API_KEY`, **nothing leaves your machine**, apart from the
one-time model download on first run.

When the answer layer is on, exactly one thing is sent per question: the
`TOP_K` retrieved passages (5 by default), each with its filename, date, and
chunk number, plus your question and the system prompt. Passages that did not
match are not sent. Your folder, your filenames beyond those five, and the index
itself are not sent. If you keep writing you would not paste into a hosted
model, leave the key unset and use local mode, which is the default.

## How it works

```
your writing (.md, .txt, .json conversations)
   ↓  read + skip unsupported files          ingest.py
   ↓  extract a date (metadata → filename → file mtime)
   ↓  chunk: 700 chars, 150 overlap
passages
   ↓  embed locally (all-MiniLM-L6-v2)       embeddings.py
index.json   (text + vector + source + date + chunk number)

your question
   ↓  embed locally                          ask.py
   ↓  cosine similarity, top 5
passages with receipts  [file #chunk]  date  score
   ↓  (optional, only with a key + model set)
a short answer that cites those passages
```

## Build it

### Step 1: Run it as-is on the sample

From this folder:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 ingest.py sample-data
python3 ask.py "What did I keep saying about building products?"
```

`sample-data/` holds six short synthetic files written for this project: a 2019
journal entry, a 2021 project note, a 2022 post, a 2024 reflection, an undated
scratch file, and a 2024 conversation export. They share deliberate themes so
retrieval has something real to find.

The ingest prints one line per file and a summary:

```
  indexed: 2019-05-14-journal.md -> 2 chunks, date 2019-05-14 (from filename)
  indexed: 2021-02-03-project-note.txt -> 2 chunks, date 2021-02-03 (from metadata)
  ...
Files read:    6
Chunks:        12
Backend:       sentence-transformers
```

Other questions the sample answers well:

```bash
python3 ask.py "How did my thinking about AI workflows change?"
python3 ask.py "What was I worried about before starting a project?"
python3 ask.py "Which ideas appeared more than once?"
python3 ask.py            # interactive loop
```

### Step 2: Read the indexer

Three files, each doing one job.

**`embeddings.py`** turns text into vectors. It tries sentence-transformers
first and falls back to a hashing embedding if that import fails, so the repo
runs with zero installs. `backend_name()` reports which one is live, and the
index records it: vectors from the two backends are not comparable, so changing
backend triggers a full rebuild rather than silently bad results.

**`ingest.py`** walks the folder, skips hidden and unsupported files by name,
reads each supported file, flattens JSON conversations into `role: text` lines,
finds a date, splits the text into 700-character chunks with 150 characters of
overlap, embeds them in one batch, and writes `index.json` atomically through a
temp file. Each record carries its text, vector, source path, chunk number, date,
and how the date was found.

The overlap is the part worth understanding: a hard split at 700 characters will
land mid-sentence and cut an idea in half, so each chunk repeats the last 150
characters of the one before it. A thought that straddles a boundary survives in
at least one chunk whole.

**`ask.py`** loads the index, embeds your question with the same model, scores
every chunk by cosine similarity (the vectors are unit length, so the dot product
is the cosine), and prints the top 5 with their receipts. Below a score of 0.20
it says so plainly rather than presenting noise as a result.

### Step 3: Point it at your own writing

```bash
mkdir my-writing
cp ~/somewhere/journal/*.md my-writing/
python3 ingest.py my-writing
python3 ask.py "what have I said about this before?"
```

`my-writing/` is the default folder when you run `python3 ingest.py` with no
argument. It is already in the repo's `.gitignore`, along with `index.json`, so
your writing and the index built from it cannot be committed by accident. If you
keep your writing somewhere else, pass that path instead and keep it outside the
repo entirely.

**Accepted files:** `.md`, `.txt`, `.json`. Subfolders are walked. Hidden files
and every other extension are skipped and listed in the output, so you can see
what was ignored rather than wondering.

**The JSON conversation format.** One object, exactly this shape:

```json
{
  "title": "Deciding what to cut",
  "date": "2024-06-02",
  "messages": [
    {"role": "user", "text": "..."},
    {"role": "assistant", "text": "..."}
  ]
}
```

`title` and `date` are optional; `messages` must be a non-empty list and every
message needs a `text` string. See `sample-data/conversation-2024-06-02.json`.
This is deliberately one narrow format, not a universal importer: exports from
different products all differ, so converting yours into this shape is a small
script you write once. A file that does not match is skipped with the reason
printed, and the rest of the folder still indexes.

**How dates are decided**, in this order:

1. A metadata date in the file: a `date: YYYY-MM-DD` line in the first 10 lines
   of a `.md` or `.txt`, or the `"date"` field of a conversation JSON.
2. A `YYYY-MM-DD` found in the filename, for example `2019-05-14-journal.md`.
3. The file's modification time.

The third case is a guess, and copying files around resets it, so `ask.py` labels
those results "from file mtime, no date in the writing itself" instead of showing
a date that looks authoritative. If dates matter to you, put one in the filename.

**Rebuilding:** just rerun `python3 ingest.py <folder>`. Files are tracked by
SHA-256, so unchanged files are skipped, changed files are re-embedded, deleted
files are pruned, and pointing at a different folder rebuilds cleanly. The write
goes through a temp file and an atomic replace, so an interrupted run cannot
leave a half-written index.

### Step 4: Turn on cited answers

Local mode gives you passages. The optional layer turns those passages into a
couple of sentences that cite them.

```bash
cp .env.example .env          # then edit it
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=<a chat model your account can call>
python3 ask.py "How did my thinking about AI workflows change?"
```

Both variables are required. There is no default model on purpose: model names
change and get retired, so this project will not guess one for you. If the key is
set and the model is not, `ask.py` says so and stays in local mode rather than
failing. To see what your account can call:

```bash
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

What gets sent, per question: the 5 retrieved passages with their filenames,
dates, and chunk numbers, your question, and the system prompt in `prompts.md`.
Nothing else. The prompt requires every claim to carry a `[file #chunk]` receipt
and requires the model to say when the passages do not support an answer. The
retrieved passages are printed underneath the answer either way, so you can check
it against the source in the same breath.

If the call fails, `ask.py` prints the actual error and falls back to local mode.
It does not fail silently, because a silent fallback looks identical to a working
answer layer that had nothing to say.

### Step 5: Make it yours

Small changes that pay off, roughly in order of effort:

- Raise `TOP_K` in `ask.py` to 8 for broad "what did I think about X" questions,
  drop it to 3 for specific ones.
- Print the whole chunk instead of the first 400 characters: change
  `SNIPPET_CHARS`.
- Add a `--since 2022` flag that filters `records` by the `date` field before
  scoring. Every record already carries a date.
- Group results by source file so three hits from one journal entry read as one
  result rather than three.
- Write a small converter from your own chat export into the JSON format above,
  and keep it next to `ingest.py`.

## How to build this with ChatGPT, Work, and Codex

This project is small enough to build by hand from this README alone. If you
would rather build it with AI help, this is the path that works, and the exact
prompts are in [prompts.md](prompts.md).

- **ChatGPT Chat** for the thinking, before any code. Pin the concept, then work
  out the smallest complete version: what the inputs are, what the output looks
  like, where the local/API boundary sits, what should happen when retrieval
  finds nothing. Come out with decisions, not code.
- **ChatGPT Work** to turn those decisions into the ordered build checklist: the
  five steps, the file list, the dependencies, the install sequence, and the
  acceptance checks you will hold the build to.
- **Codex** to implement it stage by stage against that checklist, running each
  command as it goes, then to review its own work from a clean environment and
  check the README's claims against the code.

Described this way it is the workflow you follow, not a transcript of how this
particular copy was produced.

## Verify it works

Run these and check each one:

- [ ] `python3 ingest.py sample-data` prints 6 files, 12 chunks, and an index path
- [ ] `index.json` now exists in this folder
- [ ] `python3 ask.py "What did I keep saying about building products?"` returns
      passages from `old-post.md` and `2021-02-03-project-note.txt`
- [ ] Every passage line starts with a `[filename #chunk]` receipt and a date
- [ ] `2019-05-14-journal.md` shows its date as "from filename",
      `old-post.md` as "from metadata", `notes-scratch.md` as "from file mtime"
- [ ] With `OPENAI_API_KEY` unset, you still get useful passages. This is the
      default path, not a degraded one
- [ ] Asking something absent, `python3 ask.py "what is my blood type?"`, prints a
      weak-match warning and invents nothing
- [ ] Running `python3 ingest.py sample-data` a second time prints "Nothing
      changed" and leaves the index intact
- [ ] Touching one sample file and re-ingesting re-embeds only that file
- [ ] `python3 ingest.py <empty folder>` exits with a message telling you what to do
- [ ] A folder holding a `.png`, a hidden file, and a malformed `.json` skips all
      three by name and indexes the rest
- [ ] Deleting `index.json` and running `ask.py` tells you to run `ingest.py`

## Extend it

- Add a time filter, so you can ask the same question of what you wrote in 2019
  and what you wrote last month, and read the two answers side by side
- Show which source files a theme appears in across years, so a repeated idea is
  visible as repetition rather than as five separate hits
- Add a `--source` flag to search one file or one subfolder
- Export an answer plus its receipts to a markdown file you can keep

## Common pitfalls

- **The first run stalls for minutes.** That is torch installing, then the 90MB
  model downloading. It happens once. Later runs take about a second on the sample.
- **Results are vague and scores hover around 0.3.** You are on the hashing
  fallback. Run `pip install -r requirements.txt` and re-ingest.
- **Everything is dated today.** None of your files carry a date in metadata or
  filename, so all of them fell through to file mtime, which copying reset. Put
  `YYYY-MM-DD` in the filenames.
- **You edited your writing and the answers did not change.** The index is a
  snapshot. Re-run `ingest.py` after changing files.
- **A whole file got skipped.** Check the ingest output; it names every skipped
  file and why. Malformed conversation JSON is the usual cause.
- **Chunks too big or too small.** At 700 characters a chunk holds a couple of
  paragraphs. Much smaller and passages lose their context; much larger and one
  chunk covers several topics and matches everything weakly. Change
  `CHUNK_CHARS`, then re-ingest, since old chunks stay as they were.
- **Expecting a written answer in local mode.** Local mode returns passages, by
  design. The synthesized answer needs `OPENAI_API_KEY` and `OPENAI_MODEL`.
- **Turning the key on for writing you would not paste into a chatbot.** Setting
  both variables sends the retrieved passages to OpenAI. That is the whole
  boundary. Leave the key unset for anything sensitive.
- **Weak results on a real question.** Sometimes your archive genuinely does not
  cover it. The score threshold exists so the tool admits that instead of
  dressing up the nearest five passages as an answer.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
