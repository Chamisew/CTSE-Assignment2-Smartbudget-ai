"""
Data Collector Agent — Member 1
Responsible for reasoning about already-loaded expense data.
"""

from crewai import Agent
from langchain_ollama import OllamaLLM


def create_collector_agent() -> Agent:
    """
    Create and return the Data Collector Agent.

    Returns:
        Configured CrewAI Agent instance
    """
    llm = "ollama/mistral"

    return Agent(
        role="Expense Data Collector",
        goal=(
            "Validate already-loaded expense data and summarize its quality clearly."
        ),
        backstory=(
            "You are a meticulous data engineer. You only reason about the data "
            "already provided to you and never invent, assume, or fabricate values."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )