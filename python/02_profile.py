"""Step 2: profile the combined raw file. Read-only; prints a report and saves it
to docs/run_logs/02_profile_output.txt. Compatible with Python 3.9+ and pandas 2.x."""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "combined" / "complaints_2024_2025_raw.csv"
OUT = ROOT / "docs" / "run_logs" / "02_profile_output.txt"

lines = []
def say(text=""):
    print(text)
    lines.append(str(text))

df = pd.read_csv(SRC, dtype=str, keep_default_na=False)
say(f"FILE: {SRC.name}")
say(f"Rows: {len(df):,}   Columns: {df.shape[1]}")

say("\n== 1. Duplicates ==")
say(f"Duplicate Complaint IDs: {df['Complaint ID'].duplicated().sum():,}")
say(f"Fully identical rows (ignoring source_file): {df.drop(columns='source_file').duplicated().sum():,}")

say("\n== 2. Missing values ('None' text or blank) ==")
miss = ((df == "None") | (df == "")).sum().sort_values(ascending=False)
for col, n in miss.items():
    say(f"  {n/len(df):6.1%}  {n:>8,}  {col}")

say("\n== 3. Distinct values per column ==")
for col in df.columns:
    say(f"  {df[col].nunique():>8,}  {col}")

received = pd.to_datetime(df["Date received"], errors="coerce", utc=True)
sent = pd.to_datetime(df["Date sent to company"], errors="coerce", utc=True)
say("\n== 4. Dates ==")
say(f"Date received:        {received.min()}  to  {received.max()}  (unparseable: {received.isna().sum()})")
say(f"Date sent to company: {sent.min()}  to  {sent.max()}  (unparseable: {sent.isna().sum()})")
days = (sent - received).dt.total_seconds() / 86400
say(f"Days from received to sent: median {days.median():.2f}, mean {days.mean():.2f}, p95 {days.quantile(.95):.2f}, max {days.max():.2f}")
say(f"Negative gaps (sent before received): {(days < 0).sum():,}")

say("\n== 5. Product by month (check category consistency) ==")
df["month"] = received.dt.strftime("%Y-%m")
pm = df.pivot_table(index="month", columns="Product", values="Complaint ID", aggfunc="count", fill_value=0)
pm.columns = [c[:22] for c in pm.columns]
say(pm.to_string())

say("\n== 6. Categorical columns ==")
for col in ["Product", "Sub-product", "Company public response", "Submitted via",
            "Company response to consumer", "Timely response?", "Tags"]:
    say(f"\n-- {col}")
    for v, n in df[col].value_counts().items():
        say(f"  {n:>8,}  {v}")

say("\n== 7. Issue and sub-issue counts by product ==")
for p, g in df.groupby("Product"):
    say(f"\n-- {p}: {g['Issue'].nunique()} issues, {g['Sub-issue'].nunique()} sub-issues")
    for v, n in g["Issue"].value_counts().head(8).items():
        say(f"  {n:>8,}  {v}")

say("\n== 8. State ==")
valid = df["State"].str.fullmatch(r"[A-Z]{2}")
say(f"Rows with two-letter state: {valid.sum():,}; other values: {(~valid).sum():,}")
say(df.loc[~valid, "State"].value_counts().head(10).to_string())

say("\n== 9. Companies ==")
comp = df["Company"].value_counts()
say(f"Distinct company names: {len(comp):,}")
say("Top 20 by complaints:")
for v, n in comp.head(20).items():
    say(f"  {n:>8,}  {v}")
say(f"Companies with >= 500 complaints: {(comp >= 500).sum()}")
say(f"Companies with < 30 complaints: {(comp < 30).sum()} (share of complaints: {comp[comp < 30].sum()/len(df):.1%})")

def norm(s):
    s = s.upper()
    s = re.sub(r"\b(INC|LLC|LTD|CORP|CORPORATION|CO|COMPANY|NA|N A|NATIONAL ASSOCIATION|HOLDINGS|GROUP)\b", " ", s)
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()
groups = {}
for name in comp.index:
    groups.setdefault(norm(name), []).append(name)
say("\nPossible same-company spellings (names that normalise identically):")
found = False
for k, names in groups.items():
    if len(names) > 1:
        found = True
        say("  " + " | ".join(f"{n} ({comp[n]:,})" for n in names))
if not found:
    say("  none found by simple normalisation")

first = {}
for name in comp.index:
    first.setdefault(norm(name).split(" ")[0] if norm(name) else name, []).append(name)
say("\nCompanies sharing a first word (review manually, may be different companies):")
shown = 0
for k, names in sorted(first.items(), key=lambda kv: -sum(comp[n] for n in kv[1])):
    if len(names) > 1 and shown < 15:
        say("  " + " | ".join(f"{n} ({comp[n]:,})" for n in names[:5]))
        shown += 1

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nSaved to {OUT}")
