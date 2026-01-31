---
name: write-protection
description: Safety mechanisms for preventing accidental data modifications
---

# Write Protection

DeepDive protects against accidental data modifications with confirmation flows and dry-run previews.

## Safe Mode

Default behavior: All write operations require explicit confirmation.

```
@deepdive safe-mode [on|off|status]
```

- **on** (default): Confirm all INSERT/UPDATE/DELETE/ALTER
- **off**: Execute writes immediately (use with caution)
- **status**: Show current mode

## Write Operation Detection

Automatically detect destructive operations:

```python
WRITE_OPERATIONS = [
    'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'DROP',
    'ALTER', 'CREATE', 'GRANT', 'REVOKE'
]

def is_write_query(sql):
    """Check if query modifies data"""
    sql_upper = sql.strip().upper()
    
    for op in WRITE_OPERATIONS:
        if sql_upper.startswith(op):
            return True
    
    # Check for CTEs with writes
    if 'INSERT' in sql_upper or 'UPDATE' in sql_upper or 'DELETE' in sql_upper:
        return True
    
    return False
```

## Confirmation Flow

### Step 1: Detect Write Operation

```
User: @deepdive query "update all users set status = 'active'"
→ Detected UPDATE operation
```

### Step 2: Show Dry-Run Preview

```
⚠️  WRITE OPERATION DETECTED

Operation: UPDATE
Table: users
Filter: (none - affects ALL rows)

DRY-RUN PREVIEW (First 5 rows that will be affected):
┌────┬─────────────┬────────┬─────────────────────┐
│ id │ email       │ status │ last_login          │
├────┼─────────────┼────────┼─────────────────────┤
│ 1  │ a@email.com │ pending│ 2025-01-15 10:00:00 │
│ 2  │ b@email.com │ pending│ 2025-01-20 14:30:00 │
│ 3  │ c@email.com │ inactive│ 2024-12-01 09:00:00│
│ ...│ ...         │ ...    │ ...                 │
└────┴─────────────┴────────┴─────────────────────┘

Total rows to be updated: 1,247

New values:
  status: 'active' (was: varies)
```

### Step 3: Require Confirmation

```
Execute this UPDATE? 
[y] Yes, proceed
[n] No, cancel
[e] Edit query
[d] Show diff (before/after)
[w] Disable safe-mode for this session

> 
```

### Step 4: Execute or Cancel

```
User: y
→ Executing UPDATE...
→ 1,247 rows updated ✓

User: n
→ Operation cancelled ✗
```

## Dry-Run Implementation

```python
def dry_run_update(conn, sql):
    """Preview UPDATE without executing"""
    
    # Parse UPDATE statement
    # UPDATE table SET col = val WHERE condition
    
    # Build SELECT to show affected rows
    preview_sql = f"""
    SELECT *
    FROM {table}
    WHERE {condition}
    LIMIT 5
    """
    
    # Execute SELECT (read-only)
    preview_rows = execute_query(conn, preview_sql)
    
    # Count total affected
    count_sql = f"SELECT COUNT(*) FROM {table} WHERE {condition}"
    total_count = execute_query(conn, count_sql)[0]['count']
    
    return {
        'preview_rows': preview_rows,
        'total_count': total_count,
        'changes': parse_changes(sql)  # What columns will change
    }

def dry_run_delete(conn, sql):
    """Preview DELETE without executing"""
    
    # Similar to UPDATE but show what's being deleted
    preview_sql = f"""
    SELECT *
    FROM {table}
    WHERE {condition}
    LIMIT 5
    """
    
    preview_rows = execute_query(conn, preview_sql)
    
    count_sql = f"SELECT COUNT(*) FROM {table} WHERE {condition}"
    total_count = execute_query(conn, count_sql)[0]['count']
    
    return {
        'preview_rows': preview_rows,
        'total_count': total_count,
        'operation': 'DELETE'
    }

def dry_run_insert(conn, sql):
    """Preview INSERT without executing"""
    
    # Parse INSERT values
    # Show what will be inserted
    
    return {
        'values': parsed_values,
        'table': target_table,
        'estimated_rows': len(parsed_values)
    }
```

