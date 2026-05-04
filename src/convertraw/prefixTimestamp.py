"""
Extract the acquisition start time from an mzML file and rename it with a
YYYY_MM_DD_HH_MM__ prefix.
"""

import re
from pathlib import Path


# Regex to find startTimeStamp inside the <run …> opening tag without loading
# the whole file into an XML parser (faster for large mzML files).
_RUN_TAG_RE = re.compile(r'<run\b[^>]*\bstartTimeStamp=["\']([^"\']+)["\']', re.IGNORECASE)


def extract_start_timestamp(mzml_file: Path) -> str | None:
    """
    Return the startTimeStamp string from *mzml_file*, or None if not found.
    Only the first few KB of the file are scanned (the <run> tag always appears
    near the top of an mzML file).
    """
    with open(mzml_file, "r", encoding="utf-8", errors="replace") as fh:
        # Read in chunks until we find the tag or exhaust a reasonable header
        header = fh.read(65536)  # 64 KB is always enough for the preamble
    m = _RUN_TAG_RE.search(header)
    if m:
        return m.group(1)
    return None


def timestamp_to_prefix(ts: str) -> str:
    """
    Convert an ISO-8601 timestamp such as '2025-04-21T03:53:19' to a file-name
    prefix of the form 'YYYY_MM_DD_HH_MM__'.
    """
    # Accept both 'T' and ' ' as date/time separator; strip timezone suffix.
    ts_clean = ts.strip().replace(" ", "T")
    try:
        from datetime import datetime

        dt = datetime.fromisoformat(ts_clean)
        return dt.strftime("%Y_%m_%d_%H_%M__")
    except ValueError:
        # Fallback: replace separators manually
        safe = ts_clean.replace(":", "_").replace("T", "_").replace("-", "_")
        return safe[:16].rstrip("_") + "__"


def prefix_mzml_with_timestamp(mzml_file: Path, log: list[str] | None = None) -> Path | None:
    """
    Rename *mzml_file* by prepending its acquisition timestamp.
    Returns the new Path on success, or None if the timestamp could not be found.
    Appends messages to *log* (or prints directly when *log* is None).
    """

    def _log(msg: str) -> None:
        if log is None:
            print(msg)
        else:
            log.append(msg)

    ts = extract_start_timestamp(mzml_file)
    if ts is None:
        _log(f"  WARNING: No startTimeStamp found in '{mzml_file.name}', skipping rename.")
        return None

    prefix = timestamp_to_prefix(ts)
    new_name = prefix + mzml_file.name
    new_path = mzml_file.parent / new_name

    if new_path.exists():
        _log(f"  WARNING: Target already exists, skipping rename: {new_path.name}")
        return new_path

    mzml_file.rename(new_path)
    _log(f"  Renamed: {mzml_file.name}  ->  {new_path.name}")
    return new_path
