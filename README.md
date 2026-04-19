![Monthly spending trend](screenshots/01_monthly_trend.png)
*Monthly spending vs. budget across a 6-month window, with MoM variance arrows.*

# Student Budget Tracker — Power BI

Built this to learn Power BI + DAX. Tracks spending across categories (rent, food, transport, entertainment) over 6 months and pulls out the patterns I wouldn't otherwise notice — which categories blow through budget, which days of the week are expensive, where I'm actually spending vs. where I *think* I'm spending.

## Dashboard pages

![Category breakdown and budget vs actual](screenshots/03_budget_vs_actual.png)

The budget-vs-actual view was the one that changed my behavior the most — "Food Delivery" turned out to be ~2x what I had mentally budgeted. The conditional formatting flags any category more than 10% over budget.

![Weekday spending heatmap](screenshots/04_spending_heatmap.png)

Heatmap of spending by day-of-week × category. Friday and Saturday dominate, mostly driven by food and entertainment categories.

## DAX

Wrote 11 custom measures — total spending, monthly burn rate, budget allocated (with SUMMARIZE to dedupe per category), budget variance %, month-over-month change with DATEADD, running totals with DATESYTD, a days-remaining calculation for the burn rate projection. Full list with code and commentary in [`dax_measures.md`](dax_measures.md).

The one that took me the longest was Budget Allocated — the naïve `SUM(budget_allocated)` double-counts because each transaction row carries the monthly budget. Fix was a SUMX over a SUMMARIZE that deduplicates per category per month. Classic DAX gotcha.

## Data

`generate_data.py` produces a synthetic `student_spending.csv` (~6 months of realistic-ish transactions across 8 categories, 4 payment methods, 20-ish vendors). I wasn't going to upload my real bank statements. `analyze.py` is a Python companion that reproduces the core charts in pandas/seaborn for anyone who doesn't have Power BI Desktop.

## Stack

Power BI Desktop, DAX, Python (pandas, matplotlib, seaborn).

## Run

Open `student_budget.pbix` in Power BI Desktop. Or:

```bash
python generate_data.py
python analyze.py
```

See `screenshots/` for the remaining dashboard pages (payment method breakdown, top vendors, category donut, burn rate projection).
