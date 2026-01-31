---
name: vega-charts
description: Vega-Lite chart generation for data visualization and reporting
---

# Vega-Lite Charts

Generate static charts (PNG/SVG) from SQL queries using Vega-Lite specifications.

## Command: @deepdive chart

```
@deepdive chart "<natural language question>" [options]

Options:
  --type [bar|line|pie|scatter|area]  - Chart type (auto-detected by default)
  --output path                       - Custom output path
  --format [png|svg]                  - Output format (default: png)
  --width 800                         - Chart width
  --height 400                        - Chart height
```

## Examples

```bash
# Simple bar chart
@deepdive chart "sales by month"

# Line chart (time series)
@deepdive chart "daily revenue over last 30 days" --type line

# Pie chart
@deepdive chart "market share by region" --type pie

# Scatter plot
@deepdive chart "price vs quantity sold" --type scatter
```

## Generated Files

All charts saved to `.deepdive/charts/`:

```
.deepdive/charts/
├── sales-by-month-2025-01-31.png
├── daily-revenue-30d-2025-01-31.png
└── market-share-region-2025-01-31.svg
```

## Vega-Lite Specification Pattern

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "Chart Title",
  "width": 800,
  "height": 400,
  "data": {
    "values": [
      {"month": "Jan", "sales": 100},
      {"month": "Feb", "sales": 120}
    ]
  },
  "mark": "bar",
  "encoding": {
    "x": {"field": "month", "type": "ordinal"},
    "y": {"field": "sales", "type": "quantitative"}
  }
}
```

## Python Generation Script

```python
#!/usr/bin/env python3
# scripts/generate_chart.py

import json
import subprocess
import tempfile
import os
from datetime import datetime

def query_to_chart(conn, question, chart_type=None, output_path=None, 
                   width=800, height=400, format='png'):
    """
    Generate Vega-Lite chart from natural language question
    """
    
    # Step 1: Convert question to SQL
    sql = nl_to_sql(question)
    
    # Step 2: Execute query
    data = execute_query(conn, sql)
    
    # Step 3: Detect chart type if not specified
    if not chart_type:
        chart_type = detect_chart_type(data, question)
    
    # Step 4: Build Vega-Lite spec
    spec = build_vega_spec(data, chart_type, question, width, height)
    
    # Step 5: Render to image
    if not output_path:
        timestamp = datetime.now().strftime('%Y-%m-%d')
        safe_name = question.replace(' ', '-').replace('/', '-').lower()[:50]
        output_path = f".deepdive/charts/{safe_name}-{timestamp}.{format}"
    
    render_vega(spec, output_path, format)
    
    return output_path

def detect_chart_type(data, question):
    """Auto-detect best chart type based on data and question"""
    
    if len(data) == 0:
        return 'bar'
    
    columns = list(data[0].keys())
    
    # Time series detection
    time_keywords = ['date', 'time', 'day', 'month', 'year', 'over', 'trend']
    if any(kw in question.lower() for kw in time_keywords):
        return 'line'
    
    # Check for date columns
    date_cols = [c for c in columns if 'date' in c.lower() or 'time' in c.lower()]
    if date_cols:
        return 'line'
    
    # Parts of whole (percentages, shares)
    share_keywords = ['share', 'percent', 'distribution', 'breakdown', 'by']
    if any(kw in question.lower() for kw in share_keywords):
        if len(data) <= 6:
            return 'pie'
        return 'bar'
    
    # Correlation/scatter
    numeric_cols = len([c for c in columns if isinstance(data[0].get(c), (int, float))])
    if numeric_cols >= 2:
        return 'scatter'
    
    # Default
    return 'bar'

def build_vega_spec(data, chart_type, title, width, height):
    """Build Vega-Lite specification"""
    
    if not data:
        return None
    
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
            "mark": "bar",
            "encoding": {
                "x": {"field": columns[0], "type": "ordinal", "axis": {"labelAngle": -45}},
                "y": {"field": columns[1], "type": "quantitative"},
                "tooltip": [
                    {"field": columns[0], "type": "ordinal"},
                    {"field": columns[1], "type": "quantitative"}
                ]
            }
        }
    
    elif chart_type == 'line':
        spec = {
            **base_spec,
            "mark": {"type": "line", "point": True},
            "encoding": {
                "x": {"field": columns[0], "type": "temporal"},
                "y": {"field": columns[1], "type": "quantitative"},
                "tooltip": [
                    {"field": columns[0], "type": "temporal"},
                    {"field": columns[1], "type": "quantitative"}
                ]
            }
        }
    
    elif chart_type == 'pie':
        spec = {
            **base_spec,
            "mark": {"type": "arc", "innerRadius": 50},
            "encoding": {
                "theta": {"field": columns[1], "type": "quantitative"},
                "color": {"field": columns[0], "type": "nominal"},
                "tooltip": [
                    {"field": columns[0], "type": "nominal"},
                    {"field": columns[1], "type": "quantitative"}
                ]
            }
        }
    
    elif chart_type == 'scatter':
        spec = {
            **base_spec,
            "mark": "point",
            "encoding": {
                "x": {"field": columns[0], "type": "quantitative"},
                "y": {"field": columns[1], "type": "quantitative"},
                "tooltip": [
                    {"field": columns[0], "type": "quantitative"},
                    {"field": columns[1], "type": "quantitative"}
                ]
            }
        }
    
    elif chart_type == 'area':
        spec = {
            **base_spec,
            "mark": "area",
            "encoding": {
                "x": {"field": columns[0], "type": "temporal"},
                "y": {"field": columns[1], "type": "quantitative"}
            }
        }
    
    return spec

