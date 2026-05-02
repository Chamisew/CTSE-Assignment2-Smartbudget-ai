from crewai import Agent
from langchain_ollama import OllamaLLM

def create_analyst_agent() -> Agent:
    llm = "ollama/mistral"

    return Agent(
        role="Financial Analyst",
        goal="Analyze financial data",
        backstory="Basic analyst agent",
        llm=llm,
    )