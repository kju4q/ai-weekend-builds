export const meta = {
  name: 'readme-cold-start-audit',
  description: 'Check each project README for cold-start install/run readiness',
  phases: [
    { title: 'Audit', detail: 'one agent per project reads README + files' },
    { title: 'Synthesize', detail: 'rank projects by cold-start readiness' },
  ],
}

const PROJECTS = [
  '01-excalidraw-mcp-agent',
  '02-web-researcher-agent',
  '03-personal-rag-assistant',
  '04-multi-agent-research-crew',
  '05-autonomous-coding-agent',
  'vol-2/01-screenshot-to-code',
  'vol-2/02-ai-daily-digest',
  'vol-2/03-auto-skill-builder',
  'vol-2/04-content-repurposer',
  'vol-2/05-ai-inbox-triage',
]

const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['project', 'runnable', 'score', 'blockers', 'gaps', 'whatExists', 'summary'],
  properties: {
    project: { type: 'string' },
    runnable: {
      type: 'string',
      enum: ['yes', 'partial', 'no'],
      description: 'Could a cold visitor install and run it from the README alone?',
    },
    score: { type: 'integer', minimum: 0, maximum: 10, description: 'Cold-start readiness 0-10' },
    blockers: {
      type: 'array',
      description: 'Hard blockers that stop the project from running at all',
      items: { type: 'string' },
    },
    gaps: {
      type: 'array',
      description: 'Missing or unclear README pieces (deps file, env vars, commands, prereqs, versions)',
      items: { type: 'string' },
    },
    whatExists: {
      type: 'array',
      description: 'What the README/repo DOES provide correctly',
      items: { type: 'string' },
    },
    summary: { type: 'string', description: 'One-paragraph verdict' },
  },
}

phase('Audit')

const results = await parallel(PROJECTS.map((p) => () =>
  agent(
    `You are auditing whether someone landing COLD on the project at ./${p} could actually install and run it using ONLY the README and the files present in that directory. No outside knowledge, no asking the author.

Do all of this:
1. Read ./${p}/README.md in full.
2. List every file in ./${p} (recursively) and read the source/config files (e.g. *.py, *.js, *.ts, package.json, requirements.txt, pyproject.toml, .env.example, Dockerfile, etc.).
3. Cross-check the README's instructions against reality:
   - Is there a dependency manifest (requirements.txt / package.json / etc.) AND does the README tell you to install it? If the code imports libraries, are they declared anywhere?
   - Are required API keys / env vars documented (which ones, where to put them, e.g. .env)? Is there a .env.example?
   - Are the exact run commands given, and do they match the actual entry-point filenames that exist?
   - Are prerequisites stated (language/runtime version, Node/Python version, external services like a vector DB, MCP server, Excalidraw, etc.)?
   - Does the README reference files/scripts/commands that DO NOT exist in the directory?
   - Is the code present at all, or is the README pointing at code that's missing (a "build guide" with no implementation)?

Be concrete and specific — name the exact missing file, env var, package, or command. Distinguish hard BLOCKERS (can't run at all) from softer GAPS (works but rough). If something is fine, note it under whatExists so the report isn't only negative.

Return the structured verdict for project "${p}".`,
    { label: `audit:${p}`, phase: 'Audit', schema: VERDICT_SCHEMA }
  )
)).then((r) => r.filter(Boolean))

phase('Synthesize')

const synthesis = await agent(
  `Here are cold-start readiness audits for ${results.length} projects in a "weekend builds" repo. Produce a tight cross-project summary for the repo owner.

Audit data (JSON):
${JSON.stringify(results, null, 2)}

Write:
1. A one-line overall verdict on the repo.
2. A ranked table (worst -> best) with project, runnable (yes/partial/no), score, and the single biggest blocker.
3. Cross-cutting patterns — issues that recur across multiple projects (e.g. "no requirements.txt anywhere", "env vars never documented").
4. The 3 highest-leverage fixes that would most improve cold-start success across the repo.
Keep it scannable, use markdown.`,
  { label: 'synthesize', phase: 'Synthesize' }
)

return { results, synthesis }
