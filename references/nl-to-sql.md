---
name: nl-to-sql
description: Natural language to SQL translation patterns and query generation
---

# Natural Language to SQL

Transform natural language questions into SQL queries using schema context and learned corrections.

## Basic Translation Pattern

```
User: "show top 10 customers by revenue"
↓
SQL: SELECT customer_id, SUM(amount) as revenue 
     FROM orders 
     GROUP BY customer_id 
     ORDER BY revenue DESC 
     LIMIT 10
```

## Translation Process

1. **Parse Intent**: Identify query type (aggregation, filter, join, etc.)
2. **Map Entities**: Match natural language terms to table/column names
3. **Apply Schema**: Use actual table structures
4. **Check Memory**: Apply learned corrections
5. **Generate SQL**: Build query with proper syntax
6. **Validate**: Run through safety checks
7. **Execute**: Run query and return results

## Common Patterns

### Aggregation Queries

```
"total sales by month" →
SELECT DATE_TRUNC('month', order_date) as month, SUM(total) as sales
FROM orders
GROUP BY month
ORDER BY month

"average order value" →
SELECT AVG(total) as avg_order_value
FROM orders

"count of users by status" →
SELECT status, COUNT(*) as count
FROM users
GROUP BY status
```

### Filter Queries

```
"active users from last 30 days" →
SELECT *
FROM users
WHERE last_login >= CURRENT_DATE - INTERVAL '30 days'
AND status = 'active'

"orders over $1000 this year" →
SELECT *
FROM orders
WHERE total > 1000
AND order_date >= DATE_TRUNC('year', CURRENT_DATE)
```

### Join Queries

```
"customers with their orders" →
SELECT c.name, o.order_id, o.total
FROM customers c
JOIN orders o ON c.id = o.customer_id

"products that have never been ordered" →
SELECT p.name
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
WHERE oi.product_id IS NULL
```

### Time-based Queries

```
"revenue this quarter" →
SELECT SUM(total) as revenue
FROM orders
WHERE order_date >= DATE_TRUNC('quarter', CURRENT_DATE)

"month over month growth" →
WITH monthly_revenue AS (
  SELECT DATE_TRUNC('month', order_date) as month,
         SUM(total) as revenue
  FROM orders
  GROUP BY month
)
SELECT month, revenue,
       revenue - LAG(revenue) OVER (ORDER BY month) as growth
FROM monthly_revenue
```

### Top N Queries

```
"top 5 products by sales" →
SELECT p.name, SUM(oi.quantity) as units_sold
FROM products p
JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name
ORDER BY units_sold DESC
LIMIT 5
```

## Schema-Aware Translation

Use actual table schema to improve translation:

```python
def nl_to_sql(question, schema_context):
    """
    schema_context = {
        'tables': {
            'customers': ['id', 'name', 'email', 'created_at'],
            'orders': ['id', 'customer_id', 'total', 'order_date']
        }
    }
    """
    # Match question terms to schema
    # "customers" → customers table
    # "bought" → orders table
    # "when" → order_date column
    
    return generated_sql
```

## Ambiguity Resolution

When question is ambiguous, ask clarifying questions:

```
User: "show sales"
Agent: "Do you mean:
  1. Total revenue (sum of order amounts)
  2. Number of orders (count)
  3. Sales by product (breakdown)
  4. Sales over time (trend)"
```

## Handling Complex Questions

Break complex questions into steps:

```
User: "what's the average order value for customers who signed up this year"

Step 1: Identify customers who signed up this year
  → SELECT id FROM customers WHERE created_at >= '2025-01-01'

Step 2: Get their orders
  → SELECT * FROM orders WHERE customer_id IN (...)

Step 3: Calculate average
  → SELECT AVG(total) FROM orders WHERE ...

Final SQL:
SELECT AVG(o.total) as avg_order_value
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE c.created_at >= DATE_TRUNC('year', CURRENT_DATE)
```

## Learning from Corrections

Store and apply user corrections:

```json
{
  "corrections": [
    {
      "pattern": "active users",
      "correction": "status = 'active' AND email_verified = true",
      "context": "users table"
    }
  ]
}
```

Apply on future queries:

```
User: "count active users"
→ Checks memory → Finds correction
→ SELECT COUNT(*) FROM users WHERE status = 'active' AND email_verified = true
```

## Query Templates

Pre-defined templates for common queries:

```sql
-- Template: funnel_analysis
WITH stages AS (
  SELECT 'awareness' as stage, COUNT(*) as count FROM ...
  UNION ALL
  SELECT 'interest', COUNT(*) FROM ...
  UNION ALL
  SELECT 'purchase', COUNT(*) FROM ...
)
SELECT stage, count,
       count * 100.0 / LAG(count) OVER (ORDER BY stage) as conversion_rate
FROM stages;

-- Template: cohort_analysis
SELECT 
  DATE_TRUNC('month', first_order) as cohort_month,
  DATE_TRUNC('month', order_date) - DATE_TRUNC('month', first_order) as period,
  COUNT(DISTINCT customer_id) as customers
FROM ...
GROUP BY cohort_month, period;
```

## Error Recovery

When query fails, suggest fixes:

```
Query failed: column "price" does not exist
Did you mean:
  - "unit_price" in products table
  - "total" in orders table
  - "amount" in order_items table
```

## Best Practices

1. **Start simple**: Generate working query first, optimize later
2. **Use CTEs**: Complex queries → readable with WITH clauses
3. **Comment**: Add comments explaining complex logic
4. **Limit results**: Always add LIMIT for exploration queries
5. **Handle NULLs**: Use COALESCE for aggregations
6. **Date arithmetic**: Use database-specific date functions
