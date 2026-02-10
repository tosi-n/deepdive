"""
Unit tests for generate_chart.py - Chart generation and Vega-Lite spec building.
"""

import pytest
import json
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from generate_chart import (
    detect_chart_type,
    build_vega_spec,
    save_vega_spec,
    render_with_altair,
)


class TestDetectChartType:
    """Test detect_chart_type function."""

    def test_empty_data_returns_bar(self):
        result = detect_chart_type([])
        assert result == "bar"

    def test_none_data_returns_bar(self):
        result = detect_chart_type(None)
        assert result == "bar"

    def test_temporal_with_numeric_returns_line(self):
        data = [
            {"date": "2024-01-01", "value": 100},
            {"date": "2024-02-01", "value": 150},
        ]
        result = detect_chart_type(data)
        assert result == "line"

    def test_time_column_returns_line(self):
        data = [
            {"time": "08:00", "count": 50},
            {"time": "09:00", "count": 75},
        ]
        result = detect_chart_type(data)
        assert result == "line"

    def test_day_column_returns_line(self):
        data = [
            {"day": "Monday", "sales": 100},
            {"day": "Tuesday", "sales": 150},
        ]
        result = detect_chart_type(data)
        assert result == "line"

    def test_year_column_returns_line(self):
        data = [
            {"year": 2023, "value": 1000},
            {"year": 2024, "value": 1500},
        ]
        result = detect_chart_type(data)
        assert result == "line"

    def test_two_numeric_columns_returns_scatter(self):
        data = [
            {"x": 10, "y": 100},
            {"x": 20, "y": 200},
            {"x": 30, "y": 300},
        ]
        result = detect_chart_type(data)
        assert result == "scatter"

    def test_single_numeric_column_returns_pie(self):
        data = [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
        ]
        result = detect_chart_type(data)
        assert result == "pie"

    def test_small_dataset_returns_pie(self):
        data = [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
            {"category": "C", "value": 15},
            {"category": "D", "value": 25},
            {"category": "E", "value": 30},
        ]
        result = detect_chart_type(data)
        assert result == "pie"

    def test_six_items_returns_pie(self):
        data = [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
            {"category": "C", "value": 15},
            {"category": "D", "value": 25},
            {"category": "E", "value": 30},
            {"category": "F", "value": 35},
        ]
        result = detect_chart_type(data)
        assert result == "pie"

    def test_temporal_and_numeric_two_returns_line(self):
        data = [
            {"date": "2024-01-01", "x": 10, "y": 100},
            {"date": "2024-02-01", "x": 20, "y": 200},
        ]
        result = detect_chart_type(data)
        assert result == "line"

    def test_no_temporal_two_numeric_returns_scatter(self):
        data = [
            {"label": "A", "num1": 10, "num2": 100},
            {"label": "B", "num1": 20, "num2": 200},
        ]
        result = detect_chart_type(data)
        assert result == "scatter"

    def test_string_values_not_numeric(self):
        data = [
            {"category": "A", "value": "10"},
            {"category": "B", "value": "20"},
        ]
        result = detect_chart_type(data)
        assert result == "pie"

    def test_mixed_types_first_not_numeric(self):
        data = [
            {"label": "A", "value": 10},
            {"label": "B", "value": 20},
        ]
        result = detect_chart_type(data)
        assert result == "pie"

    def test_date_datetime_detection(self):
        data = [
            {"timestamp": "2024-01-01T10:00:00", "count": 100},
            {"timestamp": "2024-01-02T10:00:00", "count": 150},
        ]
        result = detect_chart_type(data)
        assert result == "line"


