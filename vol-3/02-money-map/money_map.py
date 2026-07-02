"""Money Map — turn a bank CSV into a spending map.

    python money_map.py sample-statement.csv

Produces:
  report.md   — categories, totals, recurring subscriptions, top 3 changes
  report.html — the same, with simple inline bar charts (open in a browser)

Classification uses fast local rules by default. Add --ai (and an
ANTHROPIC_API_KEY) to let Claude classify anything the rules missed and write
the "top 3 changes that would matter" section. It runs fully locally otherwise.
Nothing is uploaded unless you pass --ai.
"""

from __future__ import annotations

import argparse
import csv
import html
import os
import re
from collections import defaultdict

# Local, rule-based categorizer. Keyword (lowercased substring) -> category.
RULES = {
    "trader joes": "Groceries", "whole foods": "Groceries", "safeway": "Groceries",
    "starbucks": "Coffee & snacks", "doordash": "Takeout & delivery",
    "ubereats": "Takeout & delivery", "uber": "Transport", "shell": "Transport",
    "delta air": "Travel", "netflix": "Subscriptions", "spotify": "Subscriptions",
    "adobe": "Subscriptions", "apple.com": "Subscriptions", "planet fitness": "Subscriptions",
    "old gym": "Subscriptions", "comcast": "Utilities", "xfinity": "Utilities",
    "pg&e": "Utilities", "rent": "Housing", "cvs": "Health", "pharmacy": "Health",
    "amazon": "Shopping", "payroll": "Income", "direct dep": "Income",
}


def categorize(desc: str) -> str:
    d = desc.lower()
    for key, cat in RULES.items():
        if key in d:
            return cat
    return "Uncategorized"


def merchant_key(desc: str) -> str:
    """Normalize a description to a merchant name (strip store #s, digits)."""
    d = re.sub(r"#?\d+", "", desc.lower())
    return re.sub(r"\s+", " ", d).strip()


def load(path: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r = {k.strip().lower(): (v or "").strip() for k, v in r.items()}
            r["amount"] = float(r["amount"])
            rows.append(r)
    return rows


def detect_recurring(rows: list[dict]) -> list[dict]:
    """A charge is 'recurring' if the same merchant is billed a similar amount
    in 2+ different months. Flags likely-forgotten ones (gym/subscription-ish)."""
    by_merchant = defaultdict(list)
    for r in rows:
        if r["amount"] < 0:
            by_merchant[merchant_key(r["description"])].append(r)
    recurring = []
    for merchant, txns in by_merchant.items():
        months = {t["date"][:7] for t in txns}
        if len(months) >= 2:
            amounts = [-t["amount"] for t in txns]
            avg = sum(amounts) / len(amounts)
            forgotten = any(w in merchant for w in ("old", "gym", "adobe", "apple.com"))
            recurring.append({
                "merchant": merchant.title().strip(),
                "months": len(months),
                "avg": avg,
                "monthly_cost": avg,
                "flag": forgotten,
            })
    return sorted(recurring, key=lambda x: x["monthly_cost"], reverse=True)


def summarize(rows: list[dict]) -> dict:
    cats = defaultdict(float)
    for r in rows:
        if r["amount"] < 0:
            cats[categorize(r["description"])] += -r["amount"]
    income = sum(r["amount"] for r in rows if r["amount"] > 0)
    spent = sum(-r["amount"] for r in rows if r["amount"] < 0)
    return {
        "categories": dict(sorted(cats.items(), key=lambda x: x[1], reverse=True)),
        "income": income, "spent": spent, "net": income - spent,
    }


def top_changes_local(summary: dict, recurring: list[dict]) -> list[str]:
    tips = []
    forgotten = [r for r in recurring if r["flag"]]
    if forgotten:
        total = sum(r["monthly_cost"] for r in forgotten)
        names = ", ".join(r["merchant"] for r in forgotten)
        tips.append(f"Cancel likely-forgotten subscriptions ({names}) to save ~${total:,.0f}/mo.")
    cats = summary["categories"]
    for name in ("Coffee & snacks", "Takeout & delivery"):
        if cats.get(name, 0) > 60:
            tips.append(f"{name} is ${cats[name]:,.0f} over this period — a clear, easy lever.")
    if summary["net"] < 0:
        tips.append(f"You spent ${-summary['net']:,.0f} more than you earned — trim the top category first.")
    return (tips or ["Spending looks balanced — keep an eye on the top category."])[:3]


def top_changes_ai(rows, summary, recurring) -> list[str]:
    import anthropic

    lines = [f"{r['date']} {r['description']} {r['amount']}" for r in rows]
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=400,
        messages=[{"role": "user", "content": (
            "Here is a bank statement (negative = spending):\n" + "\n".join(lines) +
            "\n\nGive exactly the top 3 changes that would most improve this person's "
            "finances. Be specific with dollar amounts. One line each, no preamble."
        )}],
    )
    text = msg.content[0].text
    return [l.strip("-* ").strip() for l in text.splitlines() if l.strip()][:3]


