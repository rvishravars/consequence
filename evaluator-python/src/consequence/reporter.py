"""Rich-formatted result reporter."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich import box

from consequence.types import EvalResult, SuiteReport

_console = Console()


def print_result(result: EvalResult) -> None:
    """Print a single result row to stdout."""
    status = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
    if result.error:
        status = "[yellow]ERROR[/yellow]"
    _console.print(
        f"  {status}  {result.task_id:<40s}  "
        f"score={result.score:.2f}  latency={result.latency_seconds:.2f}s"
    )
    if result.error:
        _console.print(f"         [dim]{result.error}[/dim]")


def print_suite_report(report: SuiteReport) -> None:
    """Print a formatted table summarising a suite run."""
    _console.rule(f"[bold]{report.suite_name}[/bold]")

    table = Table(box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Task ID", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Tools Called", overflow="fold")
    table.add_column("Latency", justify="right")
    table.add_column("Error", overflow="fold", style="dim")

    for r in report.results:
        if r.error:
            status = "[yellow]ERROR[/yellow]"
        elif r.passed:
            status = "[green]PASS[/green]"
        else:
            status = "[red]FAIL[/red]"

        tools_called = ", ".join(tc.name for tc in r.tool_calls) or "—"
        table.add_row(
            r.task_id,
            status,
            f"{r.score:.2f}",
            tools_called,
            f"{r.latency_seconds:.2f}s",
            r.error or "",
        )

    _console.print(table)
    _console.print(
        f"[bold]Total:[/bold] {report.total}  "
        f"[green]Passed:[/green] {report.passed}  "
        f"[red]Failed:[/red] {report.failed}  "
        f"[yellow]Errored:[/yellow] {report.errored}  "
        f"Avg score: {report.avg_score:.2f}  "
        f"Avg latency: {report.avg_latency_seconds:.2f}s"
    )
    _console.print()
