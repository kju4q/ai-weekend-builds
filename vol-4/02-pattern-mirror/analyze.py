"""Pattern Mirror: turn a folder of photos into a local report about the shape
of the timeline.

    python3 analyze.py sample-data --vision metadata --output sample-output
    python3 analyze.py sample-data --vision local    --output sample-output-local

Two analysis modes:

  metadata  dates, months, gaps, duplicates, representative thumbnails.
            No model, no key, no download.
  local     everything above, plus broad visual categories and an
            indoor/outdoor read from a CLIP model running on your machine.

There is no hosted vision mode and there never will be: photos are not sent
anywhere. `--summary openai` is an optional phrasing layer that receives only
the sanitized aggregate numbers this script has already computed. See
`sanitized_aggregate()` below for the exact payload.

This tool does not detect faces, recognise people, cluster identities, or track
who appears over time.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import pathlib
import sys

import photolib
from photolib import CATEGORIES, MODEL_NAME

HERE = pathlib.Path(__file__).parent
THUMB_SIZE = (320, 320)

PRIVACY_NOTE = (
    "These are observations about the files that were available, not conclusions "
    "about anyone's emotional state, relationships, or life. A quiet month means "
    "fewer photos were found in that month, and nothing more. Visual categories "
    "come from a general-purpose model and are approximate. This report contains "
    "no face detection, no identity tracking, and no analysis of who appears."
)

SUMMARY_SYSTEM = (
    "You phrase already-computed statistics about a photo collection. You are given "
    "aggregate numbers only: month counts, quiet months, gap lengths, and category "
    "totals. You have not seen any photograph and must never imply that you have.\n"
    "Rules:\n"
    "- Use only the numbers supplied. Never add a fact that is not in the input.\n"
    "- Never invent a cause for a pattern. Report the pattern, not a reason.\n"
    "- Never identify or refer to people, relationships, or social life.\n"
    "- Never infer mental health, happiness, sadness, or life events.\n"
    "- Say 'photo activity', 'outdoor images appeared more often', 'there is a gap "
    "in the available files'. Do not say anyone was happier, sadder, busier or lonelier.\n"
    "- Mention uncertainty plainly when a month has few photos or the sample is small.\n"
    "- Never reproduce a file path.\n"
    "Return valid JSON only, with exactly these keys: "
    '{"summary": string, "notable_patterns": [string], "caveat": string}'
)


# ---------------------------------------------------------------- helpers

def die(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    sys.exit(code)


def month_label(month: str) -> str:
    return dt.date(int(month[:4]), int(month[5:7]), 1).strftime("%b %Y")


def pretty(key: str) -> str:
    return key.replace("_or_", " / ").replace("_", " ")


def load_cache(path: pathlib.Path, fingerprint: str) -> dict:
    if not path.exists():
        return {}
    try:
        blob = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        print("  cache was unreadable, starting a fresh one")
        return {}
    if blob.get("fingerprint") != fingerprint:
        print("  model, categories or confidence changed since the last run, "
              "so cached labels do not apply and will be recomputed")
        return {}
    return blob.get("entries", {})


def save_cache(path: pathlib.Path, fingerprint: str, entries: dict) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"fingerprint": fingerprint, "model": MODEL_NAME,
                               "entries": entries}, indent=1))
    os.replace(tmp, path)


def sanitized_aggregate(analysis: dict) -> dict:
    """The complete payload that the optional OpenAI phrasing layer may receive.

    Numbers only. No image bytes, no thumbnail, no EXIF, no GPS, no absolute
    path, no filename. Building it here, explicitly, is what makes the boundary
    checkable rather than merely promised.
    """
    t = analysis["timeline"]
    payload = {
        "date_range": {"start": t["date_range"]["start"][:7],
                       "end": t["date_range"]["end"][:7]} if t["date_range"] else None,
        "photos_analyzed": analysis["counts"]["accepted"],
        "monthly_counts": t["per_month"],
        "quiet_months": t["quiet_months"],
        "longest_gap_days": t["longest_gap_days"],
        "average_per_active_month": t["average_per_active_month"],
        "duplicates_grouped": analysis["counts"]["duplicates"]["exact"]
                              + analysis["counts"]["duplicates"]["near"],
        "analysis_mode": analysis["mode"],
    }
    if analysis.get("vision"):
        payload["category_counts"] = analysis["vision"]["category_counts"]
        payload["indoor_outdoor"] = analysis["vision"]["indoor_outdoor"]
        payload["photos_classified"] = analysis["counts"]["classified"]
    return payload


def local_summary(analysis: dict) -> list[str]:
    t = analysis["timeline"]
    lines = []
    if t["date_range"]:
        lines.append(
            f"{analysis['counts']['accepted']} photos span "
            f"{month_label(t['date_range']['start'][:7])} to "
            f"{month_label(t['date_range']['end'][:7])}, across "
            f"{len([m for m, c in t['per_month'].items() if c])} months with photos in them."
        )
    if t["busiest_months"]:
        m, c = t["busiest_months"][0]
        lines.append(f"Photo activity was highest in {month_label(m)} ({c} photos), "
                     f"against an average of {t['average_per_active_month']} per active month.")
    if t["quiet_months"]:
        names = ", ".join(month_label(m) for m in t["quiet_months"])
        lines.append(f"No photos were found in {names}. That is a gap in the available "
                     "files, which may mean photos were taken elsewhere or not kept.")
    if t["longest_gap_days"] and t["longest_gap_between"]:
        a, b = t["longest_gap_between"]
        lines.append(f"The longest stretch without a photo is {t['longest_gap_days']} days, "
                     f"between {a} and {b}.")
    d = analysis["counts"]["duplicates"]
    if d["exact"] or d["near"]:
        lines.append(f"{d['exact']} exact and {d['near']} near-identical images were grouped, "
                     "so a burst of near-copies cannot stand in for a whole month.")
    if analysis.get("vision"):
        cats = [f"{pretty(k)} ({v})" for k, v in list(analysis["vision"]["category_counts"].items())[:3]]
        if cats:
            lines.append("Most frequent categories among the sampled images: " + ", ".join(cats) + ".")
        io = analysis["vision"]["indoor_outdoor"]
        if io:
            parts = ", ".join(f"{k} {v}" for k, v in io.items())
            lines.append(f"Indoor and outdoor split across sampled images: {parts}.")
    return lines


def openai_summary(payload: dict, model: str) -> dict:
    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM},
            {"role": "user", "content": json.dumps(payload, sort_keys=True)},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content or "{}")


# ---------------------------------------------------------------- report

def render_report(analysis: dict, thumbs: dict[str, str]) -> str:
    template = (HERE / "report_template.html").read_text()
    t = analysis["timeline"]
    peak = max(t["per_month"].values(), default=1) or 1

    rows = []
    for month in t["months"]:
        count = t["per_month"][month]
        width = (count / peak) * 100
        cls = "bar zero" if count == 0 else "bar"
        note = " <span class='tag'>no photos found</span>" if count == 0 else ""
        rows.append(
            f"<div class='mrow'><span class='mlabel'>{html.escape(month_label(month))}</span>"
            f"<span class='track'><span class='{cls}' style='width:{width:.1f}%'></span></span>"
            f"<span class='mcount'>{count}</span>{note}</div>"
        )

    months_html = []
    for month in t["months"]:
        count = t["per_month"][month]
        if not count:
            months_html.append(
                f"<section class='month quiet'><h3>{html.escape(month_label(month))}</h3>"
                "<p class='muted'>No photos found in the available files.</p></section>")
            continue
        reps = t["representatives"].get(month, [])
        cards = ""
        for rec in reps:
            thumb = thumbs.get(rec["rel"])
            label = ""
            if rec.get("vision"):
                v = rec["vision"]
                label = (f"<span class='cat'>{html.escape(pretty(v['category']))}</span>"
                         f"<span class='conf'>{v['category_confidence']:.0%} · "
                         f"{html.escape(v['indoor_outdoor'])}</span>")
            img = (f"<img src='thumbnails/{html.escape(thumb)}' alt='representative image' loading='lazy'>"
                   if thumb else "<div class='noimg'>no thumbnail</div>")
            cards += (f"<figure>{img}<figcaption>{html.escape(rec['date'])}"
                      f"<span class='src'>date from {html.escape(rec['date_source'])}</span>"
                      f"{label}</figcaption></figure>")
        extra = ""
        if analysis.get("vision"):
            cats = analysis["vision"]["category_by_month"].get(month, {})
            io = analysis["vision"]["indoor_outdoor_by_month"].get(month, {})
            if cats:
                extra = ("<p class='muted small'>Sampled categories: "
                         + ", ".join(f"{html.escape(pretty(k))} {v}" for k, v in cats.items())
                         + (" · indoor/outdoor: " + ", ".join(f"{html.escape(k)} {v}" for k, v in io.items())
                            if io else "") + "</p>")
        months_html.append(
            f"<section class='month'><h3>{html.escape(month_label(month))} "
            f"<span class='muted'>{count} photo{'s' if count != 1 else ''}, "
            f"{len(reps)} shown</span></h3>{extra}<div class='grid'>{cards}</div></section>")

    cat_html = "<p class='muted'>Run with <code>--vision local</code> to add broad visual categories.</p>"
    io_html = ""
    if analysis.get("vision"):
        cc = analysis["vision"]["category_counts"]
        top = max(cc.values(), default=1) or 1
        cat_html = "".join(
            f"<div class='mrow'><span class='mlabel'>{html.escape(pretty(k))}</span>"
            f"<span class='track'><span class='bar cat' style='width:{(v/top)*100:.1f}%'></span></span>"
            f"<span class='mcount'>{v}</span></div>" for k, v in cc.items())
        io = analysis["vision"]["indoor_outdoor"]
        io_total = sum(io.values()) or 1
        io_html = ("<h2>Indoors and outdoors</h2><div class='io'>" + "".join(
            f"<div class='iopart'><b>{v}</b><span>{html.escape(k)}</span>"
            f"<span class='muted small'>{v/io_total:.0%}</span></div>" for k, v in io.items())
            + "</div><p class='muted small'>A read of the picture, not of how the "
              "photographer spends their time. Ambiguous images stay <em>unclear</em>.</p>")

    summary = analysis["summary"]
    if summary["kind"] == "openai":
        body = f"<p>{html.escape(summary['data'].get('summary', ''))}</p>"
        pats = summary["data"].get("notable_patterns") or []
        if pats:
            body += "<ul>" + "".join(f"<li>{html.escape(str(p))}</li>" for p in pats) + "</ul>"
        if summary["data"].get("caveat"):
            body += f"<p class='muted small'>{html.escape(str(summary['data']['caveat']))}</p>"
        origin = ("Phrased by OpenAI (<code>" + html.escape(summary.get("model", "")) +
                  "</code>) from the aggregate numbers above. No image was sent.")
    else:
        body = "<ul>" + "".join(f"<li>{html.escape(l)}</li>" for l in summary["data"]) + "</ul>"
        origin = "Written locally from the computed numbers. Nothing left this machine."

    counts = analysis["counts"]
    stats = [
        ("Photos analyzed", counts["accepted"]),
        ("Months in range", len(t["months"])),
        ("Months with no photos", len(t["quiet_months"])),
        ("Longest gap", f"{t['longest_gap_days']} days"),
        ("Duplicates grouped", counts["duplicates"]["exact"] + counts["duplicates"]["near"]),
        ("Files skipped", counts["skipped"]),
    ]
    stats_html = "".join(f"<div class='stat'><b>{html.escape(str(v))}</b><span>{html.escape(k)}</span></div>"
                         for k, v in stats)

    ds = analysis["date_sources"]
    ds_html = ", ".join(f"{v} from {html.escape(k)}" for k, v in ds.items())

    mode_desc = ("metadata only, no model" if analysis["mode"] == "metadata"
                 else f"local vision ({html.escape(MODEL_NAME)}), {counts['classified']} images classified")

    replacements = {
        "{{GENERATED}}": dt.datetime.now().strftime("%d %b %Y, %H:%M"),
        "{{RANGE}}": (f"{month_label(t['date_range']['start'][:7])} to "
                      f"{month_label(t['date_range']['end'][:7])}") if t["date_range"] else "no dates",
        "{{STATS}}": stats_html,
        "{{TIMELINE}}": "".join(rows),
        "{{MONTHS}}": "".join(months_html),
        "{{CATEGORIES}}": cat_html,
        "{{INDOOR_OUTDOOR}}": io_html,
        "{{SUMMARY_BODY}}": body,
        "{{SUMMARY_ORIGIN}}": origin,
        "{{MODE}}": mode_desc,
        "{{OPENAI_STATE}}": ("enabled for phrasing only" if summary["kind"] == "openai"
                             else "not used"),
        "{{DATE_SOURCES}}": ds_html,
        "{{NOTE}}": PRIVACY_NOTE,
    }
    for key, value in replacements.items():
        template = template.replace(key, str(value))
    return template


# ---------------------------------------------------------------- main

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="analyze.py",
        description="Turn a folder of photos into a local report about the shape of "
                    "the timeline. Vision analysis runs on your machine; photos are "
                    "never sent anywhere.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n"
               "  python3 analyze.py sample-data --vision metadata --output sample-output\n"
               "  python3 analyze.py sample-data --vision local --output sample-output-local\n"
               "  python3 analyze.py ~/Pictures/test --vision local --max-per-month 12 "
               "--output ~/pattern-mirror-output\n",
    )
    p.add_argument("folder", help="folder of photos to read (searched recursively)")
    p.add_argument("--vision", choices=["metadata", "local"], default="metadata",
                   help="metadata: dates and timeline only, no model. "
                        "local: adds broad visual categories using a local model. "
                        "(default: metadata)")
    p.add_argument("--summary", choices=["local", "openai"], default="local",
                   help="who phrases the findings. local: written on your machine. "
                        "openai: sends the sanitized aggregate numbers only, never "
                        "images. (default: local)")
    p.add_argument("--output", default="output", help="output folder (default: output)")
    p.add_argument("--max-per-month", type=int, default=8,
                   help="representative photos kept per month (default: 8)")
    p.add_argument("--confidence", type=float, default=0.50,
                   help="minimum confidence to accept a category label, else "
                        "'unclear'. This is an 11-way choice. (default: 0.50)")
    p.add_argument("--io-confidence", type=float, default=0.60,
                   help="minimum confidence to accept indoors/outdoors, else "
                        "'unclear'. A two-way choice starts at 0.50 by chance, so "
                        "this sits higher. (default: 0.60)")
    p.add_argument("--dupe-threshold", type=int, default=6,
                   help="perceptual-hash bit distance counted as a near duplicate, "
                        "0-64, lower is stricter (default: 6)")
    p.add_argument("--seed", type=int, default=0,
                   help="seed for representative selection, same seed gives the same "
                        "picks (default: 0)")
    p.add_argument("--clear-cache", action="store_true",
                   help="delete cached local-vision labels before running")
    return p


def main() -> None:
    args = build_parser().parse_args()

    source = pathlib.Path(args.folder).expanduser().resolve()
    output = pathlib.Path(args.output).expanduser().resolve()

    if not source.exists():
        die(f"No such folder: {source}")
    if not source.is_dir():
        die(f"Not a folder: {source}")
    if output == source or photolib._is_within(output, source):
        die(f"Output folder {output} is inside the photo folder {source}.\n"
            "The scan would then read its own thumbnails on the next run. "
            "Choose an output path outside the photo folder.")
    if not 0 <= args.dupe_threshold <= 64:
        die("--dupe-threshold must be between 0 and 64")
    if not 0.0 <= args.confidence <= 1.0:
        die("--confidence must be between 0.0 and 1.0")
    if not 0.0 <= args.io_confidence <= 1.0:
        die("--io-confidence must be between 0.0 and 1.0")
    if args.max_per_month < 1:
        die("--max-per-month must be at least 1")

    output.mkdir(parents=True, exist_ok=True)
    thumb_dir = output / "thumbnails"
    thumb_dir.mkdir(exist_ok=True)
    cache_path = output / "cache.json"

    if args.clear_cache and cache_path.exists():
        cache_path.unlink()
        print(f"Cleared {cache_path}")

    print(f"Scanning {source} ...")
    records, skipped = photolib.scan(source, skip_dirs={output})
    for note in skipped:
        print(f"  skipped: {note}")
    if not records:
        die(f"\nNo supported images found in {source}.\n"
            f"Supported formats: {', '.join(sorted(photolib.SUPPORTED))}.\n"
            "HEIC is not supported, see the README.")

    dupes = photolib.mark_duplicates(records, args.dupe_threshold)
    timeline = photolib.build_timeline(records, args.max_per_month, args.seed)

    date_sources: dict[str, int] = {}
    for rec in records:
        date_sources[rec["date_source"]] = date_sources.get(rec["date_source"], 0) + 1

    reps = [r for month_reps in timeline["representatives"].values() for r in month_reps]
    classified = 0

    if args.vision == "local":
        fingerprint = photolib.cache_fingerprint(args.confidence, args.io_confidence)
        cache = load_cache(cache_path, fingerprint)
        todo = [r for r in reps if r["sha256"] not in cache]
        print(f"\nLocal vision on {len(reps)} representative images "
              f"({len(cache)} cached, {len(todo)} to classify).")
        if todo:
            print(f"  loading {MODEL_NAME} (first run downloads the weights) ...")
            paths = [source / r["rel"] for r in todo]
            results = photolib.classify(paths, args.confidence, args.io_confidence)
            for rec, path in zip(todo, paths):
                cache[rec["sha256"]] = results[str(path)]
            save_cache(cache_path, fingerprint, cache)
        for rec in reps:
            rec["vision"] = cache.get(rec["sha256"])
        classified = sum(1 for r in reps if r.get("vision"))

    print("\nWriting thumbnails ...")
    thumbs: dict[str, str] = {}
    from PIL import Image, ImageOps

    for rec in reps:
        src = source / rec["rel"]
        name = f"{rec['sha256'][:16]}.jpg"
        dest = thumb_dir / name
        if not dest.exists():
            try:
                with Image.open(src) as img:
                    img.load()
                    oriented = ImageOps.exif_transpose(img).convert("RGB")
                    oriented.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
                    oriented.save(dest, quality=82)
            except Exception as e:
                print(f"  ! thumbnail failed for {rec['rel']}: {type(e).__name__}")
                continue
        thumbs[rec["rel"]] = name

    analysis = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "mode": args.vision,
        "source_folder_name": source.name,
        "settings": {"max_per_month": args.max_per_month, "confidence": args.confidence,
                     "io_confidence": args.io_confidence,
                     "dupe_threshold": args.dupe_threshold, "seed": args.seed,
                     "model": MODEL_NAME if args.vision == "local" else None},
        "counts": {"discovered": len(records) + len(skipped), "accepted": len(records),
                   "skipped": len(skipped), "representatives": len(reps),
                   "classified": classified, "duplicates": dupes},
        "date_sources": date_sources,
        "timeline": timeline,
        "photos": records,
        "note": PRIVACY_NOTE,
    }
    if args.vision == "local":
        analysis["vision"] = photolib.aggregate_vision(reps)

    payload = sanitized_aggregate(analysis)
    summary = {"kind": "local", "data": local_summary(analysis)}

    if args.summary == "openai":
        key, model = os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL")
        if not key or not model:
            absent = [n for n, v in (("OPENAI_API_KEY", key), ("OPENAI_MODEL", model)) if not v]
            missing = " and ".join(absent)
            verb = "is" if len(absent) == 1 else "are"
            print(f"\n--summary openai was requested but {missing} {verb} not set.")
            print("Keeping the locally written summary. Set both, or drop --summary openai.")
        else:
            cached_path = output / "summary_cache.json"
            fingerprint = json.dumps(payload, sort_keys=True)
            cached = None
            if cached_path.exists():
                try:
                    blob = json.loads(cached_path.read_text())
                    if blob.get("input") == fingerprint and blob.get("model") == model:
                        cached = blob.get("output")
                except (json.JSONDecodeError, OSError):
                    cached = None
            if cached:
                print("\nReusing the cached phrasing, the aggregate has not changed.")
                summary = {"kind": "openai", "data": cached, "model": model}
            else:
                print(f"\nSending {len(json.dumps(payload))} bytes of aggregate numbers "
                      f"to OpenAI ({model}). No image, thumbnail, EXIF, or path is included.")
                try:
                    result = openai_summary(payload, model)
                    summary = {"kind": "openai", "data": result, "model": model}
                    cached_path.write_text(json.dumps(
                        {"input": fingerprint, "model": model, "output": result}, indent=1))
                except Exception as e:
                    print(f"The OpenAI call failed ({type(e).__name__}: {e}).")
                    print("Keeping the locally written summary. The analysis itself is unaffected.")

    analysis["summary"] = summary
    analysis["openai_phrasing"] = summary["kind"] == "openai"
    analysis["sanitized_aggregate_sent"] = payload if summary["kind"] == "openai" else None

    (output / "analysis.json").write_text(json.dumps(analysis, indent=1))
    (output / "report.html").write_text(render_report(analysis, thumbs))

    t = analysis["timeline"]
    print(f"\nPhotos discovered: {analysis['counts']['discovered']}")
    print(f"Photos accepted:   {len(records)}")
    print(f"Photos skipped:    {len(skipped)}")
    print(f"Date sources:      " + ", ".join(f"{v} {k}" for k, v in date_sources.items()))
    print(f"Duplicates:        {dupes['exact']} exact, {dupes['near']} near, "
          f"{dupes['unique']} unique")
    print(f"Months in range:   {len(t['months'])} ({len(t['quiet_months'])} with no photos)")
    if args.vision == "local":
        print(f"Classified:        {classified} representative images")
    print(f"\nReport: {output / 'report.html'}")
    print(f"Open it:  open {output / 'report.html'}")


if __name__ == "__main__":
    main()
