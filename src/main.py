import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID"))
DESTINATION_CHANNEL_ID = int(os.getenv("DESTINATION_CHANNEL_ID"))


async def main():
    """Fetches the last message from a source channel and forwards it to a destination channel."""
    session_name = "anon"
    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        # Get the last message from the source channel
        async for message in client.iter_messages(SOURCE_CHANNEL_ID, limit=1):
            # Send the message to the destination channel
            await client.send_message(DESTINATION_CHANNEL_ID, message.text)
            print("Message forwarded successfully!")


if __name__ == "__main__":
    asyncio.run(main())