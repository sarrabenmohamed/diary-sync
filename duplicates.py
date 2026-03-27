import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class PhotoAsset:
    uuid: str
    path: Path
    original_filename: str
    creation_date: datetime


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(
    assets: list[PhotoAsset],
) -> tuple[list[PhotoAsset], list[PhotoAsset]]:
    """
    Group assets by SHA-256 hash.
    Within each group keep the oldest (tie-break: alphabetical original_filename).
    Returns (to_keep, to_trash).
    """
    from collections import defaultdict

    groups: dict[str, list[PhotoAsset]] = defaultdict(list)
    for asset in assets:
        h = sha256(asset.path)
        groups[h].append(asset)

    to_keep: list[PhotoAsset] = []
    to_trash: list[PhotoAsset] = []

    for group in groups.values():
        if len(group) == 1:
            to_keep.append(group[0])
        else:
            sorted_group = sorted(
                group, key=lambda a: (a.creation_date, a.original_filename)
            )
            to_keep.append(sorted_group[0])
            to_trash.extend(sorted_group[1:])

    return to_keep, to_trash
