# Prompts: AI Daily Digest

## Step 1: Summarize a single source

```
You are summarizing one source for a daily digest. The reader is a builder, technically literate, time-poor.

Source: {source name}
Content:
{the article or post text, max 8000 chars}

Output:
- 1 line summary (the headline, in your own words, specific not vague)
- 2-3 bullet points (the actual substance, names and numbers preserved)
- 1 line "why this matters to a builder" (skip if it doesn't)

Rules:
- No "this article discusses..." preamble
- No filler like "interestingly" or "notably"
- Keep proper nouns and numbers exactly as written
- If the content is fluff with no real signal, output: SKIP
```

## Step 2: Synthesize the digest

```
You have summaries from multiple sources. Combine them into one daily digest.

Summaries:
{paste all step 1 outputs, with source names}

Output the digest as markdown:

# {Today's date}

## What changed today

{2-3 line synthesis of the most important things across all sources, written as if you're texting a smart friend a heads up}

## By source

### {Source 1}
{summary in step 1 format}

### {Source 2}
{summary}

...

## Worth saving for later

{1-2 items that aren't urgent but will matter in 6 months}

Rules:
- Skip sources that returned SKIP in step 1
- The "What changed today" section is the most important. Make it actually useful.
- No emojis. No "Hope you have a great day!"
- Sign off: just your name. No "Cheers,".
```

## Step 3: Subject line

```
Write the email subject for this digest. Constraints:

- Max 60 characters
- The single most important thing from today's digest
- Specific, not vague
- No clickbait, no curiosity-gap baiting
- No emojis

Digest:
{paste step 2 output}

Output ONE subject line. No quotes, no explanation.
```

## Notes on tuning

- If summaries feel generic, add to step 1: "Quote at least one specific phrase or number from the source."
- If the digest is too long, add to step 2: "Keep total length under 800 words."
- If subject lines are weak, add example good subjects to step 3 ("OpenAI ships Sora video model in API," "Stripe adds AI checkout to dashboard").

The chain runs sequentially: each source through step 1 in parallel, then step 1 outputs through step 2, then step 2 output through step 3.
