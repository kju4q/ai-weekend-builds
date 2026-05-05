# Prompts: Screenshot to Code

The exact prompts that drive each step of the build. Tweak them for your stack and style.

## Step 1: Vision read (parse the UI)

```
You are looking at a UI screenshot. Your job is to describe the structure, not the styling.

Output a JSON description with this shape:
{
  "layout": "single-column" | "two-column" | "grid" | "centered",
  "components": [
    {
      "type": "header" | "hero" | "card" | "button" | "input" | "list" | "footer",
      "content": "the visible text",
      "children": [] // nested components if any
    }
  ]
}

Rules:
- Identify only what you can see clearly. Don't guess at hidden state.
- Use the smallest accurate type. A "Sign up" element is a button, not a form.
- Skip decorative elements that don't have semantic meaning.
- If text is too small or blurry, return "[unclear]".

Image attached.
```

## Step 2: Code generation (JSON to React)

```
You are a React engineer. Given this JSON description of a UI, generate a working React component.

JSON:
{paste step 1 output}

Requirements:
- TypeScript
- Tailwind classes for styling (no inline styles)
- Functional component, default export
- No external dependencies beyond React
- Realistic placeholder content where the JSON says "[unclear]"
- Accessible: semantic HTML, alt text, aria labels where needed

Return ONLY the component code. No explanation, no markdown fence.
```

## Step 3: Validation

```
Here is a generated React component:

{paste step 2 output}

Check for:
1. Syntax errors that would prevent compilation
2. Hooks used outside of components
3. Missing imports
4. Accessibility issues that block screen readers
5. Type errors that TypeScript would catch

If anything is wrong, return:
ISSUES:
- issue 1
- issue 2

If nothing is wrong, return: OK
```

## Notes on tuning

- If components look too generic, add an example component to the Step 2 prompt as "match this style."
- If layouts are wrong, add a sketch description to Step 1 ("the header is fixed at top, hero is full-width below").
- If validation misses things, add specific rules ("never use class= without className=" etc.).

The chain is: image → JSON → code → validation → final output. Each step is a single Claude call.
