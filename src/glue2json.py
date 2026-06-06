import argparse
import json
from pathlib import Path

import boto3

from config import GLUE_DATABASE, SCHEMA_PATH

glue = boto3.client("glue")

# TLC data dictionary descriptions for richer RAG context
COLUMN_DESCRIPTIONS = {
    "vendorid": "TPEP provider: 1=Creative Mobile Technologies, 2=Curb Mobility, 6=Myle, 7=Helix.",
    "tpep_pickup_datetime": "Timestamp when the taximeter was engaged (trip start).",
    "tpep_dropoff_datetime": "Timestamp when the taximeter was disengaged (trip end).",
    "passenger_count": "Number of passengers in the vehicle.",
    "trip_distance": "Trip distance in miles as reported by the taximeter.",
    "ratecodeid": "Final rate code: 1=Standard, 2=JFK, 3=Newark, 4=Nassau/Westchester, 5=Negotiated, 6=Group, 99=Unknown.",
    "store_and_fwd_flag": "Y if trip was stored in vehicle memory before upload; N otherwise.",
    "pulocationid": "TLC taxi zone ID where the meter was engaged (pickup).",
    "dolocationid": "TLC taxi zone ID where the meter was disengaged (dropoff).",
    "payment_type": "Payment method: 1=Credit card, 2=Cash, 3=No charge, 4=Dispute, 5=Unknown, 6=Voided.",
    "fare_amount": "Time-and-distance fare calculated by the meter (USD).",
    "extra": "Miscellaneous extras and surcharges (USD).",
    "mta_tax": "MTA tax triggered by the metered rate (USD).",
    "tip_amount": "Tip amount; auto-populated for card tips, excludes cash tips.",
    "tolls_amount": "Total tolls paid during the trip (USD).",
    "improvement_surcharge": "Improvement surcharge at flag drop, levied since 2015 (USD).",
    "total_amount": "Total charged to passenger; excludes cash tips (USD).",
    "congestion_surcharge": "NYS congestion surcharge collected on the trip (USD).",
    "airport_fee": "Airport pickup fee for LaGuardia and JFK (USD).",
    "cbd_congestion_fee": "MTA Congestion Relief Zone fee (from Jan 2025) (USD).",
}


def get_table_schema(database_name: str, table_name: str) -> dict:
    """Fetch Glue table schema and enrich with business descriptions."""
    response = glue.get_table(DatabaseName=database_name, Name=table_name)
    table = response["Table"]

    columns = []
    for col in table["StorageDescriptor"]["Columns"]:
        name = col["Name"].lower()
        columns.append(
            {
                "name": name,
                "type": col["Type"],
                "description": COLUMN_DESCRIPTIONS.get(
                    name, f"Column '{name}' of type {col['Type']}."
                ),
            }
        )

    return {
        "table_name": table_name,
        "database": database_name,
        "location": table["StorageDescriptor"]["Location"],
        "description": (
            f"NYC Yellow Taxi trip records in {table_name}. "
            f"Each row is one trip with timestamps, zones, distance, and fare components."
        ),
        "columns": columns,
    }


def save_schema(output_path: str | Path | None = None, table_name: str | None = None) -> Path:
    from config import GLUE_TABLE

    table_name = table_name or GLUE_TABLE
    output_path = Path(output_path or SCHEMA_PATH)
    schema = get_table_schema(GLUE_DATABASE, table_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2))
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Glue table schema to JSON.")
    parser.add_argument(
        "-o",
        "--output",
        default=SCHEMA_PATH,
        help="Output JSON path",
    )
    args = parser.parse_args()

    path = save_schema(args.output)
    print(f"Schema saved to {path}")
