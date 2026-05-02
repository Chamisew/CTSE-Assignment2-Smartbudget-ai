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