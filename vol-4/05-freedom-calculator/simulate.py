"""Freedom Calculator: explore a year of stated assumptions, ten thousand times.

    python3 simulate.py sample-config.json --output sample-output

Reads a JSON config describing income, expenses, and a starting balance, samples
a sequence of months many times over, and summarizes the spread of outcomes.

Everything is local and deterministic for a given seed. There is no network call,
no external data source, no API key, and no model anywhere in this file. The only
inputs are the config you pass and the seed inside it.

What this is: a way to see how the range of simulated outcomes moves when you
change one of your own assumptions.

What this is not: a prediction, a plan, or financial advice. Every number it
prints describes the assumptions in the config file and nothing else.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
import pathlib
import random
import statistics
import sys

DISTRIBUTIONS = ("fixed", "normal", "uniform", "triangular")
PERCENTILES = (10, 25, 50, 75, 90)
HISTOGRAM_BINS = 40

DISCLAIMER = (
    "These results describe simulations from the assumptions in this file. "
    "They do not predict the future and are not financial advice."
)

NOT_MODELLED = (
    "detailed taxes",
    "inflation",
    "investment returns",
    "debt interest",
    "correlation between income and expenses",
    "currency changes",
    "unexpected events beyond the one-time expenses you configured",
    "behavioral changes, such as spending less during a thin month",
    "real market data of any kind",
)


class ConfigError(Exception):
    """Raised for anything wrong in the config. Never guesses a missing value."""


# ---------------------------------------------------------------- validation

def _number(value: object, field: str, *, minimum: float | None = None,
            allow_negative: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{field} must be a number, got {type(value).__name__}")
    number = float(value)
    if math.isnan(number) or math.isinf(number):
        raise ConfigError(f"{field} must be a finite number")
    if not allow_negative and number < 0:
        raise ConfigError(f"{field} cannot be negative, got {number:g}")
    if minimum is not None and number < minimum:
        raise ConfigError(f"{field} must be at least {minimum:g}, got {number:g}")
    return number


def _integer(value: object, field: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{field} must be a whole number, got {type(value).__name__}")
    if value < minimum:
        raise ConfigError(f"{field} must be at least {minimum}, got {value}")
    return value


def validate_amount(spec: object, field: str) -> dict:
    """Validate one money-per-month field.

    A plain number is shorthand for a fixed amount. An object names a
    distribution and its parameters. Anything else is an error, because a
    silently guessed distribution would quietly change every number downstream.
    """
    if isinstance(spec, (int, float)) and not isinstance(spec, bool):
        return {"distribution": "fixed",
                "amount": _number(spec, field, allow_negative=False)}
    if not isinstance(spec, dict):
        raise ConfigError(f"{field} must be a number or an object with a "
                          f"\"distribution\", got {type(spec).__name__}")

    dist = spec.get("distribution")
    if dist is None:
        raise ConfigError(f"{field}.distribution is required, one of "
                          f"{', '.join(DISTRIBUTIONS)}")
    if dist not in DISTRIBUTIONS:
        raise ConfigError(f"{field}.distribution {dist!r} is not supported, use one "
                          f"of {', '.join(DISTRIBUTIONS)}")

    out: dict = {"distribution": dist}
    if dist == "fixed":
        if "amount" not in spec:
            raise ConfigError(f"{field}.amount is required for a fixed distribution")
        out["amount"] = _number(spec["amount"], f"{field}.amount", allow_negative=False)
    elif dist == "normal":
        for key in ("mean", "sd"):
            if key not in spec:
                raise ConfigError(f"{field}.{key} is required for a normal distribution")
        out["mean"] = _number(spec["mean"], f"{field}.mean")
        out["sd"] = _number(spec["sd"], f"{field}.sd", allow_negative=False)
        if out["sd"] == 0:
            raise ConfigError(f"{field}.sd is 0, which is a fixed value. Use "
                              f"\"distribution\": \"fixed\" instead, so the config "
                              f"says what it means.")
    elif dist == "uniform":
        for key in ("low", "high"):
            if key not in spec:
                raise ConfigError(f"{field}.{key} is required for a uniform distribution")
        out["low"] = _number(spec["low"], f"{field}.low")
        out["high"] = _number(spec["high"], f"{field}.high")
        if out["low"] >= out["high"]:
            raise ConfigError(f"{field}.low ({out['low']:g}) must be less than "
                              f"{field}.high ({out['high']:g})")
    elif dist == "triangular":
        for key in ("low", "high"):
            if key not in spec:
                raise ConfigError(f"{field}.{key} is required for a triangular distribution")
        out["low"] = _number(spec["low"], f"{field}.low")
        out["high"] = _number(spec["high"], f"{field}.high")
        if out["low"] >= out["high"]:
            raise ConfigError(f"{field}.low ({out['low']:g}) must be less than "
                              f"{field}.high ({out['high']:g})")
        mode = spec.get("mode", (out["low"] + out["high"]) / 2.0)
        out["mode"] = _number(mode, f"{field}.mode")
        if not out["low"] <= out["mode"] <= out["high"]:
            raise ConfigError(f"{field}.mode ({out['mode']:g}) must sit between "
                              f"{field}.low and {field}.high")

    if "minimum" in spec:
        out["minimum"] = _number(spec["minimum"], f"{field}.minimum")
    if "maximum" in spec:
        out["maximum"] = _number(spec["maximum"], f"{field}.maximum")
    if "minimum" in out and "maximum" in out and out["minimum"] > out["maximum"]:
        raise ConfigError(f"{field}.minimum cannot be greater than {field}.maximum")
    return out


def validate_config(raw: object) -> dict:
    if not isinstance(raw, dict):
        raise ConfigError("the config must be a JSON object")

    required = ("months", "runs", "starting_balance", "monthly_income",
                "monthly_fixed_expenses", "monthly_variable_expenses")
    missing = [f for f in required if f not in raw]
    if missing:
        raise ConfigError("missing required field(s): " + ", ".join(missing))

    config: dict = {
        "name": str(raw.get("name", "unnamed scenario")),
        "currency": str(raw.get("currency", "USD")),
        "months": _integer(raw["months"], "months", minimum=1),
        "runs": _integer(raw["runs"], "runs", minimum=1),
        "starting_balance": _number(raw["starting_balance"], "starting_balance"),
        "monthly_income": validate_amount(raw["monthly_income"], "monthly_income"),
        "monthly_fixed_expenses": validate_amount(raw["monthly_fixed_expenses"],
                                                  "monthly_fixed_expenses"),
        "monthly_variable_expenses": validate_amount(raw["monthly_variable_expenses"],
                                                     "monthly_variable_expenses"),
    }
    seed = raw.get("seed", 0)
    config["seed"] = _integer(seed, "seed", minimum=-2**31)

    one_time = raw.get("one_time_expenses", [])
    if not isinstance(one_time, list):
        raise ConfigError("one_time_expenses must be a list")
    items = []
    for i, entry in enumerate(one_time, start=1):
        if not isinstance(entry, dict):
            raise ConfigError(f"one_time_expenses[{i}] must be an object")
        for key in ("month", "amount"):
            if key not in entry:
                raise ConfigError(f"one_time_expenses[{i}].{key} is required")
        month = _integer(entry["month"], f"one_time_expenses[{i}].month", minimum=1)
        if month > config["months"]:
            raise ConfigError(
                f"one_time_expenses[{i}].month is {month}, which is outside the "
                f"{config['months']} month(s) being simulated")
        items.append({
            "month": month,
            "amount": _number(entry["amount"], f"one_time_expenses[{i}].amount"),
            "label": str(entry.get("label", f"one-time expense {i}")),
        })
    config["one_time_expenses"] = items
    return config


def load_config(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ConfigError(f"no config file at {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"{path.name} is not valid JSON: {e.msg} "
                          f"(line {e.lineno}, column {e.colno})") from None
    except OSError as e:
        raise ConfigError(f"{path.name} could not be read ({type(e).__name__})") from None
    return validate_config(raw)


# ---------------------------------------------------------------- sampling

def sample(rng: random.Random, spec: dict) -> float:
    """Draw one value. Always consumes the same number of random draws for a
    given distribution, which is what keeps two runs with the same seed
    comparable when you change an unrelated assumption."""
    dist = spec["distribution"]
    if dist == "fixed":
        value = spec["amount"]
    elif dist == "normal":
        value = rng.gauss(spec["mean"], spec["sd"])
    elif dist == "uniform":
        value = rng.uniform(spec["low"], spec["high"])
    else:
        value = rng.triangular(spec["low"], spec["high"], spec["mode"])
    if "minimum" in spec:
        value = max(value, spec["minimum"])
    if "maximum" in spec:
        value = min(value, spec["maximum"])
    return value


def percentile(sorted_values: list[float], p: float) -> float:
    """Linear interpolation between the two closest ranks."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * (p / 100.0)
    low, high = math.floor(k), math.ceil(k)
    if low == high:
        return sorted_values[int(k)]
    return sorted_values[low] * (high - k) + sorted_values[high] * (k - low)


