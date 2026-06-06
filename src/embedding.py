import json
import re

import boto3

from config import AWS_REGION, BEDROCK_EMBED_MODEL

bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def get_embedding(text: str) -> list[float]:
    """Generate a vector embedding for text using Amazon Titan."""
    response = bedrock_runtime.invoke_model(
        modelId=BEDROCK_EMBED_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text}),
    )
    response_body = json.loads(response["body"].read())
    return response_body["embedding"]


if __name__ == "__main__":
    sample = (
        "NYC Yellow Taxi trips with fare_amount, trip_distance, and pickup times."
    )
    vector = get_embedding(sample)
    print(f"Embedding dimension: {len(vector)}")
