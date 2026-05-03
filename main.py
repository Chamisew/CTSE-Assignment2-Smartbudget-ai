"""
SmartBudget AI — Main entry point.
Hybrid architecture: tools execute deterministically, agents reason about results.
"""

import re
from crewai import Crew, Task, Process
from agents.collector_agent import create_collector_agent
from agents.categorizer_agent import create_categorizer_agent
from agents.analyst_agent import create_analyst_agent
from agents.reporter_agent import create_reporter_agent
from tools.read_csv_tool import ReadCSVTool
from tools.database_tool import SaveDatabaseTool
from tools.statistics_tool import StatisticsTool
from tools.report_tool import GenerateReportTool


def _clean_report_content(report_content: str) -> str:
    """Strip code fences and accidental tool-call artifacts from model output."""
    clean_content = report_content.strip()

    if "```markdown" in clean_content:
        start = clean_content.find("```markdown") + len("```markdown")
        end = clean_content.rfind("```")
        if end > start:
            clean_content = clean_content[start:end].strip()
    elif clean_content.startswith("```"):
        clean_content = clean_content.strip("`").strip()

    if "[{\"name\"" in clean_content:
        clean_content = clean_content[:clean_content.find("[{\"name\"")].strip()

    return clean_content


def phase1_execute_tools(csv_path: str) -> dict:
    """
    Execute all tools directly in Python without LLM involvement.

    Returns a shared state dictionary that later agents can reason about.
    """
    print("\n" + "=" * 60)
    print("   PHASE 1 — Deterministic Tool Execution")
    print("=" * 60)

    print("\n[Tool 1] read_csv_file running...")
    raw_data = ReadCSVTool()._run(csv_path)
    raw_lower = raw_data.lower().strip()
    if raw_lower.startswith("file not found") or raw_lower.startswith("unexpected error") or raw_lower.startswith("missing columns"):
        raise RuntimeError(f"Tool 1 failed: {raw_data}")

    print("   Loaded expense records successfully")

    print("\n[Tool 2] save_to_database running...")
    db_result = SaveDatabaseTool()._run(raw_data)
    db_lower = db_result.lower().strip()
    if db_lower.startswith("error") or db_lower.startswith("database error"):
        raise RuntimeError(f"Tool 2 failed: {db_result}")

    print(f"   {db_result}")

    print("\n[Tool 3] calculate_statistics running...")
    statistics = StatisticsTool()._run("all")
    stat_lower = statistics.lower().strip()
    if stat_lower.startswith("statistics error"):
        raise RuntimeError(f"Tool 3 failed: {statistics}")

    print("   Statistics calculated from database")

    state = {
        "csv_path": csv_path,
        "raw_data": raw_data,
        "db_result": db_result,
        "statistics": statistics,
        "report_path": None,
    }

    print("\n   Phase 1 complete — all tools executed successfully")
    return state