def histogram(values: list[float], bins: int) -> dict:
    lowest, highest = min(values), max(values)
    if math.isclose(lowest, highest):
        return {"bin_edges": [lowest, highest], "counts": [len(values)],
                "bin_width": 0.0}
    width = (highest - lowest) / bins
    counts = [0] * bins
    for value in values:
        index = int((value - lowest) / width)
        if index >= bins:
            index = bins - 1
        counts[index] += 1
    edges = [lowest + i * width for i in range(bins + 1)]
    return {"bin_edges": edges, "counts": counts, "bin_width": width}


# ---------------------------------------------------------------- simulation

def simulate(config: dict) -> dict:
    """Run the whole thing. One row of monthly balances per run."""
    rng = random.Random(config["seed"])
    months = config["months"]
    runs = config["runs"]
    income_spec = config["monthly_income"]
    fixed_spec = config["monthly_fixed_expenses"]
    variable_spec = config["monthly_variable_expenses"]

    one_time_by_month: dict[int, float] = {}
    for item in config["one_time_expenses"]:
        one_time_by_month[item["month"]] = one_time_by_month.get(item["month"], 0.0) \
            + item["amount"]

    ending_balances: list[float] = []
    never_negative = 0
    balances_by_month: list[list[float]] = [[] for _ in range(months)]
    total_income_sum = 0.0
    total_expense_sum = 0.0

    for _ in range(runs):
        balance = config["starting_balance"]
        dipped = False
        for month in range(1, months + 1):
            income = sample(rng, income_spec)
            fixed = sample(rng, fixed_spec)
            variable = sample(rng, variable_spec)
            one_time = one_time_by_month.get(month, 0.0)

            total_income_sum += income
            total_expense_sum += fixed + variable + one_time

            balance += income - fixed - variable - one_time
            balances_by_month[month - 1].append(balance)
            if balance < 0:
                dipped = True
        ending_balances.append(balance)
        if not dipped:
            never_negative += 1

    ending_sorted = sorted(ending_balances)
    above_zero = sum(1 for b in ending_balances if b > 0)

    monthly_bands = []
    for index, column in enumerate(balances_by_month, start=1):
        column.sort()
        monthly_bands.append({
            "month": index,
            "p10": percentile(column, 10),
            "p50": percentile(column, 50),
            "p90": percentile(column, 90),
        })

    month_run_pairs = runs * months
    return {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "scenario": config["name"],
        "currency": config["currency"],
        "runs": runs,
        "months": months,
        "seed": config["seed"],
        "starting_balance": config["starting_balance"],
        "ending_balance": {
            "mean": statistics.fmean(ending_balances),
            "percentiles": {f"p{p}": percentile(ending_sorted, p) for p in PERCENTILES},
            "minimum": ending_sorted[0],
            "maximum": ending_sorted[-1],
        },
        "runs_ending_above_zero": {
            "count": above_zero,
            "percent": 100.0 * above_zero / runs,
        },
        "runs_never_below_zero": {
            "count": never_negative,
            "percent": 100.0 * never_negative / runs,
        },
        "average_monthly_income": total_income_sum / month_run_pairs,
        "average_monthly_expenses": total_expense_sum / month_run_pairs,
        "monthly_bands": monthly_bands,
        "histogram": histogram(ending_balances, HISTOGRAM_BINS),
        "assumptions": config,
        "not_modelled": list(NOT_MODELLED),
        "disclaimer": DISCLAIMER,
    }


