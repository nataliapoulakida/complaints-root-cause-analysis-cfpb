"""Step 1: combine the six raw CFPB exports into one file.

Reads every CSV in data/ (the originals are never modified), checks that all
files have the same columns, drops duplicate Complaint IDs, and writes
data/combined/complaints_2024_2025_raw.csv with an extra 'source_file' column.
Standard library only, so it runs anywhere Python 3 is installed.
"""
import csv
import sys
from pathlib import Path

csv.field_size_limit(10**9)

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data"
OUT = RAW_DIR / "combined" / "complaints_2024_2025_raw.csv"

files = sorted(RAW_DIR.glob("*.csv"))
if not files:
    sys.exit(f"No CSV files found in {RAW_DIR}")

header = None
seen_ids = set()
per_file = {}
duplicates = 0
total_written = 0
min_date, max_date = "9999", ""

OUT.parent.mkdir(exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as out_fh:
    writer = None
    for f in files:
        with open(f, newline="", encoding="utf-8") as in_fh:
            reader = csv.reader(in_fh)
            file_header = next(reader)
            if header is None:
                header = file_header
                writer = csv.writer(out_fh)
                writer.writerow(header + ["source_file"])
            elif file_header != header:
                sys.exit(f"Column mismatch in {f.name}")
            id_col = header.index("Complaint ID")
            date_col = header.index("Date received")
            n = 0
            for row in reader:
                n += 1
                cid = row[id_col]
                if cid in seen_ids:
                    duplicates += 1
                    continue
                seen_ids.add(cid)
                d = row[date_col][:10]
                min_date, max_date = min(min_date, d), max(max_date, d)
                writer.writerow(row + [f.name])
                total_written += 1
            per_file[f.name] = n

print("Rows read per file:")
for name, n in per_file.items():
    print(f"  {n:>8,}  {name}")
print(f"Total rows read:        {sum(per_file.values()):,}")
print(f"Duplicate IDs dropped:  {duplicates:,}")
print(f"Rows written:           {total_written:,}")
print(f"Date received range:    {min_date} to {max_date}")
print(f"Output: {OUT}")
