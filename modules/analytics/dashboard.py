"""
Analytics Dashboard Module
AI-Powered Civic Issue Reporting and Management System

Aggregates real-time SQLite metrics and generates interactive Plotly visualizations
for citizen and municipal administrator dashboards.
"""

import sqlite3
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from modules.database import get_connection

# Visual theme colors matching our civic-tech palette
STATUS_COLORS = {
    "Submitted": "#C49B59",
    "Under Review": "#657A62",
    "Approved": "#C49B59",
    "In Progress": "#C49B59",
    "Resolved": "#657A62",
    "Rejected": "#B87568",
}


def get_citizen_analytics_data(user_id: int) -> Dict[str, Any]:
    """
    Fetches real SQLite analytics data for the specified citizen.
    """
    data = {
        "total_complaints": 0,
        "status_distribution": [],
        "category_distribution": [],
        "monthly_trend": [],
        "resolution_rate": 0.0,
    }
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. Total & Status Distribution
            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM complaints
                WHERE user_id = ?
                GROUP BY status;
                """,
                (user_id,),
            )
            status_rows = [dict(r) for r in cursor.fetchall()]
            data["status_distribution"] = status_rows
            data["total_complaints"] = sum(r["count"] for r in status_rows)

            resolved_count = sum(r["count"] for r in status_rows if r["status"] == "Resolved")
            if data["total_complaints"] > 0:
                data["resolution_rate"] = round((resolved_count / data["total_complaints"]) * 100.0, 1)

            # 2. Category Distribution
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM complaints
                WHERE user_id = ?
                GROUP BY category
                ORDER BY count DESC;
                """,
                (user_id,),
            )
            data["category_distribution"] = [dict(r) for r in cursor.fetchall()]

            # 3. Monthly Trend
            cursor.execute(
                """
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
                FROM complaints
                WHERE user_id = ?
                GROUP BY month
                ORDER BY month ASC;
                """,
                (user_id,),
            )
            data["monthly_trend"] = [dict(r) for r in cursor.fetchall()]

        return data
    except sqlite3.Error:
        return data


