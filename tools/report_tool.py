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
