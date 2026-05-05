# Prompts: Auto-Skill Builder

## Step 1: Detect corrections

```
You are reviewing a chat between a user and Claude. Find every moment where the user corrects Claude's output.

A "correction" is any message where the user:
- Tells Claude to redo something differently
- Names something Claude did wrong (style, tone, format, structure, facts)
- Asks for less of something (shorter, fewer options, no preamble)
- Asks for more of something (more detail, examples, alternatives)
- Bans a phrase or pattern ("don't say...", "stop using...")

Output JSON:
[
  {
    "user_message": "the exact text",
    "preceding_claude_output": "what Claude said that triggered the correction (1-2 sentences)",
    "correction_type": "style" | "tone" | "format" | "structure" | "factual" | "scope",
    "rule": "the rule extracted in the user's voice"
  }
]

Skip messages that aren't corrections (new questions, follow-ups, agreements).

Chat:
{paste the chat export here}
```

## Step 2: Cluster corrections into rules

```
You have a list of corrections from a chat. Cluster them into reusable rules.

Corrections:
{paste step 1 output}

For each cluster, output:
{
  "rule": "the rule, written as an instruction Claude can follow",
  "examples": ["specific instance 1", "specific instance 2"],
  "frequency": number_of_times_user_made_this_correction
}

Rules:
- Merge similar corrections (e.g., "shorter" + "be more concise" + "trim that down" = one rule)
- Use the user's actual words where possible
- Don't invent rules that weren't actually corrected for
- Order by frequency descending

Output JSON.
```

## Step 3: Generate skill file

```
You have a list of clustered rules from a user's chat history. Generate a Claude skill file.

Rules:
{paste step 2 output}

Output a skill file in this exact format:

---
name: {short-kebab-case-name based on the strongest rule}
description: >
  {one-sentence description of when to apply this skill, in third person}
---

# {Title in plain English}

## How to behave

{Bulleted list of rules, in second person ("Don't use em dashes" not "User dislikes em dashes")}

## Examples of corrections this skill prevents

{Cite 3-5 specific examples from the rules' "examples" arrays, lightly cleaned}

## Notes

{Anything about edge cases or rule precedence}

Rules:
- The skill name should reflect the dominant pattern
- Frequency 1 corrections go in "Notes" not "How to behave" (single corrections aren't habits)
- The description triggers when the skill should load. Be specific.
- Don't editorialize. The user's corrections are the source of truth.
```

## Notes on tuning

- If the skill files miss the user's voice, add to step 3: "Use the user's exact phrasing where possible. Don't paraphrase."
- If too many trivial corrections become rules, raise the frequency threshold (only frequency >= 3 makes it into "How to behave").
- If the same rule appears across multiple chats, merge skill files manually and add a `version` field to track evolution.

The chain is: chat → corrections → clusters → skill file. Run on each new chat, append findings to existing skills.
