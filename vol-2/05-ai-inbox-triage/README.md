# 05: AI Inbox Triage

Connect your inbox, agent reads overnight, you wake up to 3 drafts and a clean feed.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Advanced | Full day | Node.js or Python, Anthropic API, Gmail API, OAuth |

## What you'll build

An agent that runs while you sleep. It reads your Gmail inbox, classifies what matters vs what doesn't, drafts replies in your voice for the 3 most important emails, and presents you a clean morning view (drafts ready to send, low-priority items archived, decisions surfaced).

You wake up to a triaged inbox instead of starting your day buried.

## What you'll learn

- Gmail API authentication (OAuth flow, refresh tokens)
- Email classification with Claude (urgency, type, action required)
- Drafting in your voice (similar pattern to project #4)
- Building an agent loop: read → classify → draft → present
- Real-world API integration with real-world stakes

This is the hardest project in vol 2. It touches OAuth (annoying), real user data (sensitive), and voice-matching (subjective). Worth doing.

## Prerequisites

- Node.js 18+ or Python 3.10+
- An Anthropic API key
- A Google Cloud Console account
- A Gmail account you're willing to let an agent read (start with a test account)
- Comfort with OAuth flows and API token management
- A `voice.md` similar to project #4 (your reply voice can be different from your content voice)

## How it works

```
schedule trigger (cron, 5am daily)
    ↓
Gmail API: fetch unread emails from the last 24 hours
    ↓
for each email:
   Claude call: classify (priority, category, action_required, should_draft_reply)
    ↓
for emails with should_draft_reply = true:
   Claude call: draft a reply in user's voice
    ↓
   Gmail API: save draft (so user can edit/send from Gmail directly)
    ↓
Claude call: synthesize morning summary
    ↓
write summary to ./output/{date}.md
    ↓
optionally: send summary to Slack DM or push notification
```

The agent doesn't auto-send. It only drafts. Human review is mandatory.

## Build it

### Step 1: Set up Gmail API access

This is the most painful step. Block 30-60 minutes for it.

1. Go to [Google Cloud Console](https://console.cloud.google.com), create a new project
2. Enable the Gmail API for the project
3. Create OAuth credentials (desktop app type)
4. Download the credentials JSON, save it locally as `credentials.json`
5. The first time you run your script, it will open a browser for OAuth consent. Grant access. The script saves a refresh token so future runs don't need browser interaction.

Test by writing a script that just lists the subjects of your last 5 unread emails. If that works, the auth layer is done.

### Step 2: Scaffold

Make a new project. Install:

- The Gmail API client (`googleapis` for Node, `google-api-python-client` for Python)
- The Anthropic SDK
- A scheduler if you're not using cron (`node-cron` or similar)

Set up `.env` with `ANTHROPIC_API_KEY` and Google credentials path.

### Step 3: Build the email fetcher

Write a function `fetchUnread()` that:

1. Authenticates with Gmail (using the saved refresh token)
2. Fetches unread emails from the last 24 hours
3. Returns each email as `{from, subject, date, body}`

Cap body length at ~4000 chars to stay within Claude's context limits.

### Step 4: Build the classifier

Write a function `classifyEmail(email)` that:

1. Calls Claude with the prompt from `prompts.md` Step 1
2. Returns the parsed classification JSON

Test on 10 different emails. Sanity-check the priorities. If newsletters are getting marked "critical," tighten the prompt with examples.

### Step 5: Build the draft generator

Write a function `draftReply(email, voice)` that:

1. Calls Claude with the prompt from `prompts.md` Step 2
2. Returns the draft email body as a string

Test by drafting replies for 3-5 real emails. Check that the voice matches yours and that the drafts address what the sender actually asked.

### Step 6: Build the Gmail draft saver

Write a function `saveDraft(originalEmail, replyBody)` that uses the Gmail API to:

1. Create a draft reply (with the right `In-Reply-To` headers so it threads correctly)
2. Save it to the user's Drafts folder

Test by checking Gmail for the saved draft.

### Step 7: Build the morning summary

Write a function `generateSummary(classifications, drafts)` that:

1. Calls Claude with the prompt from `prompts.md` Step 3
2. Returns the morning summary as markdown

Write the summary to `./output/{date}.md`. Optionally pipe to Slack or push notification.

### Step 8: Wire it all together

Main function:

```
emails = fetchUnread()
classifications = parallel(classifyEmail for email in emails)
drafts = parallel(draftReply for emails where should_draft_reply)
for draft in drafts: saveDraft to Gmail
summary = generateSummary(classifications, drafts)
write summary to disk
```

### Step 9: Schedule it

Cron at 5am daily, or GitHub Actions on a schedule. Logs go to `./logs/`.

Run for 3 mornings. Tune the classification thresholds and draft voice based on what you'd actually edit before sending.

## The prompts

Classification, drafting, and summary prompts are in [`prompts.md`](prompts.md).

## Verify it works

- [ ] OAuth flow completes and the refresh token persists between runs
- [ ] `fetchUnread()` returns clean email objects
- [ ] Classifications match your gut sense for priority
- [ ] Drafts sound like you, not like a generic assistant
- [ ] Drafts thread correctly in Gmail (replies show under the original)
- [ ] Morning summary surfaces what actually mattered, not noise

## Extend it

- Add a "snooze" classification (emails to handle later in the week)
- Auto-reply to obvious low-stakes emails (ones you'd send a one-liner to)
- Surface "this person hasn't heard back from you in 2 weeks" reminders
- Tag emails with categories (client, family, newsletter, recruiting) and route differently
- Add Slack delivery for the morning summary
- Track which drafts you actually sent vs edited heavily, feed that back into voice.md

## Privacy note

This agent reads your inbox. The tradeoff is yours to make. Recommendations:

- Run it on a test/secondary Gmail account first until you trust the behavior
- Limit to a specific Gmail label if you want a smaller blast radius
- Never store full email content in logs that get committed to git
- Use a `.gitignore` that catches `output/`, `logs/`, `credentials.json`, `token.json`

## Common pitfalls

- **OAuth flow fails**: usually the credentials JSON has the wrong app type. It must be "Desktop app," not "Web application."
- **Drafts don't thread**: missing `In-Reply-To` and `References` headers. Get them from the original email's headers.
- **Classifications drift**: emails from specific senders (clients) should always be high priority. Add explicit rules in the Step 1 prompt.
- **Drafts feel generic**: voice.md isn't doing enough work. Add 5-10 examples of replies you actually sent.
- **API rate limits**: Gmail and Anthropic both have limits. Add a small delay (200ms) between calls if you process a lot of emails.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
