"""Property-based evaluation tests for SmartBudget tool accuracy and security."""

import csv
import re
import sqlite3
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

import tools.database_tool as database_tool
import tools.statistics_tool as statistics_tool
from tools.database_tool import CATEGORIES, SaveDatabaseTool, categorize_expense
from tools.read_csv_tool import ReadCSVTool
from tools.statistics_tool import StatisticsTool


def _extract_loaded_count(result: str) -> int:
    match = re.search(r"Successfully loaded (\d+) valid expense records", result)
    assert match is not None, f"Unexpected collector output format: {result}"
    return int(match.group(1))


def _is_valid_amount(value: str) -> bool:
    try:
        amount = float(value)
        return amount > 0 and amount != float("inf") and amount != float("-inf") and amount == amount
    except ValueError:
        return False


class TestPropertyBasedEvaluation:
    """Evaluation suite focused on output correctness and basic security constraints."""

    @settings(max_examples=60, deadline=None)
    @given(st.text(min_size=0, max_size=80))
    def test_categorizer_outputs_only_allowed_categories(self, description: str):
        category = categorize_expense(description)
        assert category in CATEGORIES

    @settings(max_examples=40, deadline=None)
    @given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters=","), min_size=0, max_size=40))
    def test_categorization_is_case_insensitive(self, description: str):
        lower = categorize_expense(description.lower())
        upper = categorize_expense(description.upper())
        assert lower == upper

    @settings(max_examples=30, deadline=None)
    @given(
        st.lists(
            st.fixed_dictionaries(
                {
                    "date": st.one_of(
                        st.just("2026-01-15"),
                        st.just("2026/01/15"),
                        st.text(min_size=0, max_size=7),
                    ),
                    "description": st.text(
                        alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters=","),
                        min_size=0,
                        max_size=60,
                    ),
                    "amount": st.one_of(
                        st.floats(
                            min_value=-10000,
                            max_value=100000,
                            allow_nan=False,
                            allow_infinity=False,
                        ).map(lambda x: f"{x}"),
                        st.sampled_from(["", "abc", "NaN", "inf", "-inf"]),
                    ),
                    "currency": st.sampled_from(["LKR", "USD", "EUR", ""]),
                }
            ),
            min_size=1,
            max_size=25,
        )
    )
    def test_collector_valid_record_count_matches_validation_rules(self, rows):
        tool = ReadCSVTool()
        csv_path = Path("data/property_eval_expenses.csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "description", "amount", "currency"])
            writer.writeheader()
            writer.writerows(rows)

        result = tool._run(str(csv_path))
        loaded_count = _extract_loaded_count(result)

        expected_count = sum(
            1
            for row in rows
            if _is_valid_amount(row["amount"]) and row["date"] and len(row["date"]) >= 8
        )
        assert loaded_count == expected_count

        if csv_path.exists():
            csv_path.unlink()


@settings(max_examples=30, deadline=None)
@given(st.text(min_size=0, max_size=64))
def test_statistics_month_filter_resists_injection_and_never_crashes(month_filter: str):
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "budget_eval.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                description TEXT,
                amount REAL,
                currency TEXT,
                category TEXT
            )
            """
        )
        conn.executemany(
            "INSERT INTO expenses VALUES (NULL,?,?,?,?,?)",
            [
                ("2026-01-01", "Supermarket", 3500, "LKR", "food"),
                ("2026-01-02", "Taxi", 700, "LKR", "transport"),
                ("2026-01-03", "Electricity", 6200, "LKR", "bills"),
            ],
        )
        conn.commit()
        conn.close()

        old_db_path = statistics_tool.DB_PATH
        statistics_tool.DB_PATH = str(db_path)
        try:
            tool = StatisticsTool()
            result = tool._run(month_filter)
        finally:
            statistics_tool.DB_PATH = old_db_path

        assert "Statistics error" not in result
        assert "OVERALL SUMMARY:" in result
        assert "Grand total spent:" in result


@settings(max_examples=20, deadline=None)
@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=120))
def test_database_tool_treats_malicious_description_as_data(description: str):
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "budget_eval.db"
        old_db_path = database_tool.DB_PATH
        database_tool.DB_PATH = str(db_path)
        try:
            payload = description + " '; DROP TABLE expenses; --"
            records = (
                "Loaded 1 records.\n"
                "Records: [{'date': '2026-01-01', 'description': '"
                + payload.replace("'", "\\'")
                + "', 'amount': 1234.5, 'currency': 'LKR'}]"
            )

            tool = SaveDatabaseTool()
            result = tool._run(records)
            assert "successfully saved" in result.lower()

            conn = sqlite3.connect(db_path)
            count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
            stored_desc = conn.execute("SELECT description FROM expenses LIMIT 1").fetchone()[0]
            conn.close()
        finally:
            database_tool.DB_PATH = old_db_path

        assert count == 1
        assert "DROP TABLE" in stored_desc
