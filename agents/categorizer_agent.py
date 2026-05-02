"""
Categorizer Agent — Member 2
Responsible for explaining categorization decisions from existing records.
"""

from crewai import Agent
from langchain_ollama import OllamaLLM


def create_categorizer_agent() -> Agent:
    """
    Create and return the Categorizer Agent.

    Returns:
        Configured CrewAI Agent instance
    """
    llm = "ollama/mistral"
    
    return Agent(
        role="Expense Categorizer",
        goal=(
            "Explain how each expense should be categorized and justify the decision."
        ),
        backstory=(
            "You are a financial data specialist with expertise in expense management. "
            "You carefully categorize every transaction so that budget analysis "
            "is accurate, and you explain the reasoning in plain language."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )