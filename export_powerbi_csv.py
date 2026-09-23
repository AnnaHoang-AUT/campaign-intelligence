"""Export selected campaign-analysis query results as Power BI-ready CSV files.

Place this file beside:
  - campaign_analytics.db
  - campaign_queries.sql (preferred) or queries.sql

Run:
    python export_powerbi_csv.py
"""

from pathlib import Path
import re
import sqlite3

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / "campaign_analytics.db"
OUTPUT_DIR = BASE_DIR / "powerbi_exports"

SQL_CANDIDATES = [
    BASE_DIR / "campaign_queries.sql",
    BASE_DIR / "queries.sql",
]

# One CSV per management view. Values are the numbered SQL sections.
EXPORTS = {
    "campaign_engagement_attention.csv": "1.1",
    "portfolio_health.csv": "1.3",
    "channel_performance.csv": "1.2",
    "audience_reconciliation.csv": "2.1",
    "segment_value_contactability.csv": "2.3",
    "contact_pressure.csv": "2.4",
    "monthly_performance_trend.csv": "3.4",
    "customer_opportunity_review.csv": "4.1",
    "campaign_decision_queue.csv": "4.2",
    "promising_campaigns.csv": "4.3",
}

# These checks are combined into one normalized Power BI table.
VALIDATION_SECTIONS = [
    "5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9",
    "6.1", "6.2", "6.3",
]


def locate_sql_file() -> Path:
    for path in SQL_CANDIDATES:
        if path.exists():
            return path
    expected = " or ".join(path.name for path in SQL_CANDIDATES)
    raise FileNotFoundError(f"Could not find {expected} in {BASE_DIR}")


def parse_numbered_queries(sql_text: str):
    """Return {section: {title, sql}} for headings such as '-- 4.2 Title'."""
    pattern = re.compile(r"^-- (\d\.\d) (.+)$", re.MULTILINE)
    matches = list(pattern.finditer(sql_text))
    parsed = {}

    for index, match in enumerate(matches):
        section = match.group(1)
        title = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(sql_text)
        block = sql_text[start:end]

        # Descriptive comments are excluded before the SQL is executed.
        statement = "\n".join(
            line for line in block.splitlines()
            if not line.strip().startswith("--")
        ).strip().rstrip(";")

        if statement:
            parsed[section] = {"title": title, "sql": statement}

    return parsed


def export_csv(frame: pd.DataFrame, path: Path):
    # UTF-8 with BOM opens cleanly in Power BI and Excel on Windows.
    frame.to_csv(path, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")


def main():
    if not DATABASE_FILE.exists():
        raise FileNotFoundError(f"Could not find {DATABASE_FILE.name} in {BASE_DIR}")

    sql_file = locate_sql_file()
    sql_text = sql_file.read_text(encoding="utf-8-sig")
    queries = parse_numbered_queries(sql_text)
    OUTPUT_DIR.mkdir(exist_ok=True)

    with sqlite3.connect(DATABASE_FILE) as connection:
        print(f"Database: {DATABASE_FILE.name}")
        print(f"SQL file: {sql_file.name}")
        print(f"Output folder: {OUTPUT_DIR.name}\n")

        for filename, section in EXPORTS.items():
            if section not in queries:
                raise KeyError(f"Section {section} was not found in {sql_file.name}")

            frame = pd.read_sql_query(queries[section]["sql"], connection)
            frame.insert(0, "report_section", section)
            frame.insert(1, "report_title", queries[section]["title"])
            export_csv(frame, OUTPUT_DIR / filename)
            print(f"Created {filename}: {len(frame):,} rows")

        validation_frames = []
        for section in VALIDATION_SECTIONS:
            if section not in queries:
                raise KeyError(f"Section {section} was not found in {sql_file.name}")

            frame = pd.read_sql_query(queries[section]["sql"], connection)
            failed_columns = [column for column in frame.columns if column.startswith("failed_")]
            if len(failed_columns) != 1:
                raise ValueError(
                    f"Section {section} should contain one failed-count column; "
                    f"found {failed_columns}"
                )

            frame = frame.rename(columns={failed_columns[0]: "failed_count"})
            frame.insert(0, "report_section", section)
            frame.insert(1, "report_title", queries[section]["title"])
            validation_frames.append(
                frame[["report_section", "report_title", "check_name", "failed_count", "result"]]
            )

        validation_summary = pd.concat(validation_frames, ignore_index=True)
        export_csv(validation_summary, OUTPUT_DIR / "validation_summary.csv")
        print(f"Created validation_summary.csv: {len(validation_summary):,} rows")

    print("\nFinished. Import the CSV files from the powerbi_exports folder into Power BI.")


if __name__ == "__main__":
    main()
