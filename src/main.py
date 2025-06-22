import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Handle source channel ID, which could be a numeric ID or a string username
source_channel_input = os.getenv("SOURCE_CHANNEL_ID")
try:
    SOURCE_CHANNEL_ID = int(source_channel_input)
except (ValueError, TypeError):
    SOURCE_CHANNEL_ID = source_channel_input

destination_channel_input = os.getenv("DESTINATION_CHANNEL_ID")
try:
    DESTINATION_CHANNEL_ID = int(destination_channel_input)
except (ValueError, TypeError):
    DESTINATION_CHANNEL_ID = destination_channel_input

SOURCE_MESSAGE_ID = os.getenv("SOURCE_MESSAGE_ID")


async def main():
    """Fetches the last message from a source channel and forwards it to a destination channel."""
    session_name = "anon"
    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        print("Verifying destination entity...")
        try:
            destination = await client.get_entity(DESTINATION_CHANNEL_ID)
            print(f"Destination entity found: {getattr(destination, 'title', 'N/A')}")
        except Exception as e:
            print(f"Could not find the destination entity '{DESTINATION_CHANNEL_ID}'.")
            print("Please ensure the ID/username is correct and that your account has access to it.")
            print(f"Telethon error: {e}")
            return

        message_to_send = None
        if SOURCE_MESSAGE_ID:
            print(f"Attempting to fetch message with ID: {SOURCE_MESSAGE_ID}")
            try:
                message_to_send = await client.get_messages(SOURCE_CHANNEL_ID, ids=int(SOURCE_MESSAGE_ID))
            except (ValueError, TypeError):
                print(f"Error: SOURCE_MESSAGE_ID must be a number, but got '{SOURCE_MESSAGE_ID}'.")
                return
        else:
            print("SOURCE_MESSAGE_ID not set. Fetching the latest message.")
            # Get the last message from the source channel
            async for message in client.iter_messages(SOURCE_CHANNEL_ID, limit=1):
                message_to_send = message
                break

        if message_to_send:
            # Send the message to the destination channel
            await client.send_message(destination, message_to_send.text)
            print("Message forwarded successfully!")
        else:
            print("Could not find a message to forward.")


if __name__ == "__main__":
    asyncio.run(main())