class TestBuildVegaSpec:
    """Test build_vega_spec function."""

    def test_empty_data_returns_empty_dict(self):
        result = build_vega_spec([], "bar", "Test", 800, 400)
        assert result == {}

    def test_none_data_returns_empty_dict(self):
        result = build_vega_spec(None, "bar", "Test", 800, 400)
        assert result == {}

    def test_bar_chart_has_correct_schema(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "bar", "Test Chart", 800, 400)
        assert result["$schema"] == "https://vega.github.io/schema/vega-lite/v5.json"

    def test_bar_chart_has_correct_title(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "bar", "My Chart", 800, 400)
        assert result["title"] == "My Chart"

    def test_bar_chart_has_correct_dimensions(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "bar", "Test", 600, 300)
        assert result["width"] == 600
        assert result["height"] == 300

    def test_bar_chart_has_bar_mark(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "bar", "Test", 800, 400)
        assert result["mark"]["type"] == "bar"

    def test_bar_chart_has_encoding(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "bar", "Test", 800, 400)
        assert "encoding" in result
        assert "x" in result["encoding"]
        assert "y" in result["encoding"]

    def test_line_chart_has_line_mark(self):
        data = [{"date": "2024-01-01", "value": 100}]
        result = build_vega_spec(data, "line", "Test", 800, 400)
        assert result["mark"]["type"] == "line"

    def test_line_chart_has_temporal_x_for_date(self):
        data = [{"date": "2024-01-01", "value": 100}]
        result = build_vega_spec(data, "line", "Test", 800, 400)
        assert result["encoding"]["x"]["type"] == "temporal"

    def test_line_chart_has_ordinal_x_for_non_date(self):
        data = [{"category": "A", "value": 100}]
        result = build_vega_spec(data, "line", "Test", 800, 400)
        assert result["encoding"]["x"]["type"] == "ordinal"

    def test_line_chart_has_point(self):
        data = [{"date": "2024-01-01", "value": 100}]
        result = build_vega_spec(data, "line", "Test", 800, 400)
        assert result["mark"]["point"] is True

    def test_line_chart_has_interpolate(self):
        data = [{"date": "2024-01-01", "value": 100}]
        result = build_vega_spec(data, "line", "Test", 800, 400)
        assert result["mark"]["interpolate"] == "monotone"

    def test_pie_chart_has_arc_mark(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "pie", "Test", 800, 400)
        assert result["mark"]["type"] == "arc"

    def test_pie_chart_has_inner_radius(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "pie", "Test", 800, 400)
        assert result["mark"]["innerRadius"] == 50

    def test_pie_chart_has_theta_encoding(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "pie", "Test", 800, 400)
        assert "theta" in result["encoding"]
        assert result["encoding"]["theta"]["type"] == "quantitative"

    def test_pie_chart_has_color_encoding(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "pie", "Test", 800, 400)
        assert "color" in result["encoding"]
        assert result["encoding"]["color"]["type"] == "nominal"

    def test_scatter_chart_has_point_mark(self):
        data = [{"x": 10, "y": 100}]
        result = build_vega_spec(data, "scatter", "Test", 800, 400)
        assert result["mark"] == "point"

    def test_scatter_uses_numeric_columns(self):
        data = [{"x": 10, "y": 100, "label": "A"}]
        result = build_vega_spec(data, "scatter", "Test", 800, 400)
        assert result["encoding"]["x"]["field"] == "x"
        assert result["encoding"]["y"]["field"] == "y"

    def test_scatter_fallback_to_first_two_columns(self):
        data = [{"label": "A", "category": "B"}]
        result = build_vega_spec(data, "scatter", "Test", 800, 400)
        assert result["encoding"]["x"]["field"] == "label"
        assert result["encoding"]["y"]["field"] == "category"

    def test_area_chart_has_area_mark(self):
        data = [{"date": "2024-01-01", "value": 100}]
        result = build_vega_spec(data, "area", "Test", 800, 400)
        assert result["mark"] == "area"

    def test_area_chart_temporal_x(self):
        data = [{"timestamp": "2024-01-01T10:00:00", "value": 100}]
        result = build_vega_spec(data, "area", "Test", 800, 400)
        assert result["encoding"]["x"]["type"] == "temporal"

    def test_all_chart_types_have_tooltip(self):
        chart_types = ["bar", "line", "pie", "scatter", "area"]
        data = [{"x": 10, "y": 100}]

        for chart_type in chart_types:
            result = build_vega_spec(data, chart_type, "Test", 800, 400)
            if chart_type != "area":
                assert "tooltip" in result["encoding"], f"Missing tooltip for {chart_type}"

    def test_data_values_are_in_spec(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "bar", "Test", 800, 400)
        assert result["data"]["values"] == data


