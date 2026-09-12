#!/usr/bin/env python3
"""Fill metadata.json for a corpus profile using yt-dlp.

The caption endpoint rate-limits requests, but yt-dlp can still read the watch
page and player API JSON — only the subtitle request is refused. This fills in
upload date, channel, title, and duration for any seed that has no metadata yet.
"""

from __future__ import annotations

import argparse
import json
import time

import yt_dlp

from corpus import Corpus, add_profile_argument, load_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch metadata for one corpus profile.")
    add_profile_argument(parser)
    parser.add_argument("--sleep", type=float, default=1.0)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    corpus = Corpus(profile)
    metadata = corpus.read_json(corpus.metadata, {})
    seeds = corpus.read_json(corpus.seeds, {"selected": []})["selected"]
    targets = [seed["id"] for seed in seeds if seed["id"] not in metadata]
    print(f"profile={profile['name']} missing_metadata={len(targets)}")
    if not targets:
        return

    options: dict = {
        "quiet": True, "no_warnings": True, "skip_download": True,
        "extract_flat": False, "noplaylist": True,
    }
    filled, failed = 0, []
    with yt_dlp.YoutubeDL(options) as ydl:  # type: ignore[arg-type]
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
                    "metadata_status": "ok",
                }
                filled += 1
                print(f"OK   {index}/{len(targets)} {video_id} "
                      f"{metadata[video_id]['upload_date']} {metadata[video_id]['title'][:50]}")
            except Exception as exc:  # noqa: BLE001
                failed.append(video_id)
                print(f"FAIL {index}/{len(targets)} {video_id} "
                      f"{type(exc).__name__}: {str(exc)[:110]}")
            corpus.metadata.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            time.sleep(args.sleep)

    print(f"filled={filled} failed={len(failed)} {failed[:8]}")


if __name__ == "__main__":
    main()
