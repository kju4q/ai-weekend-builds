# 03: Auto-Skill Builder

Correct Claude during a session, hit one command, get a skill file. AI compounds instead of starting from scratch every time.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 4-6 hours | Node.js or Python, Anthropic API, Claude.ai or Claude Code chat history |

## What you'll build

A tool that reads your Claude conversations (exported JSON or live Claude Code session), finds every correction you made ("no, shorter," "use TypeScript not JavaScript," "skip the explanation"), extracts the patterns, and writes a Claude skill file you can drop into `.claude/skills/` so the corrections become permanent.

You stop correcting Claude the same way three times. Every correction compounds.

## What you'll learn

- How to extract structured rules from unstructured chat history
- The Claude skill file format (frontmatter + markdown instructions)
- Detecting "this is a correction" vs "this is a new question" using AI classification
- Clustering similar corrections into reusable rules
- Why this is the most important compounding loop in your AI workflow

## Prerequisites

- Node.js 18+ or Python 3.10+
- An Anthropic API key
- A Claude.ai chat export OR access to Claude Code's chat history files
- Comfort reading and writing JSON
- Familiarity with the Claude skill file format (see [Anthropic's docs](https://docs.anthropic.com))

## How it works

```
chat history (Claude.ai export JSON or Claude Code session log)
    ↓
Claude call per chat: detect corrections (Step 1)
    ↓
Claude call: cluster similar corrections into rules (Step 2)
    ↓
Claude call: format clusters as a Claude skill file (Step 3)
    ↓
write the skill file to .claude/skills/{name}.md
```

The hard part is the classification. Most user messages aren't corrections. The trick is teaching Claude what counts as a correction.

## Build it

### Step 1: Scaffold

Make a new project. Install:

- The Anthropic SDK
- A JSON parser (built-in for both languages)
- A file-system library to write skill files

Set up `.env` with `ANTHROPIC_API_KEY`.

### Step 2: Get a chat to work with

Two options:

- **Claude.ai**: export a chat as JSON (Settings → Export data). You get a JSON file with the full conversation.
- **Claude Code**: chat history lives in a known location on disk (varies by OS). You can read the JSON files directly.

Pick one. Get a working test fixture loaded into memory.

### Step 3: Build the correction detector

Write a function `detectCorrections(chat)` that:

1. Calls Claude with the prompt from `prompts.md` Step 1
2. Passes the full chat content
3. Returns a parsed JSON array of corrections

Test it on a chat where you remember making corrections. Verify Claude finds them. If it misses some, look at the prompt and add specific examples of what counts as a correction.

**Common pitfall**: long chats blow the context window. Chunk the chat into segments of 30-50 messages, process each, merge results.

### Step 4: Build the clusterer

Write a function `clusterCorrections(corrections)` that:

1. Calls Claude with the prompt from `prompts.md` Step 2
2. Returns a parsed JSON array of clustered rules

Each rule has a frequency count (how many times this correction appeared). Order by frequency descending.

### Step 5: Build the skill file generator

Write a function `generateSkillFile(clusteredRules)` that:

1. Calls Claude with the prompt from `prompts.md` Step 3
2. Returns a string in the Claude skill file format

The skill file has YAML frontmatter (`name`, `description`) and markdown instructions.

### Step 6: Wire it together

Make a CLI that takes a chat file path, runs Steps 3-5, writes the skill file to `./output/skills/{name}.md`.

Test on 2-3 different chats. Verify the skill files capture real patterns from each one.

### Step 7: Install and test the skill

Drop the generated skill file into `.claude/skills/` in your repo. Open Claude Code or Claude.ai with that repo. Start a new chat. Verify Claude follows the skill's rules.

If Claude doesn't follow them, the skill description (which controls when the skill loads) might be wrong. Iterate on Step 3's prompt.

## The prompts

The detection, clustering, and skill-file generation prompts are in [`prompts.md`](prompts.md).

## Verify it works

- [ ] Step 3 finds the corrections you remember making
- [ ] Step 4 doesn't duplicate similar corrections as separate rules
- [ ] Step 5 produces a valid Claude skill file (loads without errors)
- [ ] The skill actually changes Claude's behavior in a new chat

## Extend it

- Detect contradictions between corrections ("I said X, then later said not-X") and surface them
- Auto-merge new corrections into an existing skill file instead of creating new ones
- Add a CLI to review and approve corrections before they get written
- Track which corrections actually stuck vs which ones Claude still violates after the skill is loaded
- Run on a watch mode against active Claude Code sessions

## Common pitfalls

- **Detecting too many corrections**: tighten the definition. A new question isn't a correction. A clarification of scope might or might not be.
- **Detecting too few**: add specific examples to the Step 1 prompt of what counts ("messages starting with 'no,', 'actually,', 'don't', 'stop' are usually corrections")
- **Skill files too long**: cap "How to behave" rules at 10 max. Move the rest to "Notes."
- **The skill loads at the wrong time**: the description triggers loading. Make it specific to the use case ("when reviewing code in TypeScript" not "when coding").

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
