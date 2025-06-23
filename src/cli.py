import asyncio

import click

from .reposter import login as perform_login, repost_message


@click.group()
def cli():
    """A CLI tool to repost Telegram messages."""
    pass


@cli.command()
@click.option("--source", required=True, help="Source channel ID or username.")
@click.option("--message-id", required=True, type=int, help="The ID of the message to repost.")
@click.option("--destination", required=True, help="Destination channel ID or username.")
def repost(source, message_id, destination):
    """Reposts a single message from a source to a destination."""
    click.echo(f"Reposting message {message_id} from {source} to {destination}...")
    asyncio.run(repost_message(source, message_id, destination))
    click.echo("Repost command finished.")


@cli.command()
def login():
    """Creates a new session file by logging in."""
    click.echo("Starting Telegram login process...")
    asyncio.run(perform_login())


@cli.command()
def delete():
    """Deletes messages from the destination channel based on a list."""
    click.echo("Delete command is not yet implemented.")


@cli.command()
def sync():
    """(Not yet implemented)"""
    click.echo("Sync command is not yet implemented.")