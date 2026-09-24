import fnmatch
from pathlib import Path

DEFAULT_IGNORES = [
    "node_modules/",
    ".git/",
    ".hg/",
    ".svn/",
    ".next/",
    ".nuxt/",
    ".venv/",
    "venv/",
    "__pycache__/",
    "dist/",
    "build/",
    "target/",
    "*.log",
    "*.pyc",
    ".DS_Store",
    "Thumbs.db",
    "upload-one-time/",
    "backups/",
]

IGNORE_FILENAME = ".blackgitignore"


def load_ignore_patterns(project_path: Path | None = None) -> list[str]:
    patterns = list(DEFAULT_IGNORES)
    if project_path:
        ig = project_path / IGNORE_FILENAME
        if ig.exists():
            for line in ig.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def should_ignore(rel_path: str, patterns: list[str]) -> bool:
    rel = rel_path.replace("\\", "/")
    name = rel.split("/")[-1]
    for pat in patterns:
        pat = pat.replace("\\", "/")
        if pat.endswith("/"):
            if rel.startswith(pat) or f"/{pat}" in f"/{rel}":
                return True
        elif fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(name, pat):
            return True
    return False
