"""
generate_data.py — Synthetic Student Spending Data Generator
Produces ~500 realistic transactions over 6 months for PowerBI analysis.

Author: Ali Askari (github.com/awpdemon)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

SEED = 42
np.random.seed(SEED)

# --- Configuration -----------------------------------------------------------

START_DATE = datetime(2025, 7, 1)
END_DATE = datetime(2025, 12, 31)
MONTHLY_BUDGET = 2200  # total monthly budget in USD

CATEGORIES = {
    # category: (monthly_budget, avg_transaction, std_dev, freq_per_month)
    "Rent":           (850, 850, 0,    1),
    "Groceries":      (280, 18,  7,   18),
    "Dining Out":     (120, 10,  5,   16),
    "Transportation": (90,  7,   3,   16),
    "Textbooks":      (60,  30,  12,   3),
    "Entertainment":  (80,  10,  5,   12),
    "Utilities":      (100, 100, 15,   1),
    "Subscriptions":  (45,  15,  0,    3),
    "Health":         (60,  15,  8,    6),
    "Clothing":       (50,  25,  10,   4),
}

PAYMENT_METHODS = ["Debit Card", "Credit Card", "Cash", "Venmo", "Apple Pay"]
PAYMENT_WEIGHTS = [0.35, 0.25, 0.15, 0.15, 0.10]

VENDORS = {
    "Rent":           ["Campus Housing Office"],
    "Groceries":      ["Trader Joe's", "Walmart", "Aldi", "Costco", "Safeway"],
    "Dining Out":     ["Chipotle", "Starbucks", "Campus Cafe", "Panera",
                       "Pizza Hut", "Subway", "Thai Express", "Chick-fil-A"],
    "Transportation": ["Uber", "Lyft", "Metro Card", "Gas Station", "Parking Meter"],
    "Textbooks":      ["Amazon", "Campus Bookstore", "Chegg", "eBay"],
    "Entertainment":  ["AMC Theaters", "Spotify", "Steam", "Netflix", "Bowling Alley",
                       "Concert Tickets"],
    "Utilities":      ["Electric Co.", "Internet Provider", "Water Utility"],
    "Subscriptions":  ["Netflix", "Spotify", "iCloud", "ChatGPT Plus", "Adobe CC"],
    "Health":         ["CVS Pharmacy", "Campus Health Center", "GNC", "Walgreens"],
    "Clothing":       ["Uniqlo", "H&M", "Nike", "Amazon", "Goodwill"],
}

# --- Data Generation ---------------------------------------------------------


def generate_transactions() -> pd.DataFrame:
    """Generate realistic student spending transactions."""
    records = []
    current = START_DATE

    while current <= END_DATE:
        month_start = current.replace(day=1)
        days_in_month = (
            (month_start + timedelta(days=32)).replace(day=1) - month_start
        ).days

        for category, (budget, avg, std, freq) in CATEGORIES.items():
            # Vary frequency slightly each month
            actual_freq = max(1, int(np.random.normal(freq, max(1, freq * 0.2))))

            # Seasonal adjustments
            month_num = current.month
            multiplier = 1.0
            if category == "Dining Out" and month_num in (11, 12):
                multiplier = 1.3  # holiday spending
            elif category == "Textbooks" and month_num in (8, 9):
                multiplier = 2.5  # semester start
            elif category == "Entertainment" and month_num in (7, 8):
                multiplier = 1.4  # summer break
            elif category == "Clothing" and month_num in (11, 12):
                multiplier = 1.5  # holiday shopping
            elif category == "Textbooks" and month_num in (11, 12):
                multiplier = 0.2  # no books mid-semester

            for _ in range(actual_freq):
                day = np.random.randint(1, days_in_month + 1)
                tx_date = month_start.replace(day=day)

                if std == 0:
                    amount = avg * multiplier
                else:
                    amount = max(3.0, np.random.normal(avg * multiplier, std))

                amount = round(amount, 2)

                vendor = np.random.choice(VENDORS[category])
                payment = np.random.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)

                records.append({
                    "date": tx_date.strftime("%Y-%m-%d"),
                    "category": category,
                    "vendor": vendor,
                    "amount": amount,
                    "payment_method": payment,
                    "budget_allocated": budget,
                })

        # Advance to next month
        next_month = (current.month % 12) + 1
        next_year = current.year + (1 if next_month == 1 else 0)
        current = current.replace(year=next_year, month=next_month, day=1)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["transaction_id"] = [f"TXN-{i+1:04d}" for i in range(len(df))]

    # Reorder columns
    df = df[["transaction_id", "date", "category", "vendor",
             "amount", "payment_method", "budget_allocated"]]

    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print dataset summary statistics."""
    print(f"Total transactions: {len(df)}")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"Total spent: ${df['amount'].sum():,.2f}")
    print(f"Average transaction: ${df['amount'].mean():,.2f}")
    print(f"\nTransactions per category:")
    summary = (
        df.groupby("category")["amount"]
        .agg(["count", "sum", "mean"])
        .rename(columns={"count": "txns", "sum": "total", "mean": "avg"})
        .sort_values("total", ascending=False)
    )
    for cat, row in summary.iterrows():
        print(f"  {cat:<18s}  {int(row['txns']):>3d} txns  "
              f"${row['total']:>8,.2f} total  ${row['avg']:>6,.2f} avg")


# --- Main --------------------------------------------------------------------

if __name__ == "__main__":
    df = generate_transactions()
    output_path = "data/student_spending.csv"
    df.to_csv(output_path, index=False)
    print(f"Dataset saved to {output_path}\n")
    print_summary(df)