def phase2_agent_reasoning(state: dict) -> str:
    """
    Run CrewAI agents to reason over precomputed tool outputs.

    The agents do not need tool access in this phase.
    """
    print("\n" + "=" * 60)
    print("   PHASE 2 — CrewAI Agent Reasoning Pipeline")
    print("=" * 60 + "\n")

    collector = create_collector_agent()
    categorizer = create_categorizer_agent()
    analyst = create_analyst_agent()
    reporter = create_reporter_agent()

    task1 = Task(
        description=(
            f"The read_csv_file tool already ran and returned this real data from '{state['csv_path']}':\n\n"
            f"{state['raw_data']}\n\n"
            "Your job:\n"
            "1. Confirm the data is valid and complete\n"
            "2. State how many records were loaded\n"
            "3. Identify the date range of the expenses\n"
            "4. List the currency used\n"
            "5. Pass the complete records list forward exactly as shown above\n\n"
            "Do not invent or modify any data. Work only with what is shown."
        ),
        expected_output=(
            "A validation summary confirming record count, date range, currency, and the complete unmodified records list."
        ),
        agent=collector,
    )

    task2 = Task(
        description=(
            f"The save_to_database tool already ran. Database result: {state['db_result']}\n\n"
            f"The expense records that were categorized:\n{state['raw_data']}\n\n"
            "Your job:\n"
            "1. Explain which category each expense was assigned to (food, transport, bills, health, entertainment, other)\n"
            "2. Justify why each categorization makes sense\n"
            "3. Confirm the total number saved to budget.db\n"
            "4. Flag any expenses that were difficult to categorize\n\n"
            "Categories used: food, transport, bills, health, entertainment, other"
        ),
        expected_output=(
            "A clear breakdown showing each expense with its assigned category, the reasoning behind each decision, and database save confirmation."
        ),
        agent=categorizer,
        context=[task1],
    )

    task3 = Task(
        description=(
            f"The calculate_statistics tool already queried the database and returned these real statistics:\n\n"
            f"{state['statistics']}\n\n"
            "Your job:\n"
            "1. Identify the top 3 spending categories and explain why they are high\n"
            "2. Explain each anomaly detected and what it means for the budget\n"
            "3. Calculate what percentage of total spending each category represents\n"
            "4. Identify which expenses are recurring vs one-time\n"
            "5. Give an overall assessment: is this a healthy budget or concerning?\n\n"
            "Use only the real numbers shown above. Do not invent statistics."
        ),
        expected_output=(
            "Comprehensive financial analysis with top category breakdown with percentages, anomaly explanations, recurring vs one-time classification, and an overall budget health assessment."
        ),
        agent=analyst,
        context=[task2],
    )

    task4 = Task(
        description=(
            "You are writing the final SmartBudget AI financial report.\n\n"
            f"Use these real statistics from the database:\n{state['statistics']}\n\n"
            "Write a complete, professional financial report in markdown format.\n"
            "Your report must include all of these sections with proper ## headings:\n\n"
            "## Executive Summary\n"
            "## Spending by Category\n"
            "## Anomalies & Warnings\n"
            "## Savings Recommendations\n"
            "## Conclusion\n\n"
            "Requirements:\n"
            "- Minimum 400 words\n"
            "- Use real LKR numbers from the statistics\n"
            "- Be specific and professional\n"
            "- Do not include any JSON or code blocks in the report\n"
            "- Write in clear, friendly English\n"
            "Do not mention tool calls in the report body."
        ),
        expected_output=(
            "A complete professional markdown financial report with all five sections, real LKR numbers, minimum 400 words, and no JSON or code blocks."
        ),
        agent=reporter,
        context=[task3],
    )

    crew = Crew(
        agents=[collector, categorizer, analyst, reporter],
        tasks=[task1, task2, task3, task4],
        process=Process.sequential,
        verbose=True,
    )

    return str(crew.kickoff())


def phase3_save_report(report_content: str, state: dict) -> str:
    """
    Save the agent-written report directly to disk using Tool 4.
    """
    print("\n" + "=" * 60)
    print("   PHASE 3 — Saving Final Report to Disk")
    print("=" * 60)

    clean_content = _clean_report_content(report_content)

    print("\n[Tool 4] generate_report running...")
    save_result = GenerateReportTool()._run(clean_content)
    print(f"   {save_result}")

    match = re.search(r"reports/[^\s]+?\.md", save_result)
    report_path = match.group(0) if match else "reports/unknown.md"
    state["report_path"] = report_path
    return report_path


def run_smartbudget(csv_path: str = "data/expenses.csv") -> str:
    """
    Run the full SmartBudget AI hybrid pipeline.

    Args:
        csv_path: Path to the expense CSV file

    Returns:
        Path to the saved report file
    """

    try:
        state = phase1_execute_tools(csv_path)
        report_content = phase2_agent_reasoning(state)
        report_path = phase3_save_report(report_content, state)

        print("\n" + "=" * 60)
        print("   SmartBudget AI Pipeline Complete!")
        print("=" * 60)
        print(f"Report saved to: {report_path}")

        return report_path

    except Exception as e:
        print(f"\nPipeline failed: {e}")
        raise


if __name__ == "__main__":
    run_smartbudget()