# Student Budget Tracker — Power BI

I wanted to learn Power BI and DAX, so I built a dashboard around something I actually care about — where my money goes as a college student.

## What it does

Tracks spending across categories (food, rent, transport, entertainment, etc.) over 6 months and visualizes trends, category breakdowns, and monthly comparisons.

## What's in here

- `data/` — transaction dataset (synthetic — generated with `generate_data.py` since I wasn't about to upload my real bank statements)
- `dax_measures.md` — the 11 DAX measures I wrote, with explanations for each
- `analyze.py` — Python companion analysis (pandas, matplotlib, seaborn)
- `screenshots/` — dashboard screenshots

## DAX measures I built

Wrote 11 custom measures including running totals, month-over-month change, category percentages, and conditional formatting logic. See `dax_measures.md` for the full list with explanations.

## What I learned

- Power BI data modeling (relationships, star schema)
- DAX from scratch — calculated columns vs measures, CALCULATE, SUMX, time intelligence
- When to use Python for analysis vs when Power BI handles it natively
- Dashboard layout — making something that actually answers a question at a glance

## Tech

Power BI Desktop, DAX, Python (pandas, matplotlib, seaborn)
