# Prompts: Lookout

> These are **AI-assisted build prompts**: a path a reader can follow with
> ChatGPT Chat, ChatGPT Work, and Codex. They are not a record of how this
> repository's implementation was produced, and they do not claim those tools
> performed this build. The project can be built by hand from the README alone.

Two different things live in this file. The build prompts below are optional
scaffolding for a reader. The **runtime prompt** further down is real: it is the
exact prompt `check.py` sends when you pass `--judge`.

Detection needs no prompt at all. Finding a change is `difflib` against a saved
version, and it works with no key, no model, and no network beyond the fetch.

## AI-assisted build path

### 1. ChatGPT Chat: clarify the implementation

```
I am building a project called Lookout. The concept is locked and I do not want
it redesigned:

  A command-line check run. It reads a list of public web pages from a config
  file, fetches each one, compares it against every version it has saved before
  in a local archive, stays silent when nothing meaningful changed, and reports
  a clear diff when something did. The archive is the point: it knows what a
  page said three weeks ago, not just what it says now.

Do not propose a different product. No web interface, no database service, no
hosted monitoring service, no accounts. It is a weekend project: one Python file
and a config file. The script does not run itself; scheduling is the user's step
with cron, and I want that stated plainly rather than hidden behind any
suggestion of background magic.

Two boundaries I want held. First, detection is mechanical: diff against saved
versions, no model involved. Any AI judgment sits on top and only decides whether
an already-detected change matters. Second, the no-key path has to work end to
end and report the raw diff.

Help me pin down the smallest version that actually runs:

- Config format: what each source entry needs, and what should be optional.
- What exactly gets compared. Raw bytes are hopeless, so what is the extraction
  step, and what does it deliberately throw away?
- Silent churn: timestamps, view counters, build ids, session tokens. How do I
  stop those from waking me every morning, and what is the honest limit of
  whatever approach we pick? I would rather ship a documented limit than an
  overclaimed filter.
- When a new version should be written to the archive, so re-running does not
  fill it with identical entries.
- First-run behaviour, and why reporting a change on a first run would be wrong.
- Failure cases: missing config, malformed config, one source failing while
  others work, a page that returns no readable text, two runs in the same second.
- What the reader is allowed to expect this to work on, and what it cannot work
  on at all. I want the limits in the README, not discovered later.
- Verification: how do I prove no-change silence, real-change detection, and the
  noise case, without waiting for a live page to change?

Ask me only the implementation questions you actually need answered. Do not write
code yet. Finish with the decisions we settled, as a list.
```

### 2. ChatGPT Work: turn decisions into a checklist

```
Here are the decisions from our discussion:

[paste the decision list from step 1]

Turn them into a build checklist for a single weekend project. Produce:

1. Five build steps, in this order and no other: run it as-is on the fixtures,
   read the checker, point it at your own sources, put it on a schedule, turn on
   change judgment. Exact commands for each, using python3 throughout.
2. The minimal file list. Nothing beyond what those five steps need.
3. CLI behaviour: every flag, its default, and what it validates or refuses.
4. Dependencies, with the reason each one exists and what breaks without it.
5. Fixture requirements: the saved page versions needed to prove no-change
   silence, real-change detection, and the noise case offline, with no live page
   that has to change on cue.
6. The install sequence from a clean clone.
7. The local/API table: what runs locally, and exactly what leaves the machine
   when the optional judgment layer is on.
8. Acceptance checks: objective and runnable, one per requirement, including the
   no-key path and the one-source-fails-mid-run case.
9. Privacy and safety checks: what must never be committed, what must never be
   sent, and how each is enforced rather than promised.

Rules for your output:
- Do not create extra repository documents. No build plan, no build log, no
  architecture file. This checklist goes into the README and nowhere else.
- Keep detection mechanical and keep AI judgment optional and on top.
- The scheduling step stays the user's step, described honestly.
- Keep it achievable in one weekend.

Return a concise checklist I can copy into the README and hand to Codex.
```

### 3. Codex: implement the project

```
Read the README and everything currently in this folder before changing
anything. Preserve the existing description and scope.

Implement in small stages. After each, run it and show me the real output.

1. Config loading and validation. Missing file, empty file, malformed file, a
   source with no name, a source with neither url nor path, and duplicate names
   each get their own message and a non-zero exit.
2. Fetch and extract. Local paths read from disk; URLs fetched with a timeout and
   a named User-Agent. Extraction pulls readable text and drops script and style
   entirely. Compare text content, never raw bytes.
3. Normalization and comparison. Blank out the churn patterns, hash the result,
   compare against the newest archived version. Distinguish byte-identical from
   changed-only-in-ignored-text, and stay quiet for both.
4. The archive. One file per version, written atomically, and only written when
   the normalized text actually changed. Plus a history command and a command to
   print one past version.
5. Fixtures: a baseline page, a version with real content changes, and a version
   whose only changes are timestamps and counters. Prove all three behaviours
   offline.
6. The optional judgment layer, last. Off unless explicitly requested. Sends one
   diff per changed source and nothing else. Model name from the environment,
   never hardcoded. A failed call prints the error and leaves the diff intact.

Constraints:
- Do not rename the project or rewrite its opening description.
- Detection must never depend on the model. Verify the whole flow works with no
  key set.
- Nothing in the code may schedule itself: no loop, no sleep, no daemon.
- One failing source must not end the run.
- Every error path prints what to do next.
- Touch no other project in this repository.

Run every command you put in the README. If something fails, fix it and show me
the passing output.
```

### 4. Codex: verify and review

