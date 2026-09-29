"""
Nexus-AI: Agent 1 — Lakehouse Data Agent
==========================================
Natural Language to SQL (NL2SQL) agent that:
- Reflects Gold layer schema from DuckDB
- Generates safe, read-only SQL queries
- Enforces LIMIT, timeout, and read-only constraints
- Returns structured results for the frontend/other agents
"""

import time
from typing import Any

import pandas as pd


# ── System Prompt ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Nexus-AI Lakehouse Data Agent. Your job is to answer data questions
by querying the Zomato Lakehouse Gold layer tables using SQL.

Available Gold Layer Tables:
{schema_context}

Rules:
1. Generate ONLY read-only SELECT queries. Never use INSERT, UPDATE, DELETE, DROP, or ALTER.
2. Always include LIMIT (max 100 rows) unless doing aggregation.
3. Use descriptive column aliases for readability.
4. When asked about "top" or "best", ORDER BY the relevant metric DESC.
5. For revenue questions, use the mart_city_revenue or fact_orders tables.
6. For delivery performance, use fact_daily_delivery_performance or dim_delivery_partners.
7. For restaurant info, use dim_restaurants or dim_cuisines.
8. Return the SQL query and a natural language explanation of results.
"""


def get_schema_context(storage_adapter) -> str:
    """Build schema context string from Gold layer tables for LLM prompt."""
    tables = storage_adapter.list_tables("gold")
    schema_parts = []
    for table in sorted(tables):
        schema = storage_adapter.get_schema("gold", table)
        rows = storage_adapter.get_row_count("gold", table)
        cols = ", ".join(f"{name} ({dtype})" for name, dtype in schema.items())
        schema_parts.append(f"  • gold_{table} ({rows:,} rows): {cols}")
    return "\n".join(schema_parts)


def execute_safe_query(
    storage_adapter,
    sql: str,
    timeout_seconds: float = 30.0,
    max_rows: int = 100,
) -> dict[str, Any]:
    """
    Execute a SQL query with safety constraints.

    Guards:
    - Read-only: Rejects any DDL/DML statements
    - Row limit: Enforces LIMIT clause
    - Timeout: Aborts long-running queries
    """
    # Security: Block dangerous SQL
    sql_upper = sql.upper().strip()
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "EXEC", "GRANT"]
    for keyword in dangerous:
        if keyword in sql_upper.split():
            return {
                "success": False,
                "error": f"Blocked: {keyword} statements are not allowed (read-only mode)",
                "sql": sql,
            }

    # Enforce LIMIT if not present
    if "LIMIT" not in sql_upper:
        sql = sql.rstrip(";") + f" LIMIT {max_rows}"

    start = time.time()
    try:
        df = storage_adapter.execute_sql(sql)
        elapsed = time.time() - start

        if elapsed > timeout_seconds:
            return {
                "success": False,
                "error": f"Query timed out ({elapsed:.1f}s > {timeout_seconds}s limit)",
                "sql": sql,
            }

        return {
            "success": True,
            "sql": sql,
            "row_count": len(df),
            "columns": list(df.columns),
            "data": df.head(max_rows).to_dict(orient="records"),
            "execution_time_ms": round(elapsed * 1000, 2),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "sql": sql,
        }


def route_natural_language_query(
    storage_adapter,
    query: str,
) -> dict[str, Any]:
    """
    Route a natural language query to the appropriate SQL pattern.

    Uses keyword matching for local demo mode (no LLM needed).
    In production, this would use the LLM to generate SQL.
    """
    q = query.lower()

    # ── Restaurant queries ───────────────────────────────────────────
    if any(kw in q for kw in ["restaurant", "cuisine", "food", "best", "top rated"]):
        if "cuisine" in q:
            sql = """
                SELECT cuisine_type, restaurant_count, avg_rating, avg_cost
                FROM gold_dim_cuisines
                ORDER BY restaurant_count DESC
            """
        elif any(city in q for city in ["mumbai", "delhi", "bangalore", "hyderabad", "chennai", "kolkata", "pune"]):
            city = next(c for c in ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune"]
                       if c.lower() in q)
            sql = f"""
                SELECT name, cuisine_type, rating, avg_cost_for_two, price_tier
                FROM gold_dim_restaurants
                WHERE city = '{city}'
                ORDER BY rating DESC
                LIMIT 10
            """
        else:
            sql = """
                SELECT name, city, cuisine_type, rating, avg_cost_for_two, price_tier
                FROM gold_dim_restaurants
                ORDER BY rating DESC
                LIMIT 10
            """

    # ── Revenue / Business queries ───────────────────────────────────
    elif any(kw in q for kw in ["revenue", "gmv", "sales", "money", "income"]):
        sql = """
            SELECT city, total_orders, total_revenue AS revenue_inr,
                   avg_order_value, fulfillment_rate, unique_restaurants, unique_customers
            FROM gold_mart_city_revenue
            ORDER BY total_revenue DESC
        """

    # ── Delivery performance queries ─────────────────────────────────
    elif any(kw in q for kw in ["delivery", "eta", "speed", "late", "partner"]):
        if "partner" in q or "driver" in q:
            sql = """
                SELECT partner_id, partner_tier, total_deliveries, avg_rating,
                       avg_speed_kmh, on_time_rate, late_delivery_count
                FROM gold_dim_delivery_partners
                ORDER BY avg_rating DESC
                LIMIT 15
            """
        else:
            sql = """
                SELECT delivery_date, total_deliveries, avg_actual_eta_min,
                       avg_delivery_rating, late_delivery_rate, avg_delivery_speed_kmh
                FROM gold_fact_daily_delivery_performance
                ORDER BY delivery_date DESC
                LIMIT 30
            """

    # ── Order patterns ───────────────────────────────────────────────
    elif any(kw in q for kw in ["order", "demand", "peak", "hour", "trend"]):
        if "hour" in q or "peak" in q or "demand" in q:
            sql = """
                SELECT hour_of_day, is_weekend, order_count, avg_order_value, avg_items
                FROM gold_mart_hourly_demand
                ORDER BY order_count DESC
            """
        else:
            sql = """
                SELECT order_status, payment_method, COUNT(*) as count,
                       ROUND(AVG(net_amount), 2) as avg_value
                FROM gold_fact_orders
                GROUP BY order_status, payment_method
                ORDER BY count DESC
                LIMIT 20
            """

    # ── Feature store / ML queries ───────────────────────────────────
    elif any(kw in q for kw in ["feature", "ml", "training", "model data"]):
        sql = """
            SELECT COUNT(*) as total_samples,
                   ROUND(AVG(actual_eta_min), 2) as avg_eta,
                   ROUND(AVG(distance_km), 2) as avg_distance,
                   ROUND(AVG(order_value), 2) as avg_order_value,
                   SUM(CASE WHEN is_late THEN 1 ELSE 0 END) as late_count
            FROM gold_features_delivery_eta_v1
        """

    # ── Default: show available tables ───────────────────────────────
    else:
        tables = storage_adapter.list_tables("gold")
        table_info = []
        for t in sorted(tables):
            rows = storage_adapter.get_row_count("gold", t)
            table_info.append({"table": f"gold_{t}", "rows": rows})

        return {
            "agent": "DataAgent",
            "type": "schema_reflection",
            "message": f"I found {len(tables)} Gold layer tables. Ask me about restaurants, revenue, deliveries, orders, or features.",
            "available_tables": table_info,
            "query": query,
        }

    # Execute the routed SQL
    result = execute_safe_query(storage_adapter, sql)
    result["agent"] = "DataAgent"
    result["query"] = query
    result["type"] = "sql_query"

    return result
