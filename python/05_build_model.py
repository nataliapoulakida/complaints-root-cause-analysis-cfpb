"""Step 5: build the star schema tables for Power BI.

Reads  data/clean/complaints_clean.csv
Writes data/model/fact_complaints.csv and the dimension tables
       dim_date, dim_product, dim_issue, dim_company, dim_state, dim_channel, dim_response
Checks that every fact row finds its dimension rows and that totals match the clean file.
Compatible with Python 3.9+ and pandas 2.x.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "clean" / "complaints_clean.csv"
OUT = ROOT / "data" / "model"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(SRC, dtype=str, keep_default_na=False)
for c in ["timely_flag", "has_outcome", "relief_flag", "monetary_relief_flag", "unusual_month",
          "company_total_complaints", "company_ranked"]:
    df[c] = df[c].astype(int)
n = len(df)


def make_dim(cols, key):
    d = df[cols].drop_duplicates().sort_values(cols).reset_index(drop=True)
    d.insert(0, key, range(1, len(d) + 1))
    return d


dims = {
    "dim_product": make_dim(["product", "sub_product"], "product_key"),
    "dim_issue": make_dim(["issue", "sub_issue"], "issue_key"),
    "dim_company": make_dim(["company", "company_type", "company_total_complaints", "company_ranked"], "company_key"),
    "dim_state": make_dim(["state"], "state_key"),
    "dim_channel": make_dim(["submitted_via"], "channel_key"),
    "dim_response": make_dim(["company_response"], "response_key"),
}
assert dims["dim_company"]["company"].is_unique, "a company has more than one type or size"

# Date table: every day of the window, with the columns Power BI needs
days = pd.date_range("2024-01-01", "2025-12-31", freq="D")
dim_date = pd.DataFrame({"date": days.strftime("%Y-%m-%d")})
dim_date["year"] = days.year
dim_date["quarter"] = "Q" + days.quarter.astype(str)
dim_date["year_quarter"] = days.year.astype(str) + "-Q" + days.quarter.astype(str)
dim_date["month_num"] = days.month
dim_date["month_name"] = days.strftime("%b")
dim_date["year_month"] = days.strftime("%Y-%m")
dim_date["month_start"] = days.strftime("%Y-%m-01")
dims["dim_date"] = dim_date

# Fact table: one row per complaint, keys instead of descriptive text
fact = df.copy()
for name, key, cols in [("dim_product", "product_key", ["product", "sub_product"]),
                        ("dim_issue", "issue_key", ["issue", "sub_issue"]),
                        ("dim_company", "company_key", ["company", "company_type", "company_total_complaints", "company_ranked"]),
                        ("dim_state", "state_key", ["state"]),
                        ("dim_channel", "channel_key", ["submitted_via"]),
                        ("dim_response", "response_key", ["company_response"])]:
    fact = fact.merge(dims[name][[key] + cols], on=cols, how="left")
    assert fact[key].notna().all(), f"unmatched {key}"
fact = fact.rename(columns={"date_received": "date_key"})
fact_cols = ["complaint_id", "date_key", "product_key", "issue_key", "company_key", "state_key",
             "channel_key", "response_key", "tags", "timely_flag", "has_outcome", "relief_flag",
             "monetary_relief_flag", "unusual_month"]
fact = fact[fact_cols]

# Checks ---------------------------------------------------------------------------
assert len(fact) == n, "fact row count changed"
assert fact["complaint_id"].is_unique
assert fact["date_key"].isin(dim_date["date"]).all(), "date outside the date table"
for name, key in [("dim_product", "product_key"), ("dim_issue", "issue_key"), ("dim_company", "company_key"),
                  ("dim_state", "state_key"), ("dim_channel", "channel_key"), ("dim_response", "response_key")]:
    assert dims[name][key].is_unique
    assert fact[key].isin(dims[name][key]).all()
for c in ["timely_flag", "has_outcome", "relief_flag", "monetary_relief_flag", "unusual_month"]:
    assert fact[c].sum() == df[c].sum(), f"{c} total changed"
print(f"fact_complaints: {len(fact):,} rows (clean file: {n:,})")
for name, d in dims.items():
    print(f"{name}: {len(d):,} rows")
print("All checks passed: keys unique, every fact row matches every dimension, totals unchanged.")

fact.to_csv(OUT / "fact_complaints.csv", index=False, encoding="utf-8")
for name, d in dims.items():
    d.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8")
print(f"Written to {OUT}")
