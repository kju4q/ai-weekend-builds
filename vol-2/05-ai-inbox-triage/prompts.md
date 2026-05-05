# Prompts: AI Inbox Triage

## Step 1: Classify a single email

```
You are triaging emails for a builder. Classify this one.

Email:
From: {sender}
Subject: {subject}
Date: {date}
Body:
{body, max 4000 chars}

Output JSON:
{
  "priority": "critical" | "important" | "normal" | "low" | "spam",
  "category": "client" | "team" | "personal" | "newsletter" | "transactional" | "recruiting" | "other",
  "action_required": "reply" | "decision" | "review" | "none",
  "urgency_window": "today" | "this_week" | "no_rush",
  "summary": "1-2 sentence summary of what they want, in plain language",
  "decision_needed": "if action_required is decision, what's the decision",
  "should_draft_reply": boolean
}

Rules:
- "critical" is reserved for actual emergencies (revenue at risk, deadline today, security issue). Use sparingly.
- Newsletters and transactional emails are almost always "low" priority.
- If the email is asking yes/no, action_required is "decision."
- "should_draft_reply" is true only if a reply is expected AND would benefit from a draft (not a one-line yes/no the user can fire off).
```

## Step 2: Draft a reply

```
You are drafting a reply email for the user.

Original email:
From: {sender}
Subject: {subject}
Body:
{body}

User's voice (from voice.md):
{paste voice.md}

Rules:
- Match the user's voice. No em dashes. Short paragraphs. Direct.
- Address what the sender actually asked. Don't pad.
- If the email needs a decision the user has to make, write the reply assuming the user will edit the decision in. Mark the placeholder with [DECISION: ...]
- No "Hope this finds you well" or similar opener. Get to the point.
- No "Let me know if you have any questions" closer. End on the substance.
- Sign off: just the user's first name.
- 50-150 words unless the original demands more.

Output ONLY the email body. No subject line, no commentary.
```

## Step 3: Morning summary

```
You have classifications and drafts for today's inbox. Generate the morning summary.

Classifications:
{paste step 1 outputs for all emails}

Drafts:
{paste step 2 outputs for the ones that were drafted}

Output the summary as markdown:

# Inbox triage: {today's date}

## Drafts ready ({count})

For each: a 1-line "what they're asking" + the draft + the link to edit in Gmail.

## Decisions needed ({count})

For each: the decision question, the deadline, and your recommendation if the email gives enough context to form one.

## Worth reading ({count})

Important newsletters or threads, with 1-line summaries.

## Archived ({count})

A count, not a list. Filtered out as low priority.

## Stats

- Total processed: X
- Drafts written: X
- Decisions surfaced: X
- Time saved estimate: X minutes
```

## Notes on tuning

- The biggest leverage is voice.md. Without good voice examples, drafts feel generic.
- Re-classify if priorities feel off. Add specific examples to step 1 ("an email from {client name} about an active contract is always 'critical'").
- The "should_draft_reply" decision is conservative by default. Loosen if you want drafts for more emails.
- Don't auto-send. Always require human review before any draft becomes a sent email. The cost of a bad agent reply is too high.

The chain runs: fetch unread emails → classify each in parallel → draft for the qualifying ones in parallel → synthesize summary. End-to-end takes 2-5 minutes for a typical inbox.