## Diff View

Show before/after comparison:

```
DIFF PREVIEW:

Row 1 (id: 1):
  email: a@email.com → a@email.com (unchanged)
  status: pending → ACTIVE [CHANGED]
  last_login: 2025-01-15 10:00:00 → (unchanged)

Row 2 (id: 2):
  email: b@email.com → b@email.com (unchanged)
  status: pending → ACTIVE [CHANGED]
  ...
```

## Batch Protection

Prevent accidental mass updates:

```python
def check_batch_safety(conn, sql, threshold=1000):
    """Warn about large operations"""
    
    dry_run = dry_run_update(conn, sql)
    
    if dry_run['total_count'] > threshold:
        print(f"⚠️  WARNING: This affects {dry_run['total_count']} rows")
        print(f"   Threshold: {threshold}")
        print("\n   Suggestions:")
        print("   - Add a WHERE clause to limit scope")
        print("   - Use LIMIT clause")
        print("   - Run in smaller batches")
        return False
    
    return True
```

## ALTER Table Protection

Extra caution for schema changes:

```
⚠️  SCHEMA MODIFICATION DETECTED

Operation: ALTER TABLE users
Changes:
  - DROP COLUMN phone_number
  - ADD COLUMN mobile_number VARCHAR(20)

⚠️  This operation:
  - Cannot be undone easily
  - May break existing applications
  - Could lose data (DROP COLUMN)

REQUIRED: Type "users" to confirm table name
> users

Additional confirmation required for DROP operations.
Continue? [y/n]
```

## Transaction Safety

Wrap writes in transactions:

```python
def execute_write_safely(conn, sql, dry_run_result):
    """Execute write with rollback capability"""
    
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN")
        
        # Execute the write
        cursor.execute(sql)
        
        # Get affected count
        affected = cursor.rowcount
        
        # Confirm success
        print(f"✓ {affected} rows affected")
        
        # Commit
        conn.commit()
        
        return {'success': True, 'affected': affected}
        
    except Exception as e:
        # Rollback on error
        conn.rollback()
        print(f"✗ Error: {e}")
        print("Transaction rolled back - no changes made")
        return {'success': False, 'error': str(e)}
```

## Backup Recommendations

Before destructive operations:

```
⚠️  DESTRUCTIVE OPERATION: DROP TABLE

Table: temp_import_data

Recommended: Create backup first?
[b] Create backup (CREATE TABLE ... AS SELECT)
[y] Proceed without backup
[n] Cancel

> b

Creating backup: temp_import_data_backup_2025-01-31
✓ Backup created with 5,432 rows

Proceed with DROP? [y/n]
```

## Safe Mode Exceptions

Allow specific safe writes:

```python
SAFE_EXCEPTIONS = [
    'INSERT INTO log_table',      # Logging is safe
    'UPDATE users SET last_login', # Updating timestamps
]

def is_exceptionally_safe(sql):
    """Check if query is in safe exceptions list"""
    for pattern in SAFE_EXCEPTIONS:
        if pattern in sql:
            return True
    return False
```

## Audit Trail

Log all write operations:

```json
{
  "audit_log": [
    {
      "timestamp": "2025-01-31T14:30:00Z",
      "operation": "UPDATE",
      "sql": "UPDATE users SET status = 'active' WHERE id = 123",
      "affected_rows": 1,
      "confirmed": true,
      "dry_run_previewed": true
    }
  ]
}
```

## Best Practices

1. **Always preview**: Never skip dry-run for unknown scopes
2. **Add WHERE clauses**: Be specific about what to modify
3. **Test on subset**: Use LIMIT for initial testing
4. **Backup first**: Before ALTER/DROP operations
5. **Review counts**: If affected count seems wrong, cancel
6. **Use transactions**: Enable for production databases
7. **Log everything**: Maintain audit trail

## Emergency Recovery

If accidental write occurs:

```
@deepdive undo
→ Shows last 5 write operations
→ Can restore from backup if created
→ Or manually craft REVERSE operation
```

Note: Not all databases support true UNDO. Prevention is better than cure.