# ---------------------------------------------------------------- report

def money(value: float, currency: str) -> str:
    return f"{currency} {value:,.0f}"


def svg_histogram(results: dict) -> str:
    hist = results["histogram"]
    counts = hist["counts"]
    edges = hist["bin_edges"]
    if not counts:
        return "<p class='muted'>No ending balances to plot.</p>"

    width, height = 720, 260
    pad_left, pad_bottom, pad_top = 54, 34, 12
    plot_w = width - pad_left - 12
    plot_h = height - pad_bottom - pad_top
    peak = max(counts) or 1
    bar_w = plot_w / len(counts)

    bars = []
    for i, count in enumerate(counts):
        bar_h = (count / peak) * plot_h
        x = pad_left + i * bar_w
        y = pad_top + plot_h - bar_h
        zero_side = "neg" if edges[i + 1] <= 0 else "pos"
        bars.append(
            f"<rect class='bar {zero_side}' x='{x:.2f}' y='{y:.2f}' "
            f"width='{max(bar_w - 1, 0.6):.2f}' height='{bar_h:.2f}'>"
            f"<title>{count} run(s) between {edges[i]:,.0f} and {edges[i + 1]:,.0f}</title>"
            f"</rect>")

    ticks = []
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        value = edges[0] + (edges[-1] - edges[0]) * fraction
        x = pad_left + plot_w * fraction
        # The end labels are anchored inward, otherwise a centred label at the
        # far edge is clipped by the viewBox and loses its last digit.
        anchor = "start" if fraction == 0.0 else "end" if fraction == 1.0 else "middle"
        ticks.append(f"<text class='tick' x='{x:.1f}' y='{height - 12}' "
                     f"text-anchor='{anchor}'>{value:,.0f}</text>")

    zero_line = ""
    if edges[0] < 0 < edges[-1]:
        zero_x = pad_left + plot_w * ((0 - edges[0]) / (edges[-1] - edges[0]))
        zero_line = (f"<line class='zero' x1='{zero_x:.1f}' y1='{pad_top}' "
                     f"x2='{zero_x:.1f}' y2='{pad_top + plot_h}'/>"
                     f"<text class='zerolabel' x='{zero_x:.1f}' y='{pad_top - 1}' "
                     f"text-anchor='middle'>0</text>")

    return (f"<svg viewBox='0 0 {width} {height}' role='img' "
            f"aria-label='Distribution of ending balances across simulated runs'>"
            f"<line class='axis' x1='{pad_left}' y1='{pad_top + plot_h}' "
            f"x2='{pad_left + plot_w}' y2='{pad_top + plot_h}'/>"
            f"{''.join(bars)}{zero_line}{''.join(ticks)}"
            f"<text class='tick' x='4' y='{pad_top + 10}'>{peak} runs</text></svg>")


