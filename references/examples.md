---
name: examples
description: Real-world usage scenarios for RevOps, Video Production, and general data analysis
---

# DeepDive Examples

Real-world scenarios demonstrating DeepDive capabilities.

## Scenario 1: RevOps / Growth Analytics

**Context**: Sales team has data scattered across Salesforce, HubSpot exports, and Excel forecasts. Need unified view.

### Setup

```bash
# 1. Initialize
@deepdive init

# 2. Configure multiple sources
# .deepdive/.env
SALESFORCE_URL=postgresql://sf-replica.internal:5432/salesforce
HUBSPOT_CSV_PATH=./data/hubspot_export.csv
FORECAST_DB=sqlite:///data/forecasts.db
```

### Load CSV Data

```python
# Convert CSV to SQLite for querying
import pandas as pd
import sqlite3

df = pd.read_csv('data/hubspot_export.csv')
conn = sqlite3.connect('.deepdive/hubspot.db')
df.to_sql('contacts', conn, if_exists='replace', index=False)
conn.close()
```

### Analysis Examples

#### Pipeline Health

```
User: "Show funnel from lead to closed-won this quarter"

DeepDive:
→ Query: 
  SELECT stage, COUNT(*) as count, SUM(amount) as value
  FROM opportunities
  WHERE created_date >= DATE_TRUNC('quarter', CURRENT_DATE)
  GROUP BY stage
  ORDER BY count DESC

→ Results:
  Prospecting: 145 leads, $2.3M
  Qualification: 89 leads, $1.8M
  Proposal: 45 leads, $1.2M
  Negotiation: 23 leads, $800K
  Closed-Won: 12 leads, $450K

→ Suggestion: @deepdive chart "conversion funnel"
```

#### Sales Rep Performance

```
User: "Top 10 reps by revenue this month vs quota"

DeepDive:
→ Multi-table join
→ Calculate attainment %
→ Identify top/bottom performers

→ @deepdive chart "attainment by rep"
```

#### Lead Scoring Analysis

```
User: "Which lead sources have highest conversion?"

DeepDive:
→ Join leads → contacts → opportunities
→ Calculate conversion by source
→ Time to conversion analysis

→ Insights: "Webinar leads convert 3x faster than cold outreach"
```

#### MRR Calculation

```
User: "Calculate MRR by product line"

DeepDive:
→ Learned correction: "MRR = monthly_recurring_revenue"
→ Query subscriptions table
→ Handle upgrades/downgrades/churn

→ @deepdive chart "MRR trend by product"
```

### Learned Patterns (RevOps)

```json
{
  "corrections": [
    {
      "pattern": "active pipeline",
      "correction": "stage NOT IN ('Closed-Lost', 'Closed-Won')",
      "context": "opportunities"
    },
    {
      "pattern": "ARR",
      "correction": "SUM(amount) WHERE contract_type = 'annual'",
      "context": "subscriptions"
    },
    {
      "pattern": "SQL",
      "correction": "sales_qualified_lead = true",
      "context": "leads",
      "explanation": "Sales Qualified Lead, not Structured Query Language"
    }
  ]
}
```

---

## Scenario 2: Video Production Company

**Context**: Manage projects across documents, emails, meeting transcripts. Need to track deliverables and timelines.

### Setup

```bash
# 1. Initialize
@deepdive init

# 2. Create unified database
# .deepdive/.env
DATABASE_URL=sqlite:///production.db
```

### Data Ingestion

```python
# Parse documents into structured tables
import os
import json
import sqlite3

def ingest_documents(docs_folder):
    """Convert various docs into queryable SQLite tables"""
    
    conn = sqlite3.connect('.deepdive/production.db')
    cursor = conn.cursor()
    
    # Create projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT,
            client TEXT,
            status TEXT,
            start_date TEXT,
            due_date TEXT,
            budget REAL,
            deliverables TEXT,  -- JSON array
            documents TEXT      -- JSON array of source files
        )
    ''')
    
    # Parse each document
    for doc in os.listdir(docs_folder):
        # Extract project info using NLP/parsing
        project_data = parse_document(os.path.join(docs_folder, doc))
        
        cursor.execute('''
            INSERT OR REPLACE INTO projects 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_data['id'],
            project_data['name'],
            project_data['client'],
            project_data['status'],
            project_data['start_date'],
            project_data['due_date'],
            project_data['budget'],
            json.dumps(project_data['deliverables']),
            json.dumps([doc])
        ))
    
    conn.commit()
    conn.close()
```

### Analysis Examples

#### Project Timeline

```
User: "What projects are due this week?"

DeepDive:
→ Query: 
  SELECT name, client, due_date, 
         julianday(due_date) - julianday('now') as days_remaining
  FROM projects
  WHERE due_date BETWEEN date('now') AND date('now', '+7 days')
  ORDER BY due_date

→ Results:
  Brand Video - Acme Corp - Due: 2025-02-02 (2 days)
  Product Demo - StartupX - Due: 2025-02-05 (5 days)
```

