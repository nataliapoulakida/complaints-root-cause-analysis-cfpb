"""Step 4: run the SQL in sql/01_kpis.sql with DuckDB and save each result as a CSV.

Reads  data/clean/complaints_clean.csv  and  sql/01_kpis.sql
Writes sql/results/<query name>.csv     and  docs/run_logs/04_sql_run_summary.txt
Change FOCUS to analyse a different company. Compatible with Python 3.9+ and duckdb 1.x.
"""
import re
from pathlib import Path

import duckdb

FOCUS = "Chime Financial Inc"

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "clean" / "complaints_clean.csv"
SQL_FILE = ROOT / "sql" / "01_kpis.sql"
OUT_DIR = ROOT / "sql" / "results"
SUMMARY = ROOT / "docs" / "run_logs" / "04_sql_run_summary.txt"
OUT_DIR.mkdir(exist_ok=True)

con = duckdb.connect()
con.execute(f"""
    CREATE VIEW complaints AS
    SELECT * FROM read_csv_auto('{CSV.as_posix()}', header = true, sample_size = -1)
""")
n = con.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]

text = SQL_FILE.read_text(encoding="utf-8").replace("{{FOCUS}}", FOCUS.replace("'", "''"))
parts = re.split(r"^-- name: (\w+)\s*$", text, flags=re.MULTILINE)
queries = list(zip(parts[1::2], parts[2::2]))

lines = [f"Rows in complaints: {n:,}   Focus company: {FOCUS}", ""]
for name, body in queries:
    df = con.execute(body.strip().rstrip(";")).df()
    df.to_csv(OUT_DIR / f"{name}.csv", index=False)
    lines.append(f"{name}: {len(df):,} rows -> sql/results/{name}.csv")
print("\n".join(lines))
SUMMARY.write_text("\n".join(lines), encoding="utf-8")
