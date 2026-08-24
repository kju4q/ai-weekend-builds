# 03: Lookout

Sweeps the sources you name every morning and compares what it finds against
every version it has saved. It stays silent while nothing moves, and reports the
diff when something changes.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Medium | 4-6 hours | Python 3.10+, requests, cron or a scheduled workflow, local version archive, OpenAI API optional for judging a change |

Built with Codex. The runtime needs above are this project's own.

## What you'll build

A daily job that watches the pages you care about so you stop checking them
yourself. It saves every version it fetches, compares the new one against the
history, and says nothing at all on the days nothing changed.

The script itself checks once and exits. It does not run in the background and
it does not schedule itself. Step 4 is where you hand it to cron, and that step
is what turns a script into a lookout.

## What you'll learn

Scheduled agents, state, and diffing.

- Storing state between runs, which is what separates an agent from a script
- Diffing versions and deciding what counts as a real change
- Scheduling a job and having it stay quiet by default
- Writing a notification worth reading, because it only arrives when it matters

## Prerequisites

- **Python 3.10 or later.** Verified on 3.12.13 (macOS 26.5.1, Apple M2 Pro).
  Use `python3` everywhere, including inside the activated virtualenv.
- **Install:**

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  python3 -m pip install -r requirements.txt
  ```

  On Windows the activation line is `venv\Scripts\activate`. That installs
  `requests==2.34.2`, `PyYAML==6.0.3`, and `openai==3.3.1`. Nothing else is
  downloaded and there is no model to fetch. The install took 9 seconds on the
  verification machine with the wheels already in pip's cache; a cold download of
  three small pure-Python wheels is still quick, but expect more than 9 seconds. Text extraction uses `html.parser` and
  diffing uses `difflib`, both from the standard library.
- **The config** is a YAML file. Each source needs a `name` and either a `url`
  to fetch or a `path` to read from disk. `sources.example.yml` is documented
  inline and is what Step 1 runs against.
- **Optional: an OpenAI API key,** only for `--judge`. Everything works without
  it, and without it is the default.
- **Sources are public web pages.** This fetches a URL with `requests` and reads
  the HTML. It does not log in, does not run JavaScript, and does not get past
  bot protection. See Step 3 for what that rules out.

## Local vs API

| Part | Runs where |
|---|---|
| Fetching your named sources | Local process, over the network |
| Extracting the readable text | 100% local |
| Diffing against the archive | 100% local |
| The version archive | 100% local, on your disk |
| Deciding whether a change matters | Your own eyes, or optional OpenAI with `--judge` |

Without `--judge`, nothing about your sources is sent anywhere except the request
to the page itself. The whole detection path is mechanical: extract text, blank
out the churn, hash it, compare, diff.

With `--judge`, and only when both `OPENAI_API_KEY` and `OPENAI_MODEL` are set,
one thing is sent per detected change: **the source name and the unified diff of
that single change.** Not the archive, not the full page, not your other sources,
not the URL. If three sources change in one run, that is three separate calls,
each carrying only its own diff. Judgment is a layer on top of detection, never
the thing doing the detecting: a change is found by diffing before the model is
asked about it, so the model's opinion cannot invent or suppress a change.

## How it works

```
sources.yml
   ↓  fetch each source (requests, or read a local path)
raw HTML
   ↓  extract readable text (html.parser, drops script and style)
   ↓  blank out ignored churn: timestamps, counters, build ids
normalized text
   ↓  hash it, compare against the newest archived version
identical            →  stay silent
ignored text only    →  stay silent, one quiet line
really different     →  archive the new version
                        ↓
                     unified diff, with both version stamps
                        ↓
                     optional: --judge sends that diff to OpenAI
                     for a matters / does not matter / unclear call
```

## Build it

### Step 1: Run it as-is on the fixtures

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
cp fixtures/status-page.v1.html fixtures/current.html
python3 check.py --sources sources.example.yml
```

`sources.example.yml` watches `fixtures/current.html`, a local file, so this runs
offline with no network and no live page that has to change on cue. The first run
prints:

```
First run for 1 source: Northwind plans.
Archived as the baseline. Nothing is reported as changed on a first run, because
there is nothing to compare against yet.
```

That is the documented first-run behaviour: everything is new, everything is
archived, nothing is reported. Run it again and it stays quiet:

```
Nothing meaningful changed (1 byte-identical).
```

Now make the page really change. `fixtures/status-page.v2.html` raises the Team
price, puts a region into degraded status, and shortens the refund window:

```bash
cp fixtures/status-page.v2.html fixtures/current.html
python3 check.py --sources sources.example.yml
```

