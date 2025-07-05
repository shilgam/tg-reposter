import re
import os
import inspect
from pathlib import Path
from datetime import datetime
from typing import Literal, Optional, List

def dest_slug(dest: str) -> str:
    """Return a slug for the destination: strip '-100' prefix if numeric."""
    if dest.startswith('-100') and dest[4:].isdigit():
        return dest[4:]
    return dest

def parse_publish_ts(path: str) -> Optional[datetime]:
    """Extract and parse the publish timestamp from a file path. Returns None if not found or invalid."""
    m = re.search(r'(\d{8}_\d{6})', Path(path).name)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d_%H%M%S")
        except ValueError:
            return None
    return None

def _get_output_dir() -> Path:
    """Return the correct output directory depending on test mode.

    This replicates the logic from src.reposter.get_data_dirs() without importing that module,
    in order to avoid circular import issues.
    """
    test_mode_env = os.getenv("TEST_MODE") == "1"
    running_tests = any('pytest' in frame.filename or 'unittest' in frame.filename for frame in inspect.stack())
    if test_mode_env or running_tests:
        return Path("./tests/data/output")
    return Path("./data/output")

def list_runs(dest_slug: str, status: Literal["", "marked_for_deletion"]) -> List[Path]:
    """Return a sorted list of Path objects in the output directory for the given destination slug.

    Args:
        dest_slug: The slugified destination identifier.
        status: ""  for normal published runs, or "marked_for_deletion" for files awaiting deletion.

    The function is aware of test mode via get_data_dirs(), so the correct data/output directory is
    used both in production (./data/output) and during tests (./tests/data/output).
    """
    output_dir = _get_output_dir()

    if status == "marked_for_deletion":
        pattern = f"*_{dest_slug}.marked_for_deletion.txt"
    else:
        # Match files that end with just the slug and .txt, but exclude lifecycle suffixes
        # such as .marked_for_deletion or .deleted_at_X
        pattern = f"*_{dest_slug}.txt"
    return sorted(output_dir.glob(pattern))
