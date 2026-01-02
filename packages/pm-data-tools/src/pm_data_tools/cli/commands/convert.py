"""Convert command for format conversion."""

import click
from pathlib import Path
from typing import Optional


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option(
    "--from",
    "source_format",
    type=click.Choice(
        ["mspdi", "p6", "jira", "planner", "asana", "monday", "canonical"],
        case_sensitive=False,
    ),
    help="Source format (auto-detected if not specified)",
)
@click.option(
    "--to",
    "target_format",
    required=True,
    type=click.Choice(
        ["mspdi", "p6", "jira", "planner", "asana", "monday", "canonical"],
        case_sensitive=False,
    ),
    help="Target format",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Validate before conversion (default: enabled)",
)
def convert(
    input_file: Path,
    output_file: Path,
    source_format: Optional[str],
    target_format: str,
    validate: bool,
) -> None:
    """Convert project data between formats.

    INPUT_FILE: Source project file
    OUTPUT_FILE: Destination project file

    \b
    Examples:
        pm-data-tools convert project.xml project.json --to canonical
        pm-data-tools convert project.xml project.xer --from mspdi --to p6
        pm-data-tools convert data.json project.xml --to mspdi
    """
    click.echo(f"Converting {input_file} → {output_file}")
    click.echo(f"Source format: {source_format or 'auto-detect'}")
    click.echo(f"Target format: {target_format}")

    if validate:
        click.echo("Validation: enabled")
    else:
        click.echo("Validation: disabled")

    # TODO: Implement actual conversion logic in Phase 3
    click.echo("\nConverter not yet implemented (Phase 3)")
    click.echo("Will support:")
    click.echo("  - Microsoft Project (MSPDI XML)")
    click.echo("  - Primavera P6 (XER, PMXML)")
    click.echo("  - Jira, Planner, Asana, Monday.com")
    click.echo("  - Canonical JSON format")
