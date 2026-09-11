from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "expanded" / "candidate-seeds.json"
RAW_DIR = ROOT / "data" / "expanded" / "raw"
MANIFEST_PATH = ROOT / "data" / "expanded" / "manifest.json"


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        "generated_at": None,
        "language_requested": "id",
        "sources": [],
    }


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def choose_indonesian_track(api: YouTubeTranscriptApi, video_id: str):
    tracks = list(api.list(video_id))
    candidates = [track for track in tracks if track.language_code.startswith("id")]
    if not candidates:
        return None, tracks
    manual = [track for track in candidates if not track.is_generated]
    return (manual or candidates)[0], tracks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.35)
    args = parser.parse_args()

    seeds = json.loads(SEED_PATH.read_text(encoding="utf-8"))["selected"]
    selected = seeds[args.offset : args.offset + args.limit if args.limit else None]
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest()
    entries = {item["id"]: item for item in manifest.get("sources", [])}
    api = YouTubeTranscriptApi()

    for index, seed in enumerate(selected, start=args.offset + 1):
        video_id = seed["id"]
        if entries.get(video_id, {}).get("status") == "ok":
            print(f"SKIP {index}/{len(seeds)} {video_id}: already fetched")
            continue

        entry = {
            "id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": seed.get("title", ""),
            "channel": seed.get("channel", ""),
            "selection_reason": seed.get("selection_reason", ""),
            "discovery_origins": seed.get("discovery_origins", []),
        }
        try:
            track, available = choose_indonesian_track(api, video_id)
            entry["available_tracks"] = [
                {
                    "language": item.language,
                    "language_code": item.language_code,
                    "is_generated": item.is_generated,
                    "is_translatable": item.is_translatable,
                }
                for item in available
            ]
            if track is None:
                entry.update({
                    "status": "no_indonesian_track",
                    "error_type": "NoIndonesianTrack",
                })
            else:
                fetched = track.fetch()
                snippets = fetched.to_raw_data()
                raw = {
                    **entry,
                    "status": "ok",
                    "language": fetched.language,
                    "language_code": fetched.language_code,
                    "is_generated": fetched.is_generated,
                    "is_translatable": track.is_translatable,
                    "snippet_count": len(snippets),
                    "raw_snippets": snippets,
                }
                raw_path = RAW_DIR / f"{video_id}.json"
                raw_path.write_text(
                    json.dumps(raw, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                entry.update({
                    "status": "ok",
                    "language": fetched.language,
                    "language_code": fetched.language_code,
                    "is_generated": fetched.is_generated,
                    "is_translatable": track.is_translatable,
                    "snippet_count": len(snippets),
                    "raw_path": str(raw_path.relative_to(ROOT)),
                })
            print(
                f"{entry['status'].upper()} {index}/{len(seeds)} {video_id} "
                f"{entry.get('snippet_count', 0)} snippets"
            )
        except Exception as exc:
            entry.update({
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc)[:500],
            })
            print(
                f"ERROR {index}/{len(seeds)} {video_id} "
                f"{entry['error_type']}: {entry['error']}"
            )

        entries[video_id] = entry
        manifest["sources"] = list(entries.values())
        save_manifest(manifest)
        time.sleep(args.sleep)

    manifest["source_count_requested"] = len(seeds)
    manifest["source_count_ok"] = sum(
        item.get("status") == "ok" for item in entries.values()
    )
    manifest["source_count_no_indonesian_track"] = sum(
        item.get("status") == "no_indonesian_track" for item in entries.values()
    )
    manifest["source_count_error"] = sum(
        item.get("status") == "error" for item in entries.values()
    )
    save_manifest(manifest)
    print(
        f"fetched_ok={manifest['source_count_ok']} "
        f"no_id={manifest['source_count_no_indonesian_track']} "
        f"errors={manifest['source_count_error']}"
    )


if __name__ == "__main__":
    main()
