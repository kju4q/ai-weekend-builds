# Prompts: Pattern Mirror

> These are AI-assisted build prompts: a recommended path a reader can follow with
> ChatGPT Chat, ChatGPT Work, and Codex. They are not presented as the exact
> prompts used to produce this repository implementation, and they must not claim
> those tools performed this build.

This project can be built by hand from the README alone. Below, an optional path
if you want help, and then the one prompt that is genuinely part of the running
software: the phrasing prompt in `analyze.py`.

## AI-assisted build prompts

### 1. ChatGPT Chat: clarify the implementation

```
I am building a project called Pattern Mirror. Read this description and treat
the concept, the title, and the public promise as locked:

  A local tool that reads a folder of photos and renders the shape of the
  timeline: which months went quiet, where the gaps are, which broad subjects
  recur, and how the indoor/outdoor balance shifts. It runs on my machine.

One correction to that description is required, not optional: any language about
tracking people who appear, fade, or recur across years must go. This project
does not detect faces, recognise or cluster identities, count people, or build
people-presence timelines, and it never will. Replace those claims with patterns
the code can genuinely measure: quiet months, indoor versus outdoor, recurring
visual categories, changes in photo activity.

Do not otherwise redesign or reposition the project. No SaaS, no accounts, no
server for the report, no photo-service integrations, no frontend framework. It
is a weekend project: a Python CLI and a self-contained HTML report.

Help me define the smallest complete runnable implementation. Work through:

- Supported photo formats, and which ones I should refuse rather than half-support.
- Input and output: the exact output folder contents.
- Date fallbacks, in a strict order, and which case is an honest guess I should
  label as such in the report.
- Duplicate handling: exact versus near, what scope near-duplicate matching
  should use, and why deleting nothing matters.
- Representative-image selection: how to stay deterministic, avoid alphabetical
  bias, and spread across a month.
- Metadata mode versus local-vision mode, and what each one is for.
- The optional OpenAI phrasing layer over aggregate results: exactly which fields
  may be sent, and the list of things that must never be.
- Privacy constraints, stated as rules I can test rather than promises.
- A broad category list with no person, group, or social label in it.
- Indoor versus outdoor as a separate two-way axis, and why its confidence
  threshold cannot be the same number as the multi-class one.
- Performance limits on a camera roll with tens of thousands of files.
- Verification criteria: the objective checks that prove each decision.

Refuse anything involving face detection, face recognition, identity tracking,
anonymous face clustering, or people-presence analysis, and tell me if I drift
toward it. Do not infer sensitive attributes. Do not let the output state
emotional, psychological, or life-event conclusions as facts.

Ask only the implementation questions you actually need answered. Stop before
producing a plan until I have approved the important decisions.
```

### 2. ChatGPT Work: turn the decisions into a checklist

```
Here are the decisions I approved:

[paste the decision list from step 1]

Convert them into a build checklist for a single weekend project. Produce:

1. The five README build steps, in this order: run it as-is on the sample, read
   the timeline builder, turn on the local vision pass, point it at your own
   camera roll, make it yours. Exact commands for each, using python3 throughout.
2. The minimal file list. Nothing beyond what those steps need.
3. CLI behavior: every flag, its default, and what it validates or refuses.
4. Dependencies, with the reason each exists and what breaks without it.
5. Sample-data requirements: how many synthetic images, spread across which
   months, and which situations they must contain (a high month, a low month, a
   visible gap, an exact and a near duplicate, a mix of indoor and outdoor, and
   files whose only date is in the filename).
6. The installation sequence from a clean clone.
7. The Local vs API table, split by mode, stating what runs where.
8. Acceptance checks: objective and runnable, one per requirement.
9. Privacy checks: what must never be committed, what must never be sent, and how
   each is enforced in code rather than promised in prose.
10. Failure cases to handle: empty folder, corrupt image, unsupported files,
    missing dates, output folder inside the input, stale cache, missing API key.

Rules for your output:

- Do not create extra repository-planning files. No build plan, no build log, no
  architecture document, no agent instructions. This checklist goes into the
  README and nowhere else.
- Do not rewrite the existing concept, except to remove the unsupported
  people-tracking claims.
- Vision analysis stays fully local. OpenAI is optional phrasing over aggregate
  numbers only and is never a vision path.
- Keep it achievable in one weekend.

Return a concise checklist I can copy into the README and hand to Codex.
```

### 3. Codex: implement the project

