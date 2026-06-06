"""Central configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_DATA_BUCKET = os.getenv("S3_DATA_BUCKET", "shivas-nyc-taxi-datalake-2025")
S3_ATHENA_RESULTS = os.getenv("S3_ATHENA_RESULTS", "s3://shivas-athena-results-2025/")
GLUE_DATABASE = os.getenv("GLUE_DATABASE", "nyc_taxi")
GLUE_TABLE = os.getenv("GLUE_TABLE", "yellow_taxi")
BEDROCK_CHAT_MODEL = os.getenv(
    "BEDROCK_CHAT_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0"
)BEDROCK_EMBED_MODEL = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")
SCHEMA_PATH = os.getenv("SCHEMA_PATH", str(ROOT_DIR / "yellow_taxi_schema.json"))
FAISS_INDEX_KEY = os.getenv("FAISS_INDEX_KEY", "faiss/faiss_index.bin")
FAISS_METADATA_KEY = os.getenv("FAISS_METADATA_KEY", "faiss/metadata_texts.json")
