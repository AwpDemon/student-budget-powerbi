"""
forecast.py — project the next 3 months of spending per category with
prediction intervals.

n is tiny (6 months of history), so anything fancier than a very
conservative model would be overfit. The pipeline:

  1. For each category, decompose into (fixed_cost, variable_cost).
     Fixed costs get forecast as "same as last month."

  2. For variable categories, fit an exponential-smoothing model with
     an additive trend, no seasonality (seasonality needs ≥2 cycles,
     we have ~0.5). Using Holt's linear trend variant.

  3. The prediction interval is bootstrapped from the in-sample one-
     step-ahead residuals — empirical, not Gaussian, because n=6.

  4. Aggregate per-category forecasts back up to a total projection
     with summed intervals (approximate; residual covariance is ignored
     but the data is categorical so it's a reasonable simplification).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

sns.set_theme(style="whitegrid", font_scale=1.05)
OUT = Path("screenshots")
OUT.mkdir(exist_ok=True)

HORIZON = 3
N_BOOT = 2000
RNG = np.random.default_rng(31)

FIXED_COST = {"Rent", "Utilities", "Subscriptions"}


def load_monthly(df):
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    monthly = df.pivot_table(index="month", columns="category", values="amount", aggfunc="sum").fillna(0)
    return monthly


def forecast_category(series, name):
    """Return point forecast and bootstrap 80% PI for `HORIZON` months."""
    if name in FIXED_COST or series.nunique() <= 2:
        point = np.repeat(series.iloc[-1], HORIZON)
        lo = hi = point.copy()
        return point, lo, hi

    try:
        model = ExponentialSmoothing(series, trend="add", seasonal=None, initialization_method="estimated").fit(optimized=True)
    except Exception:
        model = SimpleExpSmoothing(series, initialization_method="estimated").fit(optimized=True)

    fitted = model.fittedvalues
    resid = (series - fitted).values[1:]  # drop initial
    point = model.forecast(HORIZON).values

    # Bootstrap the horizon by sampling residuals with replacement
    draws = np.empty((N_BOOT, HORIZON))
    for b in range(N_BOOT):
        shocks = RNG.choice(resid, size=HORIZON, replace=True)
        draws[b] = np.maximum(0, point + shocks)
    lo = np.quantile(draws, 0.10, axis=0)
    hi = np.quantile(draws, 0.90, axis=0)
    return np.maximum(0, point), lo, hi


def main():
    df = pd.read_csv("data/student_spending.csv", parse_dates=["date"])
    monthly = load_monthly(df)
    last_date = monthly.index.max()
    forecast_idx = pd.date_range(last_date + pd.offsets.MonthBegin(1), periods=HORIZON, freq="MS")

    cat_forecasts, cat_lo, cat_hi = {}, {}, {}
    for cat in monthly.columns:
        p, l, h = forecast_category(monthly[cat], cat)
        cat_forecasts[cat] = p
        cat_lo[cat] = l
        cat_hi[cat] = h

    total_point = sum(cat_forecasts.values())
    total_lo = sum(cat_lo.values())
    total_hi = sum(cat_hi.values())

    print("=" * 70)
    print(f"  FORECAST — next {HORIZON} months, 80% prediction interval")
    print("=" * 70)
    print(f"  {'Month':<10}  {'Point':>10}  {'P10':>10}  {'P90':>10}")
    for i, d in enumerate(forecast_idx):
        print(f"  {d.strftime('%b %Y'):<10}  ${total_point[i]:>8,.0f}   ${total_lo[i]:>8,.0f}   ${total_hi[i]:>8,.0f}")
    print()

    # --- Chart ---
    hist_total = monthly.sum(axis=1)
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(12, 9), gridspec_kw={"height_ratios": [1.3, 1]})
    ax.plot(hist_total.index, hist_total.values, "o-", color="#2B5797", lw=2, label="Actual")
    ax.plot(forecast_idx, total_point, "s--", color="#e67e22", lw=2, label="Forecast (point)")
    ax.fill_between(forecast_idx, total_lo, total_hi, color="#e67e22", alpha=0.2, label="80% PI")
    # Budget line
    monthly_budget = 2200
    ax.axhline(monthly_budget, color="#c0392b", ls=":", lw=1.5, label=f"${monthly_budget} budget")
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_title(f"3-month spending forecast (Holt's + bootstrap residuals)", fontweight="bold")
    ax.legend(loc="upper left")

    # Per-category stacked forecast
    bottom = np.zeros(HORIZON)
    palette = sns.color_palette("tab20", len(monthly.columns))
    for color, cat in zip(palette, sorted(monthly.columns, key=lambda c: -cat_forecasts[c].sum())):
        ax2.bar(range(HORIZON), cat_forecasts[cat], bottom=bottom, color=color, label=cat)
        bottom += cat_forecasts[cat]
    ax2.set_xticks(range(HORIZON))
    ax2.set_xticklabels([d.strftime("%b %Y") for d in forecast_idx])
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax2.set_title("Per-category forecast composition", fontweight="bold")
    ax2.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8, ncol=1)

    plt.tight_layout()
    fig.savefig(OUT / "09_forecast.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Chart → {OUT}/09_forecast.png")


if __name__ == "__main__":
    main()