def get_admin_analytics_data() -> Dict[str, Any]:
    """
    Fetches comprehensive city-wide analytics data from SQLite for administrators.
    """
    data = {
        "total_complaints": 0,
        "status_distribution": [],
        "category_distribution": [],
        "monthly_trend": [],
        "monthly_resolved_vs_received": [],
        "resolution_rate": 0.0,
        "top_categories": [],
        "top_locations": [],
        "ai_confidence_distribution": [],
        "total_citizens": 0,
        "total_duplicate_flags": 0,
        "pending_count": 0,
        "in_progress_count": 0,
        "resolved_count": 0,
        "recent_complaints": [],
    }
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. Status Distribution & Total
            cursor.execute("SELECT status, COUNT(*) as count FROM complaints WHERE is_archived = 0 AND is_withdrawn = 0 GROUP BY status;")
            status_rows = [dict(r) for r in cursor.fetchall()]
            data["status_distribution"] = status_rows
            data["total_complaints"] = sum(r["count"] for r in status_rows)

            resolved_count = sum(r["count"] for r in status_rows if r["status"] == "Resolved")
            data["resolved_count"] = resolved_count
            pending_count = sum(r["count"] for r in status_rows if r["status"] in ("Submitted", "Under Review"))
            data["pending_count"] = pending_count
            in_progress_count = sum(r["count"] for r in status_rows if r["status"] == "In Progress")
            data["in_progress_count"] = in_progress_count

            if data["total_complaints"] > 0:
                data["resolution_rate"] = round((resolved_count / data["total_complaints"]) * 100.0, 1)

            # 2. Category Distribution & Top Issues
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM complaints
                WHERE is_archived = 0 AND is_withdrawn = 0
                GROUP BY category
                ORDER BY count DESC;
                """
            )
            cat_rows = [dict(r) for r in cursor.fetchall()]
            data["category_distribution"] = cat_rows
            data["top_categories"] = cat_rows[:5]

            # 3. Top Reported Locations (by address text)
            cursor.execute(
                """
                SELECT location_address, COUNT(*) as count
                FROM complaints
                WHERE is_archived = 0 AND is_withdrawn = 0
                  AND location_address IS NOT NULL AND location_address != ''
                GROUP BY location_address
                ORDER BY count DESC
                LIMIT 10;
                """
            )
            data["top_locations"] = [dict(r) for r in cursor.fetchall()]

            # 4. Monthly Trend (Past 12 Months)
            cursor.execute(
                """
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
                FROM complaints
                WHERE is_archived = 0 AND is_withdrawn = 0
                GROUP BY month
                ORDER BY month ASC
                LIMIT 12;
                """
            )
            data["monthly_trend"] = [dict(r) for r in cursor.fetchall()]

            # 5. Monthly Resolved vs Received
            cursor.execute(
                """
                SELECT strftime('%Y-%m', created_at) as month,
                       COUNT(*) as received,
                       SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved
                FROM complaints
                WHERE is_archived = 0 AND is_withdrawn = 0
                GROUP BY month
                ORDER BY month ASC
                LIMIT 12;
                """
            )
            data["monthly_resolved_vs_received"] = [dict(r) for r in cursor.fetchall()]

            # 6. AI Confidence Distribution
            cursor.execute(
                """
                SELECT
                    CASE
                        WHEN ai_confidence IS NULL THEN 'No AI'
                        WHEN ai_confidence >= 0.8 THEN 'High (>=80%)'
                        WHEN ai_confidence >= 0.5 THEN 'Medium (50-79%)'
                        ELSE 'Low (<50%)'
                    END as confidence_band,
                    COUNT(*) as count
                FROM complaints
                WHERE is_archived = 0 AND is_withdrawn = 0
                GROUP BY confidence_band;
                """
            )
            data["ai_confidence_distribution"] = [dict(r) for r in cursor.fetchall()]

            # 7. Total Registered Citizens
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'citizen';")
            row = cursor.fetchone()
            if row:
                data["total_citizens"] = row[0]

            # 8. Duplicate Matches Count
            cursor.execute("SELECT COUNT(*) FROM duplicate_matches;")
            row_dup = cursor.fetchone()
            if row_dup:
                data["total_duplicate_flags"] = row_dup[0]

            # 9. Recent Complaints (last 10)
            cursor.execute(
                """
                SELECT c.id, c.title, c.category, c.status, c.location_address,
                       c.created_at, u.full_name AS citizen_name
                FROM complaints c
                JOIN users u ON c.user_id = u.id
                WHERE c.is_archived = 0 AND c.is_withdrawn = 0
                ORDER BY c.created_at DESC
                LIMIT 10;
                """
            )
            data["recent_complaints"] = [dict(r) for r in cursor.fetchall()]

        return data
    except sqlite3.Error:
        return data


def build_monthly_resolved_vs_received_chart(
    monthly_list: List[Dict[str, Any]], title: str = "Monthly Resolved vs Received"
) -> go.Figure:
    """Creates a grouped bar chart showing monthly resolved vs received complaints."""
    if not monthly_list:
        fig = go.Figure()
        fig.update_layout(title=title, annotations=[{"text": "No Data Available", "showarrow": False}])
        return fig

    df = pd.DataFrame(monthly_list)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Received",
        x=df["month"],
        y=df["received"],
        marker_color="#657A62",
    ))
    fig.add_trace(go.Bar(
        name="Resolved",
        x=df["month"],
        y=df["resolved"],
        marker_color="#718B69",
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#303A32")),
        barmode="group",
        xaxis=dict(title="Month"),
        yaxis=dict(title="Count", dtick=1),
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )
    return fig


def build_status_donut_chart(status_list: List[Dict[str, Any]], title: str = "Status Distribution"):
    """Creates a modern donut chart showing complaint status distribution."""
    if not status_list:
        fig = go.Figure()
        fig.update_layout(title=title, annotations=[{"text": "No Data Available", "showarrow": False}])
        return fig

    df = pd.DataFrame(status_list)
    colors = [STATUS_COLORS.get(s, "#CBD5E0") for s in df["status"]]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=df["status"],
                values=df["count"],
                hole=0.45,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                textinfo="label+percent",
                hoverinfo="label+value+percent",
            )
        ]
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#303A32")),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        height=320,
    )
    return fig


def build_category_bar_chart(category_list: List[Dict[str, Any]], title: str = "Issues by Category"):
    """Creates a horizontal bar chart ranking civic issue categories."""
    if not category_list:
        fig = go.Figure()
        fig.update_layout(title=title, annotations=[{"text": "No Data Available", "showarrow": False}])
        return fig

    df = pd.DataFrame(category_list)
    df = df.sort_values(by="count", ascending=True)

    fig = go.Figure(
        data=[
            go.Bar(
                x=df["count"],
                y=df["category"],
                orientation="h",
                marker=dict(
                    color="#657A62",
                    line=dict(color="#52674F", width=1),
                ),
                text=df["count"],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#303A32")),
        xaxis=dict(title="Complaint Count", dtick=1),
        yaxis=dict(title=""),
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    return fig


def build_monthly_trend_chart(monthly_list: List[Dict[str, Any]], title: str = "Monthly Complaint Inflow"):
    """Creates a line and area chart showing complaint trends over time."""
    if not monthly_list:
        fig = go.Figure()
        fig.update_layout(title=title, annotations=[{"text": "No Data Available", "showarrow": False}])
        return fig

    df = pd.DataFrame(monthly_list)

    fig = go.Figure(
        data=[
            go.Scatter(
                x=df["month"],
                y=df["count"],
                mode="lines+markers",
                fill="tozeroy",
                fillcolor="rgba(36, 91, 69, 0.15)",
                line=dict(color="#657A62", width=3),
                marker=dict(size=8, color="#52674F"),
            )
        ]
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#303A32")),
        xaxis=dict(title="Month (YYYY-MM)"),
        yaxis=dict(title="Reported Issues", dtick=1),
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    return fig

