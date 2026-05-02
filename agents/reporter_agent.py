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