def svg_bands(results: dict) -> str:
    bands = results["monthly_bands"]
    if not bands:
        return "<p class='muted'>No monthly bands to plot.</p>"

    width, height = 720, 280
    pad_left, pad_bottom, pad_top = 62, 34, 14
    plot_w = width - pad_left - 14
    plot_h = height - pad_bottom - pad_top

    start = results["starting_balance"]
    lows = [b["p10"] for b in bands] + [start]
    highs = [b["p90"] for b in bands] + [start]
    low, high = min(lows), max(highs)
    if math.isclose(low, high):
        low, high = low - 1, high + 1
    span = high - low

    def point(index: int, value: float) -> tuple[float, float]:
        x = pad_left + (plot_w * index / max(len(bands), 1))
        y = pad_top + plot_h - ((value - low) / span) * plot_h
        return x, y

    def path_for(key: str) -> str:
        pieces = []
        x0, y0 = point(0, start)
        pieces.append(f"M {x0:.1f} {y0:.1f}")
        for i, band in enumerate(bands, start=1):
            x, y = point(i, band[key])
            pieces.append(f"L {x:.1f} {y:.1f}")
        return " ".join(pieces)

    upper = [point(0, start)] + [point(i, b["p90"]) for i, b in enumerate(bands, start=1)]
    lower = [point(i, b["p10"]) for i, b in enumerate(bands, start=1)][::-1] \
        + [point(0, start)]
    area = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in upper + lower) + " Z"

    grid = []
    for fraction in (0.0, 0.5, 1.0):
        value = low + span * fraction
        y = pad_top + plot_h - fraction * plot_h
        grid.append(f"<line class='grid' x1='{pad_left}' y1='{y:.1f}' "
                    f"x2='{pad_left + plot_w}' y2='{y:.1f}'/>")
        grid.append(f"<text class='tick' x='{pad_left - 6}' y='{y + 4:.1f}' "
                    f"text-anchor='end'>{value:,.0f}</text>")

    zero_line = ""
    if low < 0 < high:
        y = pad_top + plot_h - ((0 - low) / span) * plot_h
        zero_line = (f"<line class='zero' x1='{pad_left}' y1='{y:.1f}' "
                     f"x2='{pad_left + plot_w}' y2='{y:.1f}'/>")

    labels = []
    for i, band in enumerate(bands, start=1):
        if len(bands) <= 12 or i % 2 == 0:
            x, _ = point(i, band["p50"])
            labels.append(f"<text class='tick' x='{x:.1f}' y='{height - 12}' "
                          f"text-anchor='middle'>{band['month']}</text>")

    return (f"<svg viewBox='0 0 {width} {height}' role='img' "
            f"aria-label='Monthly balance bands from the 10th to the 90th percentile'>"
            f"{''.join(grid)}{zero_line}"
            f"<path class='band' d='{area}'/>"
            f"<path class='line p90' d='{path_for('p90')}'/>"
            f"<path class='line p50' d='{path_for('p50')}'/>"
            f"<path class='line p10' d='{path_for('p10')}'/>"
            f"{''.join(labels)}</svg>")


