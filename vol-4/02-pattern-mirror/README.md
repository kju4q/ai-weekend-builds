# 02: Pattern Mirror

Reads years of your camera roll and shows you the shape of your life: what you
photograph in your busiest months, the months the pictures stop, the settings and
subjects that keep coming back. It all runs locally.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Easy-Medium | 3-5 hours | Python 3.10+, Pillow, local CLIP model, OpenAI API optional for phrasing only |

Built with Codex. The runtime needs above are this project's own.

## What you'll build

A local pass over your camera roll that reads the images in bulk and renders the
timeline as something you can look at. Not a photo browser. A report that shows
which months went quiet, where the longest gaps are, which broad subjects recur
across the year, and how the indoor and outdoor balance shifts from month to
month.

It deliberately does not look for people. There is no face detection, no
identity clustering, and no "who appeared when" timeline anywhere in this
project. It measures when photos exist and what kind of scene they show.

## What you'll learn

Vision models and timeline analysis.

- Running a vision model over thousands of images without paying for every one
- Reading dates and metadata as the spine of the analysis
- Turning a timeline into a shape you can read at a glance
- Recognizing that absence in the data is itself a finding

## Prerequisites

- **Python 3.10 or later.** Verified on 3.12.13 (macOS 26.5.1, Apple M2 Pro,
  16GB). Use `python3` everywhere, including inside the activated virtualenv.
- **Install:**

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  python3 -m pip install -r requirements.txt
  ```

  On Windows the activation line is `venv\Scripts\activate` instead. Every
  Python command in this README stays `python3`.

  That installs `Pillow==12.3.0`, `sentence-transformers==6.0.0`, and
  `openai==3.3.1`. sentence-transformers pulls in torch, which is a multi-GB
  download and the slowest part of the install. Metadata mode needs only Pillow,
  so you can start there.

- **Supported image formats:** `.jpg`, `.jpeg`, `.png`, `.webp`. **HEIC is not
  supported.** iPhone photos exported as HEIC will be skipped and counted, not
  silently ignored. Convert them first, or export as JPEG. This is not general
  camera-roll compatibility and the tool says so when it skips a file.
- **Optional: an OpenAI API key,** used only to phrase the summary paragraph from
  numbers the local pipeline already computed. Nothing about it touches images.
- **The local model:** `clip-ViT-B-32`, loaded through sentence-transformers and
  run on your machine. On the verification run it downloaded **588 MB** into
  `~/.cache/huggingface` and the whole first `--vision local` pass, download plus
  model load plus classifying 12 sample images, took **77 seconds** end to end.
  Download size is fixed; the time depends on your network and hardware, so
  expect a different number. Later runs reuse the cached weights and the sample
  finishes in under a second.
- **Start on a copy.** Point this at a copied folder holding a few months before
  you aim it at a whole camera roll. Local vision is sampled, but a scan of tens
  of thousands of files still takes real time, and you want to see the shape of
  the output before you wait for it.

## Local vs API

**Metadata mode** (`--vision metadata`, the default):

| Part | Runs where |
|---|---|
| Scanning files | 100% local |
| Reading EXIF, dates, orientation | 100% local |
| Duplicate detection | 100% local |
| Timeline, gaps, monthly counts | 100% local |
| Thumbnails and `report.html` | 100% local |
| Model | none |
| API | none |

**Local-vision mode** (`--vision local`): everything above, plus

| Part | Runs where |
|---|---|
| The CLIP model | 100% local, on your machine |
| Category and indoor/outdoor classification | 100% local |
| Label cache | 100% local, in your output folder |

No photo, thumbnail, or piece of metadata leaves the machine in either mode. The
only network access in the whole project is the one-time model download from
Hugging Face, and the optional phrasing call below.

**Optional OpenAI phrasing** (`--summary openai`, off unless you ask for it):

All image analysis is finished before this runs. OpenAI is not a vision path in
this project and there is no flag that makes it one. What gets sent is exactly
the output of `sanitized_aggregate()` in `analyze.py`:

- `date_range` as two `YYYY-MM` strings
- `photos_analyzed`, `photos_classified`, `duplicates_grouped`
- `monthly_counts`, `quiet_months`, `longest_gap_days`, `average_per_active_month`
- `category_counts` and `indoor_outdoor` totals
- `analysis_mode`

On the sample that payload is 346 bytes of numbers. What is never sent: images,
thumbnails, EXIF, GPS coordinates, filenames, absolute paths, per-photo rows, or
hashes. The model phrases the findings; it does not classify anything and does
not compute anything. The report is fully usable without it, and that is the
default. When this layer is on, it is no longer true that everything stayed on
your machine, so the report labels itself accordingly.

## How it works

```
photo folder
   ↓  scan recursively, skip hidden / unsupported / unreadable   photolib.scan
   ↓  date: EXIF DateTimeOriginal → filename date → file mtime
   ↓  correct EXIF orientation, record size
