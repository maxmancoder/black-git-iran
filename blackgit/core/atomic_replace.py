import shutil
from datetime import datetime
from pathlib import Path

from .zip_handler import ZipError


def backup_project(project_path: Path, backup_root: Path) -> Path:
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = backup_root / f"backup-{project_path.name}-{stamp}"
    n = 1
    while dest.exists():
        dest = backup_root / f"backup-{project_path.name}-{stamp}-{n}"
        n += 1
    shutil.copytree(project_path, dest)
    return dest


def _normalize_root(extracted: Path) -> Path:
    """If zip contained a single top folder, use it as content root."""
    entries = [e for e in extracted.iterdir() if e.name not in (".", "..")]
    files = [e for e in entries if e.is_file()]
    dirs = [e for e in entries if e.is_dir()]
    if not files and len(dirs) == 1:
        return dirs[0]
    return extracted


def atomic_replace(
    project_path: Path,
    extracted: Path,
    backup_root: Path,
    mode: str = "full",
) -> dict:
    """
    mode:
      full     -> clear target, copy extracted content (Restore کامل)
      merge    -> overwrite same-name files, keep extras
      new_only -> copy only files that don't exist in target
    """
    if not project_path.is_dir():
        raise ZipError(f"پروژه مقصد وجود ندارد: {project_path}")

    # safety: never clear the target if extracted lives inside it (or vice versa)
    try:
        proj_r = project_path.resolve()
        ext_r = extracted.resolve()
        if proj_r == ext_r or proj_r in ext_r.parents or ext_r in proj_r.parents:
            raise ZipError(
                "پوشه استخراج و پروژه مقصد همپوشانی دارند — عملیات لغو شد"
            )
    except OSError:
        pass

    content_root = _normalize_root(extracted)
    backup_path = backup_project(project_path, backup_root)

    copied = 0
    skipped = 0

    if mode == "full":
        for entry in project_path.iterdir():
            if entry.name == ".git" and entry.is_dir():
                continue  # keep git history if present
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
        for src in content_root.rglob("*"):
            rel = src.relative_to(content_root)
            dst = project_path / rel
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied += 1
    elif mode in ("merge", "new_only"):
        for src in content_root.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(content_root)
            dst = project_path / rel
            if dst.exists() and mode == "new_only":
                skipped += 1
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
    else:
        raise ZipError(f"حالت نامعتبر: {mode}")

    return {"copied": copied, "skipped": skipped, "backup": str(backup_path)}


def cleanup_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
