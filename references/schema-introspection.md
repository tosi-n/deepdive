---
name: schema-introspection
description: Database schema discovery, table relationships, and metadata extraction
---

# Schema Introspection

Discover and document database structure for better query generation and visualization.

## List All Tables

### PostgreSQL

```sql
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

### MySQL

```sql
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = DATABASE()
ORDER BY table_name;
```

### SQLite

```sql
SELECT name, type
FROM sqlite_master
WHERE type = 'table'
ORDER BY name;
```

### BigQuery

```sql
SELECT table_name, table_type
FROM `project.dataset.INFORMATION_SCHEMA.TABLES`
ORDER BY table_name;
```

## Get Table Schema

### PostgreSQL

```sql
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'customers'
  AND table_schema = 'public'
ORDER BY ordinal_position;
```

### MySQL

```sql
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'customers'
  AND table_schema = DATABASE()
ORDER BY ordinal_position;
```

### SQLite

```sql
PRAGMA table_info(customers);
```

## Get Primary Keys

### PostgreSQL

```sql
SELECT 
    kcu.column_name,
    tc.table_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'PRIMARY KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.ordinal_position;
```

### MySQL

```sql
SELECT 
    column_name,
    table_name
FROM information_schema.key_column_usage
WHERE constraint_name = 'PRIMARY'
  AND table_schema = DATABASE();
```

## Get Foreign Keys

### PostgreSQL

```sql
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public';
```

### MySQL

```sql
SELECT
    table_name,
    column_name,
    referenced_table_name,
    referenced_column_name
FROM information_schema.key_column_usage
WHERE referenced_table_name IS NOT NULL
  AND table_schema = DATABASE();
```

### SQLite

```sql
PRAGMA foreign_key_list(orders);
```

## Get Indexes

### PostgreSQL

```sql
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

### MySQL

```sql
SELECT 
    table_name,
    index_name,
    column_name
FROM information_schema.statistics
WHERE table_schema = DATABASE()
ORDER BY table_name, index_name, seq_in_index;
```

## Sample Data Preview

Get representative sample for understanding:

```sql
-- PostgreSQL/MySQL/SQLite
SELECT *
FROM customers
ORDER BY RANDOM()  -- PostgreSQL/SQLite
-- ORDER BY RAND()  -- MySQL
LIMIT 5;
```

## Table Statistics

### Row Counts

```sql
-- PostgreSQL (fast estimate)
SELECT relname, reltuples::BIGINT as row_count
FROM pg_class
WHERE relkind = 'r'
AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');

-- MySQL
SELECT table_name, table_rows
FROM information_schema.tables
WHERE table_schema = DATABASE();

-- SQLite
SELECT count(*) FROM customers;
```

### Column Statistics

```sql
-- Get min/max/null counts for each column
SELECT 
    MIN(created_at) as earliest,
    MAX(created_at) as latest,
    COUNT(*) as total_rows,
    COUNT(created_at) as non_null_created
FROM customers;
```

## Schema JSON Export

Export full schema for analysis:

```python
def export_schema(conn, db_type):
    schema = {
        'database_type': db_type,
        'tables': {}
    }
    
    # Get tables
    tables = get_tables(conn)
    
    for table in tables:
        schema['tables'][table] = {
            'columns': get_columns(conn, table),
            'primary_key': get_primary_key(conn, table),
            'foreign_keys': get_foreign_keys(conn, table),
            'indexes': get_indexes(conn, table),
            'row_count': get_row_count(conn, table)
        }
    
    return schema
```

## Relationship Detection

Detect implied relationships (naming conventions):

```python
def detect_relationships(schema):
    relationships = []
    
    for table, info in schema['tables'].items():
        for column in info['columns']:
            # Pattern: *_id suggests foreign key
            if column.endswith('_id'):
                referenced_table = column.replace('_id', '')
                if referenced_table in schema['tables']:
                    relationships.append({
                        'from_table': table,
                        'from_column': column,
                        'to_table': referenced_table,
                        'to_column': 'id',
                        'type': 'implied'
                    })
    
    return relationships
```

## Schema Caching

Cache schema for performance:

```python
import json
import os
from datetime import datetime

def cache_schema(schema, project_path):
    cache_file = os.path.join(project_path, '.deepdive', 'schema_cache.json')
    
    cache_data = {
        'cached_at': datetime.now().isoformat(),
        'schema': schema
    }
    
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)

def load_cached_schema(project_path, max_age_hours=24):
    cache_file = os.path.join(project_path, '.deepdive', 'schema_cache.json')
    
    if not os.path.exists(cache_file):
        return None
    
    with open(cache_file, 'r') as f:
        cache_data = json.load(f)
    
    cached_at = datetime.fromisoformat(cache_data['cached_at'])
    age = datetime.now() - cached_at
    
    if age.total_seconds() > max_age_hours * 3600:
        return None
    
    return cache_data['schema']
```

## Schema Comparison

Compare schemas between environments:

```python
def compare_schemas(schema1, schema2):
    differences = {
        'tables_only_in_1': [],
        'tables_only_in_2': [],
        'columns_different': [],
        'relationships_different': []
    }
    
    tables1 = set(schema1['tables'].keys())
    tables2 = set(schema2['tables'].keys())
    
    differences['tables_only_in_1'] = list(tables1 - tables2)
    differences['tables_only_in_2'] = list(tables2 - tables1)
    
    # Compare common tables
    for table in tables1 & tables2:
        cols1 = {c['name'] for c in schema1['tables'][table]['columns']}
        cols2 = {c['name'] for c in schema2['tables'][table]['columns']}
        
        if cols1 != cols2:
            differences['columns_different'].append({
                'table': table,
                'only_in_1': list(cols1 - cols2),
                'only_in_2': list(cols2 - cols1)
            })
    
    return differences
```

## Best Practices

1. **Cache aggressively**: Schema rarely changes, cache for 24h
2. **Sample data**: Always show samples when describing tables
3. **Show relationships**: Foreign keys help understand data model
4. **Document enums**: Show distinct values for enum-like columns
5. **Respect permissions**: Only introspect tables user has access to
