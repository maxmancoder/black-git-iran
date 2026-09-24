import json
from datetime import datetime
from pathlib import Path

METADATA_FILENAME = ".black-sync.json"


def create_metadata(
    project: str,
    version: str,
    files: int,
    file_hashes: dict[str, str] | None = None,
    author: str = "",
    message: str = "",
) -> dict:
    return {
        "project": project,
        "version": version,
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "files": files,
        "author": author,
        "message": message,
        "fileHashes": file_hashes or {},
    }


def read_metadata(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def metadata_json(meta: dict) -> bytes:
    return json.dumps(meta, indent=2, ensure_ascii=False).encode("utf-8")
