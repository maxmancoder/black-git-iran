import json
import os
from dataclasses import dataclass, asdict, fields
from pathlib import Path


def app_data_dir() -> Path:
    base = Path(os.environ.get("APPDATA", str(Path.home()))) / "BlackGitIran"
    base.mkdir(parents=True, exist_ok=True)
    return base


@dataclass
class Settings:
    rubika_group_url: str = ""
    project_path: str = ""
    temp_path: str = ""
    receive_mode: str = "full"  # full | merge | new_only
    author: str = ""
    transport: str = "rubika"  # rubika | lan (future)

    @staticmethod
    def load() -> "Settings":
        path = app_data_dir() / "settings.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                known = {f.name for f in fields(Settings)}
                return Settings(**{k: v for k, v in data.items() if k in known})
            except (json.JSONDecodeError, TypeError):
                pass
        s = Settings()
        if not s.temp_path:
            s.temp_path = str(Path(os.environ.get("TEMP", "/tmp")) / "BlackGitIran" / "upload-one-time")
        return s

    def save(self) -> None:
        path = app_data_dir() / "settings.json"
        path.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def temp_dir(self) -> Path:
        p = Path(self.temp_path) if self.temp_path else Path(os.environ.get("TEMP", "/tmp")) / "BlackGitIran" / "upload-one-time"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def project_dir(self) -> Path | None:
        if self.project_path and Path(self.project_path).exists():
            return Path(self.project_path)
        return None

    @property
    def backup_dir(self) -> Path:
        p = app_data_dir() / "backups"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def browser_profile_dir(self) -> Path:
        p = app_data_dir() / "browser-profile"
        p.mkdir(parents=True, exist_ok=True)
        return p
