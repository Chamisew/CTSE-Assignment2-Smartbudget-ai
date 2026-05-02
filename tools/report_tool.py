"""
Tool for generating and saving the final financial report.
Member 4's custom tool.
"""

import os
from datetime import datetime
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from logs.logger import log_agent_action


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


class ReportInput(BaseModel):
    """Input schema for the ReportTool."""
    report_content: str = Field(
        description="The full financial report content to save as markdown"
    )


class GenerateReportTool(BaseTool):
    """
    Saves the final financial analysis report as a markdown file.
    Automatically names the file with a timestamp.
    """

    name: str = "generate_report"
    description: str = (
        "Takes the complete financial report content and saves it as a "
        "markdown (.md) file in the reports/ folder with a timestamp."
    )
    args_schema: type[BaseModel] = ReportInput