def bar(value: float, maximum: float, width: int = 30) -> str:
    n = int((value / maximum) * width) if maximum else 0
    return "█" * n


def render_md(summary, recurring, changes) -> str:
    m = ["# Money Map\n", f"**Income:** ${summary['income']:,.2f}  ",
         f"**Spent:** ${summary['spent']:,.2f}  ",
         f"**Net:** ${summary['net']:,.2f}\n", "## Where it went\n"]
    mx = max(summary["categories"].values(), default=1)
    for cat, amt in summary["categories"].items():
        m.append(f"- `{bar(amt, mx):<30}` **{cat}** — ${amt:,.2f}")
    m.append("\n## Recurring / subscriptions\n")
    for r in recurring:
        flag = "  ⚠️ likely forgotten" if r["flag"] else ""
        m.append(f"- **{r['merchant']}** — ~${r['monthly_cost']:,.2f}/mo, seen in {r['months']} months{flag}")
    m.append("\n## Top 3 changes that would matter\n")
    for i, c in enumerate(changes, 1):
        m.append(f"{i}. {c}")
    return "\n".join(m) + "\n"


def render_html(summary, recurring, changes) -> str:
    mx = max(summary["categories"].values(), default=1)
    rows = ""
    for cat, amt in summary["categories"].items():
        pct = (amt / mx) * 100
        rows += (f'<div class="row"><span class="label">{html.escape(cat)}</span>'
                 f'<span class="track"><span class="fill" style="width:{pct:.0f}%"></span></span>'
                 f'<span class="amt">${amt:,.0f}</span></div>')
    subs = "".join(
        f'<li>{html.escape(r["merchant"])} — ~${r["monthly_cost"]:,.0f}/mo'
        f'{" <b>⚠ likely forgotten</b>" if r["flag"] else ""}</li>' for r in recurring)
    tips = "".join(f"<li>{html.escape(c)}</li>" for c in changes)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Money Map</title>
<style>
  body{{font:16px/1.5 -apple-system,system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 20px;color:#1f2430;background:#faf9f7}}
  h1{{font-weight:600}} h2{{margin-top:32px;color:#3a4252}}
  .stat{{display:inline-block;margin-right:24px}} .stat b{{font-size:1.4em}}
  .row{{display:flex;align-items:center;gap:12px;margin:6px 0}}
  .label{{width:150px}} .track{{flex:1;background:#eceae5;border-radius:6px;height:16px}}
  .fill{{display:block;height:100%;border-radius:6px;background:linear-gradient(90deg,#7c9cbf,#b08cc4)}}
  .amt{{width:80px;text-align:right;font-variant-numeric:tabular-nums}}
  li{{margin:4px 0}}
</style></head><body>
<h1>Money Map</h1>
<p><span class="stat">Income<br><b>${summary['income']:,.0f}</b></span>
   <span class="stat">Spent<br><b>${summary['spent']:,.0f}</b></span>
   <span class="stat">Net<br><b>${summary['net']:,.0f}</b></span></p>
<h2>Where it went</h2>{rows}
<h2>Recurring / subscriptions</h2><ul>{subs}</ul>
<h2>Top 3 changes that would matter</h2><ol>{tips}</ol>
</body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--ai", action="store_true", help="use Claude for the top-3 advice")
    args = ap.parse_args()

    rows = load(args.csv_path)
    summary = summarize(rows)
    recurring = detect_recurring(rows)

    if args.ai and os.getenv("ANTHROPIC_API_KEY"):
        try:
            changes = top_changes_ai(rows, summary, recurring)
        except Exception as e:
            print(f"(AI advice failed: {e}; using local rules)")
            changes = top_changes_local(summary, recurring)
    else:
        changes = top_changes_local(summary, recurring)

    with open("report.md", "w") as f:
        f.write(render_md(summary, recurring, changes))
    with open("report.html", "w") as f:
        f.write(render_html(summary, recurring, changes))
    print("Wrote report.md and report.html")
    print(f"Income ${summary['income']:,.0f} | Spent ${summary['spent']:,.0f} | "
          f"Net ${summary['net']:,.0f} | {len(recurring)} recurring merchants")


if __name__ == "__main__":
    main()