```
=== CHANGED: Northwind plans
    2026-08-24T19-41-45Z  ->  2026-08-24T19-41-45Z-2

--- Northwind plans @ 2026-08-24T19-41-45Z
+++ Northwind plans @ 2026-08-24T19-41-45Z-2
@@ -3,10 +3,10 @@
 Plans
 Starter: $12 per month, 2 projects, community support
-Team: $40 per month, 10 projects, email support
+Team: $48 per month, 10 projects, email support
 Business: $150 per month, unlimited projects, priority support
 Service status
-All systems operational.
+Degraded performance in the EU-West region. We are investigating.
 Policies
-Annual plans are billed up front. Refunds are available within 30 days of purchase.
+Annual plans are billed up front. Refunds are available within 14 days of purchase.
 Data is retained for 90 days after cancellation.
 Last updated: <ignored>
```

Three real changes, named, with both version stamps. Then the interesting case.
`fixtures/status-page.v3.html` changes the "Last updated" timestamp, the render
timer, the visitor counter, the build id, and a session token in a script tag,
and changes nothing a reader would care about:

```bash
cp fixtures/status-page.v3.html fixtures/current.html
python3 check.py --sources sources.example.yml
```

```
Nothing meaningful changed (1 changed only in ignored text).
```

That silence is the feature. A page that rewrites its own footer on every request
would otherwise wake you every morning with nothing to say. Note also that v3 was
not archived: a new version that says the same thing is not worth keeping, so the
archive still holds two versions, not three.

### Step 2: Read the checker

One file, `check.py`, and the flow is worth following end to end.

**Config.** `load_sources()` reads the YAML, then validates it rather than
trusting it: a missing file, an empty file, malformed YAML, a source with no
`name`, a source with neither `url` nor `path`, and duplicate names each produce
their own message and a non-zero exit. Names are unique because the name keys the
archive folder, so renaming a source starts its history over.

**Fetch.** `fetch()` reads a local `path` directly, or GETs a `url` with a 20
second timeout and a named User-Agent. Each source is fetched inside its own
try/except in `check_one()`, so one dead host cannot take down the run.

**Extraction.** `extract_text()` runs an `html.parser` subclass that drops
`script`, `style`, `noscript`, `template`, `svg`, and `head` entirely, and turns
block-level tags into line breaks so the diff lands on readable lines. What gets
compared is **text content, never raw bytes**: minified CSS, reordered
attributes, and a rebuilt JS bundle are invisible here, and that is most of what
a redeploy changes on a page whose words did not move.

**Normalization.** `normalize()` replaces every match of the ignore patterns with
`<ignored>`. The defaults in `DEFAULT_IGNORE` cover timestamps, clock times,
render timers, "Visitors today" counters, build identifiers, and hex tokens. This
is a regex list, not intelligence: it catches the patterns named in it and
nothing else. Step 5 covers adding your own.

**Comparison.** `check_one()` hashes the normalized text and compares it against
the newest archived version. Equal hashes mean silence, and the run distinguishes
"byte-identical" from "changed only in ignored text" so you can tell which is
happening. Different hashes mean a new version is archived and a unified diff is
printed, computed on the normalized text so a line whose only change was a
timestamp never reaches the report.

**The archive.** One JSON file per version under `archive/<slug>/<stamp>.json`,
holding the extracted text, both hashes, the URL, and the fetch time. Writes go
through a temp file and an atomic replace. A new version is only written when the
normalized text actually changed, which is what keeps the archive from filling
with identical entries.

One detail worth knowing about, because it is the kind of bug that hides for
months: `versions()` sorts on the filename **stem**, not the whole filename. With
the extension attached, `...10Z-2.json` sorts before `...10Z.json`, because `-`
is below `.` in ASCII, and the newest version would be read as the oldest. That
only bites when two runs land inside the same second, which is exactly what
replaying the fixtures does.

### Step 3: Point it at your own sources

```bash
cp sources.example.yml sources.yml
```

Then edit it:

```yaml
sources:
  - name: Landlord fee schedule
    url: https://example.com/fees
    note: The bit I care about is the late-payment section.

  - name: Some status page
    url: https://status.example.com/
    ignore:
      - 'Queue length: \d+'
      - 'Quote of the day:.*'
```

```bash
python3 check.py --sources sources.yml
```

`sources.yml` is already gitignored, because your watch list says a lot about
you.

**What works.** Public pages that return their content in the initial HTML
response. Documentation, pricing pages, policy and terms pages, status pages,
changelogs, job boards, council and government notice pages.

**What does not work,** and this is not a limitation you can configure your way
out of:

- **Anything behind a login.** There is no session handling and no cookie jar.
- **Bot-protected pages.** Cloudflare interstitials, hCaptcha, and friends return
  a challenge page. The Lookout will faithfully archive the challenge page and
  then tell you every time the challenge token rotates.
- **JavaScript-rendered content.** No browser runs here. If the content arrives
  by fetch after page load, the extracted text will be the empty shell. When
  extraction finds no readable text at all, the source reports an error rather
  than silently archiving nothing.
