# SPEC: The Graph of Everything You Know

Paste this into your assistant with the first prompt in [prompts.md](prompts.md).
Edit it first: choose local or cloud extraction, and your folders.

## One sentence

Read what I have read, built and written, extract the people, ideas and projects
in it, connect them with sources, and answer questions across the graph.

## Inputs

- Folders of `.md` and `.txt` files: notes, reading highlights, project READMEs,
  drafts
- Sample data: `sample-data/notes/`, `sample-data/reading/`,
  `sample-data/projects/`, all invented, and `sample-data/questions.md` with
  expected answers

## Outputs

- `graph.db`: `nodes(id, type, name, aliases)` and
  `edges(src, rel, dst, source_file, sentence)`
- `ask.py "question"` prints an answer and the sentences and files it used
- `view.html`: the graph, self-contained, no network

## Entity and relation types (closed lists)

- Entities: `person`, `idea`, `project`, `source` (a book, article, talk)
- Relations: `wrote` (person to source), `about` (source to idea),
  `uses` (project to idea), `inspired` (source or person to project),
  `built` (me to project), `disagrees_with` (idea to idea)

## Out of scope

- Live sync with note apps
- Multi-user anything
- Inventing connections that no sentence supports

## Constraints

- Python 3.10+, SQLite. No graph database server.
- Every edge must have `source_file` and `sentence`. An edge without them is
  rejected at insert time.
- Extraction returns JSON validated against the closed type lists
- If extraction uses a cloud API, the README of my build says which folders are
  sent

## Milestones

### M1: Schema and one file
- Build: `db.py`, `extract.py <file>` printing facts as JSON
- Acceptance check: on `sample-data/notes/2026-03-attention.md`, every printed
  fact has a sentence that appears verbatim in the file (`extract.py --verify`
  checks this and prints the count that fail)

### M2: Whole folder
- Build: `ingest.py <folder>` writes all facts to `graph.db`
- Acceptance check: `ingest.py sample-data` then the verify check over the whole
  database reports zero edges whose sentence is missing from its file

### M3: Merge
- Build: `merge.py` with an alias table
- Acceptance check: "Mira Okafor", "Okafor" and "M. Okafor" in the
  sample end up as one `person` node with the other two as aliases

### M4: Ask
- Build: `ask.py`: pick start nodes from the question, walk up to 2 hops,
  answer from the collected sentences only
- Acceptance check: `ask.py --eval sample-data/questions.md` prints, per
  question, whether the answer names the expected entities and cites at least
  one expected file. Target: 4 of 5.

### M5: View
- Build: `view.py` writes `view.html`
- Acceptance check: opens with the network off and shows every node from the
  sample

## Done means

- [ ] Every acceptance check passes on sample-data/
- [ ] One month of my real notes ingested, verify check at zero
- [ ] One question answered that I could not have answered by searching
