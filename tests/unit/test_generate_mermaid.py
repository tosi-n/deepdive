"""
Unit tests for generate_mermaid.py - Mermaid diagram generation from database schemas.
"""

import pytest
import json
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from generate_mermaid import (
    generate_erd,
    generate_lineage,
    generate_query_plan,
    save_and_open,
)


class TestGenerateErd:
    """Test generate_erd function."""

    def test_empty_schema_returns_er_header_only(self):
        result = generate_erd({})
        assert result == "erDiagram"

    def test_empty_tables_returns_er_header_only(self):
        result = generate_erd({"tables": {}})
        assert result == "erDiagram"

    def test_single_table_no_columns(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [],
                    "primary_key": [],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_erd(schema)
        assert "erDiagram" in result
        assert "USERS {" in result

    def test_single_table_with_columns(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "name", "type": "VARCHAR(50)"},
                    ],
                    "primary_key": [],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_erd(schema)
        assert "USERS {" in result
        assert "INT id" in result
        assert "VARCHAR(50) name" in result

    def test_primary_key_marked(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "name", "type": "VARCHAR(50)"},
                    ],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_erd(schema)
        assert "INT id PK" in result

    def test_non_primary_key_no_pk_marker(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "name", "type": "VARCHAR(50)"},
                    ],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_erd(schema)
        assert "VARCHAR(50) name" in result
        assert "VARCHAR(50) name PK" not in result

    def test_multiple_primary_keys(self):
        schema = {
            "tables": {
                "order_items": {
                    "columns": [
                        {"name": "order_id", "type": "INT"},
                        {"name": "item_id", "type": "INT"},
                        {"name": "quantity", "type": "INT"},
                    ],
                    "primary_key": [{"column": "order_id"}, {"column": "item_id"}],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_erd(schema)
        assert "INT order_id PK" in result
        assert "INT item_id PK" in result

    def test_relationship_added(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                    ],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [],
                },
                "orders": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [
                        {"column": "user_id", "references_table": "users", "references_column": "id"}
                    ],
                }
            }
        }
        result = generate_erd(schema)
        assert "ORDERS ||--o{ USERS" in result

    def test_relationship_not_added_for_missing_table(self):
        schema = {
            "tables": {
                "orders": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [
                        {"column": "user_id", "references_table": "users", "references_column": "id"}
                    ],
                }
            }
        }
        result = generate_erd(schema)
        assert "USERS ||--o{ ORDERS" not in result

    def test_filtered_tables_only_includes_specified(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [],
                },
                "orders": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [
                        {"column": "user_id", "references_table": "users", "references_column": "id"}
                    ],
                },
                "products": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_erd(schema, tables=["users", "orders"])
        assert "USERS {" in result
        assert "ORDERS {" in result
        assert "PRODUCTS {" not in result

    def test_filtered_includes_related_tables(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [],
                },
                "orders": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [
                        {"column": "user_id", "references_table": "users", "references_column": "id"}
                    ],
                }
            }
        }
        result = generate_erd(schema, tables=["orders"])
        assert "ORDERS {" in result
        assert "USERS {" in result

    def test_tables_sorted_alphabetically(self):
        schema = {
            "tables": {
                "zebra": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                },
                "alpha": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                },
            }
        }
        result = generate_erd(schema)
        alpha_pos = result.find("ALPHA {")
        zebra_pos = result.find("ZEBRA {")
        assert alpha_pos < zebra_pos

    def test_table_missing_from_schema_ignored(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_erd(schema, tables=["users", "missing_table"])
        assert "USERS {" in result
        assert "MISSING_TABLE" not in result

    def test_foreign_key_without_references_table_ignored(self):
        schema = {
            "tables": {
                "orders": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [
                        {"column": "user_id"}
                    ],
                }
            }
        }
        result = generate_erd(schema)
        assert "||--o{" not in result

    def test_unknown_column_handled_gracefully(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [
                        {"type": "INT"},
                    ],
                    "primary_key": [],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_erd(schema)
        assert "unknown" in result.lower()


class TestGenerateLineage:
    """Test generate_lineage function."""

    def test_empty_schema_returns_graph_header(self):
        result = generate_lineage({})
        assert result == "graph LR"

    def test_empty_tables_returns_graph_header(self):
        result = generate_lineage({"tables": {}})
        assert result == "graph LR"

    def test_no_foreign_keys_returns_graph_header(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_lineage(schema)
        assert result == "graph LR"

    def test_single_relationship(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                },
                "orders": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [],
                    "foreign_keys": [
                        {"column": "user_id", "references_table": "users", "references_column": "id"}
                    ],
                }
            }
        }
        result = generate_lineage(schema)
        assert "USERS -->|FK| ORDERS" in result

    def test_multiple_relationships(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                },
                "orders": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [],
                    "foreign_keys": [
                        {"column": "user_id", "references_table": "users", "references_column": "id"}
                    ],
                },
                "posts": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [],
                    "foreign_keys": [
                        {"column": "user_id", "references_table": "users", "references_column": "id"}
                    ],
                }
            }
        }
        result = generate_lineage(schema)
        assert "USERS -->|FK| ORDERS" in result
        assert "USERS -->|FK| POSTS" in result

    def test_specific_table_shows_upstream_only(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                },
                "orders": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [],
                    "foreign_keys": [
                        {"column": "user_id", "references_table": "users", "references_column": "id"}
                    ],
                },
            }
        }
        result = generate_lineage(schema, table_name="orders")
        assert "USERS -->|FK| ORDERS" in result

    def test_specific_table_shows_downstream(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                },
                "orders": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [],
                    "foreign_keys": [
                        {"column": "user_id", "references_table": "users", "references_column": "id"}
                    ],
                },
            }
        }
        result = generate_lineage(schema, table_name="users")
        assert "USERS -->|FK| ORDERS" in result

    def test_missing_table_returns_graph_header(self):
        result = generate_lineage({"tables": {}}, table_name="missing")
        assert result == "graph LR"