- **Pages that are mostly one changing number.** Technically it works, but every
  run is a change and you will turn it off within a week.

Check a new source once by hand before trusting it: `--only "Some source"` runs
just that one, and `--show "Some source"` prints exactly what got archived, which
is the fastest way to find out you archived a cookie banner.

**First run.** Everything is new, everything is archived, nothing is reported as
changed. There is no baseline to compare against yet, so a first run that said
"changed" would be lying.

**How the archive grows.** One JSON file per meaningful change per source,
holding that version's extracted text. A page of a few thousand words is a few
kilobytes, so a source that really changes once a week costs a few hundred
kilobytes a year. Sources that never change cost nothing after the baseline,
because unchanged and noise-only fetches are not archived. It is plain files, so
`du -sh archive/` tells you the truth and deleting a source's folder resets its
history.

Look at what you have collected with:

```bash
python3 check.py --sources sources.yml --history "Landlord fee schedule"
python3 check.py --sources sources.yml --show "Landlord fee schedule" --version 2026-08-24T19-41-45Z
```

The first lists every archived version oldest first, with how many lines changed
between each. The second prints the text of one version, which is the "what did
this page say three weeks ago" question the archive exists to answer.

### Step 4: Put it on a schedule

Nothing above runs on its own. `check.py` checks once and exits. This step is
what makes it a lookout rather than a script you forget to run.

Use absolute paths, use the virtualenv's Python directly, and use `--quiet` so
cron only mails you when something actually changed:

```bash
crontab -e
```

```cron
# Lookout: every morning at 07:15
15 7 * * * cd /Users/you/lookout && /Users/you/lookout/venv/bin/python3 check.py --sources sources.yml --quiet
```

The five fields are minute, hour, day of month, month, day of week. `15 7 * * *`
is 07:15 every day. `0 * * * *` would be the top of every hour.

With `--quiet` the script prints nothing on a run where nothing changed, and cron
mails you only when a command produces output. So a silent morning means a silent
inbox, and anything arriving in that inbox is a real diff. Verified: a `--quiet`
run against unchanged sources produced zero bytes of output.

Two things to know. Cron does not load your shell profile, so if you use
`--judge` you have to set the variables in the crontab itself or source a file in
the command. And cron only fires while the machine is awake; a laptop that was
shut at 07:15 simply misses that run, and the next run compares against whatever
was last archived, so nothing is lost beyond the timing.

**The alternative:** a scheduled workflow, GitHub Actions being the obvious one,
runs on a schedule without your machine being on. It changes the problem rather
than removing it: the archive has to live somewhere that persists between runs,
which means committing it to the repo or using the cache, and a public repo means
publishing your watch list. Honest summary: cron on a machine that is usually on
is the simpler answer for a personal lookout, and a scheduled workflow is the
right answer when you need it to run whether or not you are.

### Step 5: Turn on change judgment

Detection is already done by this point. A diff has been found mechanically and
archived. The optional layer only answers "does this matter", and only when you
ask for it:

```bash
cp .env.example .env
# put OPENAI_API_KEY and OPENAI_MODEL in it, then export them
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=<a chat model your account can call>
python3 check.py --sources sources.yml --judge
```

Both variables are required and there is no default model, on purpose: model
names change and this project will not guess one for you. With `--judge` and no
key it says so and prints the raw diff, which is the default behaviour anyway.

What is sent, per changed source: the source name and that source's unified diff.
Nothing else. Not the archive, not the full page text, not the URL, not your other
sources. The prompt is in [prompts.md](prompts.md) and requires the model to judge
only the supplied diff, to answer `unclear` when the diff is ambiguous rather
than guessing, and to keep it to a sentence or two. The output looks like:

```
=== CHANGED: Northwind plans
    2026-08-24T19-41-45Z  ->  2026-08-24T19-41-45Z-2
    matters: yes
    The Team plan price rose from $40 to $48 and the refund window shortened
    from 30 days to 14.

--- Northwind plans @ ...
```

The diff is always printed underneath, so the judgment is something you can check
rather than something you have to trust. If the call fails, the failure is printed
and the diff is unaffected: detection never depended on it.

## How to build this with ChatGPT, Work, and Codex

This project can be built by hand from this README alone. If you would rather
build it with AI help, this is the path, and the prompts are in
[prompts.md](prompts.md).

- **ChatGPT Chat** for the thinking, before any code. Pin the concept, then settle
  the smallest complete version: the config shape, what "meaningful change" means,
  where the line sits between mechanical diffing and AI judgment, and what should
  happen on a first run.
- **ChatGPT Work** to turn those decisions into the ordered build checklist: the
  five steps, the file list, the dependencies, the install sequence, and the
  acceptance checks.
