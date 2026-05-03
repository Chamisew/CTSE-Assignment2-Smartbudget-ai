"""
Tool for reading and validating expense CSV files.
Member 1's custom tool.
"""

import csv
import math
import os
from typing import Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from logs.logger import log_agent_action


class ReadCSVInput(BaseModel):
    """Input schema for the ReadCSVTool."""
    file_path: str = Field(
        description="Path to the CSV file containing expense data"
    )


class ReadCSVTool(BaseTool):
    """
    Reads an expense CSV file, validates its structure,
    and returns clean structured data as a string.
    """

    name: str = "read_csv_file"
    description: str = (
        "Reads an expense CSV file and returns validated expense records. "
        "The CSV must have columns: date, description, amount, currency."
    )
    args_schema: type[BaseModel] = ReadCSVInput

    def _run(self, file_path: str) -> str:
        """
        Read and validate the CSV file.

        Args:
            file_path: Path to the expenses CSV file

        Returns:
            String containing validated expense records or error message
        """
        try:
            # Check file exists
            if not os.path.exists(file_path):
                error = f"File not found: {file_path}"
                log_agent_action(
                    agent_name="DataCollectorAgent",
                    input_data=file_path,
                    tool_called="read_csv_file",
                    output=error,
                    status="error"
                )
                return error

            required_columns = {"date", "description", "amount", "currency"}
            valid_rows = []
            errors = []

            with open(file_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                # Validate columns exist
                if not required_columns.issubset(set(reader.fieldnames or [])):
                    missing = required_columns - set(reader.fieldnames or [])
                    error = f"Missing columns: {missing}"
                    log_agent_action(
                        agent_name="DataCollectorAgent",
                        input_data=file_path,
                        tool_called="read_csv_file",
                        output=error,
                        status="error"
                    )
                    return error

                for i, row in enumerate(reader, start=2):
                    try:
                        # Validate amount is a positive number
                        amount = float(row["amount"])
                        if not math.isfinite(amount) or amount <= 0:
                            errors.append(f"Row {i}: amount must be positive")
                            continue

                        # Validate date format
                        if not row["date"] or len(row["date"]) < 8:
                            errors.append(f"Row {i}: invalid date")
                            continue

                        valid_rows.append({
                            "date": row["date"].strip(),
                            "description": row["description"].strip(),
                            "amount": amount,
                            "currency": row["currency"].strip()
                        })

                    except ValueError:
                        errors.append(f"Row {i}: invalid amount value")

            result = (
                f"Successfully loaded {len(valid_rows)} valid expense records.\n"
                f"Validation errors: {len(errors)}\n"
                f"Records: {valid_rows}"
            )

            log_agent_action(
                agent_name="DataCollectorAgent",
                input_data=file_path,
                tool_called="read_csv_file",
                output=f"Loaded {len(valid_rows)} records",
                status="success"
            )

            return result

        except Exception as e:
            error = f"Unexpected error reading CSV: {str(e)}"
            log_agent_action(
                agent_name="DataCollectorAgent",
                input_data=file_path,
                tool_called="read_csv_file",
                output=error,
                status="error"
            )
            return error