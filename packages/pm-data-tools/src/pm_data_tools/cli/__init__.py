"""Command-line interface for PM Data Tools."""

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="pm-data-tools")
def main() -> None:
    """PM Data Tools - Project management data interoperability.

    Convert, validate, and inspect project management data across multiple formats.
    """
    pass  # pragma: no cover


# Register commands
from .commands import convert, validate, inspect_cmd

main.add_command(convert)
main.add_command(validate)
main.add_command(inspect_cmd)


if __name__ == "__main__":
    main()
