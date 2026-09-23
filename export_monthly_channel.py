
import sqlite3
import pandas as pd
from pathlib import Path

# ---------------------------------------
# Connect to existing database
# ---------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "campaign_analytics.db"

OUTPUT_DIR = BASE_DIR / "powerbi_exports"
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------
# Query monthly channel spending
# ---------------------------------------

query = """
SELECT
    strftime('%Y-%m', start_date) AS campaign_month,
    channel,
    COUNT(*) AS campaigns_started,
    ROUND(SUM(cost), 2) AS spend
FROM campaigns
GROUP BY
    strftime('%Y-%m', start_date),
    channel
ORDER BY
    campaign_month,
    channel;
"""

with sqlite3.connect(DB_PATH) as conn:
    df = pd.read_sql_query(query, conn)

# ---------------------------------------
# Export CSV
# ---------------------------------------

output_file = OUTPUT_DIR / "monthly_channel_spend.csv"

df.to_csv(output_file, index=False)

print("Monthly channel spending exported successfully!")
print(f"File: {output_file}")
print(f"Rows: {len(df)}")

print("\nPreview:")
print(df.head(10))