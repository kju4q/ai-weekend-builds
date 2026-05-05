# 02: AI Daily Digest

Pick five sources, get one email every morning with what actually matters.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Easy | 3-5 hours | Node.js or Python, Anthropic API, your favorite email service |

## What you'll build

An automation that reads from 5 sources you pick (newsletters, blogs, RSS feeds, X accounts, anywhere with a URL), summarizes what's worth your time, and emails you a single digest every morning. You set it up once, it runs forever, you wake up to the brief.

## What you'll learn

- Scraping multiple source types reliably (HTML, RSS, JSON APIs)
- Summarization chains that preserve specifics, not generic blurbs
- How to schedule a job (cron, GitHub Actions, or a hosted scheduler)
- Email delivery that doesn't end up in spam
- The complete shape of an automation pipeline

## Prerequisites

- Node.js 18+ or Python 3.10+
- An Anthropic API key
- An email-sending service (Resend, Postmark, SendGrid, or your own SMTP)
- Comfort with async/await and reading library docs
- Patience with HTML scraping (it's always more work than you think)

## How it works

```
5 source URLs (RSS feeds, sitemaps, or HTML pages)
    ↓
fetch and parse each (in parallel)
    ↓
Claude call per source: summarize each one
    ↓
Claude call: synthesize all summaries into one digest
    ↓
Claude call: write the email subject line
    ↓
send the email
    ↓
log what was sent for the next day's "what changed" diff
```

Most of the work is the scraping layer. The Claude part is straightforward.

## Build it

### Step 1: Scaffold

Make a new project. Install:

- An HTTP library (fetch is built-in for Node 18+, requests for Python)
- An RSS/HTML parser (`rss-parser` for Node, `feedparser` for Python; `cheerio` or `BeautifulSoup` for HTML)
- The Anthropic SDK
- An email sender library

Set up `.env` with `ANTHROPIC_API_KEY`, your email service's API key, and the email address to send to.

### Step 2: Set up the sources file

Make a `sources.json` (or YAML if you prefer):

```json
[
  { "name": "Stratechery", "url": "https://stratechery.com/feed/", "type": "rss" },
  { "name": "Anthropic blog", "url": "https://anthropic.com/news", "type": "html" }
]
```

Start with 1-2 sources. Add more once the pipeline works.

### Step 3: Build the fetchers

Write one function per source type:

- `fetchRSS(url)` returns the latest 5 items as `{title, content, url, date}`
- `fetchHTML(url)` returns recent items by parsing the page (this varies by site, you'll write some custom logic per source)

Test each one in isolation. Print the items. If you can reliably get title + content for each item, you're past the worst part.

**Common pitfall**: HTML scraping breaks. Sites change. Wrap each fetcher in error handling so one broken source doesn't kill the whole digest.

### Step 4: Build the summarizer

For each source's items (or the most recent batch):

1. Concatenate the source's content (cap at ~8000 chars)
2. Call Claude with the prompt from `prompts.md` Step 1
3. Get back a summary

If the source returns SKIP, drop it from the digest.

### Step 5: Build the synthesizer

Take all the per-source summaries. Call Claude with the prompt from `prompts.md` Step 2. Get back the full digest as markdown.

### Step 6: Generate the subject line

Call Claude with the prompt from `prompts.md` Step 3. Use the digest as input. Get a one-line subject.

### Step 7: Send the email

Use your email service to send the digest. Subject from Step 6. Body from Step 5.

Test with yourself as recipient. Make sure it doesn't go to spam.

### Step 8: Schedule it

Two easy options:

- **GitHub Actions**: write a `.yml` that runs on a schedule, calls your script. Free for public repos.
- **Cron on a server**: if you have one running.

Run at 5am daily. Logs go to a `./digests/` folder so you have a history.

## The prompts

The summarization, synthesis, and subject prompts are in [`prompts.md`](prompts.md).

## Verify it works

- [ ] Each fetcher returns clean items for its source
- [ ] Each summary is specific (names and numbers preserved)
- [ ] The full digest reads like a smart friend's morning brief, not generic
- [ ] The email subject is specific, under 60 chars
- [ ] Email arrives on time, doesn't go to spam

## Extend it

- Group items by topic (AI, business, tech) automatically
- Add a "what changed since yesterday" diff section
- Send to Slack DM instead of email
- Build a web view at a stable URL so you can read on your phone
- Add a "saved for later" reaction that creates a Notion or Raindrop entry
- Track which items you actually click and feed that back into source prioritization

## Common pitfalls

- **HTML scraping breaks**: write per-source fallbacks, don't trust one parser to handle everything
- **Summaries get generic**: the prompt in Step 1 has a "no fluff" rule. If summaries still feel vague, add: "Quote at least one specific phrase or number."
- **Email goes to spam**: send from a domain you control with proper SPF/DKIM/DMARC, not a free address
- **Digest gets too long**: cap each source to 1-2 items, cap the synthesis word count

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
