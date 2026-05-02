from crewai import Agent


def create_collector_agent() -> Agent:
    """
    Create and return the Data Collector Agent.
    """

    return Agent(
        role="Data Collector",
        goal="Process expense data",
        backstory="Basic data processing agent",
        llm="ollama/mistral",
        verbose=True
    )