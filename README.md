# DeepDive - Universal Data Agent Skill

Transform any coding agent into a data analyst. DeepDive enables natural language database querying, automatic visualization, and self-learning query correction for PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, and Redshift.

[![Skill](https://img.shields.io/badge/Skill-Universal%20Data%20Agent-blue)](https://skills.sh)
[![Databases](https://img.shields.io/badge/Databases-6%20Types-green)](./references/connectors.md)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

## Overview

DeepDive is a **universal skill** for AI coding agents (Claude Code, Cursor, OpenCode, etc.) that provides:

- **Natural Language Queries**: Ask questions in plain English, get SQL results
- **Multi-Database Support**: PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, Redshift
- **Visualizations**: Generate Mermaid diagrams and Vega-Lite charts
- **Self-Learning**: Improves accuracy from user corrections
- **Write Protection**: Safety confirmations for data modifications
- **Project Scope**: Isolated per-project configuration and memory

## Installation

### Method 1: Vercel Skill Lab (Recommended)

```bash
# Coming soon - submit your skill to Vercel Skill Lab
# Users install via:
npx skills add @vercel/deepdive-data-agent
```

### Method 2: Direct GitHub Install

```bash
# Claude Code
npx skills add https://github.com/tosi-n/deepdive

# Cursor
# Copy deepdive/ folder to ~/.cursor/skills/

# OpenCode  
npx skills add https://github.com/tosi-n/deepdive

# Generic (any agent supporting skills)
git clone https://github.com/tosi-n/deepdive.git
cp -r deepdive ~/.config/<agent>/skills/
```

### Method 3: Manual Installation

```bash
# Clone the repository
git clone https://github.com/tosi-n/deepdive.git

# Copy to your agent's skills directory
# For Claude Code:
cp -r deepdive ~/.claude/skills/

# For OpenCode:
cp -r deepdive ~/.config/opencode/skills/

# For Cursor:
cp -r deepdive ~/.cursor/skills/
```

## Quick Start

### 1. Initialize Project

```bash
@deepdive init
```

This creates a `.deepdive/` directory with:
- `.env` - Database credentials (add this to `.gitignore`!)
- `memory.json` - Learned corrections (per-project)
- `diagrams/` - Generated Mermaid files
- `charts/` - Generated chart images

### 2. Configure Database

Edit `.deepdive/.env`:

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/mydb

# MySQL
DATABASE_URL=mysql://user:password@localhost:3306/mydb

# SQLite
DATABASE_URL=sqlite:///path/to/database.db

# BigQuery
BIGQUERY_PROJECT_ID=your-project
BIGQUERY_DATASET=your-dataset
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Snowflake
SNOWFLAKE_ACCOUNT=account.region
SNOWFLAKE_USER=user
SNOWFLAKE_PASSWORD=password
SNOWFLAKE_DATABASE=database
SNOWFLAKE_SCHEMA=schema

# Redshift
REDSHIFT_HOST=host.redshift.amazonaws.com
REDSHIFT_PORT=5439
REDSHIFT_DATABASE=database
REDSHIFT_USER=user
REDSHIFT_PASSWORD=password
```

### 3. Start Querying

```bash
# Natural language queries
@deepdive query "show top 10 customers by revenue"
@deepdive query "what's the average order value this month"
@deepdive query "which products have low inventory"

# Preview data
@deepdive preview "SELECT * FROM orders LIMIT 20"

# Schema exploration
@deepdive schema
@deepdive schema customers
```

### 4. Visualize

```bash
# Generate ERD diagram
@deepdive visualize schema
# Opens browser with interactive diagram

# Create chart
@deepdive chart "monthly revenue trend"
# Generates .deepdive/charts/monthly-revenue-trend-YYYY-MM-DD.png

# Focused ERD
@deepdive visualize erd --tables customers,orders,products
```

### 5. Learn & Improve

When DeepDive gets something wrong, correct it:

```
User: "Show active customers"
Agent: SELECT * FROM customers WHERE status = 'active'
User: "Active customers should also have made a purchase in the last 90 days"

Agent: Got it! I'll update the query.
💾 Save this correction for future queries? (y/n)
User: y

✓ Saved to .deepdive/memory.json
```

View learned patterns:
```bash
@deepdive learn
```

## Supported Commands

| Command | Description |
|---------|-------------|
| `@deepdive init` | Initialize .deepdive/ directory |
| `@deepdive connect <type>` | Setup database connection |
| `@deepdive query "<question>"` | Natural language → SQL |
| `@deepdive preview "<query>"` | Show results as table |
| `@deepdive schema [table]` | Show table structure |
| `@deepdive visualize schema` | Generate ERD diagram |
| `@deepdive visualize erd` | Focused ERD |
| `@deepdive visualize lineage` | Data flow diagram |
| `@deepdive chart "<question>"` | Generate chart |
| `@deepdive learn` | View learned corrections |
| `@deepdive history` | Show query history |
| `@deepdive safe-mode [on\|off]` | Toggle write protection |

## Safety Features

### Write Protection

By default, all INSERT/UPDATE/DELETE operations require confirmation:

```
@deepdive query "update customers set status = 'active'"

⚠️  WRITE OPERATION DETECTED

Operation: UPDATE
Table: customers
Filter: (none - affects ALL 5,247 rows)

DRY-RUN PREVIEW (First 5 rows):
┌────┬─────────────┬──────────┐
│ id │ name        │ status   │
├────┼─────────────┼──────────┤
│ 1  │ John Doe    │ pending  │
│ 2  │ Jane Smith  │ inactive │
...

Execute this UPDATE? [y/n/d/w] 
y - Yes, proceed
n - No, cancel  
d - Show diff
w - Disable safe-mode
```

### Query Validation

All queries are validated for:
- SQL injection patterns
- Common mistakes (e.g., `= NULL` instead of `IS NULL`)
- Missing WHERE clauses on UPDATE/DELETE
- Batch size warnings (>1000 rows)

## Real-World Examples

### RevOps / Growth Analytics

Analyze scattered sales data across multiple systems:

```bash
# Multi-source analysis
@deepdive connect postgres  # Salesforce replica
@deepdive query "conversion funnel this quarter"
@deepdive chart "MRR by product line"
@deepdive visualize lineage

# Learned patterns:
# - "active pipeline" → status NOT IN ('Closed-Lost', 'Closed-Won')
# - "ARR" → annual contract value
# - "SQL" → sales_qualified_lead (not Structured Query Language!)
```

### Video Production Company

Track projects across documents and emails:

```bash
# Parse documents into queryable database
@deepdive connect sqlite
@deepdive query "projects due this week"
@deepdive query "budget utilization by client"
@deepdive chart "project timeline"
@deepdive visualize schema

# Cross-reference with meeting transcripts
@deepdive query "action items from last week's meetings"
```

### General Data Exploration

Explore an unfamiliar database:

```bash
@deepdive connect postgres
@deepdive schema                    # List all tables
@deepdive visualize schema          # See relationships
@deepdive query "interesting patterns in the data"
@deepdive chart "key metrics"
```

## Skill Architecture

```
deepdive/
├── SKILL.md                           # Entry point with triggers
├── references/
│   ├── connectors.md                  # Database connection patterns
│   ├── nl-to-sql.md                   # Natural language translation
│   ├── schema-introspection.md        # Schema discovery queries
│   ├── mermaid-viz.md                 # Diagram generation
│   ├── vega-charts.md                 # Chart specifications
│   ├── user-learning.md               # Correction memory system
│   ├── write-protection.md            # Safety mechanisms
│   └── examples.md                    # Real-world scenarios
└── scripts/
    ├── generate_mermaid.py            # CLI for diagrams
    ├── generate_chart.py              # CLI for charts
    └── validate_query.py              # SQL safety checker
```

## Distribution

### Vercel Skill Lab

To submit to [Vercel Skill Lab](https://vercel.com/marketplace/category/agents):

1. **Prerequisites**:
   - Vercel account
   - GitHub repository with skill
   - `SKILL.md` in root directory

2. **Submission Process**:
   ```bash
   # Fork vercel-labs/agent-skills template
   # Add your skill to skills/ directory
   # Submit PR or use Vercel CLI
   
   npm i -g vercel
   vercel skills publish ./deepdive
   ```

3. **Requirements**:
   - YAML frontmatter in SKILL.md with `name` and `description`
   - Clear trigger keywords in description
   - Progressive disclosure (references/ folder)
   - No extraneous files (no README, CHANGELOG in skill root)

### Anthropic Skills Registry

Submit to [skills.sh](https://skills.sh):

1. Create release with `.skill` file (zip of skill directory)
2. Submit via form or API
3. Include: name, description, tags, GitHub URL

### GitHub Distribution

Direct installation works with most agents:

```bash
# Users install with:
npx skills add https://github.com/tosi-n/deepdive

# Or git clone:
git clone https://github.com/tosi-n/deepdive.git ~/.claude/skills/deepdive
```

### NPM Distribution (Optional)

For CLI tooling alongside the skill:

```bash
npm install -g @tosi-n/deepdive-init
# Provides: deepdive init, deepdive doctor, etc.
```

## Requirements

- Python 3.8+
- Database drivers:
  ```bash
  pip install psycopg2-binary pymysql sqlite3 google-cloud-bigquery snowflake-connector-python
  ```
- Visualization (optional):
  ```bash
  pip install altair pandas
  npm install -g vega-lite
  ```

## Security

- **Credentials**: Stored in `.deepdive/.env` (never committed)
- **Local Only**: No data sent to external APIs
- **Read-First**: Write operations require explicit confirmation
- **Audit Trail**: Query history logged locally
- **No Training**: Your data doesn't train any models

## Contributing

Contributions welcome! Areas for expansion:

- Additional database connectors (MongoDB, DynamoDB, etc.)
- More chart types and templates
- Additional NLP patterns for query generation
- Integration with data catalogs (dbt, Amundsen)
- Custom visualization themes

## License

MIT License - See [LICENSE](./LICENSE) for details.

## Acknowledgments

Built with insights from:
- [Anthropic Skills Guide](https://skills.sh/anthropics/skills/skill-creator)
- [Vercel Skill Ecosystem](https://vercel.com/changelog/introducing-skills-the-open-agent-skills-ecosystem)
- [OpenAI Data Agent](https://openai.com/index/inside-our-in-house-data-agent/)
- [Hex AI](https://hex.tech/capability/ai/)

---

**Made with ❤️ for data people everywhere**

*Star ⭐ this repo if it helps you analyze data faster!*
