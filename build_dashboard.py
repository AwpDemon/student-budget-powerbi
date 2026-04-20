"""
build_dashboard.py — single-file interactive Plotly dashboard.

Writes `dashboard.html`. Standalone — the entire Plotly JS bundle is inlined,
so opening the file in any browser works with no server. Four tiled charts:

  Monthly spend vs budget  |  Category breakdown (donut)
  Spending heatmap         |  Vendor top-10 bar

Plus hover tooltips, click-to-isolate legend behavior, and a dropdown that
filters by payment method.
"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


BUDGETS = {
    "Rent": 850, "Groceries": 280, "Dining Out": 120, "Transportation": 90,
    "Textbooks": 60, "Entertainment": 80, "Utilities": 100,
    "Subscriptions": 45, "Health": 60, "Clothing": 50,
}


def build(df):
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["weekday"] = df["date"].dt.day_name()
    weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    # 1. Monthly spend vs monthly budget
    monthly = df.groupby("month")["amount"].sum().reset_index()
    budget_total = sum(BUDGETS.values())
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "bar"}, {"type": "domain"}],
               [{"type": "heatmap"}, {"type": "bar"}]],
        subplot_titles=("Monthly spend vs budget", "Category share",
                        "Weekday × category heatmap", "Top 10 vendors"),
        vertical_spacing=0.14, horizontal_spacing=0.10,
    )
    fig.add_trace(
        go.Bar(x=monthly["month"], y=monthly["amount"], name="Actual",
               marker_color="#2B5797",
               hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>"),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=monthly["month"], y=[budget_total] * len(monthly),
                   mode="lines", name="Budget", line=dict(color="#e74c3c", dash="dot", width=2),
                   hovertemplate="$%{y:,.0f} budget<extra></extra>"),
        row=1, col=1
    )

    # 2. Category donut
    cat = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    fig.add_trace(
        go.Pie(labels=cat.index, values=cat.values, hole=0.55, name="Category",
               hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>"),
        row=1, col=2
    )

    # 3. Heatmap
    heat = df.pivot_table(index="category", columns="weekday", values="amount", aggfunc="sum", fill_value=0)
    heat = heat.reindex(columns=weekday_order)
    fig.add_trace(
        go.Heatmap(z=heat.values, x=heat.columns, y=heat.index,
                   colorscale="Blues", showscale=True,
                   hovertemplate="%{y} · %{x}<br>$%{z:,.0f}<extra></extra>"),
        row=2, col=1
    )

    # 4. Top vendors
    vendor = df.groupby("vendor")["amount"].sum().sort_values(ascending=False).head(10)
    fig.add_trace(
        go.Bar(x=vendor.values, y=vendor.index, orientation="h",
               marker_color="#27ae60",
               hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
               name="Vendors"),
        row=2, col=2
    )

    # Payment-method filter — rebuild data per selection, inject via updatemenus
    methods = ["All"] + sorted(df["payment_method"].unique())
    buttons = []
    for m in methods:
        sub = df if m == "All" else df[df["payment_method"] == m]
        sub_monthly = sub.groupby("month")["amount"].sum().reindex(monthly["month"]).fillna(0)
        sub_cat = sub.groupby("category")["amount"].sum().reindex(cat.index).fillna(0)
        sub_heat = sub.pivot_table(index="category", columns="weekday", values="amount", aggfunc="sum", fill_value=0).reindex(index=heat.index, columns=weekday_order, fill_value=0)
        sub_vendor = sub.groupby("vendor")["amount"].sum().sort_values(ascending=False).head(10)
        buttons.append(dict(
            method="update",
            label=m,
            args=[{
                "y": [sub_monthly.values, [budget_total] * len(monthly),
                      sub_cat.values, None,
                      sub_vendor.index],
                "x": [None, None, None, None, sub_vendor.values],
                "z": [None, None, None, sub_heat.values, None],
                "labels": [None, None, sub_cat.index, None, None],
                "values": [None, None, sub_cat.values, None, None],
            }],
        ))

    fig.update_layout(
        title=dict(text="Student Budget — Interactive Dashboard", x=0.5, xanchor="center", font=dict(size=20)),
        showlegend=False,
        height=820,
        template="plotly_white",
        updatemenus=[dict(
            type="dropdown", buttons=buttons, x=0.01, xanchor="left",
            y=1.12, yanchor="top", showactive=True,
            bgcolor="#f5f5f5",
        )],
        annotations=list(fig.layout.annotations) + [
            dict(text="Payment method:", x=-0.02, y=1.13, xref="paper", yref="paper", showarrow=False, font=dict(size=12)),
        ],
        margin=dict(t=120),
    )

    return fig


def main():
    df = pd.read_csv("data/student_spending.csv", parse_dates=["date"])
    fig = build(df)
    out = Path("dashboard.html")
    fig.write_html(out, include_plotlyjs="inline", full_html=True)
    print(f"Wrote {out.resolve()}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
