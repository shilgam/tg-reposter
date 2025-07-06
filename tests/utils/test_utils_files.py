import os
from datetime import datetime
from pathlib import Path

import pytest

from src.utils_files import dest_slug, parse_publish_ts, list_runs
from src.reposter import get_data_dirs


class TestDestSlug:
    def test_dest_slug_numeric_private(self):
        assert dest_slug("-100123456") == "123456"
        # Extra sanity – numeric without -100 should just strip any '-'
        assert dest_slug("-987654") == "987654"
        # Public channel username
        assert dest_slug("@mychannel") == "mychannel"


class TestParsePublishTs:
    def test_parse_publish_ts_valid_invalid(self):
        dt = parse_publish_ts("20250706_153045_slug.txt")
        assert dt == datetime(2025, 7, 6, 15, 30, 45)

        assert parse_publish_ts("not_a_timestamp.txt") is None
        assert parse_publish_ts("20250706_1530_slug.txt") is None  # wrong format


class TestListRuns:
    def _create_file(self, directory: Path, name: str):
        path = directory / name
        directory.mkdir(parents=True, exist_ok=True)
        path.write_text("dummy")
        return path

    def test_list_runs_filters_and_orders(self, temp_dirs):
        _, output_dir_str = get_data_dirs()
        output_dir = Path(output_dir_str)

        # Clean slate
        if output_dir.exists():
            for f in output_dir.iterdir():
                f.unlink()
        else:
            output_dir.mkdir(parents=True)

        # Create test files (different timestamps & suffixes)
        self._create_file(output_dir, "20250705_120000_slug.txt")
        self._create_file(output_dir, "20250705_120000_other.txt")  # different slug, should be ignored
        self._create_file(output_dir, "20250706_120000_slug.marked_for_deletion.txt")
        self._create_file(output_dir, "20250707_120000_slug.txt")
        self._create_file(output_dir, "20250707_120000_slug.marked_for_deletion.txt")

        expected_order = [
            "20250707_120000_slug.marked_for_deletion.txt",
            "20250707_120000_slug.txt",
            "20250706_120000_slug.marked_for_deletion.txt",
            "20250705_120000_slug.txt",
        ]

        result_paths = list_runs("slug", status=["", "marked_for_deletion"])
        result_names = [p.name for p in result_paths]

        assert result_names == expected_order

        # Ensure files with other slug are excluded
        assert "20250705_120000_other.txt" not in result_names
