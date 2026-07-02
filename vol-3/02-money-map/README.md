# 02: Money Map

Export your bank statement as a CSV, run one command, and get a clear map of
where the money actually went: categories, totals, the subscriptions you forgot
about, and the top 3 changes that would matter. Runs on your machine, on your CSV.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Easy-Medium | 3-5 hours | Python (standard library), Anthropic API (optional) |

## What you'll build

A local script that reads a bank CSV, classifies every transaction, detects
recurring charges (flagging the ones that look forgotten), and writes a clean
report as both markdown and a small HTML page with bar charts. No spreadsheet,
no signing your bank data into someone else's dashboard.

## What you'll learn

- Parsing messy real-world data: bank CSVs are inconsistent and human-written
- Classification two ways: fast local rules vs. an LLM for the long tail
- Normalizing merchant names (`STARBUCKS #5567` and `STARBUCKS #212` are one thing)
- Detecting recurring charges across months — the core of subscription-catching
- Turning numbers into a report a human actually reads

## Prerequisites

- Python 3.10+ (no pip installs required for the local path)
- A bank statement CSV. The repo ships a fake `sample-statement.csv` to start.
- Optional: an Anthropic API key for AI-written advice and edge-case classification

## Local vs API

| Part | Runs where |
|---|---|
| Parsing the CSV | 100% local |
| Categorizing transactions (rules) | 100% local |
| Detecting recurring subscriptions | 100% local |
| Report (markdown + HTML chart) | 100% local |
| "Top 3 changes" advice with `--ai` | Claude API (only if you pass `--ai` **and** set a key) |

Without `--ai`, your financial data never leaves the machine — not one byte.

## How it works

```
bank.csv
   ↓  parse (csv module)
transactions
   ↓  categorize (keyword rules, or Claude for the long tail)
   ↓  normalize merchants + group by month  →  detect recurring
   ↓  summarize totals per category
report.md  +  report.html
```

## Build it

### Step 1: Run it on the sample

```
python money_map.py sample-statement.csv
open report.html      # (or just read report.md)
```

You'll see categories with bar charts, a recurring-charges list with two items
flagged ⚠️ likely forgotten, and three concrete suggestions.

### Step 2: Read the categorizer

`categorize()` is a dictionary of keyword → category. This is deliberately simple
and fast. Add your own merchants — your bank's descriptions are different from the
sample's. This rule table is where you'll spend most of your tuning time.

### Step 3: Understand recurring detection

`detect_recurring()` normalizes each description to a merchant (stripping store
numbers), groups by merchant, and flags anything that appears in 2+ different
months. That's how you catch the $39.99 gym you stopped going to.

### Step 4: Point it at your real statement

Export a CSV from your bank. Most have `Date, Description, Amount` columns (with
spending as negative numbers). If your columns differ, adjust `load()`. Rerun.

### Step 5: Turn on AI advice (optional)

```
export ANTHROPIC_API_KEY=sk-ant-...
python money_map.py sample-statement.csv --ai
```

Now the "top 3 changes" section is written by Claude looking at the whole
statement, which catches patterns the local rules don't.

## Verify it works

- [ ] `python money_map.py sample-statement.csv` prints an income/spent/net line
- [ ] `report.md` lists categories sorted by total with bar charts
- [ ] The gym and Adobe show up as ⚠️ likely forgotten
- [ ] `report.html` opens in a browser and shows the bars

## Extend it

- Detect a subscription's *price increase* over time (Netflix went up — by how much?)
- Add month-over-month comparison ("takeout doubled vs last month")
- Support multiple accounts / multiple CSVs merged into one map
- Draw a real pie/line chart with a small JS charting library in the HTML
- Add a budget: color categories red when they exceed a target you set

## Common pitfalls

- **Sign convention**: some banks use positive for spending. Check one row and
  flip the logic in `load()`/`summarize()` if needed.
- **Everything is "Uncategorized"**: your bank's descriptions don't match the
  sample's keywords. Add your merchants to `RULES` — that's expected work.
- **Recurring list is noisy**: groceries appear because you shop monthly. That's
  correct; the ⚠️ flag is what points at the *forgotten* ones.
- **Sending data to AI by accident**: it only happens with `--ai`. The default is
  fully local.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
