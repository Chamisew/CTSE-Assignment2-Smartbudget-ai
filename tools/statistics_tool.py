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
where_clause = ""
params = []
if month != "all":
    where_clause = "WHERE date LIKE ?"
    params = [f"{month}%"]

# Category stats
cursor.execute(f"""
    SELECT category,
           COUNT(*),
           SUM(amount),
           AVG(amount),
           MAX(amount)
    FROM expenses {where_clause}
    GROUP BY category
""", params)

category_stats = cursor.fetchall()

# Overall stats
cursor.execute(f"""
    SELECT COUNT(*), SUM(amount), AVG(amount), MAX(amount), MIN(amount)
    FROM expenses {where_clause}
""", params)

overall = cursor.fetchone()