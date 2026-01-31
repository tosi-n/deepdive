---
name: user-learning
description: User correction memory system for improving query accuracy over time
---

# User Learning System

DeepDive learns from user corrections to improve future query accuracy.

## Memory Storage

All learned corrections stored in `.deepdive/memory.json`:

```json
{
  "version": "1.0",
  "project": "my-project",
  "last_updated": "2025-01-31T12:00:00Z",
  "corrections": [
    {
      "id": "corr-001",
      "pattern": "active users",
      "context": "users table",
      "correction": "status = 'active' AND email_verified = true",
      "explanation": "Active users must have verified email",
      "applied_count": 5,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "table_aliases": {
    "customers": ["users", "clients", "accounts"],
    "orders": ["purchases", "transactions", "sales"]
  },
  "column_mappings": {
    "revenue": {
      "tables": ["orders", "transactions"],
      "calculation": "SUM(total)"
    }
  }
}
```

## Commands

### View Learned Corrections

```
@deepdive learn
```

Output:
```
Learned Patterns (3):

1. "active users" → status = 'active' AND email_verified = true
   Context: users table | Applied 5 times

2. "MRR" → SUM(monthly_recurring_revenue)
   Context: subscriptions table | Applied 3 times

3. "churned" → status = 'canceled' AND canceled_at IS NOT NULL
   Context: subscriptions table | Applied 2 times
```

### Add Manual Correction

```
@deepdive learn add
Pattern: "qualified lead"
Correction: "lead_score > 70 AND status = 'open'"
Context: leads table
Explanation: Sales definition of qualified
```

### Edit/Delete Correction

```
@deepdive learn edit corr-001
@deepdive learn delete corr-001
```

## Automatic Learning

When user corrects a query, automatically capture:

```
User: "Show active users"
Agent: SELECT * FROM users WHERE status = 'active'
User: "No, active users should also have verified email"
Agent: Got it! I'll update the query.

Updated: SELECT * FROM users 
         WHERE status = 'active' 
         AND email_verified = true

💾 Save this correction for future queries? (y/n)
User: y
→ Saved to .deepdive/memory.json
```

## Learning Patterns

### Pattern Types

1. **Terminology Corrections**
   ```json
   {
     "pattern": "churn rate",
     "correction": "COUNT(CASE WHEN status = 'canceled' THEN 1 END) * 100.0 / COUNT(*)",
     "context": "subscriptions"
   }
   ```

2. **Filter Corrections**
   ```json
   {
     "pattern": "last month",
     "correction": "DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')",
     "context": "any table with created_at"
   }
   ```

3. **Join Corrections**
   ```json
   {
     "pattern": "customer orders",
     "correction": "JOIN orders ON customers.id = orders.customer_id (not email)",
     "context": "customers + orders"
   }
   ```

4. **Aggregation Corrections**
   ```json
   {
     "pattern": "average order value",
     "correction": "AVG(total) not SUM(total)/COUNT(*)",
     "context": "orders"
   }
   ```

5. **Column Name Mappings**
   ```json
   {
     "pattern": "customer name",
     "correction": "COALESCE(full_name, CONCAT(first_name, ' ', last_name))",
     "context": "users/customers tables"
   }
   ```

## Applying Corrections

Query generation flow with learning:

```python
def generate_query_with_learning(question, table, memory):
    # Step 1: Generate base query
    base_sql = nl_to_sql(question, table)
    
    # Step 2: Check for applicable corrections
    corrections = find_applicable_corrections(question, table, memory)
    
    # Step 3: Apply corrections
    corrected_sql = base_sql
    for correction in corrections:
        corrected_sql = apply_correction(corrected_sql, correction)
    
    return corrected_sql, corrections

def find_applicable_corrections(question, table, memory):
    applicable = []
    
    for corr in memory.get('corrections', []):
        # Match pattern in question
        if corr['pattern'].lower() in question.lower():
            # Check context (table scope)
            if corr['context'] == 'any' or table in corr['context']:
                applicable.append(corr)
    
    return applicable
```

## Context Scoping

Control where corrections apply:

- **Global**: `context: "any"` - Apply to all tables
- **Table-specific**: `context: "users"` - Only users table
- **Multi-table**: `context: "users,orders"` - Either table
- **Relationship**: `context: "users+orders"` - Only when both present

## Learning Statistics

Track correction effectiveness:

```json
{
  "correction": {
    "id": "corr-001",
    "applied_count": 15,
    "user_accepted": 14,
    "user_rejected": 1,
    "avg_confidence": 0.95
  }
}
```

## Table Aliases

Learn alternative terminology:

```json
{
  "table_aliases": {
    "customers": {
      "aliases": ["users", "clients", "accounts", "buyers"],
      "learned_from": [
        {"pattern": "clients", "count": 3},
        {"pattern": "buyers", "count": 1}
      ]
    }
  }
}
```

Query generation uses aliases:

```
User: "Show all clients"
→ Detects "clients" is alias for "customers"
→ Query customers table
```

## Column Interpretations

Learn derived metrics:

```json
{
  "column_mappings": {
    "LTV": {
      "tables": ["customers"],
      "calculation": "lifetime_value",
      "derived": false
    },
    "ARPU": {
      "tables": ["any"],
      "calculation": "SUM(revenue) / COUNT(DISTINCT user_id)",
      "derived": true,
      "time_range": "monthly"
    }
  }
}
```

## Export/Import

Share learned patterns across projects:

```bash
# Export
@deepdive learn export > deepdive-patterns.json

# Import
@deepdive learn import deepdive-patterns.json
```

## Best Practices

1. **Review periodically**: Clean up outdated corrections
2. **Be specific**: Context matters - "revenue" means different things in different tables
3. **Explain why**: Add explanations for complex business logic
4. **Test corrections**: Verify they work before saving
5. **Share knowledge**: Export/import patterns for team consistency
6. **Version control**: Commit .deepdive/memory.json to track learning evolution

## Privacy

- All learning stored locally in `.deepdive/memory.json`
- No data sent to external services
- Corrections are project-specific by default
- User controls all learned patterns (view/edit/delete)
