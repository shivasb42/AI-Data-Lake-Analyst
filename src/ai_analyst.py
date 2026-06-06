import json

import boto3

from config import AWS_REGION, BEDROCK_CHAT_MODEL, GLUE_DATABASE, GLUE_TABLE
from query_engine import run_athena_query
from vector_store import load_index_from_s3, search_similar

bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)

_index = None
_metadata_texts = None


def _get_vector_store():
    global _index, _metadata_texts
    if _index is None:
        _index, _metadata_texts = load_index_from_s3()
    return _index, _metadata_texts


def _invoke_claude(prompt: str, max_tokens: int = 800) -> str:
    response = bedrock_runtime.invoke_model(
        modelId=BEDROCK_CHAT_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        ),
    )
    body = json.loads(response["body"].read())
    return body["content"][0]["text"].strip()


def generate_sql_and_answer(user_question: str, top_k: int = 5):
    """
    RAG pipeline: retrieve schema context → generate SQL → run Athena → explain results.
    Returns (natural_language_answer, sql_query, result_dataframe).
    """
    index, metadata_texts = _get_vector_store()

    relevant_context = search_similar(user_question, index, metadata_texts, top_k=top_k)
    context_str = "\n".join(res["text"] for res in relevant_context)

    sql_prompt = f"""You are an expert AWS Athena SQL analyst for NYC Yellow Taxi data.

Relevant schema context:
{context_str}

Rules:
- Database: {GLUE_DATABASE}
- Table: {GLUE_TABLE}
- Use Athena/Presto SQL syntax
- Return ONLY one SQL query (SELECT or WITH … SELECT)
- No markdown, no explanation
- Column names are lowercase in Glue (e.g. fare_amount, tpep_pickup_datetime)
- Prefer aggregations and LIMIT for large result sets

User question: {user_question}
"""

    sql_query = _invoke_claude(sql_prompt, max_tokens=500)

    try:
        result_df = run_athena_query(sql_query)

        explain_prompt = f"""The user asked: "{user_question}"

SQL executed:
{sql_query}

Query results:
{result_df.head(20).to_string(index=False)}

Summarize the answer in clear, friendly language for a business user. Mention key numbers. Keep it concise."""

        explanation = _invoke_claude(explain_prompt, max_tokens=500)
        return explanation, sql_query, result_df

    except Exception as exc:
        return f"Error running query: {exc}", sql_query, None


if __name__ == "__main__":
    demo_questions = [
        "How many taxi trips are in the dataset?",
        "What is the average fare amount?",
        "What are the top 3 payment types by trip count?",
    ]

    for question in demo_questions:
        print("\n" + "=" * 60)
        print(f"Q: {question}")
        answer, sql, df = generate_sql_and_answer(question)
        print(f"SQL: {sql}")
        print(f"A: {answer}")
        if df is not None:
            print(df.head())
