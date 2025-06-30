from typing import Optional
import os
import glob
import sys
import asyncio
from datetime import datetime
from .reposter import parse_telegram_url, normalize_channel_id, TEST_MODE, TelegramClient, API_ID, API_HASH


def delete_from_file(delete_urls_file: Optional[str] = None) -> None:
    """
    Delete Telegram messages listed in the given file. If no file is provided,
    auto-detect the most recent dest_urls_to_delete.txt in ./data/output/.
    Parses URLs, extracts message IDs and destination channel, and deletes messages via Telethon.
    Stops immediately on any error to ensure data integrity. On success, renames the processed file
    to {TIMESTAMP}_deleted.txt.
    """
    if delete_urls_file is None:
        files = glob.glob('./data/output/dest_urls_to_delete.txt')
        if not files:
            raise FileNotFoundError('No dest_urls_to_delete.txt found in ./data/output/.')
        # If multiple, pick the most recent by modification time
        files = sorted(files, key=os.path.getmtime, reverse=True)
        delete_urls_file = files[0]

    with open(delete_urls_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    parsed = []
    for url in urls:
        channel, msg_id = parse_telegram_url(url)
        if channel and msg_id:
            channel = normalize_channel_id(channel)
            parsed.append((channel, msg_id))
        else:
            print(f"Invalid Telegram message URL: {url}", file=sys.stderr)

    async def _delete():
        session_name = "anon"
        async with TelegramClient(session_name, API_ID, API_HASH) as client:
            for channel, msg_id in parsed:
                try:
                    channel_id = channel
                    try:
                        channel_id = int(channel_id)
                    except (ValueError, TypeError):
                        pass
                    try:
                        entity = await client.get_entity(channel_id)
                    except Exception as e1:
                        print(f"[WARN] get_entity failed for channel '{channel_id}': {e1}", file=sys.stderr)
                        try:
                            entity = await client.get_input_entity(channel_id)
                        except Exception as e2:
                            print(f"[ERROR] get_input_entity also failed for channel '{channel_id}': {e2}", file=sys.stderr)
                            print(f"Could not find the channel entity '{channel_id}'.", file=sys.stderr)
                            sys.exit(1)
                    await client.delete_messages(entity, msg_id)
                    print(f"Deleted message {msg_id} from {channel}.")
                except Exception as e:
                    print(f"Error deleting message {msg_id} from {channel}: {e}", file=sys.stderr)
                    sys.exit(1)
    asyncio.run(_delete())

    # Rename the processed file to {TIMESTAMP}_deleted.txt
    dir_name = os.path.dirname(delete_urls_file)
    base_name = os.path.basename(delete_urls_file)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = os.path.join(dir_name, f"{timestamp}_deleted.txt")
    os.replace(delete_urls_file, new_name)
    print(f"Renamed {base_name} to {os.path.basename(new_name)} after successful deletion.")