class TestRenderWithAltair:
    """Test render_with_altair function."""

    def test_import_error_returns_false(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": [{"x": 10, "y": 100}]},
            "mark": "point",
            "encoding": {
                "x": {"field": "x", "type": "quantitative"},
                "y": {"field": "y", "type": "quantitative"},
            },
        }

        with patch.dict('sys.modules', {'altair': None, 'pandas': None}):
            result = render_with_altair(spec, "/tmp/test.png")
            assert result is False

    def test_valid_spec_returns_true(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": [{"x": 10, "y": 100}]},
            "mark": "point",
            "encoding": {
                "x": {"field": "x", "type": "quantitative"},
                "y": {"field": "y", "type": "quantitative"},
            },
        }

        mock_altair = MagicMock()
        mock_pd = MagicMock()

        with patch.dict('sys.modules', {'altair': mock_altair, 'pandas': mock_pd}):
            mock_chart = MagicMock()
            mock_altair.Chart.return_value.encode.return_value = mock_chart
            result = render_with_altair(spec, "/tmp/test.png")
            assert result is True

    def test_svg_format(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": [{"x": 10, "y": 100}]},
            "mark": "point",
            "encoding": {
                "x": {"field": "x", "type": "quantitative"},
                "y": {"field": "y", "type": "quantitative"},
            },
        }

        mock_altair = MagicMock()
        mock_pd = MagicMock()

        with patch.dict('sys.modules', {'altair': mock_altair, 'pandas': mock_pd}):
            result = render_with_altair(spec, "/tmp/test.svg", format='svg')
            assert result is True

    def test_render_with_color_encoding(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": [{"x": 10, "y": 100, "category": "A"}]},
            "mark": "point",
            "encoding": {
                "x": {"field": "x", "type": "quantitative"},
                "y": {"field": "y", "type": "quantitative"},
                "color": {"field": "category", "type": "nominal"},
                "tooltip": [
                    {"field": "x", "type": "quantitative"},
                    {"field": "y", "type": "quantitative"},
                ],
            },
        }

        mock_altair = MagicMock()
        mock_pd = MagicMock()

        with patch.dict('sys.modules', {'altair': mock_altair, 'pandas': mock_pd}):
            result = render_with_altair(spec, "/tmp/test.png")
            assert result is True

    def test_render_with_title_property(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": "Test Chart",
            "data": {"values": [{"x": 10, "y": 100}]},
            "mark": "point",
            "encoding": {
                "x": {"field": "x", "type": "quantitative"},
                "y": {"field": "y", "type": "quantitative"},
            },
        }

        mock_altair = MagicMock()
        mock_pd = MagicMock()

        with patch.dict('sys.modules', {'altair': mock_altair, 'pandas': mock_pd}):
            result = render_with_altair(spec, "/tmp/test.png")
            assert result is True

    def test_render_exception_handling(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": [{"x": 10, "y": 100}]},
            "mark": "point",
            "encoding": {
                "x": {"field": "x", "type": "quantitative"},
                "y": {"field": "y", "type": "quantitative"},
            },
        }

        mock_altair = MagicMock()
        mock_pd = MagicMock()
        mock_altair.Chart.side_effect = Exception("Test error")

        with patch.dict('sys.modules', {'altair': mock_altair, 'pandas': mock_pd}):
            result = render_with_altair(spec, "/tmp/test.png")
            assert result is False

    def test_mark_as_dict(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": [{"x": 10, "y": 100}]},
            "mark": {"type": "bar", "cornerRadiusEnd": 4},
            "encoding": {
                "x": {"field": "x", "type": "ordinal"},
                "y": {"field": "y", "type": "quantitative"},
            },
        }

        mock_altair = MagicMock()
        mock_pd = MagicMock()

        with patch.dict('sys.modules', {'altair': mock_altair, 'pandas': mock_pd}):
            result = render_with_altair(spec, "/tmp/test.png")
            assert result is True

    def test_arc_mark_for_pie(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": [{"category": "A", "value": 10}]},
            "mark": {"type": "arc", "innerRadius": 50},
            "encoding": {
                "theta": {"field": "value", "type": "quantitative"},
                "color": {"field": "category", "type": "nominal"},
            },
        }

        mock_altair = MagicMock()
        mock_pd = MagicMock()

        with patch.dict('sys.modules', {'altair': mock_altair, 'pandas': mock_pd}):
            result = render_with_altair(spec, "/tmp/test.png")
            assert result is True

    def test_area_mark(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": [{"date": "2024-01-01", "value": 100}]},
            "mark": "area",
            "encoding": {
                "x": {"field": "date", "type": "temporal"},
                "y": {"field": "value", "type": "quantitative"},
            },
        }

        mock_altair = MagicMock()
        mock_pd = MagicMock()

        with patch.dict('sys.modules', {'altair': mock_altair, 'pandas': mock_pd}):
            result = render_with_altair(spec, "/tmp/test.png")
            assert result is True