- **Codex** to implement it stage by stage against that checklist, running each
  command as it goes, then to review its own work from a clean environment and
  check the README's claims against the code.

Described this way it is the workflow you follow, not a transcript of how this
particular copy was produced.

## Verify it works

- [ ] `cp fixtures/status-page.v1.html fixtures/current.html` then
      `python3 check.py --sources sources.example.yml` archives the baseline and
      reports nothing as changed
- [ ] A second identical run prints "Nothing meaningful changed (1 byte-identical)"
- [ ] Copying `status-page.v2.html` over `current.html` and rerunning reports a
      diff naming the source, both version stamps, and the three real changes:
      the Team price, the degraded region, and the refund window
- [ ] Copying `status-page.v3.html` over it and rerunning prints "Nothing
      meaningful changed (1 changed only in ignored text)" and reports no diff
- [ ] After all three, `--history "Northwind plans"` lists exactly two archived
      versions, not three, because the noise-only fetch was not archived
- [ ] `--show "Northwind plans" --version <the older stamp>` prints the original
      `$40` price and `All systems operational`, so the archive really does
      remember what the page said before
- [ ] A config with a real URL fetches it successfully over the network
- [ ] A config mixing a working source, a live URL, and an unresolvable host
      reports the failure on stderr, still checks the other two, and exits 1
- [ ] Two runs on identical content leave one archived version per source
- [ ] Everything above works with `OPENAI_API_KEY` unset. Nothing prompts for a key
- [ ] `--judge` without the variables set says which are missing and prints the
      raw diff instead
- [ ] `--quiet` on an unchanged run prints zero bytes, which is what makes the
      cron line quiet
- [ ] A missing, empty, or malformed config, a source with no URL, and duplicate
      source names each produce their own message and exit 1
- [ ] `python3 -m py_compile check.py` is clean
- [ ] Nothing in the code schedules anything: `check.py` has no loop, no sleep, no
      daemon, and no background thread. It checks once and exits, and Step 4 is
      the only thing that makes it recur
- [ ] `git status` shows no `archive/`, no `sources.yml`, no `.env`, and no
      `fixtures/current.html`

## Extend it

- **Teach it which kinds of change you care about**, so a reworded footer stays
  silent and a changed price does not. Per-source `ignore` patterns are the blunt
  version of this; a rule that only watches one CSS section would be the sharp one
- Watch one region of a page by extracting between two marker strings before
  diffing, so a busy page stops being noisy
- Send the report somewhere other than stdout: a webhook, a note file, an email
- Add `--since` to `--history` so you can diff today against a version from a
  month ago rather than against the previous one
- Keep a small per-source log of how often it changes, so you can spot the sources
  that are not worth watching

## Common pitfalls

- **You forgot Step 4.** The most common failure by far. The script only runs when
  invoked, and nothing in it schedules itself. If you have not added the cron
  line, you do not have a lookout, you have a command.
- **The first run tells you nothing, and that is correct.** There is no baseline
  yet. Real reporting starts on the second run.
- **A page returns a bot challenge instead of content.** The Lookout will archive
  the challenge page and then report a change every time its token rotates. Use
  `--show` on a new source to see what actually got archived before you trust it.
- **A JavaScript-rendered page archives as an empty shell.** No browser runs here.
  If extraction finds no readable text at all, the source reports an error instead
  of quietly archiving nothing, but a page with a little static chrome and all the
  real content in JS will archive the chrome without complaint.
- **Silent churn that the ignore patterns miss.** The defaults catch timestamps,
  counters, build ids, and hex tokens. A rotating testimonial, a "3 people are
  viewing this" widget, or a shuffled related-links block will sail straight
  through and report as a change. Add a per-source `ignore` regex, then rerun. The
  filtering is a regex list, not judgment.
- **Ignore patterns that are too greedy.** `\d+` anywhere in the list would blank
  out the price you are watching. The patterns are applied to the whole page, so
  keep them anchored to the surrounding words.
- **Renaming a source in the config starts its history over.** The name keys the
  archive folder. Rename the folder under `archive/` at the same time if you want
  to keep the history.
- **`--judge` sends the diff off the device.** Only that one diff, never the
  archive, but it is still a network call containing a piece of a page you watch.
  Leave it off for anything private.
- **Cron does not see your shell profile.** A crontab line that relies on
  `OPENAI_API_KEY` from your `.zshrc` will silently run without it, print the raw
  diff, and look like the judgment layer is broken. Set variables in the crontab.
- **A sleeping laptop misses runs.** Cron does not catch up. Nothing is lost from
  the archive, but the timing of what you notice depends on the machine being awake.
- **The archive grows, slowly.** A few kilobytes per real change per source.
  Watch it with `du -sh archive/`, and delete a source's folder if you stop caring
  about its history.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
