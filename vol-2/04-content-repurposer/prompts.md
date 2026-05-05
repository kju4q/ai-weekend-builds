# Prompts: Content Repurposer

## Shared context (sent to every platform call)

```
You are repurposing one piece of content into a platform-native version.

Source content:
{paste source}

Voice rules (from voice.md):
{paste voice.md}

Hard rules (never violate):
- No em dashes
- No double dashes
- No "Here's the X you requested" openings
- No "Let me know if anything else" closings
- Never repeat the script exactly across platforms
- Every output must have a specific concrete takeaway
```

## Platform call: Instagram

```
{shared context}

Generate an Instagram caption for this content.

Constraints:
- Lowercase, short paragraphs, line breaks for breathing room
- 600-800 characters max
- 2-3 hashtags at the end (only if relevant)
- Last line is the CTA (comment a keyword for a lead magnet, or directs to bio)
- Different angle from any video script. Captions never repeat the script verbatim.

Output ONLY the caption text. No commentary.
```

## Platform call: TikTok

```
{shared context}

Generate a TikTok caption for this content.

Constraints:
- Lowercase, conversational, hook in the first line
- 600-800 characters max
- 2-3 hashtags at the end
- Different angle from any video script
- Last line is the CTA

Output ONLY the caption text. No commentary.

(Note: Instagram and TikTok captions can be identical if the content is general. Only differentiate if one platform needs a different angle.)
```

## Platform call: X

```
{shared context}

Generate an X post or thread for this content.

Constraints:
- Sharp, opinionated, builder voice
- Single tweet (under 280 chars) for hot takes
- Thread (2-6 tweets) for deeper content. Separate tweets with "---" on its own line.
- No hashtags unless trending
- The first tweet must be the hook. Don't bury it.

Output ONLY the post or thread. No commentary.
```

## Platform call: LinkedIn

```
{shared context}

Generate a LinkedIn post for this content.

Constraints:
- First line is the hook before the "see more" cut. It must earn the click.
- Personal story + insight format
- Professional framing but not corporate
- 1200-2000 characters
- Hashtags at the end (3-5, professional ones)
- Capital letters and full sentences (not the lowercase IG/TikTok style)

Output ONLY the post. No commentary.
```

## Platform call: YouTube description

```
{shared context}

Generate a YouTube video title and description for this content.

Title constraints:
- Specific, SEO-aware
- Under 70 characters
- Promises a clear takeaway
- Numbers and names beat abstractions

Description constraints:
- 150-300 words
- First 2 lines are the hook (the part visible above the "Show more" fold)
- Include keywords that match what people search for
- End with the CTA (newsletter, follow, etc.)
- Add timestamps if applicable

Output as:
TITLE: {title}

DESCRIPTION:
{description}
```

## Platform call: Newsletter

```
{shared context}

Generate a newsletter version of this content.

Constraints:
- Smart-friend register, not corporate
- 400-700 words
- Personal asides welcome
- One specific takeaway in the closing line
- Subject line at top: 60 chars max, the most important thing from this issue

Output as:
SUBJECT: {subject line}

BODY:
{body}
```

## Notes on tuning

- The voice.md file does the heavy lifting. Spend time on it.
- Run all platform calls in parallel for speed.
- Add a "review" step that flags any output that broke the hard rules. Re-run the bad ones.
- If a platform's output keeps drifting from your voice, add 3-5 more examples to voice.md from that specific platform.
