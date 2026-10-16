"""Step 3: clean the combined raw file and add analysis columns.

Reads  data/combined/complaints_2024_2025_raw.csv   (never modified)
Writes data/clean/complaints_clean.csv              (one row per complaint)
       data/clean/monthly_volume_flags.csv          (product x month, unusual-month flag)
       docs/run_logs/03_cleaning_report.txt                  (what was changed and the checks)
Decisions applied are documented in docs/02_data_quality_log.md.
Compatible with Python 3.9+ and pandas 2.x.
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "combined" / "complaints_2024_2025_raw.csv"
OUT_DIR = ROOT / "data" / "clean"
REPORT = ROOT / "docs" / "run_logs" / "03_cleaning_report.txt"
MOD_Z_CUTOFF = 3.5          # unusual month: modified z-score (median/MAD) above this
MIN_COMPLAINTS_RANKING = 500

log = []
def say(s=""):
    print(s)
    log.append(str(s))

df = pd.read_csv(SRC, dtype=str, keep_default_na=False)
n_raw = len(df)
say(f"Rows read: {n_raw:,}")

# 1. Column names -------------------------------------------------------------
df = df.rename(columns={
    "Date received": "received_raw", "Product": "product", "Sub-product": "sub_product",
    "Issue": "issue", "Sub-issue": "sub_issue",
    "Company public response": "company_public_response", "Company": "company_raw",
    "State": "state", "ZIP code": "zip_code", "Tags": "tags",
    "Submitted via": "submitted_via", "Date sent to company": "sent_raw",
    "Company response to consumer": "company_response",
    "Timely response?": "timely_response", "Complaint ID": "complaint_id",
})
df["product"] = df["product"].replace({
    "Money transfer, virtual currency, or money service": "Money transfer / virtual currency"})

# 2. Missing values: the text "None" becomes a real blank or a label ----------
for c in ["tags", "company_public_response", "sub_issue", "sub_product", "issue", "state"]:
    df[c] = df[c].where(~df[c].isin(["None", ""]), "")
said = {}
for c, label in [("sub_issue", "Not specified"), ("state", "Unknown"),
                 ("issue", "Unknown"), ("sub_product", "Unknown")]:
    said[c] = int((df[c] == "").sum())
    df[c] = df[c].replace("", label)
say("Missing values replaced by a label: " + ", ".join(f"{k}={v:,}" for k, v in said.items()))
say(f"Left as real blanks: tags={int((df['tags']=='').sum()):,}, "
    f"company_public_response={int((df['company_public_response']=='').sum()):,}")

# 3. Dates --------------------------------------------------------------------
received = pd.to_datetime(df["received_raw"], utc=True)
sent = pd.to_datetime(df["sent_raw"], utc=True)
df["date_received"] = received.dt.strftime("%Y-%m-%d")
df["month_start"] = received.dt.strftime("%Y-%m-01")
df["date_sent_to_company"] = sent.dt.strftime("%Y-%m-%d")

# 4. Company names: merge spellings that differ only in case/spacing -----------
def key(s):
    return re.sub(r"\s+", " ", s.strip()).upper()
counts = df["company_raw"].value_counts()
canon = {}
for name in counts.index:                       # most frequent spelling wins
    canon.setdefault(key(name), name.strip())
mapping = {name: canon[key(name)] for name in counts.index}
merged = [(a, b) for a, b in mapping.items() if a != b]
df["company"] = df["company_raw"].map(mapping)
say(f"Company names: {df['company_raw'].nunique():,} raw -> {df['company'].nunique():,} after merging case/spacing variants")
for a, b in merged:
    say(f"   merged '{a}' -> '{b}'")

# 5. Company type and size helpers ---------------------------------------------
bureau = df["company"].str.contains("EQUIFAX|TRANSUNION|EXPERIAN", case=False, regex=True)
df["company_type"] = bureau.map({True: "Credit bureau", False: "Bank, fintech or other"})
tot = df.groupby("company")["complaint_id"].transform("count")
df["company_total_complaints"] = tot
df["company_ranked"] = (tot >= MIN_COMPLAINTS_RANKING).astype(int)

# 6. KPI flags (1/0) --------------------------------------------------------------
df["timely_flag"] = (df["timely_response"] == "Yes").astype(int)
df["has_outcome"] = (df["company_response"] != "In progress").astype(int)
df["monetary_relief_flag"] = (df["company_response"] == "Closed with monetary relief").astype(int)
df["relief_flag"] = df["company_response"].isin(
    ["Closed with monetary relief", "Closed with non-monetary relief"]).astype(int)

# 7. Unusual-month flag (rule from the brief) ----------------------------------
# Modified z-score (Iglewicz & Hoaglin): 0.6745 * (x - median) / MAD, computed per
# product on the 24 monthly volumes. A month is flagged when the score is > 3.5,
# the standard cutoff for this measure. MAD = median absolute deviation from the median.
monthly = df.groupby(["product", "month_start"]).size().rename("complaints").reset_index()
monthly["median_month"] = monthly.groupby("product")["complaints"].transform("median")
monthly["mad"] = monthly.groupby("product")["complaints"].transform(
    lambda s: (s - s.median()).abs().median())
monthly["modified_z"] = (0.6745 * (monthly["complaints"] - monthly["median_month"]) / monthly["mad"]).round(2)
monthly["ratio_to_median"] = (monthly["complaints"] / monthly["median_month"]).round(2)
monthly["unusual_month"] = (monthly["modified_z"] > MOD_Z_CUTOFF).astype(int)
df = df.merge(monthly[["product", "month_start", "unusual_month"]], on=["product", "month_start"], how="left")
say(f"\nUnusual-month rule: modified z-score (median/MAD) > {MOD_Z_CUTOFF}, per product")
for _, r in monthly[monthly["unusual_month"] == 1].sort_values(["product", "month_start"]).iterrows():
    say(f"   FLAGGED {r['month_start']}  {r['product']}: {r['complaints']:,} vs median {r['median_month']:,.0f} "
        f"(z={r['modified_z']}, {r['ratio_to_median']}x)")
near = monthly[(monthly["unusual_month"] == 0) & (monthly["modified_z"] > 2.0)]
for _, r in near.sort_values(["product", "month_start"]).iterrows():
    say(f"   near    {r['month_start']}  {r['product']}: {r['complaints']:,} (z={r['modified_z']}, {r['ratio_to_median']}x)")

# 8. Final columns and checks ------------------------------------------------------
cols = ["complaint_id", "date_received", "month_start", "date_sent_to_company", "product", "sub_product",
        "issue", "sub_issue", "company", "company_type", "company_total_complaints", "company_ranked",
        "state", "tags", "submitted_via", "company_public_response", "company_response",
        "timely_response", "timely_flag", "has_outcome", "relief_flag", "monetary_relief_flag",
        "unusual_month"]
out = df[cols]
assert len(out) == n_raw, "row count changed"
assert out["complaint_id"].is_unique, "duplicate IDs"
assert out["date_received"].min() >= "2024-01-01" and out["date_received"].max() <= "2025-12-31"
assert set(out["timely_flag"].unique()) <= {0, 1}
say(f"\nChecks passed: {len(out):,} rows, unique IDs, dates within 2024-2025")
say(f"Credit bureau rows: {int(bureau.sum()):,}; companies ranked (>= {MIN_COMPLAINTS_RANKING}): {out.loc[out['company_ranked']==1,'company'].nunique()}")
say(f"timely_flag mean {out['timely_flag'].mean():.4f}; relief_flag mean (with outcome) "
    f"{out.loc[out['has_outcome']==1,'relief_flag'].mean():.4f}")

out.to_csv(OUT_DIR / "complaints_clean.csv", index=False, encoding="utf-8")
monthly.to_csv(OUT_DIR / "monthly_volume_flags.csv", index=False, encoding="utf-8")
REPORT.write_text("\n".join(log), encoding="utf-8")
say(f"\nWritten: {OUT_DIR / 'complaints_clean.csv'}")
