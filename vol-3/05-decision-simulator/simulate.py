"""Decision Simulator — run 10,000 futures instead of guessing one.

    python simulate.py rent-vs-buy.json
    python simulate.py job-a-vs-b.json

Reads a decision config (see the two samples), identifies the uncertain
variables, samples each 10,000 times, evaluates every option's outcome per draw,
and writes:
  results.json  — the raw distributions + summary stats
  results.html  — a beautiful interactive chart (open it in a browser)

This runs 100% locally with the Python standard library. No API key, no network.
Claude only enters if you use prompts.md to turn a plain-English decision into a
config — the simulation itself never leaves your machine.
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import statistics
import sys

# ---- samplers: each variable is either fixed or a named distribution ----

def sample(spec: dict) -> float:
    if "fixed" in spec:
        return float(spec["fixed"])
    dist = spec.get("dist")
    if dist == "normal":
        return random.gauss(spec["mean"], spec["sd"])
    if dist == "uniform":
        return random.uniform(spec["low"], spec["high"])
    if dist == "triangular":
        return random.triangular(spec["low"], spec["high"], spec.get("mode", (spec["low"] + spec["high"]) / 2))
    if dist == "bernoulli":
        return 1.0 if random.random() < spec["p"] else 0.0
    raise ValueError(f"unknown variable spec: {spec}")


def is_uncertain(spec: dict) -> bool:
    return "fixed" not in spec


# Safe evaluation namespace for option expressions.
SAFE_FUNCS = {"min": min, "max": max, "abs": abs, "round": round,
              "sqrt": math.sqrt, "exp": math.exp, "log": math.log}


def evaluate(expr: str, values: dict) -> float:
    return float(eval(expr, {"__builtins__": {}}, {**SAFE_FUNCS, **values}))


def percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return sorted_vals[int(k)]
    return sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


def summarize(vals: list[float], goal: str) -> dict:
    s = sorted(vals)
    worst = s[0] if goal == "max" else s[-1]
    return {
        "mean": statistics.fmean(vals),
        "median": percentile(s, 0.5),
        "p10": percentile(s, 0.10),
        "p90": percentile(s, 0.90),
        "worst_case": worst,          # worst 0th percentile in the goal direction
        "worst_5pct": percentile(s, 0.05 if goal == "max" else 0.95),
        "min": s[0], "max": s[-1],
    }


def run(config: dict) -> dict:
    runs = int(config.get("runs", 10000))
    variables = config["variables"]
    options = config["options"]
    goal = config.get("goal", "max")
    uncertain = [k for k, v in variables.items() if is_uncertain(v)]

    outcomes = {name: [] for name in options}
    for _ in range(runs):
        draw = {k: sample(v) for k, v in variables.items()}
        for name, expr in options.items():
            outcomes[name].append(evaluate(expr, draw))

    summary = {name: summarize(vals, goal) for name, vals in outcomes.items()}

    # Head-to-head: how often does each option beat the other(s)?
    names = list(options)
    wins = {n: 0 for n in names}
    for i in range(runs):
        vals = {n: outcomes[n][i] for n in names}
        best = max(vals, key=vals.get) if goal == "max" else min(vals, key=vals.get)
        wins[best] += 1
    win_rate = {n: wins[n] / runs for n in names}

    return {
        "title": config.get("title", "Decision"),
        "runs": runs, "goal": goal,
        "uncertain_variables": uncertain,
        "outcomes": outcomes,
        "summary": summary,
        "win_rate": win_rate,
    }


def render_html(result: dict) -> str:
    template = (pathlib.Path(__file__).parent / "chart_template.html").read_text()
    return template.replace("/*__DATA__*/", json.dumps(result))


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python simulate.py <config.json>")
    config = json.loads(pathlib.Path(sys.argv[1]).read_text())
    result = run(config)

    pathlib.Path("results.json").write_text(json.dumps(result, indent=2))
    pathlib.Path("results.html").write_text(render_html(result))

    print(f"\n{result['title']}  ({result['runs']:,} simulations)")
    print(f"Uncertain variables: {', '.join(result['uncertain_variables'])}\n")
    for name, s in result["summary"].items():
        print(f"  {name}: median {s['median']:,.0f}  "
              f"(10th–90th: {s['p10']:,.0f} to {s['p90']:,.0f})  "
              f"worst 5% ≈ {s['worst_5pct']:,.0f}")
    print("\n  Wins head-to-head:")
    for name, r in result["win_rate"].items():
        print(f"    {name}: {r*100:.0f}% of futures")
    print("\nWrote results.json and results.html — open results.html in a browser.")


if __name__ == "__main__":
    main()
