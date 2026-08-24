# Prompts: Personal API

> These are AI-assisted build prompts: a recommended path a reader can follow with
> ChatGPT Chat, ChatGPT Work, and Codex. They are not presented as the exact
> prompts used to produce this repository implementation, and they must not claim
> those tools performed this build.

The project can be built by hand from the README alone. These are optional.

**There is no runtime AI prompt in this project.** Every endpoint is implemented
with deterministic Python code and local files. The optional weather request is a
normal HTTP data lookup, not an AI feature.

## AI-assisted build prompts

### 1. ChatGPT Chat: clarify the implementation

```
I am building a project called Personal API. Read this description and treat the
title, the opening description, and the public promise as locked:

  A small local server with endpoints for your life. /today merges your calendar,
  your tasks, and the weather into one response. /idea files a thought. Nothing
  leaves localhost.

Do not redesign or reposition it. One correction is required: if the description
carries a claim about which tools produced the implementation, such as "Built
with Codex", remove it and do not replace it with another production-history
claim.

Constraints that are not up for discussion. No web framework: no FastAPI, no
Flask, no Django. No database. No model and no model key. No authentication, no
accounts, no multi-user support, no remote access. No Google Calendar, no Apple
Calendar, no phone integration, no cloud storage. No automatic startup and no
scheduler. Prefer the Python standard library, which is sufficient for this
scope. It is a weekend project: one source file and three small local files.

Help me define the smallest complete runnable implementation. Work through:

- The official endpoint list, and nothing beyond it.
- The request and response contract for each endpoint, including the error shape.
- The tasks.json format: required fields and their types.
- The calendar.json format: required fields, optional fields, and how dates parse.
- The ideas.jsonl format, and why one object per line suits appending.
- What /today should merge, and what it should deliberately leave out.
- How an idea append avoids rewriting the file, and what happens if two requests
  arrive at once.
- Date filtering, and why a date query matters for a tracked sample with fixed
  dates.
- What happens when a file is missing, empty, malformed, or holds one bad entry
  among good ones. I want partial answers with warnings, not error pages.
- The localhost boundary: binding, why there must be no host option, and what
  localhost does and does not protect against. Do not let me call it secure.
- Port configuration and the runtime data directory, and which of the flag or the
  environment variable wins.
- Sample seeding that can never overwrite real data or mutate the tracked files.
- The optional weather provider, the exact query fields sent, and the complete
  list of things that must never be sent with it.
- Every weather failure mode and how each one degrades.
- Request body limits and text length limits.
- The verification criteria that would prove each of the above.

Ask me only the implementation questions you actually need answered. Do not write
code and do not produce a plan until I have approved the important decisions.
```

### 2. ChatGPT Work: turn the decisions into a checklist

```
Here are the decisions I approved:

[paste the decision list from step 1]

Convert them into a build checklist for a single weekend project. Produce:

1. The five README build steps, in this order: run it as-is on the sample, read
   the request handler, point it at your own calendar and tasks, add an endpoint
   of your own, make it yours. Exact commands for each.
2. The minimal file list. Nothing beyond what those steps need.
3. An endpoint table: path, method, what it returns, and its error cases.
4. The local data schemas for tasks, calendar, and ideas.
5. The CLI options, each with its default and what it validates.
6. The environment variables, and which take effect only at startup.
7. Sample data requirements, including which cases the fixtures must prove:
   finished and unfinished tasks, events on more than one date, and a starting
   idea that later appends must not disturb.
8. The installation sequence from a clean clone.
9. A curl verification sequence covering every endpoint in order.
10. Graceful degradation checks for missing, empty, and malformed files.
11. The local versus network boundary, stated precisely enough to test.
12. Weather failure checks: unconfigured, invalid, unreachable, timed out,
    non-200, and malformed response.
13. Acceptance criteria that are objective and runnable.
14. Privacy checks: what must never be committed and what must never be sent.
15. An honest list of excluded capabilities, so the README cannot overclaim.

Rules for your output:
- Do not create extra repository planning files. No build plan, no build log, no
  architecture document. The checklist goes into the README and nowhere else.
- Do not rewrite the existing title or opening description.
- Do not add a web framework, a database, a model dependency, or a model key.
- Do not add authentication or remote access.
- Keep the server on 127.0.0.1.
- Keep it achievable in one weekend.
- Use python3 in every command.
- Do not use em dashes.

Return a concise checklist I can copy into the README and hand to Codex.
```

### 3. Codex: implement the project

```
Read the README, prompts.md, .env.example, and requirements.txt in this folder
before writing anything. Read the completed project 01 in this volume as the
quality reference for cold-start setup, honest capability boundaries, and
verification, but do not copy its architecture or dependencies. This project is
much smaller.

Preserve the current title and opening description exactly. Remove any claim
about which tools produced this implementation, and do not add a replacement.

Prefer the standard library. Implement in checkpoints, and after each one run it
and show me the real output before continuing.

Checkpoint 1: argument parsing, environment fallback, the server bound to
127.0.0.1, the JSON response and error helpers, and GET /health.
Checkpoint 2: the --seed-sample flag and the three file loaders, each returning
an availability flag, its rows, a count, and warnings.
Checkpoint 3: GET /tasks, GET /calendar with strict date validation, GET /ideas.
Checkpoint 4: POST /idea, appending exactly one line, with content type,
size, and text validation, and a lock around the write.
Checkpoint 5: GET /weather and GET /today, including partial responses.
Checkpoint 6: error responses for unknown routes, wrong methods, and bad input,
and graceful degradation for every missing or malformed file case.
Checkpoint 7: complete the README and prompts from behavior you actually verified.

Constraints:
- Bind to 127.0.0.1 only. No host flag, no HOST environment variable, no 0.0.0.0.
- No web framework, no database, no model, no model key, no authentication.
- Synthetic sample data only. Never use real personal content.
- Generated runtime data stays out of Git, and the tracked sample files are never
  mutated by a run.
- Every documented command uses python3.
- Exercise every endpoint with curl and paste the real responses.
- Make no unrelated changes to the repository.
- Stop and ask when a real implementation decision is unresolved rather than
  guessing.
- Do not commit or push.
```

