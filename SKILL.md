---
name: deepdive
description: Universal data agent skill for natural language database querying, schema visualization, and automated chart generation. Use when working with databases, analyzing data, creating visualizations, exploring table structures, or needing insights from PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, or Redshift. Triggers include "query the database", "analyze this data", "show me a chart", "visualize the schema", "what's in this table", or any data exploration tasks.
---

# DeepDive - Universal Data Agent

DeepDive transforms natural language into database queries, generates visualizations, and learns from user corrections to improve over time.

## Quick Start

```bash
# Setup (creates .deepdive/ directory)
@deepdive init

# Configure database in .deepdive/.env
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Query data
@deepdive query "show top 10 customers by revenue"

# Visualize schema
@deepdive visualize schema

# Create chart
@deepdive chart "monthly revenue over last 6 months"
```

## Core Commands

### Database Connection
- `@deepdive init` - Initialize .deepdive/ directory with .env template
- `@deepdive connect <type>` - Setup connection (postgres|mysql|sqlite|bigquery|snowflake)

### Natural Language Queries
- `@deepdive query "<question>"` - Convert question to SQL and execute
- `@deepdive preview "<query>"` - Show results as markdown table (limit 100 rows)

### Visualization
- `@deepdive visualize schema` - Generate ERD diagram (.deepdive/diagrams/)
- `@deepdive visualize lineage` - Show table relationships
- `@deepdive chart "<question>"` - Generate Vega-Lite chart (.deepdive/charts/)

### Learning & Safety
- `@deepdive learn` - View/update learned corrections
- `@deepdive history` - Show recent queries
- `@deepdive safe-mode [on|off]` - Require confirmation for writes (default: on)

### Scope Design
- `@deepdive scope "<business description>"` - Design data model scope
  - `--template transactional|subscription|engagement` - Use generic category template
  - `--discover` - Agent infers domain from existing database schema
  - Generates: core entities, primary metrics, causal relationships, constraints, derived metrics
  - Auto-triggers when exploratory analysis finds no existing framework
- `@deepdive scope generate-schema` - Generate database schema from scope design

## Project Structure

DeepDive creates and manages:

```
.deepdive/
├── .env                      # Database credentials (user-managed)
├── memory.json               # Learned corrections (per-project)
├── diagrams/                 # Generated .mmd files
│   ├── schema-YYYYMMDD.mmd
│   └── erd-YYYYMMDD.mmd
├── charts/                   # Generated .png/.svg files
│   └── chart-XXX.png
└── queries.log               # Query history
```

## Supported Databases

- **PostgreSQL** - Full support with advanced features
- **MySQL** - Standard SQL support
- **SQLite** - File-based, perfect for local/dev
- **BigQuery** - Google Cloud, large-scale analytics
- **Snowflake** - Cloud data warehouse
- **Redshift** - AWS analytics

## Reference Documentation

Read these files based on the task:

- **Database Connections**: [references/connectors.md](references/connectors.md)
- **Natural Language Queries**: [references/nl-to-sql.md](references/nl-to-sql.md)
- **Schema Introspection**: [references/schema-introspection.md](references/schema-introspection.md)
- **Mermaid Visualization**: [references/mermaid-viz.md](references/mermaid-viz.md)
- **Vega-Lite Charts**: [references/vega-charts.md](references/vega-charts.md)
- **User Learning**: [references/user-learning.md](references/user-learning.md)
- **Write Protection**: [references/write-protection.md](references/write-protection.md)
- **Scope Design**: [references/scope-design.md](references/scope-design.md)
- **Examples**: [references/examples.md](references/examples.md)

## Usage Patterns

### Data Exploration
```
User: "What tables are in this database?"
→ @deepdive schema introspection

User: "Show me the customer table structure"
→ @deepdive schema customers
```

### Querying
```
User: "Which customers bought something last month?"
→ Natural language → SQL → Execute → Results

User: "Chart monthly revenue"
→ Query → Vega-Lite spec → .deepdive/charts/revenue.png
```

### Visualization
```
User: "Visualize the database schema"
→ Mermaid ERD → .deepdive/diagrams/schema.mmd → Open browser

User: "Show relationships between tables"
→ Foreign key analysis → Lineage diagram
```

## Key Principles

1. **Environment Variables**: All credentials in `.deepdive/.env` (never hardcoded)
2. **Write Protection**: INSERT/UPDATE/DELETE require explicit confirmation (unless safe-mode off)
3. **Learning**: Corrections stored in `.deepdive/memory.json` and applied to future queries
4. **Project Scope**: Each project has isolated memory, diagrams, and charts
5. **Static Outputs**: All visualizations are files (.mmd, .png) for version control

## Examples

### RevOps Scenario
```
@deepdive connect postgres
@deepdive query "qualified opportunities by stage this quarter"
@deepdive chart "conversion funnel"
@deepdive visualize lineage
```

### Video Production Scenario
```
@deepdive connect sqlite  # For document analysis
@deepdive query "projects due this week from documents table"
@deepdive chart "project timeline"
```

## Scripts

Python scripts for reliable operations:

- `scripts/generate_mermaid.py` - Generate schema/ERD diagrams
- `scripts/generate_chart.py` - Create Vega-Lite charts
- `scripts/validate_query.py` - SQL safety validation

Execute scripts rather than rewriting code for deterministic results.

## Safety & Privacy

- Read-only by default for exploration
- Write operations require confirmation
- Credentials never logged or shared
- All data stays local (no cloud API calls)
- Query history stored locally only
