import os
import re
from pathlib import Path

import pytest

from src.reposter import repost_from_file
from src.utils_files import dest_slug
from src.reposter import get_data_dirs


SOURCE_URL = "https://t.me/publicsource/4"
DEST_PUBLIC = "@dummy_channel991"


@pytest.mark.asyncio
async def test_timestamp_file_written(temp_dirs, mock_telethon_client):
    """Verify that repost writes a timestamped output file."""
    # Arrange – write single source URL
    input_dir, output_dir = get_data_dirs()
    source_file = os.path.join(input_dir, "source_urls.txt")
    os.makedirs(input_dir, exist_ok=True)
    with open(source_file, "w") as f:
        f.write(SOURCE_URL + "\n")

    # Act
    await repost_from_file(DEST_PUBLIC)

    # Assert – find file with pattern YYYYMMDD_HHMMSS_slug.txt
    slug = dest_slug(DEST_PUBLIC)
    pattern = re.compile(rf"^\d{{8}}_\d{{6}}_{re.escape(slug)}\.txt$")
    files = [p for p in Path(output_dir).iterdir() if p.is_file() and pattern.match(p.name)]
    assert files, "No timestamped file created"

    # Ensure file contains at least one URL line
    with open(files[0]) as f:
        lines = [l.strip() for l in f if l.strip()]
    assert len(lines) == 1


@pytest.mark.asyncio
async def test_legacy_file_still_written(temp_dirs, mock_telethon_client):
    """Verify that new_dest_urls.txt is still written for backward compatibility."""
    # Arrange
    input_dir, output_dir = get_data_dirs()
    source_file = os.path.join(input_dir, "source_urls.txt")
    os.makedirs(input_dir, exist_ok=True)
    with open(source_file, "w") as f:
        f.write(SOURCE_URL + "\n")

    # Act
    await repost_from_file(DEST_PUBLIC)

    # Assert legacy file exists and non-empty
    legacy_file = os.path.join(output_dir, "new_dest_urls.txt")
    assert os.path.exists(legacy_file)
    with open(legacy_file) as f:
        lines = [l.strip() for l in f if l.strip()]
    assert len(lines) == 1
