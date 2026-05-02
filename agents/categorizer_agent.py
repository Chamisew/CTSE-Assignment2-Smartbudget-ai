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