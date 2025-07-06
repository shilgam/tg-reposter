import os
from pathlib import Path
import pytest

from src.delete import delete_from_file
from src.reposter import get_data_dirs
from src.utils_files import dest_slug

DEST_PUBLIC = "@dummy_channel991"
SLUG = dest_slug(DEST_PUBLIC)


def _create_marked_file(name: str, content: str = "https://t.me/c/123/1\n") -> Path:
    _, output_dir = get_data_dirs()
    os.makedirs(output_dir, exist_ok=True)
    p = Path(output_dir) / name
    p.write_text(content)
    return p


@pytest.mark.asyncio
async def test_latest_marked_selected(temp_dirs, mock_telethon_client):
    # Older file
    older = _create_marked_file(f"20250705_120000_{SLUG}.marked_for_deletion.txt")
    # Newer file
    newer = _create_marked_file(f"20250706_120000_{SLUG}.marked_for_deletion.txt")

    await delete_from_file(None, destination=DEST_PUBLIC)

    # Newer should be processed and renamed (no longer exists)
    assert not newer.exists()
    # Older should remain
    assert older.exists()


@pytest.mark.asyncio
async def test_error_when_none_found(temp_dirs, mock_telethon_client):
    with pytest.raises(FileNotFoundError):
        await delete_from_file(None, destination="@someotherdest")
