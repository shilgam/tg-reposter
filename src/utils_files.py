import re
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

def list_runs(dest_slug: str, status: Literal["", "marked_for_deletion"]) -> List[Path]:
    """List files for a given dest_slug and status in the output directory."""
    output_dir = Path("./data/output")
    pattern = f"*_{dest_slug}"
    if status == "marked_for_deletion":
        pattern = f"*_{{dest_slug}}.marked_for_deletion.txt"
    else:
        pattern = f"*_{{dest_slug}}.txt"
    return sorted(output_dir.glob(pattern))
