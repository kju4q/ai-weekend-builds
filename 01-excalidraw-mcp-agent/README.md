# 01 — Excalidraw MCP Diagram Agent

**Difficulty:** Easy
**Time:** 1-3 hours
**What it does:** Describe any system, workflow, or architecture in plain text and get a beautiful, editable diagram in Excalidraw automatically.

## Why build this

Every builder needs to visualize systems. Instead of manually dragging boxes in Excalidraw, you describe what you want and Claude creates it for you. The diagram is fully editable so you can tweak it after.

## What you need

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- [Excalidraw MCP server](https://github.com/modelcontextprotocol/servers) 
- Node.js 18+

## Setup (5 minutes)

### 1. Install the Excalidraw MCP server

```bash
npm install -g @anthropic-ai/mcp-server-excalidraw
```

### 2. Add it to Claude Code

```bash
claude mcp add excalidraw -- npx @anthropic-ai/mcp-server-excalidraw
```

### 3. Verify it's connected

Open Claude Code and run:
```
/mcp
```

You should see `excalidraw` listed as a connected server.

## Try it

Open Claude Code and paste any of these prompts:

### Starter prompt 1: Simple workflow
```
Create an Excalidraw diagram showing a content creation pipeline:
1. Idea capture (from phone, Twitter, conversations)
2. Research phase (Grok scans X, Claude analyzes)
3. Script writing (Claude drafts, I refine)
4. Recording and editing
5. Distribution across 6 platforms

Use arrows between each step. Color code: research in blue, creation in green, distribution in orange.
```

### Starter prompt 2: System architecture
```
Create an Excalidraw diagram showing a RAG (Retrieval Augmented Generation) system:
- User uploads PDFs and notes
- Documents get chunked and embedded
- Embeddings stored in a vector database
- User asks a question
- System retrieves relevant chunks
- LLM generates answer using retrieved context

Show the data flow with arrows. Group related components together.
```

### Starter prompt 3: Agent workflow
```
Create an Excalidraw diagram showing a multi-agent research system:
- Orchestrator agent receives a research question
- Spawns 3 sub-agents: web researcher, academic paper finder, social media scanner
- Each sub-agent returns findings
- Synthesizer agent combines all findings into a report
- Report goes to the user

Show the agents as separate boxes with arrows showing communication flow.
```

## Go deeper

Once you have the basics working:
- Create a CLAUDE.md file with your preferred diagram style (colors, layout, fonts)
- Build a skill file that generates diagrams in your specific visual style every time
- Connect it to your product architecture workflow so every new project starts with a visual system map

## What you'll learn

- How MCP servers work with Claude Code
- How to use AI for visual thinking, not just text
- How to set up reusable diagram workflows