def render_vega(spec, output_path, format='png'):
    """Render Vega-Lite spec to image using vl2png/vl2svg"""
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write spec to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(spec, f)
        spec_file = f.name
    
    try:
        # Use vega-lite CLI tools
        if format == 'png':
            cmd = ['vl2png', spec_file, output_path]
        else:
            cmd = ['vl2svg', spec_file, output_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Fallback to alternative rendering (e.g., altair)
            render_with_altair(spec, output_path, format)
    
    finally:
        os.unlink(spec_file)

def render_with_altair(spec, output_path, format):
    """Fallback rendering using Altair"""
    import altair as alt
    import pandas as pd
    
    # Convert spec to Altair chart
    data = pd.DataFrame(spec['data']['values'])
    
    # Build chart based on mark type
    mark_type = spec['mark']
    if isinstance(mark_type, dict):
        mark_type = mark_type['type']
    
    encoding = spec['encoding']
    x_field = encoding['x']['field']
    y_field = encoding['y']['field']
    
    if mark_type == 'bar':
        chart = alt.Chart(data).mark_bar().encode(
            x=alt.X(x_field, type=encoding['x']['type']),
            y=alt.Y(y_field, type=encoding['y']['type'])
        )
    elif mark_type == 'line':
        chart = alt.Chart(data).mark_line(point=True).encode(
            x=alt.X(x_field, type=encoding['x']['type']),
            y=alt.Y(y_field, type=encoding['y']['type'])
        )
    else:
        chart = alt.Chart(data).mark_point().encode(
            x=alt.X(x_field, type=encoding['x']['type']),
            y=alt.Y(y_field, type=encoding['y']['type'])
        )
    
    # Save
    if format == 'png':
        chart.save(output_path)
    else:
        chart.save(output_path)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', required=True, help='SQL query')
    parser.add_argument('--type', choices=['bar', 'line', 'pie', 'scatter', 'area'])
    parser.add_argument('--output', required=True)
    parser.add_argument('--format', choices=['png', 'svg'], default='png')
    parser.add_argument('--width', type=int, default=800)
    parser.add_argument('--height', type=int, default=400)
    
    args = parser.parse_args()
    
    # This would need actual DB connection in real usage
    print(f"Generating {args.type or 'auto'} chart: {args.output}")
```

## Chart Templates

### Time Series Template

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "Monthly Revenue",
  "width": 800,
  "height": 300,
  "data": {"values": []},
  "mark": {"type": "line", "point": true, "interpolate": "monotone"},
  "encoding": {
    "x": {"field": "date", "type": "temporal", "title": "Date"},
    "y": {"field": "revenue", "type": "quantitative", "title": "Revenue ($)"},
    "tooltip": [
      {"field": "date", "type": "temporal"},
      {"field": "revenue", "type": "quantitative", "format": ",.0f"}
    ]
  }
}
```

### Comparison Bar Chart

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "Sales by Region",
  "width": 600,
  "height": 400,
  "data": {"values": []},
  "mark": {"type": "bar", "cornerRadiusEnd": 4},
  "encoding": {
    "x": {"field": "region", "type": "ordinal", "sort": "-y"},
    "y": {"field": "sales", "type": "quantitative"},
    "color": {"field": "region", "type": "nominal", "legend": null}
  }
}
```

### Multi-Series Line Chart

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "Revenue by Product Line",
  "width": 800,
  "height": 400,
  "data": {"values": []},
  "mark": "line",
  "encoding": {
    "x": {"field": "month", "type": "ordinal"},
    "y": {"field": "revenue", "type": "quantitative"},
    "color": {"field": "product_line", "type": "nominal"}
  }
}
```

## Styling Best Practices

1. **Use color purposefully**: Highlight important data points
2. **Add tooltips**: Always include hover information
3. **Sort bars**: By value (descending) for easier reading
4. **Label angles**: Rotate x-axis labels if needed
5. **Consistent colors**: Use same color scheme across related charts
6. **Title clarity**: Descriptive but concise titles

## Integration with @deepdive

```
User: "Chart monthly sales"
→ Parse intent (time series)
→ Generate SQL: SELECT month, SUM(sales) FROM ... GROUP BY month
→ Execute query → Get data
→ Detect chart type: line
→ Build Vega-Lite spec
→ Render to .deepdive/charts/monthly-sales-2025-01-31.png
→ Return file path
```

## Requirements

Install Vega-Lite CLI tools:

```bash
npm install -g vega-lite
# Or use Altair as Python fallback
pip install altair pandas
```
