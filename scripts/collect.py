#!/usr/bin/env python3
"""Fetch Indonesian caption tracks for a corpus profile.

YouTube rate limits the caption endpoint after a burst. `--stop-on-block` exits at
the first HTTP 429 instead of grinding through cooldowns, and every failure is
recorded in the manifest rather than dropped. When the endpoint refuses, capture
the remaining videos through the transcript panel instead and import them with
scripts/import_panel.py — the text is identical (see README).
"""

from __future__ import annotations

import argparse
import json
import time

from corpus import REPO_ROOT, Corpus, add_profile_argument, load_profile
from youtube_transcript_api import YouTubeTranscriptApi


def choose_track(api: YouTubeTranscriptApi, video_id: str, language_code: str):
    tracks = list(api.list(video_id))
    candidates = [t for t in tracks if t.language_code.startswith(language_code)]
    if not candidates:
        return None, tracks
    manual = [t for t in candidates if not t.is_generated]
    return (manual or candidates)[0], tracks


def load_pending_ids(corpus: Corpus, reasons: set[str]) -> list[str]:
    items = corpus.read_json(corpus.pending, [])
    return [item["id"] for item in items if item["reason"] in reasons]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch captions for one corpus profile.")
    add_profile_argument(parser)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.35)
    parser.add_argument("--ids", default=None, help="Comma-separated video ids instead of a seed slice.")
    parser.add_argument("--only-pending", action="store_true",
                        help="Fetch only ids present in pending.json.")
    parser.add_argument("--pending-reasons", default="IpBlocked,never_attempted",
                        help="Comma-separated pending reasons to include with --only-pending.")
    parser.add_argument("--pause-every", type=int, default=0,
                        help="Insert --pause-for seconds after every N videos (0 disables).")
    parser.add_argument("--pause-for", type=float, default=60.0)
    parser.add_argument("--stop-on-block", action="store_true",
                        help="Exit at the first IpBlocked instead of cooling down.")
    args = parser.parse_args()

    profile = load_profile(args.profile)
    corpus = Corpus(profile)
    language_code = profile.get("language_code", "id")
    seeds = corpus.read_json(corpus.seeds, {"selected": []})["selected"]
    by_id = {seed["id"]: seed for seed in seeds}

    if args.only_pending:
        wanted = load_pending_ids(corpus, set(args.pending_reasons.split(",")))
        order = {seed["id"]: index for index, seed in enumerate(seeds)}
        wanted.sort(key=lambda vid: order.get(vid, len(seeds)))
        selected = [by_id[vid] for vid in wanted if vid in by_id]
    elif args.ids:
        selected = [
            by_id[vid]
            for vid in (item.strip() for item in args.ids.split(","))
            if vid in by_id
        ]
    else:
        selected = seeds[args.offset: args.offset + args.limit if args.limit else None]

    corpus.ensure_dirs()
    manifest = corpus.read_manifest()
    entries = {item["id"]: item for item in manifest.get("sources", [])}
    api = YouTubeTranscriptApi()
    print(f"profile={profile['name']} targets={len(selected)} sleep={args.sleep}")

    for index, seed in enumerate(selected, start=1):
        video_id = seed["id"]
        if entries.get(video_id, {}).get("status") == "ok":
            print(f"SKIP {index}/{len(selected)} {video_id}: already fetched")
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
            track, available = choose_track(api, video_id, language_code)
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
                entry.update({"status": "no_indonesian_track", "error_type": "NoIndonesianTrack"})
            else:
                fetched = track.fetch()
                snippets = fetched.to_raw_data()
                raw_path = corpus.raw_dir / f"{video_id}.json"
                raw_path.write_text(
                    json.dumps({**entry, "status": "ok", "language": fetched.language,
                                "language_code": fetched.language_code,
                                "is_generated": fetched.is_generated,
                                "is_translatable": track.is_translatable,
                                "fetch_method": "caption_api",
                                "snippet_count": len(snippets),
                                "raw_snippets": snippets}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                entry.update({
                    "status": "ok",
                    "language": fetched.language,
                    "language_code": fetched.language_code,
                    "is_generated": fetched.is_generated,
                    "is_translatable": track.is_translatable,
                    "fetch_method": "caption_api",
                    "snippet_count": len(snippets),
                    "raw_path": str(raw_path.relative_to(REPO_ROOT)),
                })
            print(f"{entry['status'].upper()} {index}/{len(selected)} {video_id} "
                  f"{entry.get('snippet_count', 0)} snippets")
        except Exception as exc:  # noqa: BLE001
            entry.update({"status": "error", "error_type": type(exc).__name__,
                          "error": str(exc)[:500]})
            print(f"ERROR {index}/{len(selected)} {video_id} {entry['error_type']}")

        entries[video_id] = entry
        manifest["sources"] = list(entries.values())
        manifest["source_count_ok"] = sum(1 for i in entries.values() if i.get("status") == "ok")
        manifest["source_count_no_indonesian_track"] = sum(
            1 for i in entries.values() if i.get("status") == "no_indonesian_track")
        manifest["source_count_error"] = sum(1 for i in entries.values() if i.get("status") == "error")
        corpus.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        if entry.get("error_type") == "IpBlocked":
            if args.stop_on_block:
                print("STOP: IpBlocked, exiting to avoid burning the block further")
                break
            print(f"COOLDOWN {args.pause_for * 3:.0f}s after IpBlocked")
            time.sleep(args.pause_for * 3)
        elif args.pause_every and index % args.pause_every == 0:
            print(f"PAUSE {args.pause_for:.0f}s after {index} videos")
            time.sleep(args.pause_for)
        else:
            time.sleep(args.sleep)

    print(f"fetched_ok={manifest['source_count_ok']} "
          f"no_track={manifest['source_count_no_indonesian_track']} "
          f"errors={manifest['source_count_error']}")


if __name__ == "__main__":
    main()
