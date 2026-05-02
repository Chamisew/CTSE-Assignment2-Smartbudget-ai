"""
Tool for calculating budget statistics from the SQLite database.
Member 3's custom tool.
"""

import sqlite3
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from logs.logger import log_agent_action


DB_PATH = "budget.db"


class StatisticsInput(BaseModel):
    """Input schema for the StatisticsTool."""
    month: str = Field(
        default="all",
        description="Month to analyze in YYYY-MM format, or 'all' for all data"
    )


class StatisticsTool(BaseTool):
    """
    Queries the SQLite database and computes financial statistics
    including totals per category, average spending, and anomalies.
    """

    name: str = "calculate_statistics"
    description: str = (
        "Queries the expense database and calculates: total spending per category, "
        "overall total, average transaction, highest expense, and spending anomalies. "
        "Pass 'all' for month to analyze all records."
    )
    args_schema: type[BaseModel] = StatisticsInput

    def _run(self, month: str = "all") -> str:
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            where_clause = ""
            params = []
            if month != "all":
                where_clause = "WHERE date LIKE ?"
                params = [f"{month}%"]

            # Total per category
            cursor.execute(
                f"""
                SELECT category,
                       COUNT(*) as count,
                       SUM(amount) as total,
                       AVG(amount) as avg,
                       MAX(amount) as max_expense
                FROM expenses {where_clause}
                GROUP BY category
                ORDER BY total DESC
                """,
                params,
            )
            category_stats = cursor.fetchall()

            # Overall totals
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) as total_transactions,
                    SUM(amount) as grand_total,
                    AVG(amount) as overall_avg,
                    MAX(amount) as highest_expense,
                    MIN(amount) as lowest_expense
                FROM expenses {where_clause}
                """,
                params,
            )
            overall = cursor.fetchone()
            if not overall:
                overall = (0, 0.0, 0.0, 0.0, 0.0)
            else:
                overall = (
                    overall[0] or 0,
                    overall[1] or 0.0,
                    overall[2] or 0.0,
                    overall[3] or 0.0,
                    overall[4] or 0.0,
                )

            # Anomalies: transactions > 2x average over same filtered scope
            anomaly_inner_filter = "WHERE date LIKE ?" if month != "all" else ""
            anomaly_params = []
            anomaly_where_parts = []
            if month != "all":
                anomaly_where_parts.append("e.date LIKE ?")
                anomaly_params.append(f"{month}%")
            anomaly_where_parts.append(
                "e.amount > (SELECT AVG(amount) * 2 FROM expenses "
                f"{anomaly_inner_filter})"
            )
            if month != "all":
                anomaly_params.append(f"{month}%")
            anomaly_where_clause = "WHERE " + " AND ".join(anomaly_where_parts)
            cursor.execute(
                f"""
                SELECT e.description, e.amount, e.category, e.date
                FROM expenses e
                {anomaly_where_clause}
                ORDER BY e.amount DESC
                """,
                anomaly_params,
            )
            anomalies = cursor.fetchall()

            stats_lines = ["=== FINANCIAL STATISTICS ===\n"]
            stats_lines.append("SPENDING BY CATEGORY:")
            for cat in category_stats:
                stats_lines.append(
                    f"  {cat[0].upper()}: {cat[2]:.2f} LKR "
                    f"({cat[1]} transactions, avg {cat[3]:.2f} LKR)"
                )

            stats_lines.append("\nOVERALL SUMMARY:")
            stats_lines.append(f"  Total transactions: {overall[0]}")
            stats_lines.append(f"  Grand total spent: {overall[1]:.2f} LKR")
            stats_lines.append(f"  Average transaction: {overall[2]:.2f} LKR")
            stats_lines.append(f"  Highest single expense: {overall[3]:.2f} LKR")
            stats_lines.append(f"  Lowest single expense: {overall[4]:.2f} LKR")

            if anomalies:
                stats_lines.append("\nANOMALIES (unusually high expenses):")
                for a in anomalies:
                    stats_lines.append(
                        f"  {a[3]} - {a[0]}: {a[1]:.2f} LKR [{a[2]}]"
                    )
            else:
                stats_lines.append("\nANOMALIES: None detected.")

            result = "\n".join(stats_lines)

            log_agent_action(
                agent_name="AnalystAgent",
                input_data=f"month={month}",
                tool_called="calculate_statistics",
                output=f"Generated stats for {overall[0]} transactions",
                status="success",
            )

            return result

        except Exception as e:
            error = f"Statistics error: {str(e)}"

            log_agent_action(
                agent_name="AnalystAgent",
                input_data=month,
                tool_called="calculate_statistics",
                output=error,
                status="error",
            )

            return error

        finally:
            if conn:
                conn.close()