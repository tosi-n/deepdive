"""
Integration tests for CLI execution of all three scripts.
"""

import pytest
import json
import sys
import os
import subprocess
import tempfile


class TestValidateQueryCLI:
    """Integration tests for validate_query.py CLI."""

    @pytest.fixture
    def script_path(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'validate_query.py'))

    def test_valid_select_returns_0(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, '--query', 'SELECT * FROM users WHERE id = 1'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Valid: ✓' in result.stdout

    def test_invalid_syntax_returns_1(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, '--query', "SELECT * FROM users WHERE name = 'test"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'Valid: ✗' in result.stdout
        assert 'ERRORS:' in result.stdout

    def test_dangerous_pattern_returns_0_non_strict(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, '--query', 'SELECT SLEEP(5)'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'WARNINGS:' in result.stdout

    def test_dangerous_pattern_strict_returns_1(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, '--query', 'SELECT SLEEP(5)', '--strict'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'ERRORS:' in result.stdout

    def test_write_operation_detected(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, '--query', 'INSERT INTO users VALUES (1)'],
            capture_output=True,
            text=True
        )
        assert 'Write Operation: Yes' in result.stdout

    def test_query_type_shown(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, '--query', 'SELECT * FROM users'],
            capture_output=True,
            text=True
        )
        assert 'Query Type: SELECT' in result.stdout

    def test_batch_check_flag(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path,
             '--query', 'DELETE FROM users',
             '--check-batch', '--estimated-rows', '2000'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert '2000 rows' in result.stdout

    def test_missing_query_argument(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

    def test_help_flag(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Validate SQL queries' in result.stdout


class TestGenerateChartCLI:
    """Integration tests for generate_chart.py CLI."""

    @pytest.fixture
    def script_path(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'generate_chart.py'))

    @pytest.fixture
    def temp_data_file(self):
        def _create(data):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(data, f)
                return f.name
        yield _create
        for f in ["/tmp/test_chart.json", "/tmp/test_chart.png", "/tmp/test_chart.svg"]:
            if os.path.exists(f):
                os.unlink(f)

    def test_missing_data_file_returns_1(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, '--data-file', '/nonexistent/data.json', '--output', '/tmp/test.png'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'not found' in result.stdout

    def test_invalid_json_returns_1(self, script_path):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('not valid json')
            path = f.name
        try:
            result = subprocess.run(
                [sys.executable, script_path, '--data-file', path, '--output', '/tmp/test.png'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 1
            assert 'Invalid JSON' in result.stdout
        finally:
            os.unlink(path)

    def test_empty_data_returns_0_no_chart(self, script_path, temp_data_file):
        data_file = temp_data_file([])
        try:
            result = subprocess.run(
                [sys.executable, script_path, '--data-file', data_file, '--output', '/tmp/test.png'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'No data' in result.stdout
        finally:
            os.unlink(data_file)

    def test_valid_data_shows_chart_type(self, script_path, temp_data_file):
        data = [{"category": "A", "value": 10}, {"category": "B", "value": 20}]
        data_file = temp_data_file(data)
        try:
            result = subprocess.run(
                [sys.executable, script_path, '--data-file', data_file, '--output', '/tmp/test.png'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'Chart type:' in result.stdout
        finally:
            os.unlink(data_file)

    def test_explicit_chart_type(self, script_path, temp_data_file):
        data = [{"category": "A", "value": 10}]
        data_file = temp_data_file(data)
        try:
            result = subprocess.run(
                [sys.executable, script_path, '--data-file', data_file, '--output', '/tmp/test.png', '--type', 'bar'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'Chart type: bar' in result.stdout
        finally:
            os.unlink(data_file)

    def test_save_as_json_format(self, script_path, temp_data_file):
        data = [{"category": "A", "value": 10}]
        data_file = temp_data_file(data)
        output_path = '/tmp/test_spec.json'
        try:
            result = subprocess.run(
                [sys.executable, script_path, '--data-file', data_file, '--output', output_path, '--format', 'json'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'Vega spec saved' in result.stdout
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                spec = json.load(f)
            assert '$schema' in spec
        finally:
            os.unlink(data_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_help_flag(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Generate charts' in result.stdout

    def test_custom_width_height(self, script_path, temp_data_file):
        data = [{"category": "A", "value": 10}]
        data_file = temp_data_file(data)
        output_path = '/tmp/test_spec.json'
        try:
            result = subprocess.run(
                [sys.executable, script_path,
                 '--data-file', data_file,
                 '--output', output_path,
                 '--width', '600',
                 '--height', '300'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
        finally:
            os.unlink(data_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_auto_chart_type_detection(self, script_path, temp_data_file):
        data = [{"date": "2024-01-01", "value": 100}, {"date": "2024-02-01", "value": 150}]
        data_file = temp_data_file(data)
        output_path = '/tmp/test_auto.png'
        try:
            result = subprocess.run(
                [sys.executable, script_path,
                 '--data-file', data_file,
                 '--output', output_path,
                 '--type', 'auto'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'Chart type: line' in result.stdout
        finally:
            os.unlink(data_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_title_from_filename(self, script_path, temp_data_file):
        data = [{"category": "A", "value": 10}]
        data_file = temp_data_file(data)
        output_path = '/tmp/my_test_chart.png'
        try:
            result = subprocess.run(
                [sys.executable, script_path,
                 '--data-file', data_file,
                 '--output', output_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
        finally:
            os.unlink(data_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_invalid_chart_type(self, script_path, temp_data_file):
        data = [{"category": "A", "value": 10}]
        data_file = temp_data_file(data)
        output_path = '/tmp/test_invalid.png'
        try:
            result = subprocess.run(
                [sys.executable, script_path,
                 '--data-file', data_file,
                 '--output', output_path,
                 '--type', 'invalid_type'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 2
        finally:
            os.unlink(data_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_svg_format_output(self, script_path, temp_data_file):
        data = [{"category": "A", "value": 10}]
        data_file = temp_data_file(data)
        output_path = '/tmp/test_chart.svg'
        try:
            result = subprocess.run(
                [sys.executable, script_path,
                 '--data-file', data_file,
                 '--output', output_path,
                 '--format', 'svg'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
        finally:
            os.unlink(data_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_custom_title_argument(self, script_path, temp_data_file):
        data = [{"category": "A", "value": 10}]
        data_file = temp_data_file(data)
        output_path = '/tmp/test_custom_title.png'
        try:
            result = subprocess.run(
                [sys.executable, script_path,
                 '--data-file', data_file,
                 '--output', output_path,
                 '--title', 'My Custom Chart Title'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
        finally:
            os.unlink(data_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_output_to_subdirectory(self, script_path, temp_data_file):
        data = [{"category": "A", "value": 10}]
        data_file = temp_data_file(data)
        output_path = '/tmp/test_subdir_output/chart.json'
        try:
            result = subprocess.run(
                [sys.executable, script_path,
                 '--data-file', data_file,
                 '--output', output_path,
                 '--format', 'json'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert os.path.exists(output_path), f"Expected {output_path} to exist. stdout: {result.stdout}, stderr: {result.stderr}"
        finally:
            os.unlink(data_file)
            if os.path.exists('/tmp/test_subdir_output'):
                import shutil
                shutil.rmtree('/tmp/test_subdir_output')

    def test_pie_chart_detection(self, script_path, temp_data_file):
        data = [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
            {"category": "C", "value": 15},
        ]
        data_file = temp_data_file(data)
        output_path = '/tmp/test_pie.png'
        try:
            result = subprocess.run(
                [sys.executable, script_path,
                 '--data-file', data_file,
                 '--output', output_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'Chart type: pie' in result.stdout
        finally:
            os.unlink(data_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_scatter_chart_detection(self, script_path, temp_data_file):
        data = [
            {"x": 1, "y": 10},
            {"x": 2, "y": 20},
            {"x": 3, "y": 30},
        ]
        data_file = temp_data_file(data)
        output_path = '/tmp/test_scatter.png'
        try:
            result = subprocess.run(
                [sys.executable, script_path,
                 '--data-file', data_file,
                 '--output', output_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'Chart type: scatter' in result.stdout
        finally:
            os.unlink(data_file)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestGenerateMermaidCLI:
    """Integration tests for generate_mermaid.py CLI."""

    @pytest.fixture
    def script_path(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'generate_mermaid.py'))

    @pytest.fixture
    def temp_schema_file(self):
        def _create(schema):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(schema, f)
                return f.name
        return _create

    def test_missing_schema_file_returns_1(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, 'erd', '--schema-file', '/nonexistent/schema.json', '--output', '/tmp/test.mmd'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert 'not found' in result.stdout

    def test_invalid_json_returns_1(self, script_path):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('not valid json')
            path = f.name
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'erd', '--schema-file', path, '--output', '/tmp/test.mmd'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 1
            assert 'Invalid JSON' in result.stdout
        finally:
            os.unlink(path)

    def test_erd_type_generates_diagram(self, script_path, temp_schema_file):
        schema = {
            "tables": {
                "users": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [{"column": "id"}],
                    "foreign_keys": [],
                }
            }
        }
        schema_file = temp_schema_file(schema)
        output_path = '/tmp/test_erd.mmd'
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'erd', '--schema-file', schema_file, '--output', output_path, '--no-open'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'Generated:' in result.stdout
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                content = f.read()
            assert 'erDiagram' in content
            assert 'USERS' in content
        finally:
            os.unlink(schema_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_schema_type_alias(self, script_path, temp_schema_file):
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
        output_path = '/tmp/test_schema.mmd'
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'schema', '--schema-file', schema_file, '--output', output_path, '--no-open'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
        finally:
            os.unlink(schema_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_lineage_type(self, script_path, temp_schema_file):
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
        output_path = '/tmp/test_lineage.mmd'
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'lineage', '--schema-file', schema_file, '--output', output_path, '--no-open'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                content = f.read()
            assert 'graph LR' in content
            assert 'USERS' in content
        finally:
            os.unlink(schema_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_query_plan_type_requires_plan_file(self, script_path, temp_schema_file):
        schema_file = temp_schema_file({"tables": {}})
        result = subprocess.run(
            [sys.executable, script_path, 'query-plan', '--schema-file', schema_file, '--output', '/tmp/test.mmd'],
            capture_output=True,
            text=True
        )
        os.unlink(schema_file)
        assert result.returncode == 1
        assert '--query-plan-file required' in result.stdout

    def test_query_plan_type(self, script_path):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as schema_f:
            json.dump({"tables": {}}, schema_f)
            schema_path = schema_f.name

        plan_data = {
            "type": "Seq Scan",
            "details": "on users",
            "children": [],
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as plan_f:
            json.dump(plan_data, plan_f)
            plan_path = plan_f.name

        output_path = '/tmp/test_query_plan.mmd'
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'query-plan',
                 '--schema-file', schema_path,
                 '--query-plan-file', plan_path,
                 '--output', output_path,
                 '--no-open'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                content = f.read()
            assert 'graph TD' in content
            assert 'Seq Scan' in content
        finally:
            os.unlink(schema_path)
            os.unlink(plan_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_tables_filter(self, script_path, temp_schema_file):
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
                "products": {
                    "columns": [{"name": "id", "type": "INT"}],
                    "primary_key": [],
                    "foreign_keys": [],
                }
            }
        }
        schema_file = temp_schema_file(schema)
        output_path = '/tmp/test_filtered.mmd'
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'erd',
                 '--schema-file', schema_file,
                 '--output', output_path,
                 '--tables', 'users,orders',
                 '--no-open'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            with open(output_path, 'r') as f:
                content = f.read()
            assert 'USERS' in content
            assert 'ORDERS' in content
        finally:
            os.unlink(schema_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_help_flag(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Generate Mermaid' in result.stdout

    def test_unknown_type_returns_error(self, script_path):
        result = subprocess.run(
            [sys.executable, script_path, 'unknown_type', '--schema-file', '/tmp/fake.json', '--output', '/tmp/test.mmd'],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

    def test_lineage_with_specific_table(self, script_path, temp_schema_file):
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
        output_path = '/tmp/test_lineage_table.mmd'
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'lineage',
                 '--schema-file', schema_file,
                 '--output', output_path,
                 '--table', 'users',
                 '--no-open'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
        finally:
            os.unlink(schema_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_erd_with_invalid_tables_filter(self, script_path, temp_schema_file):
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
        output_path = '/tmp/test_erd_filter.mmd'
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'erd',
                 '--schema-file', schema_file,
                 '--output', output_path,
                 '--tables', 'nonexistent',
                 '--no-open'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
        finally:
            os.unlink(schema_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_query_plan_file_not_found(self, script_path, temp_schema_file):
        schema_file = temp_schema_file({"tables": {}})
        result = subprocess.run(
            [sys.executable, script_path, 'query-plan',
             '--schema-file', schema_file,
             '--query-plan-file', '/nonexistent/plan.json',
             '--output', '/tmp/test.mmd',
             '--no-open'],
            capture_output=True,
            text=True
        )
        os.unlink(schema_file)
        assert result.returncode == 1
        assert 'Query plan file not found' in result.stdout

    def test_erd_opens_browser(self, script_path, temp_schema_file):
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
        output_path = '/tmp/test_browser.mmd'
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'erd',
                 '--schema-file', schema_file,
                 '--output', output_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'mermaid.live' in result.stdout
        finally:
            os.unlink(schema_file)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_lineage_opens_browser(self, script_path, temp_schema_file):
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
        output_path = '/tmp/test_lineage_browser.mmd'
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'lineage',
                 '--schema-file', schema_file,
                 '--output', output_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'mermaid.live' in result.stdout
        finally:
            os.unlink(schema_file)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestAllScriptsSmokeTests:
    """Smoke tests to ensure scripts are runnable."""

    def test_validate_query_runs(self):
        result = subprocess.run(
            [sys.executable, 'scripts/validate_query.py', '--query', 'SELECT 1'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        assert result.returncode in [0, 1]

    def test_generate_chart_runs(self):
        result = subprocess.run(
            [sys.executable, 'scripts/generate_chart.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        assert result.returncode == 0

    def test_generate_mermaid_runs(self):
        result = subprocess.run(
            [sys.executable, 'scripts/generate_mermaid.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        assert result.returncode == 0