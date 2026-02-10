#!/usr/bin/env python3
"""
Generate Vega-Lite charts from SQL query results.
Usage: python generate_chart.py --data-file <path> --type <type> --output <path> [--title <title>]
"""

import json
import argparse
import os
import sys
from datetime import datetime
from typing import List, Dict, Any


def detect_chart_type(data: List[Dict]) -> str:
    """Auto-detect best chart type based on data structure."""
    if not data:
        return 'bar'
    
    columns = list(data[0].keys())
    
    # Check for temporal columns
    temporal_keywords = ['date', 'time', 'day', 'month', 'year', 'timestamp']
    has_temporal = any(any(kw in col.lower() for kw in temporal_keywords) for col in columns)
    
    # Check for numeric columns
    numeric_cols = 0
    for col in columns:
        val = data[0].get(col)
        if isinstance(val, (int, float)):
            numeric_cols += 1
    
    if has_temporal and numeric_cols >= 1:
        return 'line'
    elif numeric_cols >= 2:
        return 'scatter'
    elif len(data) <= 6:
        return 'pie'
    else:
        return 'bar'


def build_vega_spec(data: List[Dict], chart_type: str, title: str, width: int, height: int) -> Dict:
    """Build Vega-Lite specification."""
    
    if not data:
        return {}
    
    columns = list(data[0].keys())
    
    base_spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "title": title,
        "width": width,
        "height": height,
        "data": {"values": data}
    }
    
    if chart_type == 'bar':
        spec = {
            **base_spec,
            "mark": {"type": "bar", "cornerRadiusEnd": 4},
            "encoding": {
                "x": {
                    "field": columns[0],
                    "type": "ordinal",
                    "sort": "-y",
                    "axis": {"labelAngle": -45}
                },
                "y": {
                    "field": columns[1],
                    "type": "quantitative"
                },
                "tooltip": [
                    {"field": columns[0], "type": "ordinal"},
                    {"field": columns[1], "type": "quantitative"}
                ]
            }
        }
    
    elif chart_type == 'line':
        # Detect if x-axis should be temporal
        x_type = "temporal" if any(kw in columns[0].lower() for kw in ['date', 'time', 'day', 'month']) else "ordinal"
        
        spec = {
            **base_spec,
            "mark": {"type": "line", "point": True, "interpolate": "monotone"},
            "encoding": {
                "x": {
                    "field": columns[0],
                    "type": x_type
                },
                "y": {
                    "field": columns[1],
                    "type": "quantitative"
                },
                "tooltip": [
                    {"field": columns[0], "type": x_type},
                    {"field": columns[1], "type": "quantitative"}
                ]
            }
        }
    
    elif chart_type == 'pie':
        spec = {
            **base_spec,
            "mark": {"type": "arc", "innerRadius": 50},
            "encoding": {
                "theta": {
                    "field": columns[1],
                    "type": "quantitative"
                },
                "color": {
                    "field": columns[0],
                    "type": "nominal"
                },
                "tooltip": [
                    {"field": columns[0], "type": "nominal"},
                    {"field": columns[1], "type": "quantitative"}
                ]
            }
        }
    
    elif chart_type == 'scatter':
        # Use first numeric column for x, second for y
        numeric_cols = [col for col in columns if isinstance(data[0].get(col), (int, float))]
        
        if len(numeric_cols) >= 2:
            x_field, y_field = numeric_cols[0], numeric_cols[1]
        else:
            x_field, y_field = columns[0], columns[1]
        
        spec = {
            **base_spec,
            "mark": "point",
            "encoding": {
                "x": {
                    "field": x_field,
                    "type": "quantitative"
                },
                "y": {
                    "field": y_field,
                    "type": "quantitative"
                },
                "tooltip": [
                    {"field": x_field, "type": "quantitative"},
                    {"field": y_field, "type": "quantitative"}
                ]
            }
        }
    
    elif chart_type == 'area':
        x_type = "temporal" if any(kw in columns[0].lower() for kw in ['date', 'time']) else "ordinal"
        
        spec = {
            **base_spec,
            "mark": "area",
            "encoding": {
                "x": {
                    "field": columns[0],
                    "type": x_type
                },
                "y": {
                    "field": columns[1],
                    "type": "quantitative"
                }
            }
        }
    else:
        return {}
    
    return spec


