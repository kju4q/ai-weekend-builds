# Prompts: Life Admin Brain

Retrieval needs no prompt — it is math on vectors. The only prompt in this build
is the one that turns retrieved passages into an answer. It lives in `ask.py`;
here it is broken out so you can tune it.

## The answer prompt (system)

```
You answer questions about the user's personal documents using ONLY the
provided context. Cite the source file in brackets. If the answer is not in
the context, say so plainly. Be concise and specific.
```

## The answer prompt (user turn)

```
Context:
[sample-passport.txt #0]
PASSPORT DETAILS ... Date of expiration: 08 SEP 2029 ...

[sample-lease.txt #1]
... early termination fee equal to two months rent ($3,700) ...

Question: when does my passport expire?
```

## Why "ONLY the provided context" matters

Without that line, Claude will happily answer from its training data or invent a
plausible date. The whole point of RAG is that the answer is grounded in *your*
documents. Test it: ask something your docs don't cover ("what's my blood type?")
and confirm it says the answer isn't there instead of guessing.

## Tuning

- **Answers too long**: add "Answer in one or two sentences." to the system prompt.
- **Not citing sources**: strengthen to "Every claim must end with [source]."
- **Missing the right passage**: this is a retrieval problem, not a prompt problem.
  Increase `TOP_K` in `ask.py`, shrink `CHUNK_CHARS` in `ingest.py`, or install
  sentence-transformers for better embeddings.
- **Dates read wrong**: add "Quote dates exactly as written in the context."

## Optional: natural-language document questions become structured

If you want the assistant to extract fields (all expiry dates across every doc),
add a second call:

```
From the context, extract every date that represents an expiration, renewal, or
deadline. Return JSON: [{"item": "...", "date": "...", "source": "..."}].
Only include dates actually present in the context.
```

Run that over the whole index and you have an at-a-glance "what expires when" list.
