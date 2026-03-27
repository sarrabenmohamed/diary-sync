# diary-sync

A Python CLI tool that:

1. **Syncs diary videos** — finds videos in your Apple Photos library longer than 10 minutes and uploads them to TUM Sync+Share (WebDAV), then moves the originals to the Photos trash.
2. **Cleans duplicate photos** — detects exact duplicate pictures by SHA-256 hash, keeps the oldest copy, and moves the rest to the Photos trash.

Nothing is permanently deleted — everything goes to the Photos trash, which you empty manually.

---

## Requirements

- macOS 13 Ventura or later
- Python 3.11+
- [ffprobe](https://ffmpeg.org/download.html) is **not** required — duration is read via `osxphotos`

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp config.toml.example config.toml
```

Edit `config.toml`:

```toml
[sync_share]
url = "https://syncandshare.lrz.de/remote.php/dav/files/YOUR_TUM_USERNAME/"
username = "your-tum-username"
password = "your-app-password"   # generate an App Password in Sync+Share settings

[thresholds]
min_video_duration_minutes = 10
```

> **App Password:** log in to TUM Sync+Share → Settings → Security → create an App Password. Do not use your TUM password directly.

`config.toml` is gitignored and will never be committed.

---

## Usage

```bash
# Always preview first
python diary_sync.py --dry-run

# Preview one routine at a time
python diary_sync.py --dry-run --videos-only
python diary_sync.py --dry-run --dupes-only

# Run for real
python diary_sync.py                  # both routines
python diary_sync.py --videos-only    # diary videos only
python diary_sync.py --dupes-only     # duplicate photos only
```

---

## How it works

### Diary videos routine

1. Scans your Photos library for all videos longer than the configured threshold.
2. Skips videos not downloaded from iCloud (logs `SKIP_NOT_LOCAL`).
3. Uploads each qualifying video to Sync+Share at:
   ```
   /DiaryEntries/<YYYY-MM>/<YYYY-MM-DD_HH-MM-SS>_<original_filename>
   ```
4. Verifies the upload via SHA-256 checksum (not just file size).
5. Moves the original to Photos trash **only after** the upload is verified.
6. Already-uploaded files are skipped on re-runs (safe to run repeatedly).

### Duplicate photos routine

1. Scans your Photos library for all photos.
2. Groups photos by SHA-256 hash.
3. Within each group of duplicates, keeps the **oldest** (tie-break: alphabetical filename).
4. Moves all duplicates to Photos trash.

---

## Logging

Every run appends to `run.log` in the project directory:

```
[2026-03-25 14:02:11] RUN START  mode=both  dry_run=False
[2026-03-25 14:02:15] UPLOAD OK       holiday.mov → /DiaryEntries/2024-08/
[2026-03-25 14:02:15] TRASH           holiday.mov
[2026-03-25 14:02:20] DUPE TRASH      photo_copy.heic (kept: photo.heic)
[2026-03-25 14:02:20] RUN END VIDEOS  uploaded=1 skipped=0 failed=0
[2026-03-25 14:02:20] RUN END DUPES   trashed=3 skipped=0
[2026-03-25 14:02:20] DONE
```

---

## File structure

```
diary-sync/
├── diary_sync.py        ← entry point
├── scanner.py           ← reads Photos library via osxphotos
├── uploader.py          ← WebDAV client for TUM Sync+Share
├── cleaner.py           ← moves files to Photos trash via AppleScript
├── duplicates.py        ← SHA-256 duplicate detection
├── reporter.py          ← logging to console + run.log
├── config.toml          ← your credentials (gitignored)
├── config.toml.example  ← template
└── requirements.txt
```

---

## Known limitations

- **iCloud-optimized assets** (not fully downloaded) are skipped — the script does not force-download them.
- **Partial run recovery:** if the script crashes mid-run, already-trashed originals won't be re-processed on the next run. They are recoverable from the Photos trash until you empty it.
- Log rotation is not built in — manage `run.log` size manually.
