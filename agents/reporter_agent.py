"""
Reporter Agent — Member 4
Responsible for writing the final financial report content.
"""

from crewai import Agent
from langchain_ollama import OllamaLLM


def create_reporter_agent() -> Agent:
    """
    Create and return the Reporter Agent.

    Returns:
        Configured CrewAI Agent instance
    """
    llm = "ollama/mistral"

    return Agent(
        role="Financial Report Writer",
        goal=(
            "Write a clear, professional budget report in markdown format with sections for summary, category breakdown, anomalies, and actionable savings advice."
        ),
        backstory=(
            "You are a professional financial advisor who writes clear budget reports. "
            "You write polished markdown reports from the statistics provided to you. "
            "You do not need to call any tools in this phase."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )
