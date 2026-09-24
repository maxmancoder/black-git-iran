from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable


StatusCb = Callable[[str], None]


class TransportError(Exception):
    pass


class NotLoggedInError(TransportError):
    pass


class Transport(ABC):
    """Each transport (Rubika / LAN / USB...) implements this interface."""

    @abstractmethod
    def download(
        self,
        filename: str,
        dest_dir: Path,
        on_status: StatusCb | None = None,
    ) -> Path:
        """Find `filename` in remote channel/group and save it into dest_dir."""

    @abstractmethod
    def upload(
        self,
        file_path: Path,
        on_status: StatusCb | None = None,
    ) -> None:
        """Send file to remote channel/group."""

    @abstractmethod
    def test_connection(self, on_status: StatusCb | None = None) -> bool:
        ...

    def close(self) -> None:
        pass
