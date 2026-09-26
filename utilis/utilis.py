import os
from datetime import datetime


def max_local_mtime(directory: str) -> datetime | None:
    """
    Find the most recent modification time among all files in the given directories.
    Checks multiple directories (e.g. staging and shared) to avoid re-downloading
    files that have already been moved.

    :param dirs: One or more directory paths to scan.
    :return: The latest mtime or None if no files found.
    """
    latest: float | None = None

    if not os.path.isdir(directory):
        return None
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            mtime = os.path.getmtime(filepath)
            if latest is None or mtime > latest:
                latest = mtime

    if latest is None:
        return None
    return datetime.fromtimestamp(latest)
