from crewai import Agent

def create_analyst_agent() -> Agent:
    return Agent(
        role="Financial Analyst",
        goal="Analyze financial data",
        backstory="Basic analyst agent",
    )