```
Review this project as if you had just cloned it and never seen it before.

1. Create a clean virtualenv, install from requirements.txt, and follow the
   README commands exactly as written, in order.
2. Run the three fixture flows: baseline, real change, noise. Confirm each
   behaves exactly as the README says, including which of them archives a version
   and which does not.
3. Confirm the archive really holds history: print an older version and check it
   shows the pre-change content.
4. Do one real fetch against a stable public page. Do not claim anything about
   monitoring over days; this is a single-session check.
5. Put a deliberately unresolvable host in a config alongside working sources.
   Confirm the run continues, reports the failure, and exits non-zero.
6. Re-run on identical content and confirm no duplicate archive versions.
7. Test the config error paths and the history and show commands.
8. Confirm the whole thing works with no API key set, and that --judge without a
   key explains itself and falls back to the raw diff.
9. Search the code for anything implying background execution. There should be no
   loop, no sleep, no daemon, and no claim in the docs that it runs itself.
10. Compare every claim in the README against the code, especially the claims
    about what is compared and what leaves the machine.
11. Confirm the archive, the user's own config, and .env cannot be committed, and
    that no real key is present anywhere.

Fix only confirmed problems. Do not refactor working code, do not add features,
and do not create planning documents. Report what you changed, and report clearly
what you could not test and why.
```

## Runtime prompt

The exact system prompt in `check.py`, sent only when `--judge` is passed with
both `OPENAI_API_KEY` and `OPENAI_MODEL` set:

```
You judge whether a change to a web page matters to someone watching that page.
You are given a unified diff and nothing else: no browsing, no page history, no
other context.
Rules:
- Judge only what is in the diff. Never describe anything the diff does not show.
- If the diff is too ambiguous to call, say so plainly and set matters to
  "unclear". Uncertainty is a valid answer and is better than a guess.
- Never invent a reason for the change, a date, a number, or a consequence.
- Quote or name the concrete thing that changed, using the diff's own words.
- Be brief. One or two sentences.
Return valid JSON only, with exactly these keys:
{"matters": "yes" | "no" | "unclear", "summary": string}
```

The user turn is the source name and the diff, and nothing else:

```
Page being watched: Northwind plans

Unified diff:
--- Northwind plans @ 2026-08-24T19-41-45Z
+++ Northwind plans @ 2026-08-24T19-41-45Z-2
@@ -3,10 +3,10 @@
 Plans
-Team: $40 per month, 10 projects, email support
+Team: $48 per month, 10 projects, email support
 Business: $150 per month, unlimited projects, priority support
-All systems operational.
+Degraded performance in the EU-West region. We are investigating.
```

Each clause is doing a job:

- **"a unified diff and nothing else"** is the honest description of what the
  model receives, and it sets up every other rule. The archive is not sent. The
  full page is not sent. The model cannot look anything up.
- **"Judge only what is in the diff"** keeps the summary anchored to lines the
  reader can see for themselves, directly underneath. It is also the reason the
  diff is always printed: the judgment is checkable, not authoritative.
- **"set matters to unclear"** is the clause that earns the layer its place. A
  model asked "does this matter" will always produce an opinion. A footer reword
  and a changed refund window can look similar in a diff, and a confident wrong
  call is worse than no call, because it trains you to stop reading the diff.
- **"Never invent a reason, a date, a number, or a consequence"** blocks the
  specific failure this task invites. A price rise invites "as part of their
  annual pricing update", which the diff does not say and which may be false.
- **"Quote or name the concrete thing, using the diff's own words"** because
  "the pricing section was updated" is not worth a notification, and
  "the Team plan went from $40 to $48" is.
- **"One or two sentences"** because this arrives in a cron email above a diff you
  are about to read anyway.
- **"Return valid JSON only"** so the report can place `matters` and `summary`
  separately, and a malformed reply fails loudly instead of landing mid-report.

Judgment never gates detection. The change was found by diffing before the model
was asked anything, so a wrong answer, a failed call, or no key at all changes
what you read, never whether the change was caught.

## Tuning

- **What counts as a meaningful change**: the `DEFAULT_IGNORE` list in
  `check.py`, plus per-source `ignore` regexes in the config. Anything matching is
  blanked to `<ignored>` before comparison, so it can churn without reporting.
  Adding a pattern is how you quiet a noisy source. Removing the defaults for one
  source, with `use_default_ignores: false`, is how you watch a page exactly as it
  came, timestamps included.
- **Extraction strictness**: `_TextExtractor.SKIP` decides which tags are dropped
  wholesale. Adding `nav` and `footer` there is the single biggest win on a page
  whose chrome is noisier than its content, at the cost of never noticing a
  changed nav item. `BLOCK` decides where line breaks land, which decides how the
  diff is grouped: fewer block tags means longer lines and coarser diffs.
- **Diff context size**: `--context N`, default 2. Raise it to 5 when a one-line
  diff is not enough to tell what section changed, drop it to 0 for the smallest
  possible cron email.
- **Judgment summary length**: change the last rule in the system prompt. "One
  sentence" makes it a subject line. Adding "Name the section of the page it
  appeared in" makes it more useful on long pages and slightly longer.
- **Noisy sources**: work in this order, because each step is cheaper than the
  next. Add a per-source `ignore` pattern; then add `nav` or `footer` to the
  skipped tags; then extract only the region you care about between two marker
  strings; then accept that the page is not watchable and drop it. A source that
  reports a change every single run is worse than no source, because it teaches
  you to ignore the run.
- **How often to check**: the cron schedule, not a setting in the code. Daily
  suits policy and pricing pages. Hourly suits a status page you are actively
  waiting on. Sub-hourly on someone else's server is rude and, on many hosts, the
  fastest route to being blocked.
