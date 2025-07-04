import asyncio

import click

from .reposter import login as perform_login, repost_from_file
from .delete import delete_from_file


@click.group()
def cli():
    """A CLI tool to repost Telegram messages."""
    pass


@cli.command()
@click.option("--destination", required=True, help="Destination channel ID or username.")
@click.option("--source", required=False, default="./temp/input/source_urls.txt", help="Source file with message URLs.")
@click.option("--sleep", type=float, default=None, help="Sleep interval in seconds between reposts (default: 0.1, overridden by REPOST_SLEEP_INTERVAL env var).")
def repost(destination, source, sleep):
    """Reposts messages from file to the specified destination."""
    # Validate sleep interval if provided
    if sleep is not None and sleep < 0:
        raise click.BadParameter("Sleep interval must be a positive number.")

    click.echo(f"Reposting messages to {destination} from {source}...")
    asyncio.run(repost_from_file(destination, source, sleep))
    click.echo("Repost command finished.")


@cli.command()
def login():
    """Creates a new session file by logging in."""
    click.echo("Starting Telegram login process...")
    asyncio.run(perform_login())


@cli.command()
@click.option("--delete-urls", required=False, default=None, help="File with message URLs to delete. If omitted, auto-detects the most recent dest_urls_to_delete.txt in ./data/output/.")
@click.option("--source", required=False, default=None, help="(Hidden) Ignored by delete.", hidden=True)
@click.option("--destination", required=False, default=None, help="(Hidden) Ignored by delete.", hidden=True)
@click.option("--sleep", required=False, default=None, type=float, help="(Hidden) Ignored by delete.", hidden=True)
def delete(delete_urls, source, destination, sleep):
    """Deletes messages from the destination channel based on a list."""
    import sys
    try:
        click.echo(f"Deleting messages using file: {delete_urls or '[auto-detect]'}...")
        asyncio.run(delete_from_file(delete_urls))
        click.echo("Delete command finished.")
        sys.exit(0)
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--destination", required=True, help="Destination channel ID or username.")
@click.option("--source", required=False, default="./temp/input/source_urls.txt", help="Source file with message URLs.")
@click.option("--sleep", type=float, default=None, help="Sleep interval in seconds between reposts (default: 0.1, overridden by REPOST_SLEEP_INTERVAL env var).")
@click.option("--delete-urls", required=False, default=None, help="File with message URLs to delete. If omitted, auto-detects the most recent dest_urls_to_delete.txt in ./data/output/.")
def sync(destination, source, sleep, delete_urls):
    """Reposts messages, then deletes them in sequence (abort on error)."""
    import sys
    try:
        click.echo(f"[SYNC] Reposting messages to {destination} from {source}...")
        asyncio.run(repost_from_file(destination, source, sleep))
        click.echo("[SYNC] Repost succeeded. Proceeding to delete...")
        asyncio.run(delete_from_file(delete_urls))
        click.echo("[SYNC] Delete succeeded. Sync complete.")
        sys.exit(0)
    except FileNotFoundError as e:
        click.echo(f"[SYNC] File not found: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"[SYNC] Error: {e}", err=True)
        sys.exit(1)
