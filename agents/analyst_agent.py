"""
Analyst Agent — Member 3
Responsible for analyzing precomputed financial statistics.
"""

from crewai import Agent
from langchain_ollama import OllamaLLM


def create_analyst_agent() -> Agent:
    """
    Create and return the Analyst Agent.

    Returns:
        Configured CrewAI Agent instance
    """
    llm = "ollama/mistral"

    return Agent(
        role="Financial Analyst",
        goal=(
            "Analyze detailed financial statistics and explain the implications clearly."
        ),
        backstory=(
            "You are a senior financial analyst with 10 years of experience "
            "analyzing personal and business budgets. You are precise with numbers, "
            "highlight unusual spending, and present analysis in a clear structure."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )