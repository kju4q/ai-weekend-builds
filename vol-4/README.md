# Vol 4: 5 Builds On Your Own Data (August 2026)

5 projects that make your own data work for you: your past, your patterns, your
world, your interface, your future.

| # | Project | Difficulty | Time | What you get |
|---|---------|---|---|---|
| 01 | [Past-You Searcher](01-past-you-searcher) | Medium | 4-6h | Everything you've ever written becomes one memory you can ask questions |
| 02 | [Pattern Mirror](02-pattern-mirror) | Easy-Medium | 3-5h | Years of your camera roll, rendered as the shape of your life |
| 03 | [Lookout](03-lookout) | Medium | 4-6h | Stops you checking pages, watches your sources and speaks only when something changes |
| 04 | [Personal API](04-personal-api) | Medium-Advanced | 5-8h | One local server where your life has addresses |
| 05 | [Freedom Calculator](05-freedom-calculator) | Advanced | Full day | Ten thousand simulated versions of your next year, from your own assumptions |

## Each project teaches a different concept

- **Retrieval over your own writing (#1)**: RAG and embeddings, pointed at text
  you actually wrote.
- **Vision over time (#2)**: reading images in bulk and turning a timeline into
  something you can look at.
- **Scheduled agents (#3)**: state, storage, and diffing, so a job that runs
  every day only speaks when it has something new.
- **APIs (#4)**: what an API really is, learned by building one around your own
  life.
- **Probabilistic thinking (#5)**: volatility, percentiles, and distributions
  instead of a single guessed number.

## Local vs API, at a glance

Every project runs its core on your own machine: your writing, your photos, your
sources, your day, your numbers. Two projects need no model key at all. The three
that can use one treat it as optional, for the phrasing layer only, with a local
path that still works without it.

| # | Project | Core | What a key adds |
|---|---------|------|-----------------|
| 01 | Past-You Searcher | Chunking, embeddings, retrieval, all local | Phrases the final answer in your voice |
| 02 | Pattern Mirror | Dates, grouping, and the report, all local | An alternative to the local vision pass |
| 03 | Lookout | Fetching, saved history, and diffing, all local | Summarizes what a change means |
| 04 | Personal API | Everything, bound to localhost | Nothing, no model is involved |
| 05 | Freedom Calculator | The whole simulation | Nothing, no model is involved |

Each project README has the exact breakdown.

## How this volume is built

Vol 4 is built with Codex. Projects that need a hosted model use an OpenAI API
key. Earlier volumes use an Anthropic key. Each project README states exactly
what that project needs.

## Want vol 1, 2, or 3?

[Go back to the root](../README.md), every volume is linked there.
