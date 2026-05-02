import csv
import math
import os
from typing import Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ReadCSVInput(BaseModel):
    file_path: str = Field(
        description="Path to the CSV file containing expense data"
    )


class ReadCSVTool(BaseTool):
    name: str = "read_csv_file"
    description: str = (
        "Reads an expense CSV file and returns validated expense records. "
        "The CSV must have columns: date, description, amount, currency."
    )
    args_schema: type[BaseModel] = ReadCSVInput

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"

        required_columns = {"date", "description", "amount", "currency"}
        valid_rows = []
        errors = []

        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            if not required_columns.issubset(set(reader.fieldnames or [])):
                missing = required_columns - set(reader.fieldnames or [])
                return f"Missing columns: {missing}"

            for i, row in enumerate(reader, start=2):
                try:
                    amount = float(row["amount"])
                    if not math.isfinite(amount) or amount <= 0:
                        errors.append(f"Row {i}: amount must be positive")
                        continue

                    valid_rows.append({
                        "date": row["date"],
                        "description": row["description"],
                        "amount": amount,
                        "currency": row["currency"]
                    })

                except ValueError:
                    errors.append(f"Row {i}: invalid amount")

        return f"Valid: {len(valid_rows)}, Errors: {len(errors)}"