timeline records
   ↓  sha256 (exact dupes) + dHash (near dupes, within a month)  mark_duplicates
deduplicated monthly groups
   ↓  choose representatives spread across each month            pick_representatives
   ↓  months, gaps, busiest, quietest, deltas                    build_timeline
metadata mode ────────────────────────────────┐
local CLIP model on representatives ──────────┼──▶ categories + indoor/outdoor
(cached by content hash + settings)           ↓
                        analysis.json + thumbnails/ + cache.json
                                              ↓
                       report.html + summary written locally
                                              ↓
        optional: aggregate numbers only → OpenAI phrases the summary
                       (no image, no path, no EXIF)
```

## Build it

### Step 1: Run it as-is on the sample

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 analyze.py sample-data --vision metadata --output sample-output
open sample-output/report.html
```

On Linux use `xdg-open`, on Windows `start`. The report is a plain file with
relative links, so opening it directly works and no server is involved.

`sample-data/` holds 14 synthetic images drawn for this project, spread across
March to September 2025. Nothing in it is a real photograph. What you should see:

- **14 photos analyzed, 7 months in range, 2 with no photos.** June and July 2025
  are deliberately empty and appear in the timeline as flat bars tagged "no
  photos found". A gap only exists relative to a range, which is why the empty
  months are drawn rather than skipped.
- **March 2025 as the high month** with 6 photos against an average of 2.8 per
  active month; May with 1 as the quietest.
- **Longest gap: 79 days**, between 2025-05-18 and 2025-08-05.
- **2 duplicates grouped.** `IMG_0315.jpg` is a byte-exact copy of `IMG_0313.jpg`
  and `IMG_0314.jpg` is a near-copy shifted a few pixels. Both are excluded from
  representative selection, so one lunch does not get three slots in March.
- **Date sources: 9 from EXIF, 5 from filename.** The PNG and WebP samples carry
  no EXIF, so their dates come from the `2025-04-07-...` style filenames. Each
  thumbnail caption says which source its date came from.

### Step 2: Read the timeline builder

Two Python files. `photolib.py` holds everything photo-related; `analyze.py` is
the CLI, the cache, and the report.

**Discovery.** `photolib.scan()` walks the folder with `rglob`, skips anything
hidden, anything outside the four supported extensions, and anything Pillow
cannot open, collecting a reason for each skip instead of failing. It also skips
your output folder, so a second run never analyzes its own thumbnails.

**Dates.** EXIF `DateTimeOriginal` first, then a `YYYY-MM-DD` or `YYYYMMDD`
pattern in the filename, then the file's modification time. Every record stores
which of the three was used, and the report prints it, because mtime is a guess
that copying and exporting silently rewrite.

**Orientation.** `ImageOps.exif_transpose()` runs before width and height are
recorded, before the perceptual hash, and before the thumbnail is written. The
sample includes one image stored 640x480 with EXIF orientation 6; it is recorded
as 480x640 portrait and its thumbnail comes out upright.

**Duplicates.** `mark_duplicates()` groups exact copies by sha256 across the
whole collection, and near-copies by dHash Hamming distance **within the same
month**. The month scope is deliberate: bursts happen minutes apart, so two
structurally similar photos from March and September are usually two real
occasions rather than one redundant copy. Nothing is deleted or moved; group
members are marked and excluded from representative selection, and the counts are
reported. `--dupe-threshold` sets the bit distance, default 6 of 64.

