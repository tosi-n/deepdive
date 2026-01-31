---
name: connectors
description: Database connection patterns for PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, and Redshift
---

# Database Connectors

DeepDive supports multiple database types through standardized connection patterns.

## Environment Variables

All database credentials must be stored in `.deepdive/.env`:

```bash
# PostgreSQL
DATABASE_URL=postgresql://username:password@host:port/database

# MySQL  
DATABASE_URL=mysql://username:password@host:port/database

# SQLite
DATABASE_URL=sqlite:///path/to/database.db

# BigQuery
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
BIGQUERY_PROJECT_ID=your-project
BIGQUERY_DATASET=your-dataset

# Snowflake
SNOWFLAKE_ACCOUNT=account.region
SNOWFLAKE_USER=username
SNOWFLAKE_PASSWORD=password
SNOWFLAKE_DATABASE=database
SNOWFLAKE_SCHEMA=schema
SNOWFLAKE_WAREHOUSE=warehouse

# Redshift
REDSHIFT_HOST=host.redshift.amazonaws.com
REDSHIFT_PORT=5439
REDSHIFT_DATABASE=database
REDSHIFT_USER=username
REDSHIFT_PASSWORD=password
```

## Connection Code Examples

### PostgreSQL

```python
import os
import psycopg2
from urllib.parse import urlparse

def connect_postgres():
    url = os.getenv('DATABASE_URL')
    if not url:
        raise ValueError("DATABASE_URL not set in .deepdive/.env")
    
    result = urlparse(url)
    conn = psycopg2.connect(
        host=result.hostname,
        port=result.port,
        database=result.path[1:],
        user=result.username,
        password=result.password
    )
    return conn

# Usage
conn = connect_postgres()
cursor = conn.cursor()
cursor.execute("SELECT version()")
print(cursor.fetchone())
conn.close()
```

### MySQL

```python
import os
import mysql.connector
from urllib.parse import urlparse

def connect_mysql():
    url = os.getenv('DATABASE_URL')
    if not url:
        raise ValueError("DATABASE_URL not set")
    
    result = urlparse(url)
    conn = mysql.connector.connect(
        host=result.hostname,
        port=result.port or 3306,
        database=result.path[1:],
        user=result.username,
        password=result.password
    )
    return conn
```

### SQLite

```python
import os
import sqlite3
from urllib.parse import urlparse

def connect_sqlite():
    url = os.getenv('DATABASE_URL')
    if not url:
        raise ValueError("DATABASE_URL not set")
    
    # Parse sqlite:///path/to/db.db
    path = url.replace('sqlite:///', '')
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn
```

### BigQuery

```python
from google.cloud import bigquery
import os

def connect_bigquery():
    project_id = os.getenv('BIGQUERY_PROJECT_ID')
    dataset = os.getenv('BIGQUERY_DATASET')
    
    if not project_id:
        raise ValueError("BIGQUERY_PROJECT_ID not set")
    
    client = bigquery.Client(project=project_id)
    return client, dataset

# Usage
client, dataset = connect_bigquery()
query = f"SELECT * FROM `{project_id}.{dataset}.table` LIMIT 10"
results = client.query(query).result()
```

### Snowflake

```python
import snowflake.connector
import os

def connect_snowflake():
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE')
    )
    return conn
```

### Redshift

```python
import psycopg2
import os

def connect_redshift():
    conn = psycopg2.connect(
        host=os.getenv('REDSHIFT_HOST'),
        port=os.getenv('REDSHIFT_PORT', 5439),
        database=os.getenv('REDSHIFT_DATABASE'),
        user=os.getenv('REDSHIFT_USER'),
        password=os.getenv('REDSHIFT_PASSWORD')
    )
    return conn
```

## Testing Connections

Always test connection before executing queries:

```python
def test_connection(conn_type):
    try:
        if conn_type == 'postgres':
            conn = connect_postgres()
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            conn.close()
            return f"Connected: {version}"
        elif conn_type == 'sqlite':
            conn = connect_sqlite()
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            conn.close()
            return f"Connected: SQLite {version}"
        # ... similar for others
    except Exception as e:
        return f"Connection failed: {str(e)}"
```

## Auto-Detection

Detect database type from DATABASE_URL:

```python
def detect_database_type():
    url = os.getenv('DATABASE_URL', '')
    if url.startswith('postgresql://'):
        return 'postgres'
    elif url.startswith('mysql://'):
        return 'mysql'
    elif url.startswith('sqlite://'):
        return 'sqlite'
    elif os.getenv('BIGQUERY_PROJECT_ID'):
        return 'bigquery'
    elif os.getenv('SNOWFLAKE_ACCOUNT'):
        return 'snowflake'
    elif os.getenv('REDSHIFT_HOST'):
        return 'redshift'
    else:
        raise ValueError("No database configuration found in .deepdive/.env")
```

## Connection Pooling (Production)

For production use, implement connection pooling:

```python
from psycopg2 import pool

# PostgreSQL connection pool
postgres_pool = psycopg2.pool.SimpleConnectionPool(
    1, 10,  # min, max connections
    host=result.hostname,
    port=result.port,
    database=result.path[1:],
    user=result.username,
    password=result.password
)

# Usage
conn = postgres_pool.getconn()
# ... use connection ...
postgres_pool.putconn(conn)
```

## Error Handling

Common connection errors:

| Error | Solution |
|-------|----------|
| Connection refused | Check host/port, ensure database is running |
| Authentication failed | Verify credentials in .env |
| Database not found | Check database name in URL |
| SSL required | Add `?sslmode=require` to PostgreSQL URL |

## Best Practices

1. **Never commit .env**: Add `.deepdive/.env` to .gitignore
2. **Use connection strings**: Single DATABASE_URL preferred over multiple vars
3. **Close connections**: Always close or return to pool
4. **Test on init**: Validate connection when @deepdive init runs
5. **Rotate credentials**: Support for credential rotation via env vars
