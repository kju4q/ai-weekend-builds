# 02 — One-Command Web Researcher

**Difficulty:** Easy
**Time:** 2-4 hours
**What it does:** Type a topic and it scrapes, cleans, and summarizes any website or set of websites into a structured research report. One command, full report.

## Why build this

Every project starts with research. Instead of opening 15 tabs, skimming articles, and copy-pasting into a doc, you type one command and get a clean, structured report with sources.

## What you need

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- [Firecrawl CLI](https://github.com/mendableai/firecrawl) (for web scraping, install as CLI not MCP to save context)
- A Firecrawl API key (free tier available at [firecrawl.dev](https://firecrawl.dev))

## Setup (10 minutes)

### 1. Install Firecrawl CLI

```bash
npm install -g firecrawl
```

### 2. Set your API key

```bash
export FIRECRAWL_API_KEY=your_key_here
```

Add it to your `.bashrc` or `.zshrc` so it persists.

### 3. Create your research skill file

Create a file called `research-skill.md` in your project:

```markdown
# Research Skill

When I say "research [topic]", follow this process:

1. Use Firecrawl to scrape the top 5-10 relevant URLs for the topic
2. Clean and extract the key content from each page
3. Organize findings into sections:
   - Key facts and data points
   - Different perspectives or approaches
   - What's missing or contradictory
   - Sources with links
4. Output as a clean markdown report saved to /research/[topic].md
5. End with 3 questions worth investigating further

Always cite sources. Always flag when information conflicts.
```

## Try it

### Starter prompt 1: Competitive research
```
Research the current landscape of AI coding assistants in 2026. 
Scrape these URLs using Firecrawl:
- https://docs.anthropic.com/en/docs/claude-code
- https://github.com/features/copilot
- https://cursor.com
- https://windsurf.com

For each one, extract: key features, pricing, what developers say about it, and what's missing.
Save the report to research/ai-coding-assistants.md
```

### Starter prompt 2: Topic deep dive
```
Research "agentic workflows" — what they are, how teams are implementing them, 
and what tools people are using. Scrape 5 relevant articles using Firecrawl.
Focus on practical implementations, not theory.
Save to research/agentic-workflows.md
```

### Starter prompt 3: Market research
```
Research the market for AI-powered content creation tools for solo creators.
Find and scrape 5 tools that exist right now. For each one:
- What it does
- Pricing
- What users love about it
- What users complain about (check Reddit, X, review sites)

Identify the gap. Save to research/creator-ai-tools.md
```

## Go deeper

- Add a second step where Claude analyzes the research and generates a product brief
- Build a weekly research automation that runs every Saturday
- Connect it to your q-os style system so research feeds into your content pipeline
- Add Tavily MCP alongside Firecrawl for search + scrape combo

## What you'll learn

- How to use CLI tools instead of MCP servers (and why it saves context)
- How to build research workflows that produce real, structured output
- How to chain scraping + analysis into one command
