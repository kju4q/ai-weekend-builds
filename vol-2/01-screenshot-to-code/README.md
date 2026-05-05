# 01: Screenshot to Code

Take a photo of any UI, get back a working React component.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Easy | 2-4 hours | Node.js, Anthropic API, React |

## What you'll build

A small CLI tool that takes an image (a photo of a website, an app screenshot, a Figma export) and returns a working React component matching the layout. You drop in an image, run a command, get back JSX you can paste into a project.

## What you'll learn

- How vision models read interfaces and what they're good vs bad at
- Chaining a vision call with a code-generation call so the output is structured, not freeform
- Validating AI-generated code before trusting it
- The pattern that replaces the design-to-code handoff that costs companies millions

## Prerequisites

- Node.js 18 or later, or Python 3.10 or later (your call)
- An Anthropic API key
- Comfort with async functions and reading API docs
- Recognition of valid JSX (you don't need to be a React expert)

## How it works

```
image file
    ↓
Claude vision call (image → structured JSON description)
    ↓
Claude code-gen call (JSON → React component)
    ↓
Validation call (catch syntax/accessibility issues)
    ↓
final component file written to disk
```

Three Claude calls in a chain. Each one has a single, focused job. The output of one is the input to the next.

## Build it

### Step 1: Scaffold a project

Make a new project folder. Install:

- The Anthropic SDK for your language (Node or Python)
- A way to load environment variables (dotenv for Node, python-dotenv for Python)
- A way to read images as base64 (built-in for both languages)

Set up a `.env` with your `ANTHROPIC_API_KEY`.

You don't need a UI yet. This is a CLI that reads a file, calls APIs, writes a file.

### Step 2: Get the vision call working

Write a function `describeUI(imagePath)` that:

1. Reads the image as base64
2. Sends it to Claude with the prompt from `prompts.md` Step 1
3. Returns the parsed JSON description

Test it with one screenshot. Print the result. If the JSON describes the UI accurately, you're past the hardest part.

**Common pitfall**: image size. Claude has limits. If your image is over 8000 pixels on either side, resize it first.

### Step 3: Get the code-gen call working

Write a function `generateComponent(jsonDescription)` that:

1. Takes the JSON from Step 2
2. Sends it to Claude with the prompt from `prompts.md` Step 2
3. Returns the generated React code as a string

Test by piping Step 2's output into Step 3. The output should be a valid component.

**Common pitfall**: Claude might wrap the code in markdown fences (```jsx ... ```). Strip them before saving.

### Step 4: Add validation

Write a function `validateComponent(code)` that:

1. Sends the code to Claude with the prompt from `prompts.md` Step 3
2. Returns either "OK" or a list of issues

If it returns issues, decide whether to retry the code-gen with the issues fed back, or surface them to the user.

### Step 5: Wire it into a CLI

Make `screenshot-to-code path/to/image.png` work end to end. Output goes to `./output/Component.tsx`.

Test with 3 different screenshots. If all 3 produce usable components, ship it.

## The prompts

The exact prompts for each step are in [`prompts.md`](prompts.md). Copy them, tune them for your stack and style.

## Verify it works

- [ ] Step 2 returns parseable JSON for a simple UI
- [ ] Step 3 returns valid JSX for that JSON
- [ ] Step 4 catches obvious syntax errors
- [ ] Running the CLI on a real screenshot writes a usable component

## Extend it

- Support multiple components per screenshot (header, hero, cards as separate files)
- Generate Tailwind classes that match the screenshot's spacing and colors
- Watch mode: any new screenshot in `./incoming/` automatically gets converted
- Wire it into Figma so designs get committed as PRs

## Common pitfalls

- **Image too large**: resize to 2048x2048 max before sending
- **Markdown fences in output**: strip them before saving the file
- **Hallucinated components**: if Step 3 invents elements not in the JSON, tighten Step 2's "describe only what you see" rule
- **Inconsistent style across runs**: add a style example to Step 2's prompt so Claude has an anchor

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
