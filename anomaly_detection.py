"""
anomaly_detection.py — flag unusual transactions worth a second look.

Two detectors layered:

  1. Per-category z-score on amount. If a single transaction is more than
     2.5σ above the category's non-fixed-cost mean, flag it. This catches
     "you normally spend $8 at Chipotle, this one was $67" outliers.

  2. Daily-total z-score on a 14-day rolling baseline. If a day's total
     spend is more than 2σ above its trailing mean, flag it. This catches
     cluster days ("you spent $185 last Saturday") that wouldn't trigger
     on any single transaction.

Fixed-cost categories (Rent, Utilities, Subscriptions) are excluded from
detector 1 because their variance is by design near-zero and any single
month would register as an "anomaly."
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

sns.set_theme(style="whitegrid", font_scale=1.05)
OUT = Path("screenshots")
OUT.mkdir(exist_ok=True)

FIXED_COST = {"Rent", "Utilities", "Subscriptions"}
TXN_THRESHOLD = 2.5   # sigma
DAILY_THRESHOLD = 2.0
WINDOW = 14


def detect_transaction_anomalies(df):
    working = df[~df["category"].isin(FIXED_COST)].copy()
    stats_ = working.groupby("category")["amount"].agg(["mean", "std"]).rename(
        columns={"mean": "cat_mean", "std": "cat_std"}
    )
    working = working.join(stats_, on="category")
    working["z"] = (working["amount"] - working["cat_mean"]) / working["cat_std"].replace(0, np.nan)
    flagged = working[working["z"] > TXN_THRESHOLD].sort_values("z", ascending=False)
    return flagged[["date", "category", "vendor", "amount", "cat_mean", "z"]]


def detect_daily_anomalies(df):
    df = df[~df["category"].isin(FIXED_COST)]
    daily = df.groupby(df["date"].dt.date)["amount"].sum().sort_index()
    daily.index = pd.to_datetime(daily.index)
    roll_mean = daily.rolling(WINDOW, min_periods=5).mean().shift(1)
    roll_std = daily.rolling(WINDOW, min_periods=5).std().shift(1)
    z = (daily - roll_mean) / roll_std.replace(0, np.nan)
    out = pd.DataFrame({"date": daily.index, "amount": daily.values, "roll_mean": roll_mean.values, "z": z.values})
    flagged = out[out["z"] > DAILY_THRESHOLD].dropna().sort_values("z", ascending=False)
    return out, flagged


def plot_anomalies(daily_all, daily_flag, txn_flag):
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [1.4, 1]})
    ax = axes[0]
    ax.plot(daily_all["date"], daily_all["amount"], lw=1, color="#7f8c8d", label="Daily spend")
    ax.plot(daily_all["date"], daily_all["roll_mean"], lw=1.8, color="#2B5797", label=f"{WINDOW}-day rolling mean")
    ax.scatter(daily_flag["date"], daily_flag["amount"], color="#e74c3c", s=65, zorder=5, label=f"Flagged day (z>{DAILY_THRESHOLD})")
    for _, r in daily_flag.iterrows():
        ax.annotate(f"${r['amount']:.0f}\nz={r['z']:.1f}",
                    xy=(r["date"], r["amount"]),
                    xytext=(8, 8), textcoords="offset points", fontsize=8)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_title("Daily-total anomaly detector", fontweight="bold")
    ax.legend(loc="upper right")

    ax = axes[1]
    if len(txn_flag):
        labels = [f"{r.vendor[:16]}  {r.date.strftime('%m/%d')}" for r in txn_flag.itertuples()]
        colors = sns.color_palette("Reds_r", len(labels))
        ax.barh(labels, txn_flag["amount"], color=colors)
        for i, (amt, z) in enumerate(zip(txn_flag["amount"], txn_flag["z"])):
            ax.text(amt + 0.5, i, f"${amt:.0f}  z={z:.1f}", va="center", fontsize=8)
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
        ax.set_title(f"Flagged transactions (z > {TXN_THRESHOLD}σ within category)", fontweight="bold")
    else:
        ax.text(0.5, 0.5, "No transaction-level anomalies flagged", ha="center", va="center")
        ax.axis("off")

    plt.tight_layout()
    fig.savefig(OUT / "08_anomalies.png", dpi=150, bbox_inches="tight")
    plt.close()


def main():
    df = pd.read_csv("data/student_spending.csv", parse_dates=["date"])
    txn_flag = detect_transaction_anomalies(df)
    daily_all, daily_flag = detect_daily_anomalies(df)

    print("=" * 70)
    print(f"  ANOMALIES — txn-level (z>{TXN_THRESHOLD}σ, non-fixed-cost)")
    print("=" * 70)
    for r in txn_flag.itertuples():
        print(f"   {r.date.strftime('%Y-%m-%d')}  {r.category:<14}  {r.vendor[:22]:<22}  ${r.amount:>7.2f}   z={r.z:.2f}  (cat mean ${r.cat_mean:.2f})")
    print()
    print("=" * 70)
    print(f"  ANOMALIES — daily-total (z>{DAILY_THRESHOLD}σ, 14-day rolling)")
    print("=" * 70)
    for r in daily_flag.itertuples():
        print(f"   {r.date.strftime('%Y-%m-%d')}   daily ${r.amount:>7.2f}   vs baseline ${r.roll_mean:.2f}   z={r.z:.2f}")
    print()

    plot_anomalies(daily_all, daily_flag, txn_flag.head(10))
    print(f"  Chart → {OUT}/08_anomalies.png")


if __name__ == "__main__":
    main()
