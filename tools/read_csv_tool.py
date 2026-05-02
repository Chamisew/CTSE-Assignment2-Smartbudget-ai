import csv
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

        rows = []
        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows.append(row)

        return f"Loaded {len(rows)} rows"