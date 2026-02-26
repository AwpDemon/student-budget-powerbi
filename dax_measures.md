# DAX Measures — Student Budget Tracker Dashboard

All measures are designed for a PowerBI data model with a single fact table `student_spending` and a date table generated via `CALENDARAUTO()`.

---

## 1. Total Spending

Aggregates all transaction amounts for the current filter context.

```dax
Total Spending =
    SUM(student_spending[amount])
```

---

## 2. Monthly Burn Rate

Calculates average monthly expenditure across all months in the filtered period. Used in the KPI card and burn rate trend chart.

```dax
Monthly Burn Rate =
    DIVIDE(
        [Total Spending],
        DISTINCTCOUNT(student_spending[date].[MonthNo]),
        0
    )
```

---

## 3. Budget Allocated (Total)

Sums the budget column, de-duplicated per category per month to avoid inflating from multiple transactions.

```dax
Budget Allocated =
    SUMX(
        SUMMARIZE(
            student_spending,
            student_spending[category],
            student_spending[date].[MonthNo],
            "MonthBudget", MAX(student_spending[budget_allocated])
        ),
        [MonthBudget]
    )
```

---

## 4. Budget Variance

Shows how much the student is over or under budget. Negative values indicate under-budget (good), positive values indicate overspending.

```dax
Budget Variance =
    [Total Spending] - [Budget Allocated]
```

---

## 5. Budget Variance %

Percentage deviation from budget. Displayed as a conditional-formatted KPI.

```dax
Budget Variance % =
    DIVIDE(
        [Budget Variance],
        [Budget Allocated],
        0
    )
```

---

## 6. Month-over-Month Change

Compares current month spending to the previous month. Powers the MoM trend indicator arrow on the dashboard.

```dax
MoM Spending Change =
    VAR CurrentMonth = [Total Spending]
    VAR PreviousMonth =
        CALCULATE(
            [Total Spending],
            DATEADD('Date'[Date], -1, MONTH)
        )
    RETURN
        DIVIDE(
            CurrentMonth - PreviousMonth,
            PreviousMonth,
            0
        )
```

---

## 7. Running Total (Cumulative Spend)

Running sum of spending within the selected period. Used in the area chart overlay on the monthly trend visual.

```dax
Cumulative Spending =
    CALCULATE(
        [Total Spending],
        FILTER(
            ALL('Date'[Date]),
            'Date'[Date] <= MAX('Date'[Date])
        )
    )
```

---

## 8. Category Share %

Percentage each category contributes to total spending. Drives the donut chart labels.

```dax
Category Share % =
    DIVIDE(
        [Total Spending],
        CALCULATE(
            [Total Spending],
            ALL(student_spending[category])
        ),
        0
    )
```

---

## 9. Average Transaction Size

Mean transaction value, filterable by category, vendor, or payment method.

```dax
Avg Transaction =
    AVERAGE(student_spending[amount])
```

---

## 10. Spending Forecast (Linear)

Two-month forward forecast using a simple linear extrapolation of monthly totals. Used in the burn rate chart's forecast region.

```dax
Spending Forecast =
    VAR MonthlyData =
        SUMMARIZE(
            student_spending,
            student_spending[date].[Year],
            student_spending[date].[MonthNo],
            "MonthTotal", [Total Spending]
        )
    VAR AvgSpend = AVERAGEX(MonthlyData, [MonthTotal])
    VAR MonthCount = COUNTROWS(MonthlyData)
    VAR LastMonth = MAXX(MonthlyData, [MonthTotal])
    VAR Slope =
        DIVIDE(LastMonth - MINX(MonthlyData, [MonthTotal]), MonthCount - 1, 0)
    RETURN
        LastMonth + Slope
```

---

## 11. Days Until Budget Exceeded

Estimates how many days into the current month the student can spend at their current daily rate before exceeding the monthly budget. Displayed as a gauge visual.

```dax
Days Until Budget Exceeded =
    VAR DailyRate =
        DIVIDE(
            [Total Spending],
            DISTINCTCOUNT(student_spending[date]),
            0
        )
    VAR RemainingBudget = [Budget Allocated] - [Total Spending]
    RETURN
        IF(
            RemainingBudget > 0,
            DIVIDE(RemainingBudget, DailyRate, 0),
            0
        )
```

---

## Usage Notes

- **Date Table:** Create a date table with `'Date' = CALENDARAUTO()` and mark it as the date table in the model.
- **Relationships:** Link `student_spending[date]` to `'Date'[Date]` (many-to-one).
- **Formatting:** Apply currency format (`$#,##0.00`) to all monetary measures and percentage format (`0.0%`) to variance and share measures.
- **Conditional Formatting:** Apply red/green color rules to `Budget Variance` and `MoM Spending Change` for at-a-glance status.
