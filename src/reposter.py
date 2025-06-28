import os
import re
import sys
import asyncio

# Define DummyClient at module level so it can be mocked in tests
class DummyClient:
    def __init__(self, *args, **kwargs): pass
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc, tb): pass
    async def send_message(self, *a, **kw):
        class DummyMsg: id = 12345
        return DummyMsg()
    async def send_file(self, *a, **kw): return None
    async def send_media_group(self, *a, **kw): return None
    async def get_entity(self, *a, **kw): return "dummy_entity"
    async def get_input_entity(self, *a, **kw): return "dummy_entity"
    async def get_messages(self, *a, **kw):
        class DummyMsg: pass
        return DummyMsg()
    async def is_user_authorized(self): return True

TEST_MODE = os.environ.get("TEST_MODE") == "1"

if TEST_MODE:
    TelegramClient = DummyClient
else:
    from telethon import TelegramClient

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Helper to parse Telegram message URLs
def parse_telegram_url(url):
    """Parses a Telegram message URL and returns (channel_name_or_id, message_id) or (None, None) if invalid."""
    # Match /t.me/channel_name/message_id
    m1 = re.match(r'https?://t\.me/([\w\-]+)/([0-9]+)', url)
    if m1 and m1.group(1) != 'c':
        return m1.group(1), int(m1.group(2))
    # Match /t.me/c/channel_id/message_id
    m2 = re.match(r'https?://t\.me/c/(\d+)/([0-9]+)', url)
    if m2:
        # /c/ IDs are missing the -100 prefix
        return f'-100{m2.group(1)}', int(m2.group(2))
    return None, None

def normalize_channel_id(channel):
    """If channel is all digits and doesn't start with -100, prepend -100."""
    if isinstance(channel, str) and channel.isdigit() and not channel.startswith('-100'):
        return f'-100{channel}'
    return channel

async def login():
    """Connects to Telegram and creates a session file if one doesn't exist."""
    print("Attempting to connect to Telegram to create a session...", file=sys.stderr)
    session_name = "anon"
    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        if await client.is_user_authorized():
            print("Session file is valid. You are already logged in.")
        else:
            # The login flow is handled automatically by TelegramClient on first run.
            # We can send a message to ourselves to confirm it works.
            await client.send_message("me", "Login successful!")
            print("Login successful. Session file created/updated.")


