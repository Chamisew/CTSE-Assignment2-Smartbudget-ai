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

    def _run(self, report_content: str) -> str:
        """
        Save the report content to a markdown file.

        Args:
            report_content: Full report text to save

        Returns:
            Confirmation message with file path
        """
        try:
            os.makedirs(REPORTS_DIR, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = REPORTS_DIR / f"budget_report_{timestamp}.md"

            # Add a header if not present
            if not report_content.strip().startswith("#"):
                header = (
                    f"# SmartBudget AI — Financial Report\n"
                    f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )
                report_content = header + report_content

            with open(filename, "w", encoding="utf-8") as f:
                f.write(report_content)

            result = f"Report successfully saved to: {filename}"

            log_agent_action(
                agent_name="ReporterAgent",
                input_data="Financial statistics and analysis",
                tool_called="generate_report",
                output=result,
                status="success"
            )

            return result

        except Exception as e:
            error = f"Report generation error: {str(e)}"
            log_agent_action(
                agent_name="ReporterAgent",
                input_data="report content",
                tool_called="generate_report",
                output=error,
                status="error"
            )
            return error