**The timeline.** `build_timeline()` counts photos per month, then fills in every
month between the first and last so empty ones are visible, finds the longest gap
in days between consecutive photos, and ranks busiest and quietest active months.

**Representatives.** `pick_representatives()` takes up to `--max-per-month`
non-duplicate photos per month at evenly spaced positions after sorting by date,
offset by `--seed`. Taking the first N alphabetically would return one morning of
one day, which is how a report ends up looking like a single afternoon. Same
inputs and same seed give the same picks.

**Output folder:**

```
sample-output/
├── report.html      the thing you open
├── analysis.json    every number and per-photo record, for your own scripts
├── thumbnails/      one JPEG per representative, named by content hash
└── cache.json       local vision labels (only written in --vision local)
```

### Step 3: Turn on the local vision pass

```bash
python3 analyze.py sample-data --vision local --output sample-output-local
open sample-output-local/report.html
```

**First run.** The model is `clip-ViT-B-32`. On the verification machine it
downloaded 588 MB and the full first pass took 77 seconds; yours will differ with
network and hardware. Weights land in `~/.cache/huggingface` and are reused
afterwards, so the second run of the sample took under a second.

**The categories** are a fixed list in `photolib.CATEGORIES`, so the report stays
comparable between runs: nature, city_or_streets, travel_or_landmarks, food,
animals, work_or_screens, documents_or_screenshots, art_or_objects,
events_or_decorations, home_or_interior. There is no person, group, or social
category, and adding one is not an extension this project supports.

Each category is a small ensemble of phrasings whose embeddings are averaged into
one prototype. That is standard zero-shot CLIP practice and it measurably steadied
the results here: single-sentence prompts put the sample's city street and beach
in the wrong buckets, and the ensemble fixed both.

**Confidence.** An image is compared against every prototype and the winner has
to clear a threshold or the label becomes `unclear`. There are two thresholds
because there are two questions: `--confidence` (default 0.50) governs the 11-way
category choice, and `--io-confidence` (default 0.60) governs indoors versus
outdoors, which starts at 0.50 by pure chance and so needs a higher bar. Nothing
is forced into a confident label.

On the synthetic sample this lands at 5 outdoors, 4 indoors, 3 unclear, and two
images fall to `unclear` on category. That is the honest result: the ambiguous
ones are a crude still-life drawing and a flat beach scene, and the threshold
catches exactly those rather than dressing up a coin flip as a finding. Real
photographs classify more confidently than flat vector drawings do.

**Indoors versus outdoors** is scored as its own two-way comparison, not read off
the category list. It describes the picture. It is not a claim about how much time
anyone spends outside, and the report says so on the page.

**Why sampling.** Only the representative images per month are classified, not
every file. A camera roll with 40,000 photos would otherwise mean 40,000 forward
passes to answer a question about monthly shape, and the answer barely changes
after the first handful per month. Raise `--max-per-month` when you want more
confidence and are willing to wait.

**Nothing leaves the machine.** The model runs locally, the labels are cached
locally, and there is no code path in `--vision local` that opens a network
connection after the weights are on disk.

**Optional phrasing layer.** Separate feature, off by default:

```bash
cp .env.example .env
# add OPENAI_API_KEY and OPENAI_MODEL to .env, then export them
python3 analyze.py sample-data \
  --vision local \
  --summary openai \
  --output sample-output-openai-summary
```

