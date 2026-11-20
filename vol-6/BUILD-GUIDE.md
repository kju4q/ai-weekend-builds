# Build guide: how to build any of these with an AI assistant

One of the five projects in this volume is built. The other four are plans: a
spec, the prompts, and sample data. This page is how I would turn any of those
plans into a working project with Claude Code, Codex, or whatever you build in,
without ending up with three thousand lines you do not understand.

The short version: the assistant writes code fast, so the slow part is knowing
whether the code is right. Every step below exists to make that check cheap.

## The loop

1. **Write SPEC.md first.** Inputs, outputs, and acceptance checks. Every project
   folder here ships one you can paste. Edit it until it describes what you
   actually want, before any code exists.
2. **Ask for a plan, not code.** Paste the spec and ask for the milestones, the
   files each one touches, and the risks. Read the plan. Argue with it. This is
   the cheapest point in the whole build to change your mind.
3. **Build one milestone at a time.** One milestone per request. Tell the
   assistant: "do not write the next layer until I confirm this one."
4. **Run the acceptance check after every milestone.** The check is written in
   the spec before the code, so the assistant cannot quietly redefine what done
   means.
5. **Commit each milestone that passes.** When the next milestone breaks
   something, you go back one commit, not one day.
6. **Always run on the sample data before real data.** Every project folder has
   a `sample-data/` folder of invented data. If it fails there, the bug is in
   the code. If it passes there and fails on your data, the bug is in your
   assumptions about your data. Knowing which one you are debugging halves the
   time.

## The rule that matters most

End every build request with this sentence:

```
Do not write the next layer until I confirm this one.
```

Without it, an assistant asked for a database schema will also hand you the
ingest script, the API, and a dashboard, all built on a schema you have not
looked at yet. Then a problem in the schema turns into a problem in four places.
All the prompts in this volume end by holding back the next step for the same
reason.

## The SPEC template

Copy this into `SPEC.md` at the root of your project and fill it in. Each
project folder already has a filled-in version.

```markdown
# SPEC: {project name}

## One sentence
{What it does, for whom, in one sentence a friend would understand.}

## Inputs
- {Every input: file, API, folder, typed text. Format and where it comes from.}
- Sample data: {path to invented data that exercises every input}

## Outputs
- {Every output: file, screen, message. Exact format.}

## Out of scope
- {What this version will not do, so the assistant does not build it.}

## Constraints
- Runs where: {local only, or which parts call an API}
- Language and libraries: {and which ones are not allowed}
- Secrets: {where keys live, and that they are never committed}

## Milestones
Each milestone ends in something I can run.

### M1: {name}
- Build: {what exists after this milestone}
- Acceptance check: {exact command, and exactly what it must print or produce}

### M2: {name}
- Build:
- Acceptance check:

{...}

## Done means
- [ ] Every acceptance check passes on sample-data/
- [ ] It runs on my real data
- [ ] {any number I need to see before I trust it}
```

## The three prompts I use for every build

**Plan, not code:**

```
Here is my spec:

{paste SPEC.md}

Give me a plan: the milestones in order, the files each one creates or changes,
and the two places this is most likely to go wrong. Point out anything in the
spec that is ambiguous or that you would change, and why. Do not write any code
yet.
```

**One milestone:**

```
We are on milestone {n} from the spec: {paste that milestone}.

Build only this milestone. When you are done, tell me the exact command for the
acceptance check and what it should print. Do not write the next layer until I
confirm this one.
```

**When an acceptance check fails:**

```
The acceptance check for milestone {n} failed. Here is the exact output:

{paste the output, not a description of it}

Tell me the most likely cause and the smallest experiment that confirms it.
Do not change any code yet.
```

## Why acceptance checks beat "does it look right"

An assistant that has written code will tell you the code works. That is not
dishonesty, it just has no way to know. The acceptance check is how you find
out, and it only works if you wrote it before the code. If you write the check
after seeing the output, you end up checking for what the code already does.

That is also the idea behind project 04, the auditor: a second reader with no
stake in the first one's answer.

## Commit messages that help later

One commit per passing milestone, named after the milestone:

```
git add -A && git commit -m "M2: comments clustered, acceptance check passes"
```

When you come back in a month, `git log` reads like the spec.
