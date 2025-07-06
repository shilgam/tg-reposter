import os
import re
from pathlib import Path

import pytest

from src.delete import delete_from_file
from src.reposter import get_data_dirs


@pytest.mark.asyncio
async def test_filename_contains_both_timestamps(temp_dirs, mock_telethon_client):
    input_dir, output_dir = get_data_dirs()
    # Prepare test delete file with timestamp+slug
    test_file = Path(output_dir) / "20250705_120000_dummy.marked_for_deletion.txt"
    test_file.write_text("https://t.me/dummy/1\n")

    await delete_from_file(None, destination="@dummy")

    # After deletion, file should be renamed to include deleted_at timestamp
    renamed = list(Path(output_dir).glob("20250705_120000_dummy.deleted_at_*.txt"))
    assert renamed, "Renamed file not found with dual timestamps"
