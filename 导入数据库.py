import sqlite3
import csv
import os

DB_PATH = "sales.db"
CSV_PATH = "sales_data.csv"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE sales (
    date TEXT,
    channel TEXT,
    category TEXT,
    traffic INTEGER,
    orders INTEGER,
    sales REAL,
    cost REAL
)
""")

with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = [(
        r["Date"], r["Channel"], r["Category"],
        int(r["Traffic"]), int(r["Orders"]),
        float(r["Sales"]), float(r["Cost"])
    ) for r in reader]

cur.executemany(
    "INSERT INTO sales VALUES (?,?,?,?,?,?,?)", rows
)
conn.commit()

cur.execute("SELECT COUNT(*) FROM sales")
print(f"导入完成，共 {cur.fetchone()[0]} 条记录")

cur.execute("SELECT MIN(date), MAX(date) FROM sales")
min_d, max_d = cur.fetchone()
print(f"日期范围: {min_d} ~ {max_d}")

conn.close()
