import os
import re
import sys

TEST_MODE = os.environ.get("TEST_MODE") == "1"

if TEST_MODE:
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


async def repost_from_file(destination):
    """Reads source message URLs from file and reposts them to the destination channel. Writes new message URLs to output file atomically."""
    session_name = "anon"
    input_file = "./temp/input/source_urls.txt"
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

        with open(temp_file, "w", encoding="utf-8") as out:
            for url in source_urls:
                channel, msg_id = parse_telegram_url(url)
                if channel and msg_id:
                    try:
                        source_id = normalize_channel_id(channel)
                        try:
                            source_id = int(source_id)
                        except (ValueError, TypeError):
                            pass
                        message_to_send = await client.get_messages(source_id, ids=msg_id)
                        if message_to_send:
                            sent = await client.send_message(dest_entity, message_to_send)
                            new_url = f"https://t.me/{destination}/{sent.id}"
                            out.write(new_url + "\n")
                            print(f"Reposted message {msg_id} from {channel} to {destination} as {new_url}.")
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