def describe_amount(spec: dict, currency: str) -> str:
    dist = spec["distribution"]
    if dist == "fixed":
        return f"fixed at {money(spec['amount'], currency)}"
    if dist == "normal":
        text = (f"normal, mean {money(spec['mean'], currency)}, "
                f"sd {money(spec['sd'], currency)}")
    elif dist == "uniform":
        text = (f"uniform between {money(spec['low'], currency)} and "
                f"{money(spec['high'], currency)}")
    else:
        text = (f"triangular, {money(spec['low'], currency)} to "
                f"{money(spec['high'], currency)}, mode {money(spec['mode'], currency)}")
    bounds = []
    if "minimum" in spec:
        bounds.append(f"floor {money(spec['minimum'], currency)}")
    if "maximum" in spec:
        bounds.append(f"cap {money(spec['maximum'], currency)}")
    return text + (f" ({', '.join(bounds)})" if bounds else "")


def render_report(results: dict) -> str:
    currency = results["currency"]
    config = results["assumptions"]
    pcts = results["ending_balance"]["percentiles"]

    rows = "".join(
        f"<tr><td>{html.escape(label)}</td><td class='num'>{value}</td></tr>"
        for label, value in (
            ("Scenario", html.escape(results["scenario"])),
            ("Simulated runs", f"{results['runs']:,}"),
            ("Months per run", str(results["months"])),
            ("Seed", str(results["seed"])),
            ("Starting balance", money(results["starting_balance"], currency)),
            ("Monthly income", html.escape(describe_amount(config["monthly_income"], currency))),
            ("Monthly fixed expenses",
             html.escape(describe_amount(config["monthly_fixed_expenses"], currency))),
            ("Monthly variable expenses",
             html.escape(describe_amount(config["monthly_variable_expenses"], currency))),
        ))

    one_time = config["one_time_expenses"]
    one_time_html = "<p class='muted'>None configured.</p>" if not one_time else (
        "<ul>" + "".join(
            f"<li>Month {item['month']}: {money(item['amount'], currency)} "
            f"({html.escape(item['label'])})</li>" for item in one_time) + "</ul>")

    pct_rows = "".join(
        f"<tr><td>{name}</td><td class='num'>{money(pcts[key], currency)}</td>"
        f"<td class='muted'>{note}</td></tr>"
        for name, key, note in (
            ("10th percentile", "p10", "1 in 10 simulated runs ended at or below this"),
            ("25th percentile", "p25", "1 in 4 ended at or below this"),
            ("Median", "p50", "half ended above, half below"),
            ("75th percentile", "p75", "1 in 4 ended at or above this"),
            ("90th percentile", "p90", "1 in 10 ended at or above this"),
        ))

    band_rows = "".join(
        f"<tr><td>{b['month']}</td><td class='num'>{money(b['p10'], currency)}</td>"
        f"<td class='num'>{money(b['p50'], currency)}</td>"
        f"<td class='num'>{money(b['p90'], currency)}</td></tr>"
        for b in results["monthly_bands"])

    not_modelled = "".join(f"<li>{html.escape(item)}</li>" for item in results["not_modelled"])

    above = results["runs_ending_above_zero"]
    never = results["runs_never_below_zero"]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Freedom Calculator: {html.escape(results['scenario'])}</title>
