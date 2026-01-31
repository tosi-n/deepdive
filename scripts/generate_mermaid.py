#!/usr/bin/env python3
"""
Generate Mermaid diagrams from database schemas.
Usage: python generate_mermaid.py <type> --schema-file <path> --output <path> [--tables t1,t2]
"""

import json
import argparse
import webbrowser
import urllib.parse
import os
from datetime import datetime


def generate_erd(schema, tables=None):
    """Generate Entity Relationship Diagram from schema."""
    
    if tables:
        # Include specified tables and their related tables
        relevant = set(tables)
        for table in tables:
            if table in schema.get('tables', {}):
                for fk in schema['tables'][table].get('foreign_keys', []):
                    relevant.add(fk.get('references_table'))
        tables_to_render = relevant
    else:
        tables_to_render = set(schema.get('tables', {}).keys())
    
    lines = ["erDiagram"]
    
    # Add relationships
    for table in tables_to_render:
        if table not in schema.get('tables', {}):
            continue
            
        table_info = schema['tables'][table]
        fks = table_info.get('foreign_keys', [])
        
        for fk in fks:
            ref_table = fk.get('references_table')
            if ref_table and ref_table in tables_to_render:
                # Standard one-to-many relationship notation
                lines.append(f"    {table.upper()} ||--o{{ {ref_table.upper()} : references")
    
    # Add entities with columns
    for table in sorted(tables_to_render):
        if table not in schema.get('tables', {}):
            continue
            
        table_info = schema['tables'][table]
        lines.append(f"\n    {table.upper()} {{")
        
        # Track primary keys
        pk_columns = set()
        for pk in table_info.get('primary_key', []):
            pk_columns.add(pk.get('column'))
        
        # Add columns
        for col in table_info.get('columns', []):
            col_name = col.get('name', 'unknown')
            col_type = col.get('type', 'unknown')
            
            if col_name in pk_columns:
                lines.append(f"        {col_type} {col_name} PK")
            else:
                lines.append(f"        {col_type} {col_name}")
        
        lines.append("    }")
    
    return "\n".join(lines)


def generate_lineage(schema, table_name=None):
    """Generate data lineage diagram."""
    
    lines = ["graph LR"]
    
    if table_name and table_name in schema.get('tables', {}):
        # Focus on specific table lineage
        table_info = schema['tables'][table_name]
        
        # Show upstream (tables this table references)
        for fk in table_info.get('foreign_keys', []):
            ref_table = fk.get('references_table')
            lines.append(f"    {ref_table.upper()} -->|FK| {table_name.upper()}")
        
        # Show downstream (tables that reference this table)
        for other_table, other_info in schema.get('tables', {}).items():
            if other_table != table_name:
                for fk in other_info.get('foreign_keys', []):
                    if fk.get('references_table') == table_name:
                        lines.append(f"    {table_name.upper()} -->|FK| {other_table.upper()}")
    else:
        # Show all lineage
        for table, table_info in schema.get('tables', {}).items():
            for fk in table_info.get('foreign_keys', []):
                ref_table = fk.get('references_table')
                if ref_table in schema.get('tables', {}):
                    lines.append(f"    {ref_table.upper()} -->|FK| {table.upper()}")
    
    return "\n".join(lines)


def generate_query_plan(plan_data):
    """Generate query execution plan diagram."""
    
    lines = ["graph TD"]
    
    def add_node(node, parent=None):
        node_id = f"node_{id(node)}"
        node_type = node.get('type', 'Unknown')
        details = node.get('details', '')
        
        lines.append(f"    {node_id}[{node_type}<br/>{details}]")
        
        if parent:
            lines.append(f"    {parent} --> {node_id}")
        
        for child in node.get('children', []):
            add_node(child, node_id)
    
    if plan_data:
        add_node(plan_data)
    
    return "\n".join(lines)


def save_and_open(mermaid_content, output_path, open_browser=True):
    """Save .mmd file and optionally open in browser."""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save file
    with open(output_path, 'w') as f:
        f.write(mermaid_content)
    
    print(f"✓ Generated: {output_path}")
    
    if open_browser:
        # Open with mermaid.live
        try:
            encoded = urllib.parse.quote(mermaid_content, safe='')
            url = f"https://mermaid.live/edit#pako:{encoded}"
            webbrowser.open(url)
            print(f"✓ Opened in browser: mermaid.live")
        except Exception as e:
            print(f"⚠ Could not open browser: {e}")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Generate Mermaid diagrams from database schemas')
    parser.add_argument('type', choices=['schema', 'erd', 'lineage', 'query-plan'],
                       help='Type of diagram to generate')
    parser.add_argument('--schema-file', required=True,
                       help='Path to schema JSON file')
    parser.add_argument('--output', required=True,
                       help='Output path for .mmd file')
    parser.add_argument('--tables', 
                       help='Comma-separated list of table names for ERD')
    parser.add_argument('--table',
                       help='Specific table for lineage diagram')
    parser.add_argument('--no-open', action='store_true',
                       help='Do not open browser after generation')
    parser.add_argument('--query-plan-file',
                       help='Path to query plan JSON for query-plan type')
    
    args = parser.parse_args()
    
    # Load schema
    try:
        with open(args.schema_file, 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"✗ Schema file not found: {args.schema_file}")
        return 1
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in schema file: {args.schema_file}")
        return 1
    
    # Generate diagram
    if args.type == 'schema' or args.type == 'erd':
        tables = args.tables.split(',') if args.tables else None
        mermaid = generate_erd(schema, tables)
    elif args.type == 'lineage':
        mermaid = generate_lineage(schema, args.table)
    elif args.type == 'query-plan':
        if not args.query_plan_file:
            print("✗ --query-plan-file required for query-plan type")
            return 1
        try:
            with open(args.query_plan_file, 'r') as f:
                plan_data = json.load(f)
            mermaid = generate_query_plan(plan_data)
        except FileNotFoundError:
            print(f"✗ Query plan file not found: {args.query_plan_file}")
            return 1
    else:
        print(f"✗ Unknown type: {args.type}")
        return 1
    
    # Save and open
    save_and_open(mermaid, args.output, not args.no_open)
    
    return 0


if __name__ == '__main__':
    exit(main())
