import os

from telethon import TelegramClient

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")


async def login():
    """Connects to Telegram and creates a session file if one doesn't exist."""
    print("Attempting to connect to Telegram to create a session...")
    session_name = "anon"
    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        if await client.is_user_authorized():
            print("Session file is valid. You are already logged in.")
        else:
            # The login flow is handled automatically by TelegramClient on first run.
            # We can send a message to ourselves to confirm it works.
            await client.send_message("me", "Login successful!")
            print("Login successful. Session file created/updated.")


async def repost_message(source, message_id, destination):
    """Fetches a specific message from a source channel and reposts it to a destination channel."""
    session_name = "anon"

    try:
        source_id = int(source)
    except (ValueError, TypeError):
        source_id = source

    try:
        destination_id = int(destination)
    except (ValueError, TypeError):
        destination_id = destination

    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        try:
            dest_entity = await client.get_entity(destination_id)
        except Exception as e:
            print(f"Could not find the destination entity '{destination}'. Error: {e}")
            return

        try:
            # Telethon uses integer IDs for messages
            msg_id = int(message_id)
            message_to_send = await client.get_messages(source_id, ids=msg_id)
        except Exception as e:
            print(f"Error fetching message with ID {message_id} from {source}. Error: {e}")
            return

        if message_to_send:
            await client.send_message(dest_entity, message_to_send)
            print("Message reposted successfully!")
        else:
            print(f"Could not find message with ID {message_id} in {source}.")