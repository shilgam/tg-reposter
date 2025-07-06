import os
from pathlib import Path
import re

import pytest

from src.reposter import repost_from_file, get_data_dirs
from src.utils_files import dest_slug

SOURCE_URL = "https://t.me/publicsource/4"
DEST_PUBLIC = "@dummy_channel991"


def _write_source_url():
    input_dir, _ = get_data_dirs()
    os.makedirs(input_dir, exist_ok=True)
    with open(os.path.join(input_dir, "source_urls.txt"), "w") as f:
        f.write(SOURCE_URL + "\n")


def _count_files(slug, suffix):
    _, output_dir = get_data_dirs()
    pattern = re.compile(rf"^\d{{8}}_\d{{6}}_{re.escape(slug)}{re.escape(suffix)}\.txt$")
    return [p for p in Path(output_dir).iterdir() if p.is_file() and pattern.match(p.name)]


@pytest.mark.asyncio
async def test_first_run_no_mark(temp_dirs, mock_telethon_client):
    _write_source_url()
    slug = dest_slug(DEST_PUBLIC)

    await repost_from_file(DEST_PUBLIC)

    normal_files = _count_files(slug, "")
    marked_files = _count_files(slug, ".marked_for_deletion")
    assert len(normal_files) == 1
    assert not marked_files


@pytest.mark.asyncio
async def test_second_run_marks_previous(temp_dirs, mock_telethon_client):
    slug = dest_slug(DEST_PUBLIC)

    # First run
    _write_source_url()
    await repost_from_file(DEST_PUBLIC)

    # Second run – should tag previous
    _write_source_url()
    await repost_from_file(DEST_PUBLIC)

    normal_files = _count_files(slug, "")
    marked_files = _count_files(slug, ".marked_for_deletion")

    assert len(normal_files) == 1  # only latest remains untagged
    assert len(marked_files) == 1  # previous tagged


@pytest.mark.asyncio
async def test_already_tagged_is_skipped(temp_dirs, mock_telethon_client):
    slug = dest_slug(DEST_PUBLIC)

    # First run
    _write_source_url()
    await repost_from_file(DEST_PUBLIC)

    # Manually tag previous run
    _, output_dir = get_data_dirs()
    normal_files = _count_files(slug, "")
    prev_path = normal_files[0]
    tagged_path = prev_path.with_suffix("")
    tagged_path = Path(str(tagged_path) + ".marked_for_deletion.txt")
    prev_path.rename(tagged_path)

    # Second run (there is already a tagged file)
    _write_source_url()
    await repost_from_file(DEST_PUBLIC)

    marked_files = _count_files(slug, ".marked_for_deletion")
    # Should still be exactly 1 marked file, not duplicate
    assert len(marked_files) == 1
