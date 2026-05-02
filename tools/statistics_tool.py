import sqlite3
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

DB_PATH = "budget.db"

class StatisticsInput(BaseModel):
    month: str = Field(
        default="all",
        description="Month to analyze in YYYY-MM format, or 'all'"
    )

class StatisticsTool(BaseTool):
    name: str = "calculate_statistics"
    description: str = "Basic statistics tool"
    args_schema: type[BaseModel] = StatisticsInput

    def _run(self, month: str = "all") -> str:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        return "Tool initialized"