def render_with_altair(spec: Dict, output_path: str, format: str = 'png'):
    """Render Vega-Lite spec using Altair."""
    try:
        import altair as alt
        import pandas as pd
        
        # Convert data to DataFrame
        df = pd.DataFrame(spec['data']['values'])
        
        # Build chart based on spec
        mark = spec['mark']
        encoding = spec['encoding']
        
        if isinstance(mark, dict):
            mark_type = mark['type']
        else:
            mark_type = mark
        
        # Create base chart
        chart = alt.Chart(df)
        
        # Apply mark
        if mark_type == 'bar':
            chart = chart.mark_bar(cornerRadiusEnd=4)
        elif mark_type == 'line':
            chart = chart.mark_line(point=True)
        elif mark_type == 'arc':
            chart = chart.mark_arc(innerRadius=50)
        elif mark_type == 'point':
            chart = chart.mark_point()
        elif mark_type == 'area':
            chart = chart.mark_area()
        
        # Apply encoding
        encodings = {}
        for key, val in encoding.items():
            if key == 'tooltip':
                encodings[key] = val
            else:
                encodings[key] = alt.X(val['field'], type=val['type']) if key == 'x' else \
                                 alt.Y(val['field'], type=val['type']) if key == 'y' else \
                                 alt.Theta(val['field'], type=val['type']) if key == 'theta' else \
                                 alt.Color(val['field'], type=val['type'])
        
        chart = chart.encode(**encodings)
        
        # Set title
        if 'title' in spec:
            chart = chart.properties(title=spec['title'])
        
        # Save
        if format == 'png':
            chart.save(output_path)
        else:
            chart.save(output_path)
        
        return True
    
    except ImportError:
        print("⚠ Altair not installed. Install with: pip install altair pandas")
        return False
    except Exception as e:
        print(f"✗ Error rendering with Altair: {e}")
        return False


def save_vega_spec(spec: Dict, output_path: str):
    """Save Vega-Lite spec as JSON for manual rendering."""
    with open(output_path, 'w') as f:
        json.dump(spec, f, indent=2)
    print(f"✓ Vega spec saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate charts from data')
    parser.add_argument('--data-file', required=True,
                       help='Path to JSON file with query results')
    parser.add_argument('--type', choices=['bar', 'line', 'pie', 'scatter', 'area', 'auto'],
                       default='auto',
                       help='Chart type (auto-detect if not specified)')
    parser.add_argument('--output', required=True,
                       help='Output file path')
    parser.add_argument('--format', choices=['png', 'svg', 'json'],
                       default='png',
                       help='Output format')
    parser.add_argument('--title',
                       help='Chart title')
    parser.add_argument('--width', type=int, default=800,
                       help='Chart width')
    parser.add_argument('--height', type=int, default=400,
                       help='Chart height')
    
    args = parser.parse_args()
    
    # Load data
    try:
        with open(args.data_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"✗ Data file not found: {args.data_file}")
        return 1
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in data file: {args.data_file}")
        return 1
    
    if not data:
        print("⚠ No data to chart")
        return 0
    
    # Detect or use specified chart type
    chart_type = detect_chart_type(data) if args.type == 'auto' else args.type
    print(f"Chart type: {chart_type}")
    
    # Determine title
    title = args.title
    if not title:
        # Generate from output filename
        basename = os.path.basename(args.output)
        title = basename.replace('-', ' ').replace('_', ' ').title()
        # Remove extension
        title = os.path.splitext(title)[0]
    
    # Build spec
    spec = build_vega_spec(data, chart_type, title, args.width, args.height)
    
    if not spec:
        print("✗ Could not build chart specification")
        return 1
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
    
    # Render or save
    if args.format == 'json':
        # Just save the spec
        save_vega_spec(spec, args.output)
    else:
        # Try to render
        if render_with_altair(spec, args.output, args.format):
            print(f"✓ Chart generated: {args.output}")
        else:
            # Fallback to saving spec
            spec_path = args.output.replace(f'.{args.format}', '.json')
            save_vega_spec(spec, spec_path)
            print(f"⚠ Could not render image. Vega spec saved for manual rendering.")
            print(f"  View online: https://vega.github.io/editor/#/url={spec_path}")
    
    return 0


if __name__ == '__main__':
    exit(main())
