import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import TavilySearchResults

search_tool = TavilySearchResults(max_results=5)

researcher = Agent(
    role="Senior Research Analyst",
    goal="Find comprehensive, accurate information about the given topic from multiple sources",
    backstory="""You are an expert researcher who digs deep into topics.
    You don't just find the first answer. You look for multiple perspectives,
    conflicting information, and data that others miss. You always cite your sources.""",
    tools=[search_tool],
    verbose=True
)

analyst = Agent(
    role="Strategic Analyst",
    goal="Analyze research findings and identify patterns, gaps, and opportunities",
    backstory="""You take raw research and find the story in it.
    You identify what matters, what's noise, and what the implications are.
    You think in frameworks and always ask 'so what does this mean?'""",
    verbose=True
)

writer = Agent(
    role="Report Writer",
    goal="Create a clear, structured, actionable report from the analysis",
    backstory="""You turn complex analysis into clear, readable reports.
    You write for busy people who need to make decisions.
    Every section has a clear takeaway. No fluff. No filler.""",
    verbose=True
)


def run_research(topic):
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
