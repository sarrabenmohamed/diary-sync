from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class VideoAsset:
    uuid: str
    path: Path | None   # None = not downloaded from iCloud
    original_filename: str
    creation_date: datetime
    duration_seconds: float


@dataclass
class PhotoAsset:
    uuid: str
    path: Path | None   # None = not downloaded from iCloud
    original_filename: str
    creation_date: datetime


def scan_videos(min_duration_seconds: float) -> list[VideoAsset]:
    import osxphotos

    db = osxphotos.PhotosDB()
    assets = []
    for photo in db.photos(movies=True):
        if not photo.ismovie:
            continue
        duration = photo.duration or 0.0
        if duration <= min_duration_seconds:
            continue
        path = Path(photo.path) if photo.path else None
        assets.append(
            VideoAsset(
                uuid=photo.uuid,
                path=path,
                original_filename=photo.original_filename,
                creation_date=photo.date,
                duration_seconds=duration,
            )
        )
    return assets


def scan_photos() -> list[PhotoAsset]:
    import osxphotos

    db = osxphotos.PhotosDB()
    assets = []
    for photo in db.photos(movies=False):
        if photo.ismovie:
            continue
        path = Path(photo.path) if photo.path else None
        assets.append(
            PhotoAsset(
                uuid=photo.uuid,
                path=path,
                original_filename=photo.original_filename,
                creation_date=photo.date,
            )
        )
    return assets
