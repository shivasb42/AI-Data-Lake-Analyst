#!/usr/bin/env python3
"""CLI for the AI Data Lake Analyst."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ai_analyst import generate_sql_and_answer

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Ask natural-language questions about NYC Yellow Taxi data on AWS.",
        epilog="Example: python cli.py \"What is the average trip distance?\"",
    )
    parser.add_argument("question", nargs="?", help="Question to ask the analyst")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run built-in demo questions",
    )
    args = parser.parse_args()

    if args.demo:
        questions = [
            "How many taxi trips are in January 2025?",
            "What is the average fare amount?",
            "Show the top 5 pickup zones by trip count.",
        ]
    elif args.question:
        questions = [args.question]
    else:
        parser.print_help()
        sys.exit(1)

    for question in questions:
        console.print(Panel(question, title="Question", border_style="cyan"))

        with console.status("Retrieving context, generating SQL, querying Athena..."):
            answer, sql, df = generate_sql_and_answer(question)

        console.print(Panel(sql, title="Generated SQL", border_style="yellow"))
        console.print(Panel(answer, title="Answer", border_style="green"))

        if df is not None and not df.empty:
            table = Table(show_header=True, header_style="bold")
            for col in df.columns:
                table.add_column(str(col))
            for _, row in df.head(10).iterrows():
                table.add_row(*[str(v) for v in row])
            console.print(Panel(table, title=f"Results (showing up to 10 of {len(df)} rows)"))


if __name__ == "__main__":
    main()
