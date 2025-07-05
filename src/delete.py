from typing import Optional
import os
import sys
from datetime import datetime
from pathlib import Path
from .reposter import (
    parse_telegram_url,
    TEST_MODE,
    TelegramClient,
    API_ID,
    API_HASH,
    get_data_dirs,
)
from .utils_files import dest_slug, list_runs, parse_publish_ts

async def delete_from_file(file: Optional[str] = None, destination: Optional[str] = None) -> None:
    """
    Delete Telegram messages listed in the given file. If file is None, require destination and auto-detect
    the latest .marked_for_deletion.txt for that dest_slug. After processing, always rename the file to
    {publish_ts}_{dest_slug}.deleted_at_{delete_ts}.txt
    """
    input_dir, output_dir = get_data_dirs()
    if file is None:
        if not destination:
            raise ValueError("If file is None, destination must be provided.")
        slug = dest_slug(str(destination))
        candidates = list_runs(slug, "marked_for_deletion")
        if not candidates:
            raise FileNotFoundError(f"No .marked_for_deletion.txt file found for destination {destination} in {output_dir}/.")
        # Pick the latest by timestamp
        file = str(candidates[-1])
    else:
        slug = dest_slug(str(destination)) if destination else None
    with open(file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    parsed = []
    for url in urls:
        channel, msg_id = parse_telegram_url(url)
        if channel and msg_id:
            parsed.append((channel, msg_id))
        else:
            print(f"Invalid URL: {url}", file=sys.stderr)
    session_name = "anon"
    should_exit = False
    exit_message = ""
    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        for channel, msg_id in parsed:
            if str(channel).startswith('-100'):
                entity_id = int(channel)
            else:
                entity_id = channel
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
            try:
                await client.delete_messages(entity, msg_id)
                print(f"Deleted message {msg_id} from {channel}.")
            except Exception as e:
                print(f"Error deleting message {msg_id} from {channel}: {e}", file=sys.stderr)
                should_exit = True
                exit_message = f"Delete operation failed: {e}"
                break
    if should_exit:
        print(f"[DEBUG] Exiting due to: {exit_message}", file=sys.stderr)
        raise SystemExit(1)
    # Always rename processed file to {publish_ts}_{dest_slug}.deleted_at_{delete_ts}.txt
    dir_name = os.path.dirname(file)
    base_name = os.path.basename(file)
    # Try to extract publish_ts and slug from file name
    m = None
    if slug:
        m = Path(base_name).name.split(f"_{slug}.marked_for_deletion.txt")[0] if base_name.endswith(f"_{slug}.marked_for_deletion.txt") else None
    if not m:
        # fallback: try to extract timestamp from file name
        ts = parse_publish_ts(base_name)
        publish_ts = ts.strftime("%Y%m%d_%H%M%S") if ts else datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        publish_ts = m
    delete_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = os.path.join(dir_name, f"{publish_ts}_{slug}.deleted_at_{delete_ts}.txt")
    os.replace(file, new_name)
    print(f"Renamed {base_name} to {os.path.basename(new_name)} after successful deletion.")
