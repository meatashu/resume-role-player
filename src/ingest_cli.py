"""Simple CLI to run KB ingestion for resume files and optional LinkedIn URL."""

import typer
from pathlib import Path
from src.kb_ingest import ingest_files
from src.staging import list_staged_entries, approve_staged_entry, reject_staged_entry, preview_merge_changes
import json

app = typer.Typer()

@app.command()
def run(
    files: str = typer.Argument(..., help="Comma-separated list of file paths (pdf/docx/txt)"),
    linkedin: str = typer.Option(None, help="Optional LinkedIn profile URL"),
    name: str = typer.Option(None, help="Optional name hint to add to KB"),
    direct: bool = typer.Option(False, help="Skip staging and merge directly into KB"),
    approve_id: str = typer.Option(None, help="Approve a previously staged entry"),
    reject_id: str = typer.Option(None, help="Reject a previously staged entry"),
    list_staged: bool = typer.Option(False, help="List all staged entries"),
    preview_id: str = typer.Option(None, help="Preview changes from a staged entry")
):
    """Ingest files into the knowledge base with optional staging."""
    
    # List staged entries
    if list_staged:
        entries = list_staged_entries()
        typer.echo("\nStaged entries:")
        typer.echo(json.dumps(entries, indent=2))
        return
    
    # Preview staged changes
    if preview_id:
        try:
            changes = preview_merge_changes(preview_id)
            typer.echo("\nPreviewing changes:")
            typer.echo(json.dumps(changes, indent=2))
        except ValueError as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)
        return
    
    # Approve staged entry
    if approve_id:
        try:
            result = approve_staged_entry(approve_id)
            typer.echo("\nApproved and merged staged entry:")
            typer.echo(json.dumps(result, indent=2))
        except ValueError as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)
        return
    
    # Reject staged entry
    if reject_id:
        reason = typer.prompt("Enter rejection reason")
        try:
            result = reject_staged_entry(reject_id, reason)
            typer.echo("\nRejected staged entry:")
            typer.echo(json.dumps(result, indent=2))
        except ValueError as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(code=1)
        return
    
    # Process new files
    file_list = [f.strip() for f in files.split(',') if f.strip()]
    for f in file_list:
        if not Path(f).exists():
            typer.echo(f"File not found: {f}")
            raise typer.Exit(code=1)

    result = ingest_files(file_list, linkedin_url=linkedin, name_hint=name, use_staging=not direct)
    typer.echo('\nIngestion result:')
    typer.echo(json.dumps(result, indent=2))

if __name__ == '__main__':
    app()
