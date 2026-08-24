"""Lookout: one check run over the sources you listed.

    python3 check.py --sources sources.example.yml       # a check run
    python3 check.py --sources sources.yml --quiet       # for cron: output only on change
    python3 check.py --sources sources.yml --history plans
    python3 check.py --sources sources.yml --show plans --version 2026-08-24T18-30-00Z

This script does not run itself. It checks once and exits. Putting it on a
schedule is your step, with cron or a scheduled workflow. See the README.

Fetching, text extraction, diffing, and the archive are all local. The optional
`--judge` flag sends the diff text of a detected change, and nothing else, to
the OpenAI API to decide whether the change matters.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import pathlib
import re
import sys
import unicodedata
from html.parser import HTMLParser

HERE = pathlib.Path(__file__).parent
FETCH_TIMEOUT = 20
USER_AGENT = ("Mozilla/5.0 (compatible; Lookout/1.0; "
              "+https://github.com/kju4q/ai-weekend-builds)")

# Text that changes on every fetch without the page meaning anything different.
# Each pattern is replaced by a fixed token before comparison, so it can churn
# freely without waking you up. This list is the honest limit of the filtering:
# it catches the patterns named here, not "all noise everywhere".
DEFAULT_IGNORE = [
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?\s*(UTC|GMT|Z)?",  # timestamps
    r"\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM|am|pm)?",                    # clock times
    r"\bgenerated in \d+\s*(ms|milliseconds|s|seconds)\b",          # render timers
    r"\bVisitors today:\s*[\d,]+",                                  # counters
    r"\bBuild\s+[\w.\-]+",                                          # build ids
    r"\b[0-9a-f]{8,40}\b",                                          # hashes, tokens
    r"\b\d{4}-\d{2}-\d{2}\b",                                       # bare dates
]

JUDGE_SYSTEM = (
    "You judge whether a change to a web page matters to someone watching that "
    "page. You are given a unified diff and nothing else: no browsing, no page "
    "history, no other context.\n"
    "Rules:\n"
    "- Judge only what is in the diff. Never describe anything the diff does not show.\n"
    "- If the diff is too ambiguous to call, say so plainly and set matters to "
    "\"unclear\". Uncertainty is a valid answer and is better than a guess.\n"
    "- Never invent a reason for the change, a date, a number, or a consequence.\n"
    "- Quote or name the concrete thing that changed, using the diff's own words.\n"
    "- Be brief. One or two sentences.\n"
    "Return valid JSON only, with exactly these keys: "
    '{"matters": "yes" | "no" | "unclear", "summary": string}'
)


# ---------------------------------------------------------------- extraction

class _TextExtractor(HTMLParser):
    """Pull readable text out of HTML with the standard library.

    Script, style, and template contents are dropped entirely: they change with
    every deploy and never say anything a reader cares about. Block-level tags
    become line breaks so the diff lands on sensible lines instead of one
    enormous paragraph.
    """

    SKIP = {"script", "style", "noscript", "template", "svg", "head"}
    BLOCK = {"p", "div", "li", "tr", "br", "h1", "h2", "h3", "h4", "h5", "h6",
             "section", "article", "header", "footer", "nav", "ul", "ol", "table",
             "blockquote", "pre", "hr", "form", "main", "aside"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag in self.BLOCK:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self.BLOCK:
            self._parts.append("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts)
        lines = [" ".join(line.split()) for line in raw.splitlines()]
        return "\n".join(line for line in lines if line)


def extract_text(content: str) -> str:
    """HTML to comparable text. Plain text passes through, whitespace-normalized.

    Comparison is on text content, never on raw bytes. Minified CSS, reordered
    attributes, and a rebuilt script bundle are invisible here, which is most of
    what a redeploy changes on a page whose words did not move.
    """
    content = unicodedata.normalize("NFC", content)
    if "<" in content and ">" in content:
        parser = _TextExtractor()
        try:
            parser.feed(content)
            parser.close()
            return parser.text()
        except Exception:
            pass  # malformed markup: fall through to the plain-text path
    return "\n".join(" ".join(l.split()) for l in content.splitlines() if l.strip())


def normalize(text: str, ignore_patterns: list[str]) -> str:
    """Blank out the churn so it cannot count as a change."""
    out = text
    for pattern in ignore_patterns:
        try:
            out = re.sub(pattern, "<ignored>", out)
        except re.error as e:
            print(f"  ! ignoring bad regex {pattern!r}: {e}", file=sys.stderr)
    return "\n".join(" ".join(l.split()) for l in out.splitlines() if l.strip())


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- config

def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or hashlib.sha256(name.encode()).hexdigest()[:12]


def load_sources(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"No config at {path}\n"
                         f"Copy the example:  cp sources.example.yml sources.yml")
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() in {".yml", ".yaml"}:
            import yaml

            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
    except Exception as e:
        raise SystemExit(f"{path} could not be parsed ({type(e).__name__}: {e}).\n"
                         "Compare it against sources.example.yml.")

    if data is None:
        raise SystemExit(f"{path} is empty. It needs a `sources:` list, see "
                         "sources.example.yml.")
    if isinstance(data, dict):
        data = data.get("sources")
    if not isinstance(data, list) or not data:
        raise SystemExit(f"{path} has no sources. It needs a `sources:` list with at "
                         "least one entry, see sources.example.yml.")

    out = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise SystemExit(f"{path}: source {i + 1} is not a mapping. Each entry "
                             "needs a name and either a url or a path.")
        name = entry.get("name")
        if not name:
            raise SystemExit(f"{path}: source {i + 1} has no `name`.")
        if not entry.get("url") and not entry.get("path"):
            raise SystemExit(f"{path}: source {name!r} has neither `url` nor `path`.")
        ignore = list(DEFAULT_IGNORE)
        if not entry.get("use_default_ignores", True):
            ignore = []
        ignore += list(entry.get("ignore", []) or [])
        out.append({"name": str(name), "url": entry.get("url"),
                    "path": entry.get("path"), "note": entry.get("note"),
                    "ignore": ignore, "slug": slugify(str(name))})
    names = [s["name"] for s in out]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        raise SystemExit(f"{path}: duplicate source names {sorted(dupes)}. Names key "
                         "the archive, so they have to be unique.")
    return out


# ---------------------------------------------------------------- fetching

def fetch(source: dict, config_dir: pathlib.Path) -> str:
    """Return the raw body of a source. Local paths never touch the network."""
    if source.get("path"):
        target = pathlib.Path(source["path"]).expanduser()
        if not target.is_absolute():
            target = config_dir / target
        return target.read_text(encoding="utf-8", errors="replace")

    import requests

    resp = requests.get(source["url"], timeout=FETCH_TIMEOUT,
                        headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    return resp.text


# ---------------------------------------------------------------- archive

def source_dir(archive: pathlib.Path, slug: str) -> pathlib.Path:
    return archive / slug


def versions(archive: pathlib.Path, slug: str) -> list[pathlib.Path]:
    """Archived versions, oldest first.

    Sorted on the stem rather than the whole filename. With the extension still
    attached, "...10Z-2.json" sorts before "...10Z.json", because "-" is below
    "." in ASCII, and the newest version would be read as the oldest. That only
    bites when two runs land inside the same second, which is exactly what
    replaying the fixtures does.
    """
    d = source_dir(archive, slug)
    if not d.exists():
        return []
    return sorted((p for p in d.iterdir() if p.suffix == ".json"), key=lambda p: p.stem)


def read_version(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def write_version(archive: pathlib.Path, source: dict, text: str,
                  normalized: str) -> pathlib.Path:
    d = source_dir(archive, source["slug"])
    d.mkdir(parents=True, exist_ok=True)
    base = stamp()
    path = d / f"{base}.json"
    seq = 2
    while path.exists():  # two runs inside the same second
        path = d / f"{base}-{seq}.json"
        seq += 1
    payload = {
        "name": source["name"],
        "url": source.get("url") or f"file:{source.get('path')}",
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sha256_text": sha(text),
        "sha256_normalized": sha(normalized),
        "text": text,
    }
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    return path


def version_label(path: pathlib.Path) -> str:
    return path.stem


# ---------------------------------------------------------------- diffing

def build_diff(old: str, new: str, old_label: str, new_label: str,
               context: int) -> str:
    lines = list(difflib.unified_diff(
        old.splitlines(), new.splitlines(),
        fromfile=old_label, tofile=new_label, lineterm="", n=context))
    return "\n".join(lines)


def judge(diff_text: str, source_name: str, model: str) -> dict:
    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": f"Page being watched: {source_name}\n\n"
                                        f"Unified diff:\n{diff_text}"},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content or "{}")


# ---------------------------------------------------------------- commands

def cmd_history(archive: pathlib.Path, sources: list[dict], name: str) -> int:
    match = next((s for s in sources if s["name"] == name or s["slug"] == slugify(name)), None)
    if not match:
        print(f"No source named {name!r} in the config. Known: "
              f"{', '.join(s['name'] for s in sources)}")
        return 1
    vs = versions(archive, match["slug"])
    if not vs:
        print(f"No archived versions for {match['name']!r} yet. Run a check first.")
        return 0
    print(f"{match['name']}  ({len(vs)} archived version"
          f"{'s' if len(vs) != 1 else ''}, oldest first)")
    prev_text = None
    for path in vs:
        v = read_version(path)
        size = len(v["text"].splitlines())
        marker = ""
        if prev_text is not None:
            changed = sum(1 for l in difflib.unified_diff(
                prev_text.splitlines(), v["text"].splitlines(), lineterm="", n=0)
                if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))
            marker = f"  ({changed} line{'s' if changed != 1 else ''} changed)"
        print(f"  {version_label(path)}   {size:>4} lines{marker}")
        prev_text = v["text"]
    print(f"\nRead one:  python3 check.py --show {match['name']!r} "
          f"--version {version_label(vs[0])}")
    return 0


def cmd_show(archive: pathlib.Path, sources: list[dict], name: str,
             version: str | None) -> int:
    match = next((s for s in sources if s["name"] == name or s["slug"] == slugify(name)), None)
    if not match:
        print(f"No source named {name!r} in the config.")
        return 1
    vs = versions(archive, match["slug"])
    if not vs:
        print(f"No archived versions for {match['name']!r} yet.")
        return 1
    if version:
        chosen = next((p for p in vs if p.stem == version), None)
        if not chosen:
            print(f"No version {version!r} for {match['name']!r}. Available:")
            for p in vs:
                print(f"  {version_label(p)}")
            return 1
    else:
        chosen = vs[-1]
    v = read_version(chosen)
    print(f"# {v['name']}  {version_label(chosen)}  (fetched {v['fetched_at']})")
    print(f"# {v['url']}\n")
    print(v["text"])
    return 0


def check_one(source: dict, archive: pathlib.Path, config_dir: pathlib.Path,
              context: int) -> dict:
    """Fetch, compare against the newest archived version, archive if changed."""
    result: dict = {"name": source["name"], "state": None, "diff": None,
                    "error": None, "from": None, "to": None}
    try:
        raw = fetch(source, config_dir)
    except Exception as e:
        result["state"] = "error"
        result["error"] = f"{type(e).__name__}: {e}"
        return result

    text = extract_text(raw)
    if not text.strip():
        result["state"] = "error"
        result["error"] = "fetched, but no readable text could be extracted"
        return result
    norm = normalize(text, source["ignore"])

    existing = versions(archive, source["slug"])
    if not existing:
        path = write_version(archive, source, text, norm)
        result["state"] = "new"
        result["to"] = version_label(path)
        return result

    latest_path = existing[-1]
    latest = read_version(latest_path)
    latest_norm = normalize(latest["text"], source["ignore"])

    if sha(norm) == sha(latest_norm):
        # Nothing meaningful moved. If the raw text churned, that is noise and it
        # is deliberately not archived: a new version would be a new "what did
        # this page say" entry that says the same thing.
        result["state"] = "noise" if sha(text) != sha(latest["text"]) else "unchanged"
        result["from"] = version_label(latest_path)
        return result

    path = write_version(archive, source, text, norm)
    result["state"] = "changed"
    result["from"] = version_label(latest_path)
    result["to"] = version_label(path)
    # The diff is computed on the normalized text, so a line whose only change was
    # a timestamp or a counter is identical on both sides and never reaches the
    # report. Where an ignored span sits inside a line that did change for real,
    # it shows as <ignored>.
    result["diff"] = build_diff(latest_norm, norm,
                                f"{source['name']} @ {version_label(latest_path)}",
                                f"{source['name']} @ {version_label(path)}", context)
    return result


def main() -> int:
    p = argparse.ArgumentParser(
        prog="check.py",
        description="One check run: fetch each source, compare it against the "
                    "archive, stay quiet unless something meaningful changed. "
                    "This script does not schedule itself.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n"
               "  python3 check.py --sources sources.example.yml\n"
               "  python3 check.py --sources sources.yml --quiet   # for cron\n"
               "  python3 check.py --sources sources.yml --history plans\n"
               "  python3 check.py --sources sources.yml --judge\n",
    )
    p.add_argument("--sources", default="sources.yml",
                   help="config file listing your sources (default: sources.yml)")
    p.add_argument("--archive", default=None,
                   help="where saved versions live (default: ./archive next to check.py)")
    p.add_argument("--only", metavar="NAME", action="append",
                   help="check just this source, repeatable")
    p.add_argument("--context", type=int, default=2,
                   help="lines of unchanged context around each diff hunk (default: 2)")
    p.add_argument("--quiet", action="store_true",
                   help="print nothing unless something changed or failed. This is "
                        "the flag you want in cron.")
    p.add_argument("--judge", action="store_true",
                   help="ask OpenAI whether a detected change matters. Sends the diff "
                        "text of that change only. Needs OPENAI_API_KEY and OPENAI_MODEL.")
    p.add_argument("--history", metavar="NAME", help="list archived versions of a source")
    p.add_argument("--show", metavar="NAME", help="print an archived version's text")
    p.add_argument("--version", metavar="STAMP",
                   help="which version --show should print (default: the newest)")
    args = p.parse_args()

    config_path = pathlib.Path(args.sources).expanduser()
    if not config_path.is_absolute():
        config_path = (pathlib.Path.cwd() / config_path).resolve()
    sources = load_sources(config_path)
    archive = pathlib.Path(args.archive).expanduser().resolve() if args.archive \
        else HERE / "archive"

    if args.history:
        return cmd_history(archive, sources, args.history)
    if args.show:
        return cmd_show(archive, sources, args.show, args.version)

    if args.only:
        wanted = {n.lower() for n in args.only}
        sources = [s for s in sources
                   if s["name"].lower() in wanted or s["slug"] in wanted]
        if not sources:
            print(f"No source matched {args.only}.")
            return 1

    judging = False
    if args.judge:
        key, model = os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL")
        if key and model:
            judging = True
        else:
            absent = [n for n, v in (("OPENAI_API_KEY", key), ("OPENAI_MODEL", model)) if not v]
            print(f"--judge needs {' and '.join(absent)}. "
                  "Reporting the raw diff instead, which is the default behaviour.")

    results = [check_one(s, archive, config_path.parent, args.context) for s in sources]
    changed = [r for r in results if r["state"] == "changed"]
    errors = [r for r in results if r["state"] == "error"]
    new = [r for r in results if r["state"] == "new"]
    noise = [r for r in results if r["state"] == "noise"]

    for r in changed:
        print(f"\n=== CHANGED: {r['name']}")
        print(f"    {r['from']}  ->  {r['to']}")
        if judging:
            try:
                verdict = judge(r["diff"], r["name"], os.getenv("OPENAI_MODEL"))
                matters = str(verdict.get("matters", "unclear"))
                print(f"    matters: {matters}")
                print(f"    {verdict.get('summary', '(no summary returned)')}")
            except Exception as e:
                print(f"    (judgment call failed, {type(e).__name__}: {e}. "
                      f"The diff below is unaffected.)")
        print()
        print(r["diff"])

    for r in errors:
        print(f"\n!!! FAILED: {r['name']}\n    {r['error']}", file=sys.stderr)

    if new and not args.quiet:
        print(f"\nFirst run for {len(new)} source{'s' if len(new) != 1 else ''}: "
              f"{', '.join(r['name'] for r in new)}.")
        print("Archived as the baseline. Nothing is reported as changed on a first "
              "run, because there is nothing to compare against yet.")

    if not args.quiet and not changed:
        quiet_bits = []
        if noise:
            quiet_bits.append(f"{len(noise)} changed only in ignored text")
        unchanged = [r for r in results if r["state"] == "unchanged"]
        if unchanged:
            quiet_bits.append(f"{len(unchanged)} byte-identical")
        if quiet_bits:
            print(f"\nNothing meaningful changed ({', '.join(quiet_bits)}).")

    if changed and not args.quiet:
        print(f"\n{len(changed)} source{'s' if len(changed) != 1 else ''} changed.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
