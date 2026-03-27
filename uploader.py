import hashlib
from datetime import datetime
from pathlib import Path

from webdav4.client import Client


def _remote_sha256(client: Client, remote_path: str) -> str:
    h = hashlib.sha256()
    with client.open(remote_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_remote_path(creation_date: datetime, original_filename: str) -> str:
    month_dir = creation_date.strftime("%Y-%m")
    date_prefix = creation_date.strftime("%Y-%m-%d_%H-%M-%S")
    return f"/DiaryEntries/{month_dir}/{date_prefix}_{original_filename}"


class WebDAVUploader:
    def __init__(self, url: str, username: str, password: str):
        self._client = Client(url, auth=(username, password))

    def upload(
        self,
        local_path: Path,
        remote_path: str,
        local_sha256: str,
    ) -> bool | None:
        """
        Upload a file and verify integrity via SHA-256.

        Returns:
            True   — uploaded and verified
            None   — skipped (already exists with matching size)
            False  — upload failed or checksum mismatch
        """
        # Idempotency: skip if remote exists and size matches
        if self._client.exists(remote_path):
            info = self._client.info(remote_path)
            remote_size = info.get("content_length") or info.get("size", -1)
            local_size = local_path.stat().st_size
            if remote_size == local_size:
                return None  # SKIP_EXISTS

        # Ensure the parent directory exists
        parent = str(Path(remote_path).parent)
        if not self._client.exists(parent):
            self._mkdir_p(parent)

        # Upload
        self._client.upload_file(str(local_path), remote_path, overwrite=True)

        # Verify checksum
        remote_hash = _remote_sha256(self._client, remote_path)
        return remote_hash == local_sha256

    def _mkdir_p(self, path: str) -> None:
        """Create directory and all parents."""
        parts = [p for p in path.strip("/").split("/") if p]
        current = ""
        for part in parts:
            current += f"/{part}"
            if not self._client.exists(current):
                self._client.mkdir(current)
