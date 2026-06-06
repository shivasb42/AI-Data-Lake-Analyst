import re

import awswrangler as wr
import pandas as pd

from config import GLUE_DATABASE, GLUE_TABLE, S3_ATHENA_RESULTS

_SELECT_ONLY = re.compile(r"^\s*(WITH|SELECT)\b", re.IGNORECASE | re.DOTALL)
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def _sanitize_sql(sql_query: str) -> str:
    """Strip markdown fences and enforce read-only queries."""
    sql = sql_query.strip()
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip().rstrip(";")

    if not _SELECT_ONLY.match(sql):
        raise ValueError("Only SELECT (or WITH … SELECT) queries are allowed.")
    if _FORBIDDEN.search(sql):
        raise ValueError("Query contains forbidden SQL keywords.")
    return sql


def run_athena_query(sql_query: str, database: str | None = None) -> pd.DataFrame:
    """Execute SQL on Athena and return results as a pandas DataFrame."""
    database = database or GLUE_DATABASE
    sql = _sanitize_sql(sql_query)

    df = wr.athena.read_sql_query(
        sql=sql,
        database=database,
        s3_output=S3_ATHENA_RESULTS,
    )
    return df


if __name__ == "__main__":
    from rich import print as rprint

    df = run_athena_query(
        f"SELECT COUNT(*) AS trip_count FROM {GLUE_TABLE}"
    )
    rprint(df)
