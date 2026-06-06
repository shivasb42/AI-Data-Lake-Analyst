import io
import json

import boto3
import faiss
import numpy as np

from config import FAISS_INDEX_KEY, FAISS_METADATA_KEY, S3_DATA_BUCKET, SCHEMA_PATH
from embedding import get_embedding

s3 = boto3.client("s3")


def create_and_store_vectors(
    schema_json_path: str | None = None,
    index_s3_key: str | None = None,
    metadata_s3_key: str | None = None,
):
    """Embed schema metadata and store FAISS index + texts in S3."""
    schema_json_path = schema_json_path or SCHEMA_PATH
    index_s3_key = index_s3_key or FAISS_INDEX_KEY
    metadata_s3_key = metadata_s3_key or FAISS_METADATA_KEY

    with open(schema_json_path, encoding="utf-8") as f:
        schema = json.load(f)

    metadata_texts = []
    for col in schema["columns"]:
        text = f"Column '{col['name']}' ({col['type']}): {col['description']}"
        metadata_texts.append(text)

    metadata_texts.append(
        f"Table {schema['table_name']} in database {schema['database']}: {schema['description']}"
    )

    print(f"Generating embeddings for {len(metadata_texts)} metadata chunks...")
    embeddings = [get_embedding(text) for text in metadata_texts]

    dimension = len(embeddings[0])
    index = faiss.IndexFlatIP(dimension)
    vectors = np.array(embeddings).astype(np.float32)
    faiss.normalize_L2(vectors)
    index.add(vectors)
    print(f"FAISS index created with {index.ntotal} vectors")

    buffer = io.BytesIO()
    faiss.write_index(index, buffer)
    buffer.seek(0)
    s3.upload_fileobj(buffer, S3_DATA_BUCKET, index_s3_key)
    print(f"Index uploaded to s3://{S3_DATA_BUCKET}/{index_s3_key}")

    s3.put_object(
        Bucket=S3_DATA_BUCKET,
        Key=metadata_s3_key,
        Body=json.dumps(metadata_texts),
    )
    print(f"Metadata uploaded to s3://{S3_DATA_BUCKET}/{metadata_s3_key}")

    return index, metadata_texts


def load_index_from_s3(
    index_s3_key: str | None = None,
    metadata_s3_key: str | None = None,
):
    """Load FAISS index and metadata texts from S3."""
    index_s3_key = index_s3_key or FAISS_INDEX_KEY
    metadata_s3_key = metadata_s3_key or FAISS_METADATA_KEY

    response = s3.get_object(Bucket=S3_DATA_BUCKET, Key=index_s3_key)
    buffer = io.BytesIO(response["Body"].read())
    index = faiss.read_index(buffer)

    response = s3.get_object(Bucket=S3_DATA_BUCKET, Key=metadata_s3_key)
    metadata_texts = json.loads(response["Body"].read().decode("utf-8"))

    return index, metadata_texts


def search_similar(query: str, index, metadata_texts: list[str], top_k: int = 5):
    """Return top-k schema chunks most similar to the user question."""
    query_vector = np.array(get_embedding(query)).astype(np.float32).reshape(1, -1)
    faiss.normalize_L2(query_vector)
    distances, indices = index.search(query_vector, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < 0:
            continue
        results.append(
            {"score": float(distances[0][i]), "text": metadata_texts[idx]}
        )
    return results


if __name__ == "__main__":
    create_and_store_vectors()
    idx, texts = load_index_from_s3()
    for res in search_similar("average fare by payment type", idx, texts):
        print(f"{res['score']:.4f} | {res['text']}")
