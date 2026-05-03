"""
Automated test suite for SmartBudget AI.
Each member contributes test cases for their own agent/tool.
"""

import os
import sqlite3
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.read_csv_tool import ReadCSVTool
from tools.database_tool import SaveDatabaseTool, categorize_expense
from tools.statistics_tool import StatisticsTool
from tools.report_tool import GenerateReportTool


# ─────────────────────────────────────────────
# MEMBER 1 TESTS — ReadCSVTool
# ─────────────────────────────────────────────

class TestReadCSVTool:
    """Tests for the Data Collector Agent's tool."""

    def setup_method(self):
        self.tool = ReadCSVTool()
        # Create a valid test CSV
        os.makedirs("data", exist_ok=True)
        with open("data/test_expenses.csv", "w") as f:
            f.write("date,description,amount,currency\n")
            f.write("2024-01-01,Supermarket,3500,LKR\n")
            f.write("2024-01-02,Uber ride,450,LKR\n")

    def test_valid_csv_loads_correctly(self):
        result = self.tool._run("data/test_expenses.csv")
        assert "2 valid expense records" in result

    def test_missing_file_returns_error(self):
        result = self.tool._run("data/nonexistent.csv")
        assert "not found" in result.lower()

    def test_invalid_amount_is_rejected(self):
        with open("data/bad_expenses.csv", "w") as f:
            f.write("date,description,amount,currency\n")
            f.write("2024-01-01,Test,-100,LKR\n")
        result = self.tool._run("data/bad_expenses.csv")
        assert "0 valid" in result or "error" in result.lower()

    def teardown_method(self):
        for f in ["data/test_expenses.csv", "data/bad_expenses.csv"]:
            if os.path.exists(f):
                os.remove(f)


# ─────────────────────────────────────────────
# MEMBER 2 TESTS — SaveDatabaseTool
# ─────────────────────────────────────────────

class TestSaveDatabaseTool:
    """Tests for the Categorizer Agent's tool."""

    def setup_method(self):
        self.tool = SaveDatabaseTool()
        if os.path.exists("budget.db"):
            os.remove("budget.db")

    def test_categorize_food_correctly(self):
        assert categorize_expense("Supermarket groceries") == "food"

    def test_categorize_transport_correctly(self):
        assert categorize_expense("Uber ride to office") == "transport"

    def test_categorize_bills_correctly(self):
        assert categorize_expense("Electricity bill") == "bills"

    def test_unknown_expense_is_other(self):
        assert categorize_expense("Random unknown thing") == "other"

    def test_database_saves_records(self):
        sample = (
            "Loaded 2 records.\n"
            "Records: [{'date': '2024-01-01', 'description': 'Supermarket', "
            "'amount': 3500.0, 'currency': 'LKR'}, "
            "{'date': '2024-01-02', 'description': 'Uber ride', "
            "'amount': 450.0, 'currency': 'LKR'}]"
        )
        result = self.tool._run(sample)
        assert "successfully saved" in result.lower()
        conn = sqlite3.connect("budget.db")
        count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
        conn.close()
        assert count == 2

    def teardown_method(self):
        if os.path.exists("budget.db"):
            os.remove("budget.db")


# ─────────────────────────────────────────────
# MEMBER 3 TESTS — StatisticsTool
# ─────────────────────────────────────────────

class TestStatisticsTool:
    """Tests for the Analyst Agent's tool."""

    def setup_method(self):
        self.tool = StatisticsTool()
        # Seed a test database
        if os.path.exists("budget.db"):
            os.remove("budget.db")
        conn = sqlite3.connect("budget.db")
        conn.execute("""
            CREATE TABLE expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, description TEXT,
                amount REAL, currency TEXT, category TEXT
            )
        """)
        conn.executemany(
            "INSERT INTO expenses VALUES (NULL,?,?,?,?,?)",
            [
                ("2024-01-01", "Supermarket", 3500, "LKR", "food"),
                ("2024-01-02", "Uber", 450, "LKR", "transport"),
                ("2024-01-03", "Electricity", 8200, "LKR", "bills"),
            ]
        )
        conn.commit()
        conn.close()

    def test_statistics_returns_grand_total(self):
        result = self.tool._run("all")
        assert "12150.00" in result  # 3500+450+8200

    def test_statistics_shows_categories(self):
        result = self.tool._run("all")
        assert "FOOD" in result
        assert "TRANSPORT" in result

    def test_anomaly_detected_for_high_expense(self):
        result = self.tool._run("all")
        # Electricity at 8200 is >2x the average (4050)
        assert "Electricity" in result or "ANOMAL" in result

    def teardown_method(self):
        if os.path.exists("budget.db"):
            os.remove("budget.db")


# ─────────────────────────────────────────────
# MEMBER 4 TESTS — GenerateReportTool
# ─────────────────────────────────────────────

class TestGenerateReportTool:
    """Tests for the Reporter Agent's tool."""

    def setup_method(self):
        self.tool = GenerateReportTool()

    def test_report_file_is_created(self):
        result = self.tool._run("## Test Report\nThis is a test.")
        assert "successfully saved" in result.lower()
        # Check a file was actually created
        files = os.listdir("reports")
        assert any("budget_report_" in f for f in files)

    def test_report_contains_header(self):
        self.tool._run("Some report content without header.")
        files = sorted(os.listdir("reports"))
        latest = open(f"reports/{files[-1]}").read()
        assert "SmartBudget AI" in latest

    def test_empty_report_still_saves(self):
        result = self.tool._run("   ")
        assert "saved" in result.lower()

    def teardown_method(self):
        if os.path.exists("reports"):
            for f in os.listdir("reports"):
                os.remove(f"reports/{f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])