---
name: scope-design
description: Data model scope design framework for defining entities, metrics, relationships, and constraints
---

# Scope Design Framework

Design a complete data model scope from business requirements. Auto-triggers when exploratory analysis detects no existing schema/framework.

## When to Use

### Explicit User Invocation
```
@deepdive scope "answer these questions about my domain"
@deepdive scope "design a data model for my business"
@deepdive scope "what entities and metrics should I track"
```

### Auto-Detection Triggers
When `@deepdive query` or `@deepdive schema` encounters:
- Zero tables or empty database
- Request for metrics that don't exist
- No clear entity definitions
- Missing business context

```
User: "what's our customer lifetime value"
Agent: No CLV metric found. Auto-offering scope design...
```

## For Non-Domain Experts

If the user can't describe their domain, the agent must **discover and infer**.

### 1. Agent Discovery from Database

```
@deepdive scope --discover

Agent analyzes:
- Table names and structures
- Column names and types
- Sample data values
- Foreign key patterns
```

**Discovery patterns (domain-agnostic):**

| Pattern | Indicators | Generic Metrics |
|---------|------------|-----------------|
| Transactional | orders, items, total, payment, transaction | Volume, Value, Frequency |
| Membership | users, accounts, status, join_date, subscription | Retention, Growth, Activity |
| Hierarchical | parent_id, category, level, org_structure | Depth, Breadth, Distribution |
| Temporal | date, timestamp, period, fiscal_ | Trends, Seasonality, Velocity |
| Asset-based | inventory, location, quantity, capacity | Utilization, Turnover, Capacity |

**Agent output:**
```
"Based on your schema, I detected:
- 6 tables with order/transaction patterns
- Customer_id and product_id references
- Date columns suggesting time-series data

Pattern: Transactional + Temporal
Suggests: Actor, Action, Object entities
Metrics: Volume, Value, Frequency over time

Does this match your business? (confirm or adjust)"
```

### 2. Category-Based Templates

**Use generic patterns, not domain-specific metrics:**

```yaml
template: transactional
description: One-time exchanges between actors
entities:
  - Actor: who performs the action
  - Action: the transaction/event
  - Object: what's being exchanged
metrics_pattern:
  - volume: count(actions)
  - value: sum(action.value)
  - rate: action / actor_count

template: subscription
description: Recurring access or service
entities:
  - Account: holder of subscription
  - Plan: tier/type of access
  - Period: time-bounded intervals
metrics_pattern:
  - active_count
  - retention_rate
  - expansion_rate / contraction_rate

template: engagement
description: Ongoing interaction with content/platform
entities:
  - User: participant
  - Session: engagement instance
  - Content: what's consumed
metrics_pattern:
  - active_users
  - session_frequency
  - content_interaction_rate
```

### 3. User Mapping to Actual Domain

Agent provides generic, user maps to their terms:

```
Agent: "Transactional pattern detected. Map to your domain:"
- Actor → ? (Customer, Patient, Student, Member...)
- Action → ? (Order, Visit, Enrollment, Booking...)
- Object → ? (Product, Room, Class, Flight...)

User: "We're a gym"
Actor: Member
Action: Visit
Object: Class

Agent: "Setting up:
Member (retention, visit frequency)
Visit (volume, peak times)
Class (utilization, popularity)"
```

## Framework Output

### 1. Core Entities
```yaml
entities:
  - name: Member
    description: Gym members with active memberships
    attributes: [id, name, joined_at, status]
    events: [signup, visit, churn]
```

### 2. Primary Metrics (Entity-Scoped)
```yaml
metrics:
  primary:
    - name: retention_rate
      entity: Member
      formula: active / total
      update_trigger: status_change
```

### 3. Causal Relationships
```yaml
relationships:
  - from: Class
    to: Visit
    type: enables
```

### 4. Constraints
```yaml
constraints:
  - rule: visit_capacity <= class_capacity
  - unique: [member_id, class_id, date]
```

### 5. Derived Metrics
```yaml
derived:
  - name: utilization_rate
    formula: visit_capacity / class_capacity
```

## Usage

```bash
# Agent discovers from existing data
@deepdive scope --discover

# Use generic template
@deepdive scope --template transactional

# Describe, agent infers
@deepdive scope "I run a gym"

# Generate schema from scope
@deepdive scope generate-schema

# Query using defined metrics
@deepdive query "member retention by month"
```

## Discovery Reference

### Schema Indicators
```
orders*, transactions*, payments*    → Transactional
users*, accounts*, members*          → Membership
categories*, hierarchies*, levels*   → Hierarchical
appointments*, visits*, sessions*    → Engagement/Temporal
inventory*, locations*, assets*      → Asset-based
```

### Column Indicators
```
*_at, *_date, timestamp              → Temporal
status, type, category               → Classification
total, amount, price, value          → Value metrics
count, frequency, ratio              → Rate metrics
```

### Value Indicators
```
'active', 'pending', 'completed'     → Status values
2024-01-01, 2024-12-31               → Date ranges
$100, 50%, 1000 units                → Numeric scales
```

## Key Principles

1. **Agent infers, user confirms** - No domain expertise required
2. **Generic patterns, not specific metrics** - Maps to any domain
3. **Entity-scoped metrics** - Each metric belongs to one entity
4. **Update-trigger based** - Metrics update on specific events
5. **Constraints first** - Define rules before calculations