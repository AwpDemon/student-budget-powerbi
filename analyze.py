"""
analyze.py — Student Budget Tracker Visualizations
Creates publication-quality charts mimicking a PowerBI dashboard layout.

Author: Ali Askari (github.com/awpdemon)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

# --- Style -------------------------------------------------------------------

sns.set_theme(style="whitegrid", font_scale=1.1)
PALETTE = sns.color_palette("muted", 10)
BG_COLOR = "#F7F7F8"
ACCENT = "#2B5797"
OVER_COLOR = "#E74C3C"
UNDER_COLOR = "#27AE60"

OUTPUT_DIR = Path("screenshots")
OUTPUT_DIR.mkdir(exist_ok=True)


def load_data() -> pd.DataFrame:
    df = pd.read_csv("data/student_spending.csv", parse_dates=["date"])
    df["month"] = df["date"].dt.to_period("M")
    df["month_label"] = df["date"].dt.strftime("%b %Y")
    return df


# --- Chart 1: Monthly Spending Trend ----------------------------------------

def chart_monthly_trend(df: pd.DataFrame) -> None:
    spent = df.groupby("month")["amount"].sum()
    # De-duplicate budget: one value per category per month
    budget = (
        df.drop_duplicates(subset=["category", "month"])
        .groupby("month")["budget_allocated"].sum()
    )
    monthly = pd.DataFrame({"spent": spent, "budget": budget}).reset_index()
    monthly["month_str"] = monthly["month"].astype(str)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    x = range(len(monthly))
    bars = ax.bar(x, monthly["spent"], color=ACCENT, width=0.6,
                  label="Actual Spending", zorder=3)
    ax.plot(x, monthly["budget"], color=OVER_COLOR, marker="o",
            linewidth=2.5, label="Budget Allocated", zorder=4)

    # Annotate bars
    for i, (bar, val) in enumerate(zip(bars, monthly["spent"])):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
                f"${val:,.0f}", ha="center", va="bottom", fontsize=9,
                fontweight="bold", color=ACCENT)

    ax.set_xticks(x)
    ax.set_xticklabels(monthly["month_str"], rotation=0)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_title("Monthly Spending vs Budget", fontsize=16, fontweight="bold",
                 pad=15)
    ax.set_ylabel("Amount (USD)")
    ax.legend(loc="upper left", frameon=True)
    ax.set_ylim(0, monthly[["spent", "budget"]].max().max() * 1.2)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "01_monthly_trend.png", dpi=150,
                bbox_inches="tight")
    plt.close()
    print("  -> 01_monthly_trend.png")


# --- Chart 2: Category Breakdown (Donut) ------------------------------------

def chart_category_donut(df: pd.DataFrame) -> None:
    cat_totals = df.groupby("category")["amount"].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor(BG_COLOR)

    wedges, texts, autotexts = ax.pie(
        cat_totals, labels=cat_totals.index, autopct="%1.1f%%",
        pctdistance=0.78, colors=PALETTE, startangle=140,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
    )
    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight("bold")
    for t in texts:
        t.set_fontsize(10)

    total = cat_totals.sum()
    ax.text(0, 0, f"${total:,.0f}\nTotal", ha="center", va="center",
            fontsize=18, fontweight="bold", color="#333")
    ax.set_title("Spending by Category", fontsize=16, fontweight="bold", pad=20)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "02_category_donut.png", dpi=150,
                bbox_inches="tight")
    plt.close()
    print("  -> 02_category_donut.png")


# --- Chart 3: Budget vs Actual by Category -----------------------------------

def chart_budget_vs_actual(df: pd.DataFrame) -> None:
    # Calculate total budget across all months per category
    months = df["month"].nunique()
    cat_budget = (
        df.drop_duplicates(subset=["category", "month"])
        .groupby("category")["budget_allocated"].sum()
    )
    cat_actual = df.groupby("category")["amount"].sum()

    compare = pd.DataFrame({"budget": cat_budget, "actual": cat_actual}).fillna(0)
    compare["variance"] = compare["actual"] - compare["budget"]
    compare = compare.sort_values("actual", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    y = range(len(compare))
    ax.barh(y, compare["budget"], height=0.4, label="Budget",
            color="#BDC3C7", zorder=3)
    colors = [OVER_COLOR if v > 0 else UNDER_COLOR for v in compare["variance"]]
    ax.barh([i + 0.4 for i in y], compare["actual"], height=0.4,
            label="Actual", color=colors, zorder=3)

    ax.set_yticks([i + 0.2 for i in y])
    ax.set_yticklabels(compare.index)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_title("Budget vs Actual by Category (6-Month Total)",
                 fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Amount (USD)")

    # Custom legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#BDC3C7", label="Budget"),
        Patch(facecolor=UNDER_COLOR, label="Under Budget"),
        Patch(facecolor=OVER_COLOR, label="Over Budget"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", frameon=True)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "03_budget_vs_actual.png", dpi=150,
                bbox_inches="tight")
    plt.close()
    print("  -> 03_budget_vs_actual.png")


# --- Chart 4: Spending Heatmap (Day of Week x Category) ---------------------

def chart_spending_heatmap(df: pd.DataFrame) -> None:
    df["dow"] = df["date"].dt.day_name()
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]

    pivot = df.pivot_table(
        values="amount", index="category", columns="dow",
        aggfunc="mean", fill_value=0,
    )[dow_order]

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor(BG_COLOR)

    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlOrRd",
                linewidths=1, linecolor="white", ax=ax,
                cbar_kws={"label": "Avg Transaction ($)"})

    ax.set_title("Average Spending by Category & Day of Week",
                 fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Day of Week")
    ax.set_ylabel("")
    plt.xticks(rotation=30, ha="right")

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "04_spending_heatmap.png", dpi=150,
                bbox_inches="tight")
    plt.close()
    print("  -> 04_spending_heatmap.png")


# --- Chart 5: Monthly Burn Rate & Forecast -----------------------------------

def chart_burn_rate(df: pd.DataFrame) -> None:
    monthly = df.groupby("month")["amount"].sum().reset_index()
    monthly["month_num"] = range(len(monthly))
    monthly["month_str"] = monthly["month"].astype(str)

    # Linear regression for trend forecast
    x = monthly["month_num"].values
    y = monthly["amount"].values
    coeffs = np.polyfit(x, y, 1)
    trend_line = np.polyval(coeffs, x)

    # Forecast 2 more months
    future_x = np.array([len(x), len(x) + 1])
    future_y = np.polyval(coeffs, future_x)
    future_labels = ["Jan 2026", "Feb 2026"]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    ax.plot(x, y, "o-", color=ACCENT, linewidth=2.5, markersize=8,
            label="Monthly Spend", zorder=4)
    ax.plot(x, trend_line, "--", color="#999", linewidth=1.5,
            label="Trend Line", zorder=3)
    ax.plot(future_x, future_y, "s--", color=OVER_COLOR, markersize=8,
            linewidth=2, label="Forecast", zorder=4)

    all_labels = list(monthly["month_str"]) + future_labels
    ax.set_xticks(list(x) + list(future_x))
    ax.set_xticklabels(all_labels, rotation=0)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))

    # Shade forecast region
    ax.axvspan(len(x) - 0.5, len(x) + 1.5, alpha=0.08, color=OVER_COLOR)
    ax.text(len(x) + 0.5, max(y) * 1.05, "Forecast", ha="center",
            fontsize=10, color=OVER_COLOR, fontstyle="italic")

    slope_pct = (coeffs[0] / y[0]) * 100
    direction = "+" if coeffs[0] > 0 else ""
    ax.set_title(f"Monthly Burn Rate & 2-Month Forecast "
                 f"({direction}${coeffs[0]:,.0f}/mo)",
                 fontsize=16, fontweight="bold", pad=15)
    ax.set_ylabel("Total Spent (USD)")
    ax.legend(loc="upper left", frameon=True)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "05_burn_rate.png", dpi=150,
                bbox_inches="tight")
    plt.close()
    print("  -> 05_burn_rate.png")


# --- Chart 6: Payment Method Distribution ------------------------------------

def chart_payment_methods(df: pd.DataFrame) -> None:
    pay_totals = df.groupby("payment_method")["amount"].agg(["sum", "count"])
    pay_totals = pay_totals.sort_values("sum", ascending=False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor(BG_COLOR)

    # By total amount
    bars1 = ax1.bar(range(len(pay_totals)), pay_totals["sum"],
                    color=PALETTE[:len(pay_totals)], zorder=3)
    ax1.set_xticks(range(len(pay_totals)))
    ax1.set_xticklabels(pay_totals.index, rotation=20, ha="right")
    ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax1.set_title("Total Amount by Payment Method", fontsize=13,
                  fontweight="bold")
    ax1.set_facecolor(BG_COLOR)
    for bar, val in zip(bars1, pay_totals["sum"]):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20,
                 f"${val:,.0f}", ha="center", va="bottom", fontsize=9)

    # By transaction count
    bars2 = ax2.bar(range(len(pay_totals)), pay_totals["count"],
                    color=PALETTE[:len(pay_totals)], zorder=3)
    ax2.set_xticks(range(len(pay_totals)))
    ax2.set_xticklabels(pay_totals.index, rotation=20, ha="right")
    ax2.set_title("Transaction Count by Payment Method", fontsize=13,
                  fontweight="bold")
    ax2.set_facecolor(BG_COLOR)
    for bar, val in zip(bars2, pay_totals["count"]):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                 f"{int(val)}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "06_payment_methods.png", dpi=150,
                bbox_inches="tight")
    plt.close()
    print("  -> 06_payment_methods.png")


# --- Chart 7: Top Vendors Treemap-Style Bar ----------------------------------

def chart_top_vendors(df: pd.DataFrame) -> None:
    vendor_totals = (
        df.groupby("vendor")["amount"]
        .agg(["sum", "count"])
        .sort_values("sum", ascending=True)
        .tail(12)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    colors = sns.color_palette("viridis", len(vendor_totals))
    bars = ax.barh(range(len(vendor_totals)), vendor_totals["sum"],
                   color=colors, zorder=3)

    ax.set_yticks(range(len(vendor_totals)))
    ax.set_yticklabels(vendor_totals.index)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_title("Top 12 Vendors by Total Spending",
                 fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Total Spent (USD)")

    for bar, (_, row) in zip(bars, vendor_totals.iterrows()):
        ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height() / 2,
                f"${row['sum']:,.0f} ({int(row['count'])} txns)",
                va="center", fontsize=9)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "07_top_vendors.png", dpi=150,
                bbox_inches="tight")
    plt.close()
    print("  -> 07_top_vendors.png")


# --- Main --------------------------------------------------------------------

def main():
    print("Loading data...")
    df = load_data()
    print(f"  {len(df)} transactions loaded\n")

    print("Generating visualizations:")
    chart_monthly_trend(df)
    chart_category_donut(df)
    chart_budget_vs_actual(df)
    chart_spending_heatmap(df)
    chart_burn_rate(df)
    chart_payment_methods(df)
    chart_top_vendors(df)

    print(f"\nAll charts saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
