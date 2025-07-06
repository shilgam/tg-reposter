from typing import Optional
import os
import sys
from datetime import datetime
from pathlib import Path

from .reposter import (
    parse_telegram_url,
    TelegramClient,
    API_ID,
    API_HASH,
    get_data_dirs,
    normalize_channel_id,
)

from .utils_files import dest_slug, list_runs


async def delete_from_file(
    delete_urls_file: Optional[str] = None,
    destination: Optional[str] = None,
) -> None:
    """
    Async: Delete Telegram messages listed in the given file. If *delete_urls_file* is ``None`` the
    function will attempt to auto-detect the latest ``.marked_for_deletion`` file for the provided
    *destination* channel.  The *destination* parameter **must** be supplied in this case; the
    legacy fallback to ``new_dest_urls.txt`` has been removed.

    The function parses URLs, extracts message IDs and destination channel, and deletes messages via
    Telethon.  It stops immediately on any error to ensure data integrity.  On success, the
    processed file is renamed to ``{publish_ts}_{slug}.deleted_at_{delete_ts}.txt``.
    """
    if delete_urls_file is None:
        if destination is None:
            raise FileNotFoundError(
                "No delete file provided and destination not specified for auto-detection."
            )

        # Auto-detect latest .marked_for_deletion for given destination slug
        _, output_dir = get_data_dirs()
        norm_dest = str(normalize_channel_id(destination))
        slug = dest_slug(norm_dest)
        candidates = list_runs(slug, status=["marked_for_deletion"])
        if not candidates:
            raise FileNotFoundError(
                f"No .marked_for_deletion file found for destination '{destination}'."
            )
        delete_urls_file = str(candidates[0])

    with open(delete_urls_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    parsed = []
    for url in urls:
        channel, msg_id = parse_telegram_url(url)
        if channel and msg_id:
            # Keep original channel value for entity resolution
            parsed.append((channel, msg_id))
        else:
            print(f"Invalid URL: {url}", file=sys.stderr)

    session_name = "anon"
    should_exit = False
    exit_message = ""

    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        for channel, msg_id in parsed:
            # For private channels (starting with -100), use int; for public, use string
            if str(channel).startswith('-100'):
                entity_id = int(channel)
            else:
                entity_id = channel

            # Entity resolution - if this fails, exit immediately
            entity = None
            try:
                entity = await client.get_entity(entity_id)
            except Exception as e1:
                print(f"[WARN] get_entity failed for channel '{entity_id}': {e1}", file=sys.stderr)
                try:
                    entity = await client.get_input_entity(entity_id)
                except Exception as e2:
                    print(f"[ERROR] get_input_entity also failed for channel '{entity_id}': {e2}", file=sys.stderr)
                    print(f"Could not find the channel entity '{entity_id}'.", file=sys.stderr)
                    should_exit = True
                    exit_message = "Entity resolution failed"
                    break

            # Message deletion - if this fails, exit immediately
            try:
                await client.delete_messages(entity, msg_id)
                print(f"Deleted message {msg_id} from {channel}.")
            except Exception as e:
                print(f"Error deleting message {msg_id} from {channel}: {e}", file=sys.stderr)
                # Exit immediately on any delete error for data integrity
                should_exit = True
                exit_message = f"Delete operation failed: {e}"
                break

    # Exit outside the client context if needed
    if should_exit:
        print(f"[DEBUG] Exiting due to: {exit_message}", file=sys.stderr)
        raise SystemExit(1)

    # Rename the processed file to {TIMESTAMP}_deleted.txt
    import re

    dir_name = os.path.dirname(delete_urls_file)
    base_name = os.path.basename(delete_urls_file)

    # Determine original publish_ts and slug if encoded in filename
    m = re.match(r"^(?P<publish>\d{8}_\d{6})_(?P<slug>[^.]+)", base_name)
    if m:
        publish_ts = m.group("publish")
        slug = m.group("slug")
    else:
        publish_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = Path(base_name).stem.replace("new_dest_urls", "legacy")

    delete_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = os.path.join(dir_name, f"{publish_ts}_{slug}.deleted_at_{delete_ts}.txt")

    os.replace(delete_urls_file, new_name)
    print(f"Renamed {base_name} to {os.path.basename(new_name)} after successful deletion.")