<style>
  :root {{ --bg:#faf9f7; --card:#fff; --fg:#1f2430; --muted:#6b7280; --line:#e8e5e0;
           --accent:#7c9cbf; --accent2:#b08cc4; --warn:#c2703f; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#16181d; --card:#1e2128; --fg:#e8e6e3; --muted:#9aa1ad; --line:#2c3038; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ font:16px/1.6 -apple-system, system-ui, "Segoe UI", sans-serif;
          max-width:860px; margin:0 auto; padding:44px 20px 72px;
          color:var(--fg); background:var(--bg); }}
  h1 {{ font-size:1.85rem; font-weight:600; margin:0 0 4px; letter-spacing:-.5px; }}
  h2 {{ font-size:1.05rem; font-weight:600; margin:42px 0 14px; padding-bottom:8px;
        border-bottom:1px solid var(--line); }}
  .lede {{ color:var(--muted); margin:0 0 6px; }}
  .muted {{ color:var(--muted); }}
  .small {{ font-size:.87rem; }}
  .stats {{ display:flex; flex-wrap:wrap; gap:10px; margin:26px 0 6px; }}
  .stat {{ flex:1 1 150px; background:var(--card); border:1px solid var(--line);
           border-radius:10px; padding:14px 16px; }}
  .stat b {{ display:block; font-size:1.4rem; font-weight:600; letter-spacing:-.5px; }}
  .stat span {{ color:var(--muted); font-size:.8rem; }}
  table {{ width:100%; border-collapse:collapse; margin:8px 0; }}
  td, th {{ text-align:left; padding:7px 10px; border-bottom:1px solid var(--line);
            vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; font-size:.85rem; }}
  .num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  svg {{ width:100%; height:auto; background:var(--card); border:1px solid var(--line);
         border-radius:10px; margin:6px 0; }}
  .bar {{ fill:var(--accent); }}
  .bar.neg {{ fill:var(--warn); }}
  .axis, .grid {{ stroke:var(--line); stroke-width:1; }}
  .zero {{ stroke:var(--warn); stroke-width:1.5; stroke-dasharray:4 3; }}
  .zerolabel, .tick {{ fill:var(--muted); font-size:11px; }}
  .band {{ fill:var(--accent); opacity:.16; }}
  .line {{ fill:none; stroke-width:2; }}
  .line.p50 {{ stroke:var(--accent2); }}
  .line.p10, .line.p90 {{ stroke:var(--accent); stroke-width:1.4; stroke-dasharray:5 3; }}
  .note {{ margin:38px 0 0; padding:16px 18px; border-radius:10px;
           border:1px solid var(--line); background:var(--card);
           color:var(--muted); font-size:.9rem; }}
  ul {{ margin:6px 0; padding-left:20px; }}
  li {{ margin:3px 0; }}
