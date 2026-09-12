#!/usr/bin/env python3
"""Report which candidates for a corpus profile still have no transcript, and why."""

from __future__ import annotations

import argparse
import json
from collections import Counter

from corpus import Corpus, add_profile_argument, load_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="List pending candidates for one profile.")
    add_profile_argument(parser)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    corpus = Corpus(profile)
    seeds = corpus.read_json(corpus.seeds, {"selected": []})["selected"]
    metadata = corpus.read_json(corpus.metadata, {})
    manifest = corpus.read_manifest()

    entries = {entry["id"]: entry for entry in manifest.get("sources", [])}
    pending = []
    for seed in seeds:
        video_id = seed["id"]
        entry = entries.get(video_id)
        if entry is None:
            reason = "never_attempted"
        elif entry.get("status") == "ok":
            continue
        elif entry.get("status") == "no_indonesian_track":
            reason = "no_indonesian_track"
        else:
            reason = entry.get("error_type", entry.get("status", "unknown"))
        meta = metadata.get(video_id, {})
        pending.append({
            "id": video_id,
            "reason": reason,
            "date": meta.get("upload_date", ""),
            "channel": meta.get("channel", ""),
            "title": meta.get("title", seed.get("title", "")),
        })

    ok = sum(1 for entry in entries.values() if entry.get("status") == "ok")
    print(f"profile={profile['name']} seeds={len(seeds)} ok={ok} pending={len(pending)}")
    print(Counter(item["reason"] for item in pending))
    for item in pending:
        print(f'  {item["reason"]:<20} {item["id"]}  {item["date"]}  {item["title"][:70]}')

    corpus.pending.write_text(
        json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
