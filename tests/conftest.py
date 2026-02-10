"""
Pytest configuration and shared fixtures for DeepDive test suite.
"""

import json
import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def sample_sql_queries():
    """Sample SQL queries for testing."""
    return {
        "select_valid": "SELECT id, name FROM users WHERE active = true",
        "select_with_wildcard": "SELECT * FROM users",
        "select_without_where": "SELECT * FROM users",
        "select_numeric": "SELECT 1",
        "select_expression": "SELECT 1 + 2",
        "insert_into": "INSERT INTO users (name, email) VALUES ('test', 'test@test.com')",
        "insert_values": "INSERT INTO users VALUES (1, 'test')",
        "update_basic": "UPDATE users SET name = 'new' WHERE id = 1",
        "update_no_where": "UPDATE users SET active = false",
        "delete_from": "DELETE FROM users WHERE id = 1",
        "delete_no_where": "DELETE FROM users",
        "truncate_table": "TRUNCATE TABLE users",
        "drop_table": "DROP TABLE users",
        "drop_database": "DROP DATABASE mydb",
        "alter_table": "ALTER TABLE users ADD COLUMN age INT",
        "create_table": "CREATE TABLE test (id INT, name VARCHAR(100))",
        "grant_select": "GRANT SELECT ON users TO analyst",
        "revoke_write": "REVOKE INSERT ON users FROM intern",
        "cte_with_insert": "WITH new_users AS (INSERT INTO users VALUES (1)) SELECT * FROM users",
        "cte_with_update": "WITH updated AS (UPDATE users SET active = true) SELECT * FROM users",
        "dangerous_drop_after_semicolon": "SELECT 1; DROP TABLE users",
        "dangerous_delete_after_semicolon": "SELECT 1; DELETE FROM users",
        "comment_injection": "SELECT * FROM users -- WHERE 1=1",
        "block_comment": "SELECT * /* comment */ FROM users",
        "union_select": "SELECT * FROM users UNION SELECT * FROM admins",
        "sleep_function": "SELECT SLEEP(5)",
        "benchmark_function": "SELECT BENCHMARK(10000000, MD5('test'))",
        "null_comparison": "SELECT * FROM users WHERE name = NULL",
        "missing_group_by": "SELECT status, COUNT(*) FROM orders GROUP BY status",
        "valid_group_by": "SELECT status, COUNT(*) FROM orders GROUP BY status, id",
        "unmatched_parentheses": "SELECT * FROM users WHERE (id = 1",
        "unmatched_quotes": "SELECT * FROM users WHERE name = 'test",
    }


@pytest.fixture
def sample_chart_data():
    """Sample chart data for testing."""
    return {
        "empty": [],
        "single_item": [{"category": "A", "value": 10}],
        "small_dataset": [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
            {"category": "C", "value": 15},
        ],
        "temporal_line": [
            {"date": "2024-01-01", "value": 100},
            {"date": "2024-02-01", "value": 150},
            {"date": "2024-03-01", "value": 200},
        ],
        "temporal_time": [
            {"time": "08:00", "value": 50},
            {"time": "09:00", "value": 75},
        ],
        "two_numeric": [
            {"x": 1, "y": 10},
            {"x": 2, "y": 20},
            {"x": 3, "y": 30},
        ],
        "single_numeric": [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
        ],
        "with_month": [
            {"month": "January", "sales": 100},
            {"month": "February", "sales": 150},
        ],
        "with_year": [
            {"year": 2023, "revenue": 1000},
            {"year": 2024, "revenue": 1500},
        ],
    }


@pytest.fixture
def sample_schema():
    """Sample database schema for mermaid generation."""
    return {
        "tables": {
            "users": {
                "columns": [
                    {"name": "id", "type": "INT"},
                    {"name": "username", "type": "VARCHAR(50)"},
                    {"name": "email", "type": "VARCHAR(100)"},
                    {"name": "created_at", "type": "TIMESTAMP"},
                ],
                "primary_key": [{"column": "id"}],
                "foreign_keys": [
                    {"column": "email", "references_table": "accounts", "references_column": "email"}
                ],
            },
            "accounts": {
                "columns": [
                    {"name": "email", "type": "VARCHAR(100)"},
                    {"name": "plan", "type": "VARCHAR(20)"},
                ],
                "primary_key": [{"column": "email"}],
                "foreign_keys": [],
            },
            "orders": {
                "columns": [
                    {"name": "id", "type": "INT"},
                    {"name": "user_id", "type": "INT"},
                    {"name": "total", "type": "DECIMAL(10,2)"},
                ],
                "primary_key": [{"column": "id"}],
                "foreign_keys": [
                    {"column": "user_id", "references_table": "users", "references_column": "id"}
                ],
            },
            "order_items": {
                "columns": [
                    {"name": "id", "type": "INT"},
                    {"name": "order_id", "type": "INT"},
                    {"name": "product_id", "type": "INT"},
                    {"name": "quantity", "type": "INT"},
                ],
                "primary_key": [{"column": "id"}],
                "foreign_keys": [
                    {"column": "order_id", "references_table": "orders", "references_column": "id"},
                    {"column": "product_id", "references_table": "products", "references_column": "id"},
                ],
            },
            "products": {
                "columns": [
                    {"name": "id", "type": "INT"},
                    {"name": "name", "type": "VARCHAR(100)"},
                    {"name": "price", "type": "DECIMAL(10,2)"},
                ],
                "primary_key": [{"column": "id"}],
                "foreign_keys": [],
            },
        }
    }


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file for testing."""
    def _create(data, filename="test_data.json"):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            path = f.name
        yield path
        if os.path.exists(path):
            os.unlink(path)
    return _create


@pytest.fixture
def temp_output_file():
    """Create a temporary output file path for testing."""
    def _create(filename="test_output.mmd"):
        path = os.path.join(tempfile.gettempdir(), filename)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    return _create