</style>
</head>
<body>

<h1>Freedom Calculator</h1>
<p class="lede">{html.escape(results['scenario'])} &middot; {results['runs']:,} simulated
runs of {results['months']} months &middot; seed {results['seed']}</p>
<p class="lede small">Generated {html.escape(results['generated_at'])}</p>

<div class="note"><strong>Read this first.</strong> {html.escape(results['disclaimer'])}
Every number below is the behaviour of the assumptions in the config file, not a
statement about what will happen.</div>

<div class="stats">
  <div class="stat"><b>{money(pcts['p50'], currency)}</b><span>Median ending balance</span></div>
  <div class="stat"><b>{money(pcts['p10'], currency)}</b><span>10th percentile</span></div>
  <div class="stat"><b>{money(pcts['p90'], currency)}</b><span>90th percentile</span></div>
  <div class="stat"><b>{above['percent']:.1f}%</b><span>runs ended above zero</span></div>
  <div class="stat"><b>{never['percent']:.1f}%</b><span>runs never went below zero</span></div>
</div>

<h2>What those last two numbers mean</h2>
<p><strong>Ended above zero</strong> counts runs whose balance was above zero on the
final month: {above['count']:,} of {results['runs']:,}. It says nothing about the
months in between, and a run can end comfortably after dipping deep into the
negative along the way.</p>
<p><strong>Never went below zero</strong> is the stricter measure: {never['count']:,}
of {results['runs']:,} runs stayed at or above zero in every single month. The gap
between the two numbers is the share of runs that recovered from a dip.</p>
<p class="muted small">Both are shares of simulated runs under the assumptions in
this config. They are not probabilities about your actual year.</p>

<h2>Distribution of ending balances</h2>
{svg_histogram(results)}
<p class="muted small">Each bar is a range of ending balances and its height is how
many runs landed there. Bars entirely at or below zero are drawn in a warmer colour.</p>

<table>
  <tr><th>Measure</th><th class="num">Ending balance</th><th>Meaning</th></tr>
  {pct_rows}
  <tr><td>Mean</td><td class="num">{money(results['ending_balance']['mean'], currency)}</td>
      <td class="muted">pulled around by the tails, which is why the median is listed too</td></tr>
  <tr><td>Lowest observed</td>
      <td class="num">{money(results['ending_balance']['minimum'], currency)}</td>
      <td class="muted">worst single run of {results['runs']:,}</td></tr>
  <tr><td>Highest observed</td>
      <td class="num">{money(results['ending_balance']['maximum'], currency)}</td>
      <td class="muted">best single run of {results['runs']:,}</td></tr>
</table>

<h2>Monthly balance bands</h2>
{svg_bands(results)}
<p class="muted small">The shaded area runs from the 10th to the 90th percentile of
balances at each month end. The solid line is the median. These are percentiles
computed independently per month, not a single run's path.</p>

<table>
  <tr><th>Month</th><th class="num">p10</th><th class="num">Median</th><th class="num">p90</th></tr>
  {band_rows}
</table>