### 4. Codex: verify and review

```
Review this project as if you had just cloned it.

1. Create a clean virtual environment and install from requirements.txt. Record
   whether pip downloaded anything and how long it took.
2. Run python3 -m py_compile server.py.
3. Run python3 server.py --help and confirm the flags match the README, with no
   host, daemon, model, or key option.
4. Start the server with the sample seeded into a generated directory.
5. Exercise every endpoint with curl and capture the actual JSON.
6. Submit two different ideas. Record the ideas file line count before and after,
   inspect the file, and confirm both lines were appended, the original sample
   line survived, and the order is preserved.
7. Test missing tasks, calendar, and ideas files in a separate empty directory,
   including a POST that has to create the ideas file.
8. Test malformed files in another directory: unparseable JSON, one bad entry
   among good ones, and a broken line in the ideas file.
9. Test invalid input: bad date query, malformed POST JSON, missing text, empty
   text, wrong content type, an oversized body, an unknown route, and an
   unsupported method. Confirm the status codes and that no response is HTML.
10. Test weather unconfigured, and prove from the log that no request was
    attempted rather than assuming it.
11. Test weather unreachable using the base URL override pointed at an address
    that refuses connections. Confirm /today still returns calendar and tasks.
12. Test live weather once if the network allows. Record the provider, the exact
    query fields sent, the response size, and the elapsed time. If the network is
    unavailable, say so rather than inventing numbers.
13. Confirm the server binds only to 127.0.0.1, that no host override exists, and
    that no documentation claims remote access.
14. Confirm there is no model dependency and no key anywhere.
15. Confirm .env, runtime data directories, caches, and logs are ignored by Git,
    and that the tracked sample files are unchanged.
16. Compare every claim in the README against actual code behavior.
17. Stop every server cleanly and confirm no process or listener remains.

Fix only confirmed problems. Do not refactor working code, do not add features,
and do not create planning documents. Report what you could not test and why.
Use python3 consistently. Do not use em dashes. Do not commit or push.
```

## No runtime AI prompt

This project has no runtime AI prompt. The routes, file parsing, date filtering,
idea append, weather lookup, and merged `/today` response are deterministic
Python behavior. OpenAI and other model providers are not involved.

## Tuning

Startup configuration takes effect when the server starts, so change it and
restart. Your local data files are different: they are read on every request, so
editing `tasks.json` or `calendar.json` shows up in the very next response with
no restart.

- **Port**: `--port 8790`, or `PERSONAL_API_PORT=8790`. The flag wins. Valid
  range is 1 to 65535, and a value outside it exits with code 2 before binding.
- **Data directory**: `--data-dir ~/personal-api-data`, or
  `PERSONAL_API_DATA_DIR`. The flag wins. A relative path is resolved against the
  directory you ran the command from, and the startup banner prints the absolute
  result so you can check it.
- **Request body limit**: `MAX_BODY_BYTES` in `server.py`, 16 KB. A larger body
  is refused with 413 before it is read. Raise it only if you genuinely file
  very long ideas.
- **Idea text limit**: `MAX_IDEA_CHARS`, 2000 characters, checked after trimming.
  Over the limit is a 400 naming the limit.
- **Weather timeout**: `WEATHER_TIMEOUT_SECONDS`, default 5. This affects only
  the optional outbound lookup. Lowering it makes a slow provider fail faster,
  and failing is graceful: `/today` keeps returning calendar and tasks.
- **Weather coordinates**: `WEATHER_LAT` and `WEATHER_LON`. Both or neither. They
  are validated as numbers in range, and they are the only local values that ever
  leave the machine.
- **Weather base URL**: `WEATHER_API_BASE_URL`, default the documented Open-Meteo
  endpoint. It exists for controlled testing, for example pointing it at
  `http://127.0.0.1:9/forecast` to watch the failure path. Only `http` and
  `https` are accepted, it can only be set in the environment by whoever runs the
  server, and it is never readable from an HTTP request.
- **Calendar file shape**: `load_calendar()` validates `id`, `title`, and
  `start`, with `end` optional. To add a field, extend the validation and the
  record it builds together. A field added to your file but not to the validator
  is silently dropped, and a field added to the validator but not documented is a
  trap for future you.
- **Task file shape**: same rule in `load_tasks()`.
- **`/today` contents**: `build_today()`. It merges the date's events, the
  unfinished tasks, and weather, and it deliberately omits ideas. Adding them is
  a two-line change if you disagree.
- **Sample seeding**: `--seed-sample` copies only files that do not already exist
  and never touches `sample-data/`. Delete the generated directory to reset the
  demo completely.

Adding remote access is not a tuning knob. It changes the security model of the
whole project, and it is outside this build.
