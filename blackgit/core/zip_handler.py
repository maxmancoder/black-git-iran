import zipfile
from pathlib import Path

from .hasher import sha256_file
from .ignore import load_ignore_patterns, should_ignore
from .metadata import METADATA_FILENAME, create_metadata, metadata_json


class ZipError(Exception):
    pass


def _iter_project_files(project_path: Path, patterns: list[str]):
    for f in sorted(project_path.rglob("*")):
        if not f.is_file():
            continue
        if f.name == METADATA_FILENAME and f.parent == project_path:
            continue
        rel = f.relative_to(project_path).as_posix()
        if should_ignore(rel, patterns):
            continue
        yield f, rel


def create_project_zip(
    project_path: Path,
    zip_path: Path,
    version: str,
    author: str = "",
    message: str = "",
) -> dict:
    """ZIP project contents (originals stay untouched). Returns metadata dict."""
    if not project_path.is_dir():
        raise ZipError(f"پروژه پیدا نشد: {project_path}")

    patterns = load_ignore_patterns(project_path)
    files = list(_iter_project_files(project_path, patterns))
    if not files:
        raise ZipError("هیچ فایلی برای ارسال وجود ندارد")

    file_hashes = {rel: sha256_file(f) for f, rel in files}
    meta = create_metadata(
        project=project_path.name,
        version=version,
        files=len(files),
        file_hashes=file_hashes,
        author=author,
        message=message,
    )

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f, rel in files:
            zf.write(f, rel)
        zf.writestr(METADATA_FILENAME, metadata_json(meta))

    meta["zipSha256"] = sha256_file(zip_path)
    meta["zipSize"] = zip_path.stat().st_size
    return meta


def extract_zip(zip_path: Path, dest: Path) -> Path:
    """Safely extract into dest. Returns dest."""
    if not zip_path.exists():
        raise ZipError(f"فایل زیپ پیدا نشد: {zip_path}")

    dest.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                raise ZipError(f"زیپ خراب است (فایل معیوب: {bad})")
            for info in zf.infolist():
                name = info.filename.replace("\\", "/")
                if name.startswith("/") or ".." in name.split("/"):
                    raise ZipError(f"مسیر ناامن در زیپ: {info.filename}")
            zf.extractall(dest)
    except zipfile.BadZipFile as e:
        raise ZipError(f"فایل زیپ نامعتبر است: {e}") from e
    return dest


def verify_extracted(extracted: Path, min_files: int = 1) -> dict | None:
    """Check extracted folder has content; return metadata if present."""
    count = sum(1 for f in extracted.rglob("*") if f.is_file())
    if count < min_files:
        raise ZipError("زیپ خالی یا ناقص است")
    from .metadata import read_metadata

    meta = read_metadata(extracted / METADATA_FILENAME)
    if meta:
        expected = meta.get("files")
        if expected and count - 1 != expected and count != expected:
            raise ZipError(
                f"تعداد فایل نادرست: انتظار {expected}، دریافت {max(count - 1, count)}"
            )
    return meta
