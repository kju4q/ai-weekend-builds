# 02: The Audience Lab

**Status: plan and prompts.** There is no application code in this folder yet.
What is here is the spec, the prompts, and invented sample data, so you can
build it yourself with an assistant using the [build guide](../BUILD-GUIDE.md).
Nothing on this page is a result I measured, because I have not built it.

Every post, comment, save and DM from your own account in one database you own,
the comments grouped by what people keep asking, and the comment-to-DM flow
(someone comments a keyword, they get a DM with the link) rebuilt by you instead
of rented from a tool.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium-Advanced | 5-8h | Python, SQLite, the platform's official API, scikit-learn |

## What you will build

- An ingest script that pulls your posts, their stats, comments and DMs through
  the platform's official API into a local SQLite file
- A clustering step that groups comments by the question behind them, so "what
  laptop", "which computer is that" and "mac or pc??" land in one pile with a
  count next to it
- A report: the questions people ask most, which posts caused them, and which
  ones you never answered
- A small webhook server that answers a keyword comment with a DM, with a dry
  run mode that only logs what it would have sent

## What you will learn

- **Platform APIs**: tokens, permissions, pagination, rate limits, and webhooks,
  which are the same shape on every platform you will ever integrate
- **Owning your data**: why a SQLite file you can query beats an analytics
  screen you can only look at
- **Clustering**: turning hundreds of messy comments into a short list of
  questions, first with TF-IDF and k-means (no downloads), then with embeddings
  if you want better groups
- **Event-driven code**: a webhook is a function someone else calls, and you
  have to handle being called twice, late, or not at all

## Prerequisites

- Python 3.10+
- A professional (business or creator) account on the platform you use, and a
  developer app with the permissions for reading comments and sending messages.
  The exact permission names change, so read the platform's current docs before
  you start, not a blog post.
- For the webhook: a way to receive HTTPS requests on your machine while
  testing, such as a tunnel
- No AI API key needed for the core. Clustering runs locally.

## Local vs API

| Part | Runs where |
|---|---|
| Fetching posts, comments, DMs | The platform's API (it is your data, coming home) |
| The database | 100% local, one SQLite file |
| Clustering comments | 100% local |
| The report | 100% local |
| Sending a DM in reply to a comment | The platform's API |
| Optional: naming each cluster in plain words | An LLM API, only if you add it, only the comment text |

Your audience's comments and messages are other people's words. Keep the
database on your machine, keep it out of git (the spec says so), and do not send
DMs to an LLM unless you have decided that is acceptable.

## How it will work

```
platform API ──> ingest.py ──> audience.db (posts, comments, dms, stats)
                                  │
                                  ├──> cluster.py ──> clusters table + report.md
                                  │
webhook ──> server.py ──> keyword match ──> send DM (or log it, in dry run)
                                  └──> every send logged in audience.db
```

## Build it in steps

The full spec with acceptance checks is in [SPEC.md](SPEC.md). In order:

1. **Load the sample data into SQLite.** No API yet. `sample-data/` has invented
   posts, comments and DMs in the same shape the API returns. Get the schema
   right against those first.
2. **Cluster the sample comments.** The sample has a handful of repeated
   questions hidden in 60 comments. Your clustering should find them.
3. **Write the report.** Top questions, the post that triggered each, and which
   ones have no reply from you.
4. **Connect the real API.** Only now. Pull one page of your own posts, then all
   of them, then comments, handling pagination and rate limits.
5. **Build the comment-to-DM flow in dry run.** It logs what it would send.
   Replay the sample comments through it before any real comment touches it.
6. **Turn on real sends**, for one keyword on one post, and watch the log.

## Verify checklist

- [ ] Loading `sample-data/` twice gives the same row counts (ingest is idempotent)
- [ ] The clustering puts at least 6 of the 8 laptop questions from the sample in one cluster
- [ ] The report lists the unanswered questions from the sample
- [ ] The webhook in dry run logs exactly one DM per matching comment, even when
      the same event is delivered twice
- [ ] `audience.db` is listed in `.gitignore`

## Extend it

- Name each cluster in plain words with a small model, sending only the comment
  text, never usernames
- Track a question over time: is "how long did this take" growing?
- Draft an answer post for the top unanswered question
- Add a second platform into the same tables

## Common pitfalls

- **Starting with the API.** Permissions and app review can eat an afternoon.
  Build against the sample data first so that afternoon is not wasted.
- **Clustering on raw text.** Emoji, @mentions and "this!!!" dominate short
  comments. Strip them before clustering or every cluster is about emoji.
- **Sending a DM twice.** Webhooks are delivered at least once, which means
  sometimes twice. Store the comment id and refuse to send for one you have
  already handled.
- **Ignoring the platform's automation rules.** Read them before you turn on
  real sends. Rebuilding the flow does not exempt you from them.

## Files

- [SPEC.md](SPEC.md): paste-ready spec with milestones and acceptance checks
- [prompts.md](prompts.md): the prompts for your coding assistant
- [sample-data/](sample-data): invented posts, comments and DMs. No real people.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
