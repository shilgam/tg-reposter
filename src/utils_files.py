from __future__ import annotations

"""Utility helpers for file-naming conventions used by the repost / delete workflow.

This module deliberately contains **no Telegram logic**.  It focuses purely on
parsing and file-system helpers that will be reused by both the repost and
delete flows.

Patterns handled (YYYYMMDD_HHMMSS timestamp):

1. Untagged run output          -> ``{publish_ts}_{slug}.txt``
2. Marked-for-deletion tagging  -> ``{publish_ts}_{slug}.marked_for_deletion.txt``

Later phases introduce additional suffixes (``.deleted_at_…``) but the helpers
here focus on the two patterns required for Plan step 1.
"""

import os

# NOTE: We define a lightweight copy of get_data_dirs here to avoid circular
# imports.  This helper is pure-utility (no Telegram dependencies) and keeps
# src.utils_files fully standalone.


def _get_data_dirs():
    """Return (input_dir, output_dir) matching the logic in src.reposter.

    Duplicated here to avoid circular imports; kept minimal and in sync with
    the original.
    """

    TEST_MODE = os.environ.get("TEST_MODE") == "1"

    def _is_running_tests() -> bool:
        import inspect

        for frame in inspect.stack():
            if 'pytest' in frame.filename or 'unittest' in frame.filename:
                return True
        return False

    if TEST_MODE or _is_running_tests():
        return "./tests/data/input", "./tests/data/output"
    return "./data/input", "./data/output"


from datetime import datetime
import re
from pathlib import Path
from typing import Iterable, List


__all__ = [
    "dest_slug",
    "parse_publish_ts",
    "list_runs",
]

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def dest_slug(dest: str) -> str:
    """Return a slug suitable for filenames based on a Telegram destination.

    If *dest* is numeric and starts with the Telegram private-channel prefix
    ``-100``, that prefix is stripped to make the slug shorter and to avoid the
    leading minus sign, e.g.::

        >>> dest_slug("-100123456789")
        '123456789'

    For all other inputs the string is returned with a leading "@" removed (if
    present) so that public channel usernames like "@mychannel" become
    "mychannel".
    """

    # Remove surrounding whitespace just in case
    dest = dest.strip()

    # Numeric IDs (may start with optional '-')
    numeric_part = dest.lstrip("-")
    if numeric_part.isdigit():
        # Telegram private IDs always start with -100; strip that if present
        if dest.startswith("-100"):
            return dest[4:]
        # Otherwise return digits without any leading '-'
        return numeric_part

    # Non-numeric – likely a username, strip leading "@" if present
    if dest.startswith("@"):
        return dest[1:]

    return dest


def parse_publish_ts(path: str | Path) -> datetime | None:
    """Parse the ``YYYYMMDD_HHMMSS`` publish timestamp from a filename.

    Returns ``datetime`` if the filename starts with a valid timestamp block,
    otherwise *None*.
    """

    fname = Path(path).name  # ensure we only look at the final component
    m = re.match(r"^(\d{8}_\d{6})_", fname)
    if not m:
        return None

    try:
        return datetime.strptime(m.group(1), "%Y%m%d_%H%M%S")
    except ValueError:
        # In case the numeric part can't be parsed (shouldn't normally happen)
        return None


def list_runs(dest_slug: str, status: Iterable[str] | None = None) -> List[Path]:
    """Return run-files for *dest_slug* filtered by *status*.

    Parameters
    ----------
    dest_slug:
        The slug returned by :func:`dest_slug`.
    status:
        Iterable containing status suffixes to include.  The empty string ""
        represents *no suffix* (the base run file).  Defaults to
        ["", "marked_for_deletion"].  Values are matched literally **without**
        the leading dot.

    Returns
    -------
    list[Path]
        Sorted **newest → oldest** by publish timestamp.
    """

    if status is None:
        status = ("", "marked_for_deletion")

    # Normalise to set for faster membership checks and ensure strings
    status_set = {str(s) for s in status}

    _, output_dir_str = _get_data_dirs()
    output_dir = Path(output_dir_str)
    if not output_dir.exists():
        # Nothing to return
        return []

    pattern_re = re.compile(
        rf"^(\d{{8}}_\d{{6}})_{re.escape(dest_slug)}(?:\.(?P<suffix>[\w_]+))?\.txt$"
    )

    matches: list[tuple[Path, datetime, str]] = []  # (path, ts, suffix)
    for p in output_dir.iterdir():
        if not p.is_file():
            continue
        m = pattern_re.match(p.name)
        if not m:
            continue
        suffix = m.group("suffix") or ""
        if suffix not in status_set:
            continue
        ts = parse_publish_ts(p)
        if ts is None:
            # Skip files without valid timestamp – defensive
            continue
        matches.append((p, ts, suffix))

    # Primary: timestamp DESC, Secondary: suffix presence (non-empty suffix first)
    matches.sort(key=lambda t: (-t[1].timestamp(), t[2] == ""))
    return [p for p, _, _ in matches]
