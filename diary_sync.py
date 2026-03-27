#!/usr/bin/env python3
"""
diary_sync.py — iCloud diary sync and duplicate photo cleaner.

Usage:
    python diary_sync.py --dry-run                 # preview both routines
    python diary_sync.py --dry-run --videos-only   # preview diary entries only
    python diary_sync.py --dry-run --dupes-only    # preview duplicate cleanup only
    python diary_sync.py --videos-only             # run diary entries for real
    python diary_sync.py --dupes-only              # run duplicate cleanup for real
    python diary_sync.py                           # run everything for real
"""
import argparse
import logging
import sys
import tomllib
from pathlib import Path

from cleaner import move_to_photos_trash
from duplicates import PhotoAsset, find_duplicates, sha256
from reporter import setup_logger
from scanner import scan_photos, scan_videos
from uploader import WebDAVUploader, build_remote_path

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.toml"
LOG_PATH = BASE_DIR / "run.log"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(
            f"ERROR: config.toml not found at {CONFIG_PATH}\n"
            f"Copy config.toml.example to config.toml and fill in your credentials.",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def run_videos(
    uploader: WebDAVUploader | None,
    logger: logging.Logger,
    dry_run: bool,
    min_duration_minutes: float,
) -> None:
    min_secs = min_duration_minutes * 60
    logger.info("Scanning Photos library for videos...")
    videos = scan_videos(min_secs)
    logger.info(f"Found {len(videos)} video(s) longer than {min_duration_minutes:.0f} min")

    uploaded = skipped = failed = 0

    for video in videos:
        name = video.original_filename

        if video.path is None:
            logger.info(f"SKIP_NOT_LOCAL  {name}  (not downloaded from iCloud)")
            skipped += 1
            continue

        remote_path = build_remote_path(video.creation_date, name)

        if dry_run:
            duration_min = video.duration_seconds / 60
            logger.info(
                f"DRY_RUN UPLOAD  {name}  ({duration_min:.1f} min) → {remote_path}"
            )
            continue

        local_hash = sha256(video.path)
        result = uploader.upload(video.path, remote_path, local_hash)

        if result is None:
            logger.info(f"SKIP_EXISTS     {name}")
            skipped += 1
        elif result is True:
            logger.info(f"UPLOAD OK       {name} → {remote_path}")
            if move_to_photos_trash(video.uuid):
                logger.info(f"TRASH           {name}")
            else:
                logger.warning(f"TRASH_FAIL      {name}  (uploaded but could not trash)")
            uploaded += 1
        else:
            logger.error(f"UPLOAD_FAIL     {name}  (checksum mismatch after upload)")
            failed += 1

    logger.info(f"RUN END VIDEOS  uploaded={uploaded} skipped={skipped} failed={failed}")


def run_dupes(logger: logging.Logger, dry_run: bool) -> None:
    logger.info("Scanning Photos library for duplicate photos...")
    raw_photos = scan_photos()

    local_photos = []
    skipped = 0

    for p in raw_photos:
        if p.path is None:
            logger.info(f"SKIP_NOT_LOCAL  {p.original_filename}  (not downloaded from iCloud)")
            skipped += 1
        else:
            local_photos.append(
                PhotoAsset(
                    uuid=p.uuid,
                    path=p.path,
                    original_filename=p.original_filename,
                    creation_date=p.creation_date,
                )
            )

    logger.info(
        f"Hashing {len(local_photos)} local photo(s) to detect duplicates..."
    )
    _, to_trash = find_duplicates(local_photos)
    logger.info(f"Found {len(to_trash)} duplicate(s)")

    trashed = 0
    for asset in to_trash:
        if dry_run:
            logger.info(f"DRY_RUN DUPE    {asset.original_filename}")
            continue
        if move_to_photos_trash(asset.uuid):
            logger.info(f"DUPE TRASH      {asset.original_filename}")
            trashed += 1
        else:
            logger.warning(f"TRASH_FAIL      {asset.original_filename}")

    logger.info(f"RUN END DUPES   trashed={trashed} skipped={skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync diary videos to TUM Sync+Share and clean duplicate photos."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without uploading or deleting anything.",
    )
    parser.add_argument(
        "--videos-only",
        action="store_true",
        help="Run only the diary videos routine.",
    )
    parser.add_argument(
        "--dupes-only",
        action="store_true",
        help="Run only the duplicate photos routine.",
    )
    args = parser.parse_args()

    if args.videos_only and args.dupes_only:
        print("ERROR: --videos-only and --dupes-only are mutually exclusive.", file=sys.stderr)
        sys.exit(1)

    logger = setup_logger(LOG_PATH)
    mode = "videos" if args.videos_only else "dupes" if args.dupes_only else "both"
    logger.info(f"RUN START  mode={mode}  dry_run={args.dry_run}")

    config = load_config()

    run_videos_routine = not args.dupes_only
    run_dupes_routine = not args.videos_only

    uploader = None
    if run_videos_routine and not args.dry_run:
        sync = config["sync_share"]
        uploader = WebDAVUploader(sync["url"], sync["username"], sync["password"])

    if run_videos_routine:
        min_min = config["thresholds"]["min_video_duration_minutes"]
        run_videos(uploader, logger, args.dry_run, min_min)

    if run_dupes_routine:
        run_dupes(logger, args.dry_run)

    logger.info("DONE")


if __name__ == "__main__":
    main()
