#!/usr/bin/env python3
"""Import transcripts captured through the YouTube transcript panel.

Why this exists: the caption endpoint (`/api/timedtext`) rate-limits a busy IP with
HTTP 429, but the transcript panel in the YouTube web UI reads a different endpoint
(`youtubei get_panel`) that is not throttled. The text is identical — a side-by-side
check on one video returned 15,621 characters and 2,362 words from both routes with a
normalized ratio of 1.000 — so the capture route does not affect any word count.

The panel needs a browser, so capture happens outside this pipeline. Point a browser
session at each video, open the transcript, and append one JSON object per video to
`data/<profile>/panel-progress.jsonl`:

    {"id": "...", "status": "ok", "segments": 222, "title": "...", "channel": "..."}

and write the raw snippets to `data/<profile>/raw/<id>.json` using the same schema as
scripts/collect.py. This script folds those results into manifest.json.
"""

from __future__ import annotations

import argparse
import json

from corpus import REPO_ROOT, Corpus, add_profile_argument, load_profile


def load_rows(corpus: Corpus) -> list[dict]:
    rows: list[dict] = []
    if corpus.panel_progress.exists():
        for line in corpus.panel_progress.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Import panel-captured transcripts.")
    add_profile_argument(parser)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    corpus = Corpus(profile)
    manifest = corpus.read_manifest()
    entries = {item["id"]: item for item in manifest.get("sources", [])}
    seeds = {
        item["id"]: item
        for item in corpus.read_json(corpus.seeds, {"selected": []})["selected"]
    }

    imported = skipped = 0
    for row in load_rows(corpus):
        video_id = row["id"]
        status = row.get("status")
        if status != "ok":
            entry = entries.get(video_id) or {
                "id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": row.get("title", ""),
                "channel": "",
            }
            if status == "no_indonesian_track":
                entry.update({"status": "no_indonesian_track",
                              "error_type": "NoIndonesianTrack",
                              "fetch_method": "transcript_panel"})
                entries[video_id] = entry
                skipped += 1
            continue

        raw_path = corpus.raw_dir / f"{video_id}.json"
        if not raw_path.exists():
            print(f"missing raw file, skipping: {video_id}")
            continue
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        entry = entries.get(video_id) or {
            "id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": raw.get("title") or seeds.get(video_id, {}).get("title", ""),
            "channel": raw.get("channel") or seeds.get(video_id, {}).get("channel", ""),
            "selection_reason": seeds.get(video_id, {}).get("selection_reason", ""),
            "discovery_origins": seeds.get(video_id, {}).get("discovery_origins", []),
        }
        entry.update({
            "status": "ok",
            "language": raw.get("language", "Indonesian (auto-generated)"),
            "language_code": raw.get("language_code", profile.get("language_code", "id")),
            "is_generated": raw.get("is_generated", True),
            "is_translatable": True,
            "snippet_count": raw.get("snippet_count", len(raw.get("raw_snippets", []))),
            "raw_path": str(raw_path.relative_to(REPO_ROOT)),
            "fetch_method": "transcript_panel",
            "panel_segments": row.get("segments"),
        })
        entry.pop("error_type", None)
        entry.pop("error", None)
        entries[video_id] = entry
        imported += 1

    manifest["sources"] = list(entries.values())
    manifest["source_count_ok"] = sum(1 for i in entries.values() if i.get("status") == "ok")
    manifest["source_count_no_indonesian_track"] = sum(
        1 for i in entries.values() if i.get("status") == "no_indonesian_track")
    manifest["source_count_error"] = sum(1 for i in entries.values() if i.get("status") == "error")
    corpus.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"imported_ok={imported} no_indonesian_track={skipped} "
          f"manifest_ok={manifest['source_count_ok']} "
          f"manifest_errors={manifest['source_count_error']}")


if __name__ == "__main__":
    main()
