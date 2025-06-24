import asyncio

import click

from .reposter import login as perform_login, repost_from_file


@click.group()
def cli():
    """A CLI tool to repost Telegram messages."""
    pass


@cli.command()
@click.option("--destination", required=True, help="Destination channel ID or username.")
def repost(destination):
    """Reposts messages from file to the specified destination."""
    click.echo(f"Reposting messages to {destination}...")
    asyncio.run(repost_from_file(destination))
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