class TestGenerateChartMain:
    """Tests for the main() function in generate_chart.py"""

    @pytest.fixture
    def temp_data_file(self):
        def _create(data):
            import tempfile
            import json
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(data, f)
                return f.name
        return _create

    def test_main_with_json_format(self, temp_data_file, capsys):
        import sys
        import os
        from generate_chart import main as chart_main
        original_argv = sys.argv
        data_file = temp_data_file([{"category": "A", "value": 10}])
        try:
            sys.argv = ['generate_chart.py', '--data-file', data_file, '--output', '/tmp/test_output.json', '--format', 'json']
            result = chart_main()
            assert result == 0
            assert os.path.exists('/tmp/test_output.json')
        finally:
            sys.argv = original_argv
            if os.path.exists('/tmp/test_output.json'):
                os.unlink('/tmp/test_output.json')

    def test_main_with_custom_title(self, temp_data_file, capsys):
        import sys
        import os
        from generate_chart import main as chart_main
        original_argv = sys.argv
        data_file = temp_data_file([{"category": "A", "value": 10}])
        try:
            sys.argv = ['generate_chart.py', '--data-file', data_file, '--output', '/tmp/test_title.json', '--title', 'Custom Title', '--format', 'json']
            result = chart_main()
            assert result == 0
        finally:
            sys.argv = original_argv
            if os.path.exists('/tmp/test_title.json'):
                os.unlink('/tmp/test_title.json')

    def test_main_with_empty_data(self, temp_data_file, capsys):
        import sys
        from generate_chart import main as chart_main
        original_argv = sys.argv
        data_file = temp_data_file([])
        try:
            sys.argv = ['generate_chart.py', '--data-file', data_file, '--output', '/tmp/test_empty.json', '--format', 'json']
            result = chart_main()
            assert result == 0
        finally:
            sys.argv = original_argv


class TestSaveVegaSpec:
    """Test save_vega_spec function."""

    def test_saves_json_file(self):
        spec = {"test": "data"}
        path = os.path.join(tempfile.gettempdir(), "test_spec.json")
        save_vega_spec(spec, path)
        assert os.path.exists(path)

        with open(path, 'r') as f:
            loaded = json.load(f)
        assert loaded == spec

        os.unlink(path)


class TestDetectChartTypeEdgeCases:
    """Test edge cases for chart type detection."""

    def test_single_item_returns_pie(self):
        data = [{"category": "A", "value": 10}]
        result = detect_chart_type(data)
        assert result == "pie"

    def test_all_string_columns_returns_pie(self):
        data = [
            {"name": "A", "label": "X"},
            {"name": "B", "label": "Y"},
        ]
        result = detect_chart_type(data)
        assert result == "pie"

    def test_column_name_case_insensitive(self):
        data = [
            {"DATE": "2024-01-01", "value": 100},
            {"DATE": "2024-02-01", "value": 150},
        ]
        result = detect_chart_type(data)
        assert result == "line"

    def test_timestamp_column(self):
        data = [
            {"timestamp": "2024-01-01T10:00:00Z", "count": 100},
            {"timestamp": "2024-01-02T10:00:00Z", "count": 150},
        ]
        result = detect_chart_type(data)
        assert result == "line"


class TestBuildVegaSpecEdgeCases:
    """Test edge cases for Vega spec building."""

    def test_unknown_chart_type_returns_empty(self):
        data = [{"x": 10, "y": 100}]
        result = build_vega_spec(data, "unknown_type", "Test", 800, 400)
        assert result == {}

    def test_bar_chart_uses_first_two_columns(self):
        data = [{"first": "A", "second": 10, "third": 20}]
        result = build_vega_spec(data, "bar", "Test", 800, 400)
        assert result["encoding"]["x"]["field"] == "first"
        assert result["encoding"]["y"]["field"] == "second"

    def test_data_values_is_list(self):
        data = [{"category": "A", "value": 10}]
        result = build_vega_spec(data, "bar", "Test", 800, 400)
        assert isinstance(result["data"]["values"], list)
        assert len(result["data"]["values"]) == 1