async def repost_from_file(destination, source=None):
    """Reads source message URLs from file and reposts them to the destination channel. Writes new message URLs to output file atomically."""
    session_name = "anon"
    input_file = source or "./temp/input/source_urls.txt"
    output_dir = "./temp/output"
    output_file = os.path.join(output_dir, "new_dest_urls.txt")
    temp_file = os.path.join(output_dir, "new_dest_urls.txt.tmp")

    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f:
        source_urls = [line.strip() for line in f if line.strip()]

    print(f"Read {len(source_urls)} source URLs from {input_file}.", file=sys.stderr)

    any_invalid = False
    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        try:
            destination_id = normalize_channel_id(destination)
            try:
                # Try to convert destination_id to int if possible (required for private channels)
                destination_id = int(destination_id)
            except (ValueError, TypeError):
                # If conversion fails, keep as string (works for public channels/usernames)
                pass
            # Telethon requires integer IDs for private channels; string usernames work for public channels.
            # If you use a string for a private channel, entity resolution will fail.
            try:
                dest_entity = await client.get_entity(destination_id)
            except Exception as e1:
                print(f"[WARN] get_entity failed for destination '{destination_id}': {e1}", file=sys.stderr)
                try:
                    dest_entity = await client.get_input_entity(destination_id)
                except Exception as e2:
                    print(f"[ERROR] get_input_entity also failed for destination '{destination_id}': {e2}", file=sys.stderr)
                    print(f"Could not find the destination entity '{destination}'.", file=sys.stderr)
                    sys.exit(1)
        except Exception as e:
            print(f"Could not resolve the destination entity '{destination}'. Error: {e}", file=sys.stderr)
            sys.exit(1)

        with open(temp_file, "w", encoding="utf-8") as out:
            for url in source_urls:
                channel, msg_id = parse_telegram_url(url)
                if channel and msg_id:
                    try:
                        source_id = normalize_channel_id(channel)
                        try:
                            # Try to convert source_id to int if possible (required for private channels)
                            source_id = int(source_id)
                        except (ValueError, TypeError):
                            # If conversion fails, keep as string (works for public channels/usernames)
                            pass
                        # Telethon requires integer IDs for private channels; string usernames work for public channels.
                        # If you use a string for a private channel, message resolution will fail.
                        message_to_send = await client.get_messages(source_id, ids=msg_id)
                        # Debug: print type and attributes of message_to_send
                        print(f"[DEBUG] message_to_send type: {type(message_to_send)}", file=sys.stderr)
                        if hasattr(message_to_send, '__dict__'):
                            print(f"[DEBUG] message_to_send.__dict__: {message_to_send.__dict__}", file=sys.stderr)
                        else:
                            print(f"[DEBUG] message_to_send: {message_to_send}", file=sys.stderr)
                        # Try to print media info if present
                        if hasattr(message_to_send, 'media'):
                            print(f"[DEBUG] message_to_send.media: {message_to_send.media}", file=sys.stderr)
                        if hasattr(message_to_send, 'document'):
                            print(f"[DEBUG] message_to_send.document: {message_to_send.document}", file=sys.stderr)
                        if hasattr(message_to_send, 'photo'):
                            print(f"[DEBUG] message_to_send.photo: {message_to_send.photo}", file=sys.stderr)
                        if hasattr(message_to_send, 'media_group_id'):
                            print(f"[DEBUG] message_to_send.media_group_id: {message_to_send.media_group_id}", file=sys.stderr)
                        # --- Media group logic ---
                        grouped_id = getattr(message_to_send, 'grouped_id', None)
                        if grouped_id:
                            print(f"[DEBUG] Message is part of a media group (grouped_id={grouped_id}), fetching all group messages", file=sys.stderr)
                            # Fetch all messages in the group (limit to 10 for safety)
                            group_msgs = await client.get_messages(source_id, filter=None, min_id=0, max_id=msg_id+1, limit=10)
                            # Filter messages with the same grouped_id
                            group_msgs = [m for m in group_msgs if getattr(m, 'grouped_id', None) == grouped_id]
                            # Sort by message id (Telegram albums are ordered)
                            group_msgs = sorted(group_msgs, key=lambda m: m.id)
                            media_list = []
                            for m in group_msgs:
                                if hasattr(m, 'media') and m.media:
                                    media_list.append(m.media)
                            if media_list:
                                print(f"[DEBUG] Sending media group with {len(media_list)} items to {dest_entity}", file=sys.stderr)
                                sent_msgs = await client.send_media_group(dest_entity, media_list)
                                # Write URLs for each sent message
                                for sent in sent_msgs:
                                    new_url = f"https://t.me/{destination}/{sent.id}"
                                    out.write(new_url + "\n")
                                print(f"Reposted media group {grouped_id} from {channel} to {destination} as {len(sent_msgs)} messages.")
                                await asyncio.sleep(1/10)
                                continue  # Skip the single-message send below
                        # --- End media group logic ---
                        if message_to_send:
                            print(f"[DEBUG] Sending message_to_send to {dest_entity}", file=sys.stderr)
                            sent = await client.send_message(dest_entity, message_to_send)
                            new_url = f"https://t.me/{destination}/{sent.id}"
                            out.write(new_url + "\n")
                            print(f"Reposted message {msg_id} from {channel} to {destination} as {new_url}.")
                            await asyncio.sleep(1/10)  # Wait 40 seconds before sending the next message
                        else:
                            print(f"Could not find message with ID {msg_id} in {channel}.")
                    except Exception as e:
                        print(f"Error reposting message {msg_id} from {channel}: {e}", file=sys.stderr)
                else:
                    print(f"Invalid Telegram message URL: {url}", file=sys.stderr)
                    any_invalid = True

    os.replace(temp_file, output_file)
    print(f"Wrote new destination URLs to {output_file} (atomic write).")
    if any_invalid:
        sys.exit(1)
