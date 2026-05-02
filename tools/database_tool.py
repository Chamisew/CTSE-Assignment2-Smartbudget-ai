"""
Tool for saving categorized expenses into a local SQLite database.
Member 2's custom tool.
"""

import sqlite3
import ast
from typing import Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from logs.logger import log_agent_action


DB_PATH = "budget.db"

CATEGORIES = {
    "food": ["supermarket", "grocery", "restaurant", "lunch", "dinner",
             "breakfast", "cafe", "food", "meal"],
    "transport": ["uber", "taxi", "bus", "train", "petrol", "fuel",
                  "ride", "transport"],
    "bills": ["electricity", "water", "internet", "mobile", "phone",
              "bill", "subscription", "netflix"],
    "health": ["pharmacy", "doctor", "medicine", "hospital", "clinic",
               "health", "gym"],
    "entertainment": ["cinema", "movie", "concert", "game", "sport",
                      "entertainment"],
    "other": []
}


def categorize_expense(description: str) -> str:
    """
    Categorize an expense based on its description keywords.

    Args:
        description: The expense description text

    Returns:
        Category string
    """
    desc_lower = description.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in desc_lower for keyword in keywords):
            return category
    return "other"


class SaveDatabaseInput(BaseModel):
    """Input schema for the SaveDatabaseTool."""
    records_str: str = Field(
        description="String representation of the list of expense record dicts"
    )


class SaveDatabaseTool(BaseTool):
    """
    Categorizes expenses and saves them into a local SQLite database.
    Creates the database and table if they do not exist.
    """

    name: str = "save_to_database"
    description: str = (
        "Takes expense records as a string, categorizes each one, "
        "and saves them into the local SQLite database budget.db."
    )
    args_schema: type[BaseModel] = SaveDatabaseInput

    def _run(self, records_str: str) -> str:
        """
        Parse, categorize, and save expense records to SQLite.

        Args:
            records_str: String of expense records list

        Returns:
            Summary of what was saved
        """
        try:
            # Parse the records from string
            # Extract the list portion from the collector agent's output
            start = records_str.find("[")
            end = records_str.rfind("]") + 1
            if start == -1 or end == 0:
                return "Error: Could not find expense records list in input."

            list_str = records_str[start:end]
            records = ast.literal_eval(list_str)

            # Setup database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    category TEXT NOT NULL
                )
            """)

            # Clear old data for fresh run
            cursor.execute("DELETE FROM expenses")

            # Insert categorized records
            saved_count = 0
            for record in records:
                category = categorize_expense(record["description"])
                cursor.execute(
                    "INSERT INTO expenses (date, description, amount, currency, category) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (record["date"], record["description"],
                     record["amount"], record["currency"], category)
                )
                saved_count += 1

            conn.commit()
            conn.close()

            result = (
                f"Successfully saved {saved_count} expenses to database. "
                f"Categories used: {list(CATEGORIES.keys())}"
            )

            log_agent_action(
                agent_name="CategorizerAgent",
                input_data=f"{saved_count} records received",
                tool_called="save_to_database",
                output=result,
                status="success"
            )

            return result

        except Exception as e:
            error = f"Database error: {str(e)}"
            log_agent_action(
                agent_name="CategorizerAgent",
                input_data=records_str[:100],
                tool_called="save_to_database",
                output=error,
                status="error"
            )
            return error