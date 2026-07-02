# Prompts: Money Map

The local path uses no prompts — it's rules and arithmetic. These prompts power
the optional `--ai` path and are worth building even if you start with rules.

## Prompt 1: Classify the long tail

Use this for transactions your keyword rules left as "Uncategorized".

```
You are categorizing bank transactions. For each description, return the single
best category from this fixed list:
Groceries, Coffee & snacks, Takeout & delivery, Transport, Travel, Subscriptions,
Utilities, Housing, Health, Shopping, Income, Other.

Rules:
- Return ONLY valid JSON: [{"description": "...", "category": "..."}]
- Use "Other" only when nothing else fits.
- A recurring digital charge (streaming, software, gym) is "Subscriptions".

Transactions:
{paste the uncategorized descriptions, one per line}
```

## Prompt 2: Top 3 changes that would matter

This is the one wired into `--ai` in `money_map.py`.

```
Here is a bank statement (negative = spending):
{all transactions, one per line}

Give exactly the top 3 changes that would most improve this person's finances.
Be specific with dollar amounts. One line each, no preamble.
```

## Why the fixed category list matters

If you don't pin the categories, Claude invents new ones every run ("Dining",
"Restaurants", "Eating Out") and your totals scatter across near-duplicates.
A fixed list keeps the map stable month to month so you can compare.

## Tuning

- **Categories drift anyway**: add "Do not invent categories outside the list."
- **Advice is generic**: add "Reference specific merchants and amounts from the
  data. No advice that would apply to anyone."
- **Want it blunter**: add "Be direct. This person can handle honesty about waste."
- **JSON breaks**: add "Return only the JSON array, no markdown fence, no prose."

## A note on privacy

Prompt 2 sends your whole statement to the API. If that's more than you want to
share, use Prompt 1 only (just the merchant strings, no amounts) — or stay on the
fully local rule-based path, which is the default.