class TestGenerateQueryPlan:
    """Test generate_query_plan function."""

    def test_empty_plan_returns_graph_header(self):
        result = generate_query_plan(None)
        assert result == "graph TD"

    def test_empty_children_returns_graph_header(self):
        result = generate_query_plan({})
        assert result == "graph TD"

    def test_simple_node(self):
        plan = {
            "type": "Seq Scan",
            "details": "on users",
            "children": [],
        }
        result = generate_query_plan(plan)
        assert "graph TD" in result
        assert "Seq Scan" in result

    def test_node_with_details(self):
        plan = {
            "type": "Index Scan",
            "details": "using idx_users_email on users",
            "children": [],
        }
        result = generate_query_plan(plan)
        assert "Index Scan" in result
        assert "idx_users_email" in result

    def test_nested_children(self):
        plan = {
            "type": "Hash Join",
            "details": "",
            "children": [
                {
                    "type": "Seq Scan",
                    "details": "on users",
                    "children": [],
                },
                {
                    "type": "Hash",
                    "details": "",
                    "children": [
                        {
                            "type": "Seq Scan",
                            "details": "on orders",
                            "children": [],
                        }
                    ],
                },
            ],
        }
        result = generate_query_plan(plan)
        assert "Hash Join" in result
        assert "Seq Scan" in result

    def test_html_line_breaks_for_details(self):
        plan = {
            "type": "Nested Loop",
            "details": "inner join",
            "children": [],
        }
        result = generate_query_plan(plan)
        assert "<br/>inner join" in result

    def test_multiple_children_at_same_level(self):
        plan = {
            "type": "Append",
            "details": "",
            "children": [
                {"type": "Scan1", "details": "", "children": []},
                {"type": "Scan2", "details": "", "children": []},
                {"type": "Scan3", "details": "", "children": []},
            ],
        }
        result = generate_query_plan(plan)
        assert "Scan1" in result
        assert "Scan2" in result
        assert "Scan3" in result

    def test_all_nodes_connected(self):
        plan = {
            "type": "Root",
            "details": "",
            "children": [
                {
                    "type": "Child1",
                    "details": "",
                    "children": [],
                },
            ],
        }
        result = generate_query_plan(plan)
        assert "-->" in result


