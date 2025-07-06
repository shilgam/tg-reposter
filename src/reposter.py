import os
import re
import sys
import inspect
import asyncio
from typing import Optional
from datetime import datetime

from src.utils_files import dest_slug

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
    async def delete_messages(self, *a, **kw): return None

TEST_MODE = os.environ.get("TEST_MODE") == "1"

if TEST_MODE:
    TelegramClient = DummyClient
else:
    from telethon import TelegramClient

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

def is_running_tests():
    # Detect if running under pytest or test framework
    for frame in inspect.stack():
        if 'pytest' in frame.filename or 'unittest' in frame.filename:
            return True
    return False

# Directory selection helper
def get_data_dirs():
    if TEST_MODE or is_running_tests():
        return "./tests/data/input", "./tests/data/output"
    else:
        return "./data/input", "./data/output"

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

def get_sleep_interval(cli_value: Optional[float]) -> float:
    """Get sleep interval with priority: CLI argument > environment variable > default (0.1)"""
    if cli_value is not None:
        return cli_value

    env_value = os.environ.get("REPOST_SLEEP_INTERVAL")
    if env_value is not None:
        try:
            return float(env_value)
        except (ValueError, TypeError):
            pass

    return 0.1  # Default value

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


async def repost_from_file(destination, source=None, sleep_interval=None):
    """Reads source message URLs from file and reposts them to the destination channel. Writes new message URLs to output file atomically."""
    session_name = "anon"
    # Directory logic: use ./data/ for user, ./tests/data/ for tests
    input_dir, output_dir = get_data_dirs()
    input_file = source or os.path.join(input_dir, "source_urls.txt")

    # --- Output filenames ---
    legacy_output_file = os.path.join(output_dir, "new_dest_urls.txt")
    legacy_temp_file = legacy_output_file + ".tmp"

    publish_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    normalized_destination = str(normalize_channel_id(destination))
    slug = dest_slug(normalized_destination)
    timestamp_filename = f"{publish_ts}_{slug}.txt"
    ts_output_file = os.path.join(output_dir, timestamp_filename)
    ts_temp_file = ts_output_file + ".tmp"

    # Normalize destination for all downstream logic (already computed above)

    # Get the actual sleep interval to use
    sleep_time = get_sleep_interval(sleep_interval)

    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f:
        source_urls = [line.strip() for line in f if line.strip()]

    print(f"Read {len(source_urls)} source URLs from {input_file}.", file=sys.stderr)
    print(f"Using sleep interval: {sleep_time} seconds between reposts.", file=sys.stderr)

    any_invalid = False
    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        try:
            destination_id = normalized_destination
            try:
                destination_id = int(destination_id)
            except (ValueError, TypeError):
                pass
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

        # Open both temp files so we can write to each simultaneously
        with open(legacy_temp_file, "w", encoding="utf-8") as legacy_out, \
             open(ts_temp_file, "w", encoding="utf-8") as ts_out:
            for i, url in enumerate(source_urls):
                channel, msg_id = parse_telegram_url(url)
                if channel and msg_id:
                    try:
                        source_id = normalize_channel_id(channel)
                        try:
                            source_id = int(source_id)
                        except (ValueError, TypeError):
                            pass
                        message_to_send = await client.get_messages(source_id, ids=msg_id)

                        # --- Media group logic ---
                        grouped_id = getattr(message_to_send, 'grouped_id', None)
                        if grouped_id:
                            # Fetch a wider window of messages around msg_id to ensure all group messages are found
                            fetch_ids = list(range(msg_id - 10, msg_id + 10))
                            group_msgs = await client.get_messages(source_id, ids=fetch_ids)
                            group_msgs = [m for m in group_msgs if getattr(m, 'grouped_id', None) == grouped_id]
                            group_msgs = sorted(group_msgs, key=lambda m: m.id)
                            media_list = []
                            for m in group_msgs:
                                if hasattr(m, 'media') and m.media:
                                    media_list.append(m.media)
                            if media_list:
                                # Only the first item can have a caption in Telegram albums
                                caption = message_to_send.message if hasattr(message_to_send, 'message') else None
                                sent_msgs = await client.send_file(dest_entity, media_list, caption=caption)
                                # send_file returns a list if multiple files, or a single Message if one file
                                if not isinstance(sent_msgs, list):
                                    sent_msgs = [sent_msgs]
                                # Write URLs for each sent message
                                for sent in sent_msgs:
                                    # Format destination URL correctly for private/public channels
                                    if normalized_destination.startswith("-100"):
                                        new_url = f"https://t.me/c/{normalized_destination[4:]}/{sent.id}"
                                    else:
                                        new_url = f"https://t.me/{normalized_destination}/{sent.id}"
                                    legacy_out.write(new_url + "\n")
                                    ts_out.write(new_url + "\n")
                                print(f"Reposted media group {grouped_id} from {channel} to {normalized_destination} as {len(sent_msgs)} messages.")
                                await asyncio.sleep(sleep_time)
                                continue  # Skip the single-message send below
                        # --- End media group logic ---
                        if message_to_send:
                            sent = await client.send_message(dest_entity, message_to_send)
                            # Format destination URL correctly for private/public channels
                            if normalized_destination.startswith("-100"):
                                dest_url = f"https://t.me/c/{normalized_destination[4:]}/{sent.id}"
                            else:
                                dest_url = f"https://t.me/{normalized_destination}/{sent.id}"
                            legacy_out.write(dest_url + "\n")
                            ts_out.write(dest_url + "\n")
                            print(f"Reposted message {msg_id} from {channel} to {normalized_destination} as {dest_url}.")

                            # Sleep between messages, but not after the last one
                            if i < len(source_urls) - 1:
                                await asyncio.sleep(sleep_time)
                        else:
                            print(f"Could not find message with ID {msg_id} in {channel}.")
                    except Exception as e:
                        print(f"Error reposting message {msg_id} from {channel}: {e}", file=sys.stderr)
                else:
                    print(f"Invalid Telegram message URL: {url}", file=sys.stderr)
                    any_invalid = True

    os.replace(legacy_temp_file, legacy_output_file)
    os.replace(ts_temp_file, ts_output_file)
    print(f"Wrote new destination URLs to {legacy_output_file} (legacy) and {ts_output_file}.")
    if any_invalid:
        sys.exit(1)
