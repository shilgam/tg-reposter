from dotenv import load_dotenv

from .cli import cli

load_dotenv()


def main():
    cli()


if __name__ == "__main__":
    main()