```
Read the README, prompts.md, .env.example, and requirements.txt in this folder
before writing anything. Preserve the existing description and scope. The only
part of the description you may change is unsupported claims about tracking
people who appear, fade, or recur; replace those with patterns the code measures.

Implement in this folder, in checkpoints. Stop after each and show me the real
command output before moving on.

Checkpoint 1, metadata mode end to end:
  - Recursive scan of .jpg/.jpeg/.png/.webp. Skip hidden, unsupported, and
    unreadable files with a named reason each. One bad file must never stop a run.
  - Dates: EXIF DateTimeOriginal, then a date in the filename, then file mtime.
    Record which was used and surface it in the report.
  - Correct EXIF orientation before measuring size, hashing, or thumbnailing.
  - Exact duplicates by content hash, near duplicates by perceptual hash. Mark and
    exclude from representative selection. Delete nothing. Report the counts.
  - Monthly timeline including the empty months, longest gap, busiest and
    quietest months, deterministic representative selection with a seed.
  - Write report.html, analysis.json, and thumbnails/. The report must open from
    the filesystem with no server.

Checkpoint 2, synthetic sample data:
  - 10 to 15 generated images across several months, containing a high month, a
    low month, a visible gap, one exact and one near duplicate, a mix of indoor
    and outdoor scenes, and files whose only date is in the filename.
  - All synthetic. Never use my real photos, and never download stock photos.

Checkpoint 3, local vision:
  - One documented local model. Zero-shot classification against a fixed, broad
    category list with no person, group, or social label in it.
  - Indoor versus outdoor as a separate two-way axis with its own threshold.
  - Below threshold, the label is "unclear". Never force a confident label.
  - Cache by image content hash plus a fingerprint of model, category list, and
    thresholds, so incompatible entries can never be reused.
  - Classify only the per-month representatives, not every file.

Checkpoint 4, optional phrasing:
  - --summary openai sends a sanitized aggregate and nothing else. Build that
    payload in one named function so the boundary is checkable.
  - Never send images, thumbnails, EXIF, GPS, filenames, or absolute paths.
  - Read the model name from OPENAI_MODEL. Do not hardcode one.
  - Missing key or failed call: say so and keep the local summary.

Throughout:
  - Never implement face detection, identity tracking, or people-presence analysis.
  - Keep generated output ignored by Git.
  - Run every documented command with python3, and fix what fails.
  - Make no unrelated changes to the repository.
  - Stop and ask when a real decision is unresolved rather than guessing.
```

### 4. Codex: verify and review

```
Review this project as if you had just cloned it.

1. Create a clean virtual environment with python3 -m venv venv, activate it, and
   install with python3 -m pip install -r requirements.txt.
2. Follow the README commands exactly, in order, as written.
3. Run metadata mode on the sample. Confirm the documented numbers match.
4. Run local mode. Record the model's real first-run download size and elapsed
   time, and the machine you measured them on. Compare against the README.
5. Open the generated report. Confirm the gap months, the representative
   thumbnails, the categories, and the indoor/outdoor section all render, and that
   it works from the filesystem with no server.
6. Test duplicate handling: confirm the exact and near copies are grouped and
   excluded from representative selection.
7. Test missing dates: a file with no EXIF and no date in its name must fall back
   to mtime and be labelled as such.
8. Test an empty folder, a corrupt image, and unsupported files. Each must be
   handled with a clear message and a sensible exit code.
9. Test cache reuse on an unchanged rerun, and cache invalidation after changing
   one image and after changing a threshold.
10. Confirm no face detection, identity tracking, or people-presence feature
    exists anywhere in the code or the report.
11. Confirm the optional phrasing layer receives only sanitized aggregate values.
    Print the exact payload and check it for image data, thumbnails, EXIF, GPS,
    filenames, and absolute paths.
12. Compare every claim in the README against actual code behavior, especially
    the claims about what leaves the machine.
13. Confirm .env, personal photos, thumbnails, reports, and caches are ignored by
    Git, and that no real key is present anywhere.

Fix only confirmed problems. Do not refactor working code, do not add features,
and do not create planning documents. Report clearly what you could not test and
why.
```

## Runtime prompt

This is the actual system prompt in `analyze.py`, used only when you pass
`--summary openai` with both variables set. It is **not** an image-analysis
prompt. The model never receives a photograph, and the local pipeline has already
finished all the analysis before this runs.

```
You phrase already-computed statistics about a photo collection. You are given
aggregate numbers only: month counts, quiet months, gap lengths, and category
totals. You have not seen any photograph and must never imply that you have.
Rules:
- Use only the numbers supplied. Never add a fact that is not in the input.
- Never invent a cause for a pattern. Report the pattern, not a reason.
- Never identify or refer to people, relationships, or social life.
- Never infer mental health, happiness, sadness, or life events.
- Say 'photo activity', 'outdoor images appeared more often', 'there is a gap in
  the available files'. Do not say anyone was happier, sadder, busier or lonelier.
- Mention uncertainty plainly when a month has few photos or the sample is small.
- Never reproduce a file path.
Return valid JSON only, with exactly these keys:
{"summary": string, "notable_patterns": [string], "caveat": string}
```

The user turn is the sanitized aggregate as JSON, and nothing else. This is the
real payload from the sample run, 346 bytes:

```json
{
 "date_range": {"start": "2025-03", "end": "2025-09"},
 "photos_analyzed": 14,
 "monthly_counts": {"2025-03": 6, "2025-04": 2, "2025-05": 1,
                    "2025-06": 0, "2025-07": 0, "2025-08": 3, "2025-09": 2},
 "quiet_months": ["2025-06", "2025-07"],
 "longest_gap_days": 79,
 "average_per_active_month": 2.8,
 "duplicates_grouped": 2,
 "analysis_mode": "local",
 "category_counts": {"nature": 2, "city_or_streets": 2, "food": 2,
                     "work_or_screens": 2, "unclear": 2,
                     "home_or_interior": 1, "travel_or_landmarks": 1},
 "indoor_outdoor": {"outdoors": 5, "indoors": 4, "unclear": 3},
 "photos_classified": 12
}
```

The expected response shape, which the implementation and this file share:

```json
{
  "summary": "A concise factual summary of the visible patterns.",
  "notable_patterns": ["A pattern grounded directly in the supplied numbers"],
  "caveat": "These observations describe the available photos, not the person's full life."
}
```

Every rule in that prompt is doing a job:

- **"aggregate numbers only ... never imply you have seen a photograph"** is the
  honest description of what this call is. A model handed counts will otherwise
  drift into "your photos show" phrasing, which misrepresents the whole design.
- **"Never add a fact that is not in the input"** keeps the summary anchored to
  numbers the reader can check against the timeline directly above it.
- **"Never invent a cause"** is the important one. A quiet month invites a story:
  travel, illness, a breakup, burnout. The data supports none of that. It supports
  "fewer files exist in this month" and stops there.
- **"Never identify or refer to people, relationships, or social life"** matches
  what the pipeline can actually see. Nothing upstream detects a person, so any
  sentence about people would be pure invention.
- **"Never infer mental health, happiness, sadness, or life events"** blocks the
  specific failure this kind of report invites most: reading photo volume as mood.
- **"Mention uncertainty when the sample is small"** because a month with two
  photos is not evidence of anything, and the summary should say so rather than
  narrating it with the same confidence as a month with two hundred.
- **"Never reproduce a file path"** is defence in depth. No path is in the payload
  in the first place, so the model has none to leak, and the rule keeps that true
  if someone later widens the payload without thinking it through.
- **"Return valid JSON only"** so the report renderer can place the pieces without
  guessing, and a malformed answer fails loudly instead of landing on the page.

## Tuning

- **Maximum images per month**: `--max-per-month`, default 8. The main lever on
  local runtime, because it decides how many images the model sees. Doubling it
  roughly doubles the vision pass. It does not change how many photos are
  scanned, dated, or deduplicated, which is all of them.
- **Date-range behavior**: the range runs from the earliest to the latest photo
  found, and every month between is drawn, including the empty ones. To narrow it,
  point the tool at a folder holding only the months you care about.
- **Duplicate similarity**: `--dupe-threshold`, default 6 of 64 bits. Lower is
  stricter. Around 10 to 12 starts grouping photos that merely look alike; 2 or 3
  catches only re-saves and near-identical frames. Near-duplicate matching is
  scoped within a month either way.
- **Category list**: `photolib.CATEGORIES`. Add or reword the phrasings per
  category; several phrasings per category work better than one. Keep them broad,
  and keep people out of them. Editing this invalidates the cache automatically.
- **Category confidence**: `--confidence`, default 0.50, over an 11-way choice.
  Raise it for fewer, firmer labels and more `unclear`; lower it to force more
  images into a bucket, which is usually a way of manufacturing certainty you do
  not have.
- **Indoor/outdoor confidence**: `--io-confidence`, default 0.60. This is a
  two-way choice that starts at 0.50 by chance, so it needs a higher bar than the
  category threshold. On the synthetic sample, 0.60 is what pushes three genuinely
  ambiguous images into `unclear` instead of letting a coin flip look like a
  finding.
- **OpenAI phrasing strictness**: tighten the system prompt above. Adding "Do not
  exceed four sentences" shortens it; adding "Every sentence must name a number
  from the input" makes it drier and much harder to drift.
- **Thumbnail size**: `THUMB_SIZE` in `analyze.py`, default 320x320. Smaller keeps
  the output folder light on a large library; the report scales them anyway.
- **Clearing the cache**: `--clear-cache`, or delete `cache.json` in the output
  folder. You rarely need to: the fingerprint covers the model, the category list,
  the prompts, and both thresholds, so incompatible entries are dropped for you.
- **Report detail**: `report_template.html` is plain HTML with `{{TOKEN}}`
  placeholders. Reorder sections, change the CSS, or drop a section entirely.
  There is no build step.

A note on cost: raising the sample size increases local runtime and nothing else.
The optional phrasing layer costs one small API call per changed aggregate, and
raising `--max-per-month` does not make that call bigger in any way that matters,
because it sends category totals rather than per-photo rows. No photo is ever
transmitted at any setting.