This sends only the sanitized aggregate listed under [Local vs API](#local-vs-api):
month counts, quiet months, gap length, category totals, the indoor/outdoor
split, and the mode. 346 bytes of numbers on the sample. **No image is sent, and
no thumbnail, EXIF field, GPS coordinate, filename, or file path is sent.** The
run prints the payload size before it calls out. If either variable is missing it
says which one and keeps the local summary. If the call fails it prints the error
and keeps the local summary. Phrasing is cached against the aggregate, so an
unchanged rerun does not pay for the call twice.

### Step 4: Point it at your own camera roll

Start with a copy of a few months, not the whole library:

```bash
mkdir -p ~/Pictures/pattern-mirror-test
# copy a few months of photos in, then:
python3 analyze.py ~/Pictures/pattern-mirror-test \
  --vision local \
  --max-per-month 12 \
  --output ~/pattern-mirror-output
```

- **Formats:** `.jpg`, `.jpeg`, `.png`, `.webp`. HEIC is skipped and counted.
  Subfolders are searched.
- **Dates:** EXIF first, then a date in the filename, then file mtime. If a whole
  folder shows today's date, mtime was the fallback and your export reset it. Put
  `YYYY-MM-DD` in the filenames if the dates matter.
- **Monthly sample size:** `--max-per-month`, default 8. This is the main lever on
  runtime in local mode, because it sets how many images the model sees.
- **Output location:** keep it outside the photo folder. The tool refuses an
  output path inside the input, because the next run would ingest its own
  thumbnails. `~/pattern-mirror-output` is a fine default.
- **Cache:** `cache.json` lives in the output folder, keyed by image content hash
  plus a fingerprint of the model, category list, and both thresholds. Unchanged
  photos are never reclassified; changed ones are. Change a threshold or the
  category list and the whole cache is correctly discarded rather than reused.
  Clear it by hand with `--clear-cache`, or by deleting the file.
- **Keep it out of Git.** `output/`, `sample-output*/`, `my-photos/`, and `.env`
  are already in the repo's `.gitignore`. Your photos, the thumbnails generated
  from them, `analysis.json`, and the report all describe your life in detail.
  Point `--output` somewhere outside the repo entirely and the question does not
  arise.

### Step 5: Make it yours

- **Change the categories.** Edit `photolib.CATEGORIES`, add your own phrasings,
  rerun. The cache fingerprint changes, so old labels are dropped automatically.
- **Different sample size:** `--max-per-month 20` for a denser read of each month.
- **Tighter or looser duplicates:** `--dupe-threshold 3` catches only very close
  copies, `12` groups aggressively. Watch the exact and near counts move.
- **Adjust the indoor/outdoor bar:** `--io-confidence 0.75` pushes more images
  into `unclear` and leaves you with fewer, firmer calls.
- **Compare two ranges:** run it on two folders, one per year, into two output
  folders, and read the reports side by side.
- **Change the report:** `report_template.html` is a plain file with `{{TOKEN}}`
  placeholders that `render_report()` fills. Edit the CSS or reorder the sections;
  there is no build step.

## How to build this with ChatGPT, Work, and Codex

> Frame this as the workflow a reader follows, not as a record of how this specific
> implementation was produced. Do not claim these tools performed this build.

This project can be built manually from the README alone. The prompts in
[prompts.md](prompts.md) provide an optional AI-assisted path.

- **ChatGPT Chat:** helps you clarify the implementation, supported inputs, the
  local-analysis boundary, the privacy rules, and the smallest runnable version,
  before any code exists.
- **ChatGPT Work:** turns your approved decisions into the ordered five-step
  checklist that this README reflects.
- **Codex:** helps you implement each step, run the commands, inspect failures,
  and verify that the code matches what the README claims.

## Verify it works

- [ ] `python3 analyze.py sample-data --vision metadata --output sample-output`
      creates `sample-output/analysis.json` and `sample-output/report.html`
- [ ] The report header reads "Mar 2025 to Sep 2025"
- [ ] Jun 2025 and Jul 2025 appear in the timeline with a count of 0 and a
      "no photos found" tag
- [ ] The stats row shows a 79-day longest gap and 2 duplicates grouped
- [ ] March shows 4 representative thumbnails from 6 photos, and the exact and
      near copies of `IMG_0313.jpg` are not among them
- [ ] Each thumbnail caption names its date source, and at least one says
      "date from filename"
- [ ] `--vision local` adds a "Broad visual categories" section with counts
- [ ] `--vision local` adds an "Indoors and outdoors" section, and `unclear` is a
      visible bucket rather than everything being forced into a label
- [ ] Local mode works with `OPENAI_API_KEY` unset. Nothing prompts for a key
- [ ] `python3 analyze.py --help` offers no OpenAI vision mode. `--vision` accepts
      only `metadata` and `local`
- [ ] Without `--summary openai`, the report footer says the summary was written
      locally and nothing left the machine
- [ ] With `--summary openai` and no key set, it names the missing variable and
      keeps the local summary
- [ ] `analysis.json` from an `--summary openai` run has a
      `sanitized_aggregate_sent` field containing only numbers: no image data, no
      thumbnail, no EXIF, no GPS, no absolute path, no filename
- [ ] A second unchanged `--vision local` run reports "12 cached, 0 to classify"
- [ ] Editing one sample image and rerunning reports "12 cached, 1 to classify"
- [ ] Changing `--confidence` prints that cached labels no longer apply
- [ ] A folder with a `.txt`, a hidden file, a zero-byte `.png`, and a corrupt
      `.jpg` skips all four by name and still analyzes the good file
- [ ] An empty folder exits non-zero with a message naming the supported formats
- [ ] `--output sample-data/out` is refused, because the scan would re-ingest its
      own thumbnails
- [ ] `report.html` opens from the filesystem with no server, and contains no
      external requests and no absolute paths
- [ ] `git status` shows no photos beyond `sample-data/`, no thumbnails, no
      `analysis.json`, no `cache.json`, no `.env`
- [ ] The report contains no face, identity, or people-presence claim. The only
      mentions of those words are the note saying the tool does not do them

## Extend it

- **Run it again later and compare reports**, so what you are looking at is the
  change rather than the snapshot
- Add your own category list for the subjects you actually photograph
- Add a `--since` / `--until` date filter and analyze one season at a time
- Compare the indoor/outdoor split between two seasons from two runs
- Track the average colour of each month and see the palette shift across the year
- Export a compact markdown summary next to the HTML report

Face clustering, identity matching, and people-presence timelines are out of
scope by design, not by omission.

## Common pitfalls

- **The first local run seems to hang.** It is downloading the model. 588 MB and
  77 seconds total on the verification machine (`clip-ViT-B-32`, macOS 26.5.1, M2
  Pro, 16GB); a slower connection makes that much longer. It happens once.
- **Installing takes a while.** sentence-transformers pulls torch, which is the
  bulk of the multi-GB install. Metadata mode needs only Pillow if you want to see
  the pipeline first.
- **Every photo is dated today.** No EXIF and no date in the filename, so
  everything fell through to file mtime, which exporting and copying reset. The
  report tells you the split; put dates in the filenames to fix it.
- **HEIC files are all skipped.** They are not supported. Convert or export to
  JPEG first. The scan names each skipped file so this is visible, not silent.
- **A burst of 30 near-identical photos still dominates a month.** Raise
  `--dupe-threshold`. Near-duplicate grouping is scoped within a month, so it will
  not touch a similar photo from a different month.
- **Categories are approximate.** This is a general-purpose model doing zero-shot
  classification against fixed phrasings, not a trained classifier for your
  library. On the flat synthetic samples two of twelve images land in `unclear`.
  Treat the counts as a rough read, not a measurement.
- **Indoor/outdoor is uncertain on ambiguous images.** A desk by a bright window
  or a covered terrace can go either way. Those land near 0.5 and become
  `unclear`, which is why the threshold is 0.60 rather than 0.50.
- **A large library takes a long time.** The scan hashes and opens every file even
  though only representatives are classified. Test on a copied subset first.
- **`--summary openai` sends data off the device.** Aggregate numbers only, never
  images, but it is still a network call about your photo activity. Leave it off
  for anything you would not describe out loud.
- **Stale labels after changing the model or the categories.** Handled: the cache
  fingerprint covers the model name, the category list, the prompts, and both
  thresholds, so incompatible entries are discarded rather than reused. If you
  ever want a clean slate anyway, `--clear-cache`.
- **Output folder inside the photo folder.** Refused outright, because the next
  run would read its own thumbnails as photos.
- **Reading the report as a story about a life.** A quiet month means fewer files
  were found in that month. It does not mean anything about how anyone felt, and
  the correlations in this report are not evidence about emotional state,
  relationships, or life events. The report repeats this at the bottom.
- **Expecting it to track people.** It does not. There is no face detection, no
  identity clustering, and no "who appeared when" analysis anywhere in the code.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