<h2>Assumptions this run used</h2>
<table>{rows}</table>
<p class="muted small">One-time expenses:</p>
{one_time_html}
<p class="muted small">Average sampled income per month:
{money(results['average_monthly_income'], currency)}. Average sampled expenses per
month, including one-time items spread across the period:
{money(results['average_monthly_expenses'], currency)}.</p>

<h2>Simplifications</h2>
<p>This version does not model any of the following. Leaving them out does not make
them unimportant, it makes this a small model with a boundary you can see:</p>
<ul>{not_modelled}</ul>

<div class="note">{html.escape(results['disclaimer'])} Changing an input and rerunning
shows how this model responds to that change. That is the whole of what it offers.</div>

</body>
</html>
"""


# ---------------------------------------------------------------- terminal

def print_summary(results: dict) -> None:
    currency = results["currency"]
    pcts = results["ending_balance"]["percentiles"]
    above = results["runs_ending_above_zero"]
    never = results["runs_never_below_zero"]

    print()
    print(f"{results['scenario']}")
    print(f"  {results['runs']:,} runs of {results['months']} months, seed {results['seed']}")
    print(f"  Starting balance: {money(results['starting_balance'], currency)}")
    print()
    print("  Ending balance")
    print(f"    p10     {money(pcts['p10'], currency):>18}")
    print(f"    p25     {money(pcts['p25'], currency):>18}")
    print(f"    median  {money(pcts['p50'], currency):>18}")
    print(f"    p75     {money(pcts['p75'], currency):>18}")
    print(f"    p90     {money(pcts['p90'], currency):>18}")
    print(f"    mean    {money(results['ending_balance']['mean'], currency):>18}")
    print(f"    range   {money(results['ending_balance']['minimum'], currency)} "
          f"to {money(results['ending_balance']['maximum'], currency)}")
    print()
    print(f"  Ended above zero:      {above['count']:,} of {results['runs']:,} "
          f"({above['percent']:.1f}% of simulated runs)")
    print(f"  Never below zero:      {never['count']:,} of {results['runs']:,} "
          f"({never['percent']:.1f}% of simulated runs)")
    print()
    print("  These are shares of simulated runs under the assumptions in the config,")
    print("  not probabilities about your actual year.")


# ---------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="simulate.py",
        description="Run a local Monte Carlo simulation of a year of stated "
                    "assumptions and write a self-contained report. Educational "
                    "exploration of your own inputs, not financial advice.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n"
               "  python3 simulate.py sample-config.json --output sample-output\n"
               "  python3 simulate.py my-config.json --output my-output --runs 50000\n"
               "  python3 simulate.py my-config.json --output my-output --seed 7\n"
               "\n"
               "Everything runs locally. No network access, no API key, no model.\n",
    )
    parser.add_argument("config", help="path to the JSON config describing your assumptions")
    parser.add_argument("--output", default="output",
                        help="directory for results.json and report.html (default: output)")
    parser.add_argument("--runs", type=int, default=None,
                        help="override the run count in the config")
    parser.add_argument("--seed", type=int, default=None,
                        help="override the seed in the config")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        config = load_config(pathlib.Path(args.config).expanduser())
        if args.runs is not None:
            config["runs"] = _integer(args.runs, "--runs", minimum=1)
        if args.seed is not None:
            config["seed"] = _integer(args.seed, "--seed", minimum=-2**31)
    except ConfigError as e:
        print(f"Config problem: {e}", file=sys.stderr)
        print("Compare your file against sample-config.json.", file=sys.stderr)
        return 2

    results = simulate(config)

    output = pathlib.Path(args.output).expanduser()
    output.mkdir(parents=True, exist_ok=True)
    results_path = output / "results.json"
    report_path = output / "report.html"
    results_path.write_text(json.dumps(results, indent=1), encoding="utf-8")
    report_path.write_text(render_report(results), encoding="utf-8")

    print_summary(results)
    print()
    print(f"  Wrote {results_path}")
    print(f"  Wrote {report_path}")
    print(f"  Open it:  open {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