class TestSaveAndOpen:
    """Test save_and_open function."""

    def test_saves_mmd_file(self):
        content = "graph LR\n    A --> B"
        with tempfile.NamedTemporaryFile(suffix='.mmd', delete=False) as f:
            path = f.name
        try:
            result = save_and_open(content, path, open_browser=False)
            assert result == path
            assert os.path.exists(path)

            with open(path, 'r') as f:
                assert f.read() == content
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_creates_directory_if_not_exists(self):
        content = "graph LR\n    A --> B"
        test_dir = os.path.join(tempfile.gettempdir(), "test_subdir_xyz")
        path = os.path.join(test_dir, "test.mmd")
        try:
            result = save_and_open(content, path, open_browser=False)
            assert os.path.exists(path)
        finally:
            if os.path.exists(path):
                os.unlink(path)
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

    def test_no_open_browser_when_disabled(self):
        content = "graph LR\n    A --> B"
        with tempfile.NamedTemporaryFile(suffix='.mmd', delete=False) as f:
            path = f.name
        try:
            with patch('generate_mermaid.webbrowser') as mock_browser:
                save_and_open(content, path, open_browser=False)
                mock_browser.open.assert_not_called()
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_opens_browser_when_enabled(self):
        content = "graph LR\n    A --> B"
        with tempfile.NamedTemporaryFile(suffix='.mmd', delete=False) as f:
            path = f.name
        try:
            with patch('generate_mermaid.webbrowser') as mock_browser:
                save_and_open(content, path, open_browser=True)
                mock_browser.open.assert_called_once()
                call_args = mock_browser.open.call_args[0][0]
                assert "mermaid.live" in call_args
                assert "pako:" in call_args
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestGenerateMermaidEdgeCases:
    """Test edge cases for mermaid generation."""

    def test_erd_handles_missing_foreign_keys_key(self):
        schema = {
            "tables": {
                "orders": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                }
            }
        }
        result = generate_erd(schema)
        assert "ORDERS {" in result

    def test_erd_handles_missing_columns_key(self):
        schema = {
            "tables": {
                "users": {
                    "primary_key": [],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_erd(schema)
        assert "USERS {" in result

    def test_erd_handles_missing_primary_key_key(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "foreign_keys": [],
                }
            }
        }
        result = generate_erd(schema)
        assert "USERS {" in result

    def test_lineage_handles_missing_foreign_keys_key(self):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                }
            }
        }
        result = generate_lineage(schema)
        assert result == "graph LR"

    def test_query_plan_handles_missing_type_key(self):
        plan = {
            "details": "some details",
            "children": [],
        }
        result = generate_query_plan(plan)
        assert "Unknown" in result

    def test_query_plan_handles_missing_children_key(self):
        plan = {
            "type": "Scan",
            "details": "test",
        }
        result = generate_query_plan(plan)
        assert "Scan" in result


class TestGenerateMermaidMain:
    """Tests for the main() function in generate_mermaid.py"""

    @pytest.fixture
    def temp_schema_file(self):
        def _create(schema):
            import tempfile
            import json
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(schema, f)
                return f.name
        return _create

    def test_main_with_erd_type(self, temp_schema_file, capsys):
        import sys
        import os
        from generate_mermaid import main as mermaid_main
        original_argv = sys.argv
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                }
            }
        }
        schema_file = temp_schema_file(schema)
        try:
            sys.argv = ['generate_mermaid.py', 'erd', '--schema-file', schema_file, '--output', '/tmp/test_erd.mmd', '--no-open']
            result = mermaid_main()
            assert result == 0
            assert os.path.exists('/tmp/test_erd.mmd')
        finally:
            sys.argv = original_argv
            os.unlink(schema_file)
            if os.path.exists('/tmp/test_erd.mmd'):
                os.unlink('/tmp/test_erd.mmd')

    def test_main_with_lineage_type(self, temp_schema_file, capsys):
        import sys
        import os
        from generate_mermaid import main as mermaid_main
        original_argv = sys.argv
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                },
                "orders": {
                    "columns": [
                        {"name": "id", "type": "INT"},
                        {"name": "user_id", "type": "INT"},
                    ],
                    "primary_key": [],
                    "foreign_keys": [
                        {"column": "user_id", "references_table": "users", "references_column": "id"}
                    ],
                }
            }
        }
        schema_file = temp_schema_file(schema)
        try:
            sys.argv = ['generate_mermaid.py', 'lineage', '--schema-file', schema_file, '--output', '/tmp/test_lineage.mmd', '--no-open']
            result = mermaid_main()
            assert result == 0
        finally:
            sys.argv = original_argv
            os.unlink(schema_file)
            if os.path.exists('/tmp/test_lineage.mmd'):
                os.unlink('/tmp/test_lineage.mmd')

    def test_main_with_schema_type_alias(self, temp_schema_file, capsys):
        import sys
        import os
        from generate_mermaid import main as mermaid_main
        original_argv = sys.argv
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                }
            }
        }
        schema_file = temp_schema_file(schema)
        try:
            sys.argv = ['generate_mermaid.py', 'schema', '--schema-file', schema_file, '--output', '/tmp/test_schema.mmd', '--no-open']
            result = mermaid_main()
            assert result == 0
        finally:
            sys.argv = original_argv
            os.unlink(schema_file)
            if os.path.exists('/tmp/test_schema.mmd'):
                os.unlink('/tmp/test_schema.mmd')