# 04 — Multi-Agent Research Crew

**Difficulty:** Medium
**Time:** 6-9 hours
**What it does:** A team of AI agents that work together. One researches the web, one analyzes data, one synthesizes everything into a final report. You give it a question, the crew handles the rest.

## Why build this

Single-agent workflows hit a ceiling. When you need deep research, one agent trying to do everything runs out of context and loses focus. A crew of specialized agents, each with one job, produces dramatically better output. This is how the top builders are working in 2026.

## What you need

- Python 3.10+
- [CrewAI](https://github.com/crewAIInc/crewAI) (multi-agent framework)
- An Anthropic API key or OpenAI API key
- [Tavily API key](https://tavily.com/) (for web search, free tier available)

## Setup (15 minutes)

### 1. Create your project

```bash
mkdir research-crew && cd research-crew
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install crewai crewai-tools tavily-python langchain-anthropic
```

### 3. Set your API keys

```bash
export ANTHROPIC_API_KEY=your_key_here
export TAVILY_API_KEY=your_key_here
```

### 4. Create the crew

Save this as `crew.py`:

```python
import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import TavilySearchResults

# Tools
search_tool = TavilySearchResults(max_results=5)

# Agent 1: The Researcher
researcher = Agent(
    role="Senior Research Analyst",
    goal="Find comprehensive, accurate information about the given topic from multiple sources",
    backstory="""You are an expert researcher who digs deep into topics.
    You don't just find the first answer. You look for multiple perspectives,
    conflicting information, and data that others miss. You always cite your sources.""",
    tools=[search_tool],
    verbose=True
)

# Agent 2: The Analyst
analyst = Agent(
    role="Strategic Analyst",
    goal="Analyze research findings and identify patterns, gaps, and opportunities",
    backstory="""You take raw research and find the story in it.
    You identify what matters, what's noise, and what the implications are.
    You think in frameworks and always ask 'so what does this mean?'""",
    verbose=True
)

# Agent 3: The Writer
writer = Agent(
    role="Report Writer",
    goal="Create a clear, structured, actionable report from the analysis",
    backstory="""You turn complex analysis into clear, readable reports.
    You write for busy people who need to make decisions.
    Every section has a clear takeaway. No fluff. No filler.""",
    verbose=True
)


def run_research(topic):
    # Task 1: Research
    research_task = Task(
        description=f"""Research the following topic thoroughly: {topic}
        
        Find at least 5 different sources. Look for:
        - Key facts and recent data
        - Different perspectives or approaches
        - What's working and what's not
        - Any surprising findings
        
        Provide all sources with links.""",
        expected_output="A comprehensive research document with findings from multiple sources, including links",
        agent=researcher
    )

    # Task 2: Analyze
    analysis_task = Task(
        description="""Analyze the research findings. Identify:
        
        1. The 3 most important patterns or insights
        2. Where sources agree and where they conflict
        3. What's missing from the current landscape
        4. The biggest opportunity or gap
        
        Be specific. Use data from the research.""",
        expected_output="A strategic analysis with clear patterns, conflicts, gaps, and opportunities identified",
        agent=analyst
    )

    # Task 3: Write report
    report_task = Task(
        description="""Create a final report that includes:
        
        1. Executive summary (3 sentences max)
        2. Key findings (bullet points with data)
        3. Analysis (patterns, gaps, opportunities)
        4. Recommendations (what to do with this information)
        5. Sources
        
        Write for someone who has 5 minutes to read this and needs to make a decision.""",
        expected_output="A polished, actionable report in markdown format",
        agent=writer,
        output_file="report.md"
    )

    # Assemble the crew
    crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[research_task, analysis_task, report_task],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    print("\n\nReport saved to report.md")
    return result


if __name__ == "__main__":
    topic = input("What should the crew research? ")
    run_research(topic)
```

## Try it

```bash
python crew.py
```

### Research prompts to try:

```
What should the crew research? The current state of AI-powered content creation tools for solo creators in 2026
```

```
What should the crew research? How are startups using agentic workflows to replace traditional SaaS tools
```

```
What should the crew research? The most effective strategies for growing a technical audience on LinkedIn and X in 2026
```

Watch the agents work. You'll see the researcher searching, the analyst thinking, and the writer producing. The final report lands in `report.md`.

## Go deeper

- Add a fourth agent: a "Devil's Advocate" that challenges the analysis before the report is written
- Add a Firecrawl tool so the researcher can scrape full articles, not just search snippets
- Make the crew async so agents work in parallel instead of sequentially
- Build a web interface where you can watch the agents working in real time
- Connect to your q-os system so research reports automatically feed into your content pipeline

## What you'll learn

- How multi-agent systems work (orchestration, task delegation, handoffs)
- How to design agent roles and backstories that produce better output
- How sequential vs parallel agent workflows differ
- How to build systems that are smarter than any single prompt
