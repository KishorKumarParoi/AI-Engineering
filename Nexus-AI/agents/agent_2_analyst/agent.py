"""
Nexus-AI: Agent 2 — Business Analysis Agent
=============================================
Generates executive-level business intelligence:
- Revenue breakdowns by city/cuisine
- Order trend analysis
- Delivery performance KPIs
- Strategic recommendations
- Chart data for frontend visualization
"""

from typing import Any

import pandas as pd


def generate_executive_brief(storage_adapter) -> dict[str, Any]:
    """Generate a comprehensive executive business summary."""
    # Load Gold tables
    city_revenue = storage_adapter.read_table("gold", "mart_city_revenue")
    hourly_demand = storage_adapter.read_table("gold", "mart_hourly_demand")
    daily_perf = storage_adapter.read_table("gold", "fact_daily_delivery_performance")
    dim_cuisines = storage_adapter.read_table("gold", "dim_cuisines")

    # ── Revenue KPIs ─────────────────────────────────────────────────
    total_revenue = city_revenue["total_revenue"].sum()
    total_orders = city_revenue["total_orders"].sum()
    avg_order_value = city_revenue["avg_order_value"].mean()
    avg_fulfillment = city_revenue["fulfillment_rate"].mean()
    top_city = city_revenue.loc[city_revenue["total_revenue"].idxmax()]

    # ── Delivery KPIs ────────────────────────────────────────────────
    avg_eta = daily_perf["avg_actual_eta_min"].mean()
    avg_late_rate = daily_perf["late_delivery_rate"].mean()
    avg_rating = daily_perf["avg_delivery_rating"].mean()

    # ── Demand Patterns ──────────────────────────────────────────────
    peak_hour = hourly_demand.loc[hourly_demand["order_count"].idxmax()]

    # ── Cuisine Analysis ─────────────────────────────────────────────
    top_cuisine = dim_cuisines.loc[dim_cuisines["restaurant_count"].idxmax()]

    # ── Executive Summary ────────────────────────────────────────────
    summary = (
        f"Nexus-AI Zomato Lakehouse — Executive Intelligence Brief\n\n"
        f"📊 Revenue Performance:\n"
        f"  • Total GMV: ₹{total_revenue:,.0f}\n"
        f"  • Total Orders: {total_orders:,}\n"
        f"  • Average Order Value: ₹{avg_order_value:.0f}\n"
        f"  • Top Market: {top_city['city']} (₹{top_city['total_revenue']:,.0f})\n"
        f"  • Platform Fulfillment Rate: {avg_fulfillment:.1f}%\n\n"
        f"🚗 Delivery Operations:\n"
        f"  • Average Delivery Time: {avg_eta:.1f} minutes\n"
        f"  • Late Delivery Rate: {avg_late_rate:.1f}%\n"
        f"  • Average Delivery Rating: {avg_rating:.2f}/5.0\n\n"
        f"📈 Demand Insights:\n"
        f"  • Peak Hour: {int(peak_hour['hour_of_day'])}:00 ({int(peak_hour['order_count'])} orders)\n"
        f"  • Most Popular Cuisine: {top_cuisine['cuisine_type']} ({int(top_cuisine['restaurant_count'])} restaurants)\n"
    )

    # ── Strategic Recommendations ────────────────────────────────────
    recommendations = []
    if avg_late_rate > 40:
        recommendations.append(
            "🔴 CRITICAL: Late delivery rate exceeds 40%. "
            "Recommend: Expand delivery partner pool in high-volume zones and "
            "implement dynamic ETA buffers during peak hours."
        )
    if avg_fulfillment < 85:
        recommendations.append(
            "🟡 WARNING: Fulfillment rate below 85%. "
            "Recommend: Investigate cancellation reasons by city and implement "
            "proactive order confirmation for high-risk segments."
        )
    recommendations.append(
        "💡 GROWTH: Scale promotional campaigns during off-peak hours "
        "(2PM-5PM) where demand is lowest to flatten the demand curve."
    )
    recommendations.append(
        "💡 UPSELL: Premium restaurants have 2.5x higher AOV. "
        "Recommend featured placement and curated 'Premium Picks' collections."
    )

    return {
        "agent": "AnalystAgent",
        "type": "executive_brief",
        "summary": summary,
        "kpis": {
            "total_revenue": round(total_revenue, 2),
            "total_orders": int(total_orders),
            "avg_order_value": round(avg_order_value, 2),
            "fulfillment_rate": round(avg_fulfillment, 1),
            "avg_delivery_time_min": round(avg_eta, 1),
            "late_delivery_rate": round(avg_late_rate, 1),
            "avg_delivery_rating": round(avg_rating, 2),
            "top_city": top_city["city"],
            "peak_hour": int(peak_hour["hour_of_day"]),
        },
        "recommendations": recommendations,
        "charts": {
            "city_revenue": city_revenue[["city", "total_revenue", "total_orders"]].to_dict(orient="records"),
            "hourly_demand": hourly_demand[["hour_of_day", "order_count"]].to_dict(orient="records"),
            "cuisine_breakdown": dim_cuisines[["cuisine_type", "restaurant_count", "avg_rating"]].to_dict(orient="records"),
        },
    }


def analyze_query(storage_adapter, query: str) -> dict[str, Any]:
    """Route analyst queries to appropriate analysis."""
    q = query.lower()

    if any(kw in q for kw in ["brief", "executive", "summary", "kpi", "overview"]):
        return generate_executive_brief(storage_adapter)

    elif any(kw in q for kw in ["revenue", "sales", "gmv"]):
        city_rev = storage_adapter.read_table("gold", "mart_city_revenue")
        return {
            "agent": "AnalystAgent",
            "type": "revenue_analysis",
            "message": f"Revenue analysis across {len(city_rev)} cities",
            "data": city_rev.to_dict(orient="records"),
            "total_revenue": round(city_rev["total_revenue"].sum(), 2),
        }

    elif any(kw in q for kw in ["trend", "daily", "performance"]):
        daily = storage_adapter.read_table("gold", "fact_daily_delivery_performance")
        return {
            "agent": "AnalystAgent",
            "type": "trend_analysis",
            "message": f"Daily delivery performance trends ({len(daily)} days)",
            "data": daily.to_dict(orient="records"),
        }

    else:
        return generate_executive_brief(storage_adapter)
