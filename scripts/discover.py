#!/usr/bin/env python3
"""Discover candidate uploads for a corpus profile.

Runs the profile's discovery queries through yt-dlp, keeps the uploads whose titles
look like the kind of material the profile wants, and writes the seed list that
scripts/collect.py consumes.

    profiles/<name>.json  ->  data/<name>/discovery.json
                          ->  data/<name>/candidate-seeds.json

Discovery is metadata-only: yt-dlp reads playlists and search results, and never
downloads media or subtitles.
"""

from __future__ import annotations

import argparse
import json
import re
import time

import yt_dlp

from corpus import Corpus, add_profile_argument, load_profile


def run_query(target: str, limit: int) -> list[dict]:
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "playlistend": limit,
        "noplaylist": False,
    }
    with yt_dlp.YoutubeDL(options) as ydl:  # type: ignore[arg-type]
        info = ydl.extract_info(target, download=False)
    entries = info.get("entries") or []
    rows = []
    for entry in entries:
        if not entry or not entry.get("id"):
            continue
        rows.append({
            "id": entry["id"],
            "title": entry.get("title") or "",
            "channel": entry.get("channel") or entry.get("uploader") or "",
            "duration": entry.get("duration"),
            "view_count": entry.get("view_count"),
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover candidates for one corpus profile.")
    add_profile_argument(parser)
    parser.add_argument("--limit", type=int, default=None,
                        help="Uploads to read per query (default from the profile, else 100).")
    parser.add_argument("--sleep", type=float, default=2.0)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    corpus = Corpus(profile)
    discovery = profile["discovery"]
    limit = args.limit or discovery.get("max_per_query", 100)

    queries = list(discovery["queries"]) + list(discovery.get("extra_searches", []))
    filters = profile["title_filters"]
    speech_re = re.compile(filters["speech_required"])
    speaker_re = re.compile(filters["speaker_required"])
    exclude_res = [
        re.compile(filters["exclude_other_speakers"]),
        re.compile(filters["exclude_commentary"]),
    ]
    official = [c.casefold().strip() for c in profile["source_tiers"]["official_channel_exact"]]
    official_anywhere = [c.casefold() for c in profile["source_tiers"]["official_channel_or_title"]]
    signal_label = profile["policy_signals"]["label"].casefold()

    all_rows: dict[str, dict] = {}
    for query in queries:
        label = query["label"]
        print(f"query {label}: {query['target']}")
        try:
            rows = run_query(query["target"], limit)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED {type(exc).__name__}: {str(exc)[:120]}")
            continue
        print(f"  {len(rows)} uploads")
        for row in rows:
            record = all_rows.setdefault(row["id"], {**row, "discovery_origins": []})
            if label not in record["discovery_origins"]:
                record["discovery_origins"].append(label)
        time.sleep(args.sleep)

    candidates = []
    for record in all_rows.values():
        title = record["title"]
        if not speech_re.search(title) or not speaker_re.search(title):
            continue
        if any(pattern.search(title) for pattern in exclude_res):
            continue
        channel = record["channel"].casefold().strip()
        is_official = any(name == channel for name in official) or any(
            name in f"{record['channel']} {title}".casefold() for name in official_anywhere
        )
        score = 0
        reason = "speech_candidate"
        if is_official:
            score += 3
            reason = "official_channel_candidate"
        if re.search(r"(?i)\bfull\b|\blengkap\b", title):
            score += 2
        if signal_label in title.casefold():
            score += 1
            if reason == "speech_candidate":
                reason = "policy_topic_candidate"
        candidates.append({
            "id": record["id"],
            "title": title,
            "channel": record["channel"],
            "duration": record.get("duration"),
            "view_count": record.get("view_count"),
            "discovery_origins": sorted(record["discovery_origins"]),
            "candidate_score": score,
            "selection_reason": reason,
            "priority": score + len(record["discovery_origins"]),
        })

    candidates.sort(key=lambda row: (-row["priority"], row["title"]))
    max_seeds = discovery.get("max_seeds", 200)
    selected = candidates[:max_seeds]

    corpus.dir.mkdir(parents=True, exist_ok=True)
    corpus.discovery.write_text(
        json.dumps({"queries": queries, "all_rows": list(all_rows.values()),
                    "candidates": candidates}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    corpus.seeds.write_text(
        json.dumps({
            "profile": profile["name"],
            "selected": selected,
            "counts": {
                "queries": len(queries),
                "unique_uploads": len(all_rows),
                "candidates": len(candidates),
                "seeds": len(selected),
            },
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"unique_uploads={len(all_rows)} candidates={len(candidates)} seeds={len(selected)}")
    print(f"wrote {corpus.discovery.name} and {corpus.seeds.name}")


if __name__ == "__main__":
    main()