#### Budget Tracking

```
User: "Projects over budget or at risk"

DeepDive:
→ Query:
  SELECT name, client, budget, actual_spend,
         (actual_spend / budget * 100) as budget_used_pct
  FROM projects
  WHERE actual_spend > budget * 0.8
  ORDER BY budget_used_pct DESC

→ @deepdive chart "budget utilization by project"
```

#### Deliverable Status

```
User: "Which deliverables are incomplete by project?"

DeepDive:
→ Parse JSON deliverables column
→ Unnest and filter incomplete items
→ Group by project

→ Results:
  Brand Video:
    ✓ Script approved
    ⏳ Filming in progress
    ⏳ Rough cut pending
    ⏳ Final edit pending
```

#### Email Analysis

```
User: "Extract action items from meeting emails"

DeepDive:
→ Parse email exports
→ Extract meetings table
→ NLP to identify action items
→ Link to projects

→ Query:
  SELECT project_name, action_item, owner, due_date
  FROM action_items
  WHERE status = 'open'
  ORDER BY due_date
```

### Visualization

```
User: "Visualize project dependencies"

DeepDive:
→ Parse deliverable relationships
→ Generate mermaid diagram:

graph TD
    A[Script Approval] --> B[Pre-Production]
    B --> C[Filming]
    C --> D[Rough Cut]
    D --> E[Client Review]
    E --> F[Final Edit]
    F --> G[Delivery]
    
    E -.->|revisions| D
```

### Learned Patterns (Video Production)

```json
{
  "corrections": [
    {
      "pattern": "in progress",
      "correction": "status = 'active'",
      "context": "projects"
    },
    {
      "pattern": "overdue",
      "correction": "due_date < date('now') AND status != 'delivered'",
      "context": "projects"
    },
    {
      "pattern": "client review",
      "correction": "deliverable_stage = 'client_review'",
      "context": "projects"
    }
  ],
  "table_aliases": {
    "projects": ["jobs", "productions", "engagements"]
  }
}
```

---

## Scenario 3: General Data Exploration

### First-Time Database Exploration

```
User: "I have a database but don't know what's in it"

@deepdive connect postgres
@deepdive schema

→ Shows all tables
→ Sample data from each
→ Relationship map

@deepdive visualize schema
→ Opens ERD diagram
```

### Quick Insights

```
User: "What interesting patterns do you see?"

DeepDive:
→ Analyze each table
→ Find correlations
→ Detect anomalies
→ Suggest visualizations

→ "Found: Orders spike on weekends, 
     Customer LTV correlates with support tickets,
     Churn risk high for customers with 3+ tickets"
```

### Ad-Hoc Reporting

```
User: "Create a report on Q4 performance"

DeepDive:
→ Query multiple tables
→ Generate charts
→ Compile markdown report
→ Save to .deepdive/reports/q4-2024.md

→ Report includes:
  - Executive summary
  - Key metrics with charts
  - Trends and anomalies
  - Recommendations
```

### Data Quality Check

```
User: "Find data quality issues"

DeepDive:
→ Check for nulls in required fields
→ Detect duplicates
→ Find outliers
→ Validate foreign keys
→ Check date ranges

→ "Issues found:
  - 23 customers with null email
  - 5 duplicate orders (same id, different totals)
  - 12 products with negative inventory"
```

---

## Common Patterns

### Multi-Source Analysis

```python
# Join across different databases
# Using SQLite as intermediate

# 1. Load data from multiple sources
load_postgres_to_sqlite('salesforce', 'opportunities')
load_csv_to_sqlite('hubspot_export.csv', 'hubspot_contacts')

# 2. Query unified view
@deepdive query "opportunities with contact info from both systems"
```

### Time-Series Analysis

```
User: "Show me trends"

→ Auto-detect time columns
→ Suggest appropriate granularity
→ Handle timezone issues
→ Generate line charts
→ Calculate YoY/MoM growth
```

### Cohort Analysis

```
User: "Cohort retention analysis"

→ Define cohort (signup month)
→ Track retention over time
→ Calculate cohort LTV
→ @deepdive chart "cohort retention heatmap"
```

### Funnel Analysis

```
User: "Conversion funnel"

→ Identify funnel stages
→ Calculate drop-off at each stage
→ Time between stages
→ @deepdive chart "funnel visualization"
```

---

## Best Practices from Examples

1. **Start with schema**: Always explore structure first
2. **Learn your domain**: Save corrections for business terminology
3. **Visualize early**: Charts reveal patterns text misses
4. **Multi-source**: Use SQLite as bridge between systems
5. **Iterate**: Start simple, add complexity as needed
6. **Document**: Save queries and insights to reports/
7. **Share**: Export learned patterns for team consistency
