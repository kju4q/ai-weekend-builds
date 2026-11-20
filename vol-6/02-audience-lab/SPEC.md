# SPEC: The Audience Lab

Paste this into your assistant with the first prompt in [prompts.md](prompts.md).
Edit it first: swap in your platform and your keyword.

## One sentence

Every post, comment, save and DM from my own account in a local SQLite database,
with comments grouped by the question behind them, and my own comment-to-DM flow.

## Inputs

- The platform's official API, using my own account's token
- Sample data: `sample-data/posts.json`, `sample-data/comments.json`,
  `sample-data/dms.json`. Invented, same shape as the API responses
- `keywords.json`: keyword to DM text, for the comment-to-DM flow

## Outputs

- `audience.db`: SQLite with tables `posts`, `post_stats`, `comments`, `dms`,
  `clusters`, `sends`
- `report.md`: the top questions with counts, the post that caused each one, and
  which ones I never replied to
- `sends` table: every DM the flow sent or would have sent, with the comment id

## Out of scope

- Posting, scheduling, or editing content
- Anyone else's account
- A web dashboard. The report is markdown.

## Constraints

- Python 3.10+, standard library plus `requests`, `scikit-learn`, and a small
  web framework for the webhook
- Clustering is local. No LLM call in the core.
- The token lives in `.env`. `.env` and `audience.db` are in `.gitignore`.
- Every API call goes through one function that handles pagination, retries
  and rate limits
- The webhook has a dry run mode, and dry run is the default

## Milestones

### M1: Schema and sample load
- Build: `db.py` (schema), `load_sample.py` (reads `sample-data/` into SQLite)
- Acceptance check: `python load_sample.py && python load_sample.py` then
  `sqlite3 audience.db "select count(*) from comments"` prints `60`, not `120`

### M2: Clustering
- Build: `cluster.py`. Clean the text (lowercase, strip emoji, mentions and
  punctuation), TF-IDF, k-means, store the cluster label per comment
- Acceptance check: `python cluster.py --k 7` prints the clusters with counts,
  and at least 6 of the 8 laptop questions in the sample land in one cluster.
  TF-IDF only matches shared words, so "mac or pc??" and "which computer do you
  use" are hard for it. If it cannot get there, that is the reason to try
  embeddings, not a reason to loosen the check.

### M3: Report
- Build: `report.py` writes `report.md`
- Acceptance check: `report.md` lists the questions in the sample with no reply
  from the account owner (`is_owner_reply` false for every reply in the thread)

### M4: Real ingest
- Build: `ingest.py` pulls my posts, stats, comments and DMs into the same tables
- Acceptance check: running it twice in a row adds zero rows the second time,
  and the comment count for one post matches what the app shows

### M5: Comment-to-DM flow, dry run
- Build: `server.py`, a webhook endpoint that matches keywords and logs sends
- Acceptance check: `python server.py --replay sample-data/comments.json`
  logs exactly one would-send for each of the 10 comments containing `link`
  as a whole word in any case, and replaying the file a second time logs zero
  new sends

### M6: Real sends
- Build: a `--live` flag
- Acceptance check: one test comment from a second account on one post gets one
  DM, and the `sends` table has one row for it

## Done means

- [ ] Every acceptance check passes on sample-data/
- [ ] M4 and M6 pass on my real account
- [ ] I can name my top three audience questions from `report.md`
