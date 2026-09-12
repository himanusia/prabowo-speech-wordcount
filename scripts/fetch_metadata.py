#!/usr/bin/env python3
"""Fill metadata.json for pending candidates.

The 429 that blocks caption downloads does not block metadata: yt-dlp can still
read the watch page and player API JSON, only the subtitle request is refused.
This fills the gaps left when an earlier metadata pass failed, so the panel
collector and the analyzer both have title/channel/upload date to work with.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import yt_dlp

ROOT = Path(__file__).resolve().parents[1]
EXPANDED = ROOT / "data" / "expanded"
METADATA_PATH = EXPANDED / "metadata.json"
PENDING_PATH = EXPANDED / "pending.json"

FIELDS = ("id", "upload_date", "channel", "title", "duration")


def main() -> None:
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    pending = json.loads(PENDING_PATH.read_text(encoding="utf-8"))
    targets = [
        item["id"]
        for item in pending
        if item["reason"] in {"IpBlocked", "never_attempted"} and item["id"] not in metadata
    ]
    print(f"missing_metadata={len(targets)}")
    if not targets:
        return

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "noplaylist": True,
    }
    filled = 0
    failed: list[str] = []
    with yt_dlp.YoutubeDL(options) as ydl:
        for index, video_id in enumerate(targets, start=1):
            try:
                info = ydl.extract_info(
                    f"https://www.youtube.com/watch?v={video_id}", download=False
                )
                metadata[video_id] = {
                    "id": video_id,
                    "upload_date": info.get("upload_date") or "",
                    "channel": info.get("channel") or info.get("uploader") or "",
                    "title": info.get("title") or "",
                    "duration": info.get("duration"),
                    "seed": metadata.get(video_id, {}).get("seed"),
                    "metadata_status": "ok",
                }
                filled += 1
                print(f"OK   {index}/{len(targets)} {video_id} {metadata[video_id]['upload_date']} {metadata[video_id]['title'][:50]}")
            except Exception as exc:  # noqa: BLE001
                failed.append(video_id)
                print(f"FAIL {index}/{len(targets)} {video_id} {type(exc).__name__}: {str(exc)[:110]}")
            METADATA_PATH.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            time.sleep(1.0)

    print(f"filled={filled} failed={len(failed)} {failed[:8]}")


if __name__ == "__main__":
    main()
