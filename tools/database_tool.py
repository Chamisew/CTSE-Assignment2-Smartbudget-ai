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