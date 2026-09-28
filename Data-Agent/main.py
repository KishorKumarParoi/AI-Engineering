import argparse
import os
import sys
import time
from typing import Optional

from dotenv import load_dotenv

# Ensure local modules are accessible
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

load_dotenv()

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from agents.data_agent import data_agent
from utils.db import DatabaseUtil

console = Console()


def print_banner():
    """Prints a sleek modern CLI banner for Data Agent."""
    banner_text = (
        "[bold cyan]DATA AGENT[/bold cyan] : [dim]Enterprise Multi-Agent Intelligence System[/dim]\n"
        "[italic green]Powered by LangGraph, PostgreSQL & Tool-Calling Agents[/italic green]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def show_database_tables():
    """Inspects and displays database tables, record counts, and status."""
    console.print("\n[bold yellow]🔍 Introspecting PostgreSQL Database...[/bold yellow]")
    try:
        db = DatabaseUtil()
        conn = db.get_connection()
        if not conn:
            console.print("[bold red]❌ Could not connect to PostgreSQL database.[/bold red]")
            return

        cursor = conn.cursor()
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        )
        tables = cursor.fetchall()

        if not tables:
            console.print("[dim]No public tables found in the database.[/dim]")
            return

        table_widget = Table(title="PostgreSQL Database Tables", header_style="bold magenta")
        table_widget.add_column("Table Name", style="cyan")
        table_widget.add_column("Row Count", justify="right", style="green")

        for (tbl_name,) in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tbl_name};")
                count = cursor.fetchone()[0]
                table_widget.add_row(tbl_name, f"{count:,}")
            except Exception:
                table_widget.add_row(tbl_name, "Error")

        console.print(table_widget)
        cursor.close()
    except Exception as e:
        console.print(f"[bold red]Database inspection error: {e}[/bold red]")


def process_query(user_query: str) -> str:
    """Invokes the top-level supervisor graph with the user query."""
    start_time = time.time()
    with console.status("[bold green]Agent thinking & orchestrating workflow...[/bold green]", spinner="dots"):
        response = data_agent.invoke({
            "messages": [HumanMessage(content=user_query)]
        })
    elapsed = time.time() - start_time

    final_text = response.get("final_response") or "Analysis completed without explicit output."
    route_used = response.get("route_response", "Unknown").upper()

    console.print(f"\n[dim]⏱️ Execution time: {elapsed:.2f}s | Route: [bold cyan]{route_used}[/bold cyan][/dim]")
    console.print(Panel(Markdown(final_text), title=f"[bold green]Response ({route_used})[/bold green]", border_style="green"))
    return final_text


def run_demo():
    """Runs a series of representative SQL and ETL queries to demonstrate system flow."""
    demo_queries = [
        # SQL Analyst Query
        "What are the top 3 most popular payment methods used by riders and total revenue for each?",
        # SQL Analyst Query 2
        "Which 5 drivers have the highest average rating in our database?",
        # ETL Analyst Query
        "Extract pokemon data from https://pokeapi.co/api/v2/pokemon/1 into data/extract as json",
    ]

    console.print("\n[bold magenta]🚀 Running Automated End-to-End Demo Suite...[/bold magenta]")
    for i, q in enumerate(demo_queries, start=1):
        console.print(f"\n[bold yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold yellow]")
        console.print(f"[bold cyan]Demo Query {i}/{len(demo_queries)}:[/bold cyan] {q}")
        process_query(q)


def interactive_session():
    """Starts an interactive REPL terminal for the user."""
    print_banner()
    console.print("[dim]Type your question in natural language. Type [bold]help[/bold] for commands, [bold]exit[/bold] to quit.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold green]data-agent[/bold green]").strip()
            if not user_input:
                continue

            cmd = user_input.lower()
            if cmd in ["exit", "quit", "q"]:
                console.print("[yellow]Exiting Data Agent. Goodbye![/yellow]")
                break
            elif cmd in ["help", "?"]:
                console.print(Panel(
                    "[bold]Available Commands:[/bold]\n"
                    "  • [cyan]tables[/cyan]  : Show active PostgreSQL tables and row counts\n"
                    "  • [cyan]demo[/cyan]    : Run automated demo queries (SQL & ETL)\n"
                    "  • [cyan]clear[/cyan]   : Clear terminal screen\n"
                    "  • [cyan]exit[/cyan]    : Quit session\n\n"
                    "[bold]Sample Queries:[/bold]\n"
                    "  • [italic]'Show me the top 5 cities with the most rides'[/italic] (SQL)\n"
                    "  • [italic]'How many active drivers are there by vehicle make?'[/italic] (SQL)\n"
                    "  • [italic]'Extract pokemon 10 from https://pokeapi.co/api/v2/pokemon/10 into data/extract as csv'[/italic] (ETL)\n"
                    "  • [italic]'Filter data/extract/extracted_data.csv for weedle and save to data/transform/test.csv'[/italic] (ETL)",
                    title="Help & Guidance",
                    border_style="cyan"
                ))
            elif cmd == "tables":
                show_database_tables()
            elif cmd == "demo":
                run_demo()
            elif cmd == "clear":
                console.clear()
                print_banner()
            else:
                process_query(user_input)

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Unexpected Error: {e}[/bold red]")


def main():
    parser = argparse.ArgumentParser(
        description="Data Agent: Multi-Agent SQL & ETL Intelligence System"
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        help="Run a single natural language query non-interactively and exit"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run predefined SQL and ETL demo queries to test the system"
    )
    parser.add_argument(
        "--tables",
        action="store_true",
        help="Display all PostgreSQL tables and record counts"
    )

    args = parser.parse_args()

    if args.tables:
        show_database_tables()
    elif args.demo:
        print_banner()
        run_demo()
    elif args.query:
        print_banner()
        process_query(args.query)
    else:
        interactive_session()


if __name__